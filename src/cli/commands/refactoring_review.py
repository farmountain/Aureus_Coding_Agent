"""
Phase 4 — Refactoring & Review Commands

Commands for safe multi-file refactoring, code review, and environment validation.
"""

import argparse
import ast
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from src.governance.policy import PolicyLoader
from src.infrastructure.repository_indexer import RepositoryIndexer
from src.cli.base_command import BaseCommand


class RefactorCommand(BaseCommand):
    """Multi-file refactoring with safety checks and rollback support."""
    
    def __init__(self, project_root: Optional[Path] = None, verbose: bool = False, dry_run: bool = False):
        super().__init__(project_root=project_root, verbose=verbose, dry_run=dry_run)
        self.indexer = RepositoryIndexer(str(self.project_root))
        self.backup_dir = self.project_root / ".aureus_backup"
        self.changes: List[Dict] = []
    
    def execute(self, args: Optional[argparse.Namespace] = None) -> Dict:
        """Execute refactoring command."""
        if not args:
            return self._format_error(ValueError("Missing arguments"), "Refactoring")
        
        self._verbose_print(f"Starting refactoring operation: {args.operation}")
        
        if args.operation == "rename":
            return self._handle_execution(
                self._rename_symbol, args.old_name, args.new_name, args.preview, args.scope,
                context="Rename operation"
            )
        elif args.operation == "move":
            return self._handle_execution(
                self._move_symbol, args.symbol, args.target_file, args.preview,
                context="Move operation"
            )
        elif args.operation == "extract":
            return self._handle_execution(
                self._extract_function, args.source, args.function_name, args.preview,
                context="Extract operation"
            )
        else:
            return self._format_error(ValueError(f"Unknown operation: {args.operation}"), "Refactoring")
    
    def _rename_symbol(self, old_name: str, new_name: str, preview: bool, scope: Optional[str]) -> Dict:
        """Rename a symbol across multiple files."""
        print(f"[*] Analyzing impact of renaming '{old_name}' to '{new_name}'...")
        
        # Find all usages using the repository indexer
        usages = self._find_all_usages(old_name, scope)
        
        if not usages:
            return {
                "status": "error",
                "message": f"Symbol '{old_name}' not found in the project"
            }
        
        # Assess risk
        risk_level = self._assess_refactoring_risk(len(usages))
        
        print(f"[*] Found {len(usages)} usage(s) across {len(set(u['file'] for u in usages))} file(s)")
        print(f"[*] Risk Level: {risk_level}")
        
        if preview:
            return self._preview_rename(old_name, new_name, usages, risk_level)
        
        # Create backup
        self._create_backup(usages)
        
        # Apply changes
        try:
            modified_files = self._apply_rename(old_name, new_name, usages)
            
            print(f"[+] Successfully renamed '{old_name}' to '{new_name}'")
            print(f"[+] Modified {len(modified_files)} file(s)")
            
            return {
                "status": "success",
                "operation": "rename",
                "old_name": old_name,
                "new_name": new_name,
                "files_modified": len(modified_files),
                "usages_updated": len(usages),
                "risk_level": risk_level,
                "backup_location": str(self.backup_dir)
            }
        except Exception as e:
            print(f"[-] Error during refactoring: {e}")
            print("[*] Rolling back changes...")
            self._rollback()
            return {"status": "error", "message": f"Refactoring failed: {e}. Changes rolled back."}
    
    def _move_symbol(self, symbol: str, target_file: str, preview: bool) -> Dict:
        """Move a symbol (function/class) to another file."""
        print(f"[*] Analyzing move of '{symbol}' to '{target_file}'...")
        
        # Find symbol definition
        definition = self._find_symbol_definition(symbol)
        if not definition:
            return {"status": "error", "message": f"Symbol '{symbol}' not found"}
        
        source_file = definition["file"]
        
        # Check if target file exists
        target_path = self.project_root / target_file
        if not target_path.exists():
            return {"status": "error", "message": f"Target file '{target_file}' does not exist"}
        
        # Find all usages
        usages = self._find_all_usages(symbol)
        
        print(f"[*] Found definition in {source_file}")
        print(f"[*] Found {len(usages)} usage(s)")
        
        if preview:
            return {
                "status": "preview",
                "operation": "move",
                "symbol": symbol,
                "source_file": source_file,
                "target_file": target_file,
                "usages": len(usages),
                "files_affected": len(set(u['file'] for u in usages)) + 2  # +2 for source and target
            }
        
        # Create backup
        affected_files = [source_file, target_file] + [u['file'] for u in usages]
        self._create_backup([{"file": f} for f in set(affected_files)])
        
        try:
            # Extract symbol code
            symbol_code = self._extract_symbol_code(source_file, symbol)
            
            # Add to target file
            self._add_symbol_to_file(target_path, symbol_code)
            
            # Remove from source file
            self._remove_symbol_from_file(source_file, symbol)
            
            # Update imports in all usage files
            self._update_imports_for_move(symbol, source_file, target_file, usages)
            
            print(f"[+] Successfully moved '{symbol}' to '{target_file}'")
            
            return {
                "status": "success",
                "operation": "move",
                "symbol": symbol,
                "source_file": source_file,
                "target_file": target_file,
                "files_modified": len(set(affected_files)),
                "backup_location": str(self.backup_dir)
            }
        except Exception as e:
            print(f"[-] Error during move: {e}")
            print("[*] Rolling back changes...")
            self._rollback()
            return {"status": "error", "message": f"Move failed: {e}. Changes rolled back."}
    
    def _extract_function(self, source: str, function_name: str, preview: bool) -> Dict:
        """Extract selected code into a new function."""
        print(f"[*] Extracting code to new function '{function_name}'...")
        
        # Parse source reference (file:line or file:start-end)
        file_path, line_range = self._parse_source_reference(source)
        
        if not file_path.exists():
            return {"status": "error", "message": f"Source file not found: {file_path}"}
        
        # Read the code to extract
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        start_line, end_line = line_range
        if start_line < 1 or end_line > len(lines):
            return {"status": "error", "message": f"Invalid line range: {start_line}-{end_line}"}
        
        code_to_extract = ''.join(lines[start_line-1:end_line])
        
        # Analyze variables used in the code
        variables = self._analyze_extracted_code_variables(code_to_extract)
        
        if preview:
            return {
                "status": "preview",
                "operation": "extract",
                "function_name": function_name,
                "file": str(file_path.relative_to(self.project_root)),
                "lines": f"{start_line}-{end_line}",
                "parameters": variables.get("parameters", []),
                "return_value": variables.get("returns", None)
            }
        
        # Create backup
        self._create_backup([{"file": str(file_path.relative_to(self.project_root))}])
        
        try:
            # Generate new function
            new_function = self._generate_extracted_function(
                function_name, code_to_extract, variables
            )
            
            # Replace code with function call
            function_call = self._generate_function_call(function_name, variables)
            
            # Update file
            new_lines = (
                lines[:start_line-1] +
                [function_call + '\n'] +
                lines[end_line:]
            )
            
            # Insert function definition (before the calling location)
            insert_line = self._find_function_insert_location(file_path, start_line)
            new_lines = (
                new_lines[:insert_line] +
                [new_function + '\n\n'] +
                new_lines[insert_line:]
            )
            
            # Write back
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            
            print(f"[+] Successfully extracted '{function_name}'")
            
            return {
                "status": "success",
                "operation": "extract",
                "function_name": function_name,
                "file": str(file_path.relative_to(self.project_root)),
                "backup_location": str(self.backup_dir)
            }
        except Exception as e:
            print(f"[-] Error during extraction: {e}")
            print("[*] Rolling back changes...")
            self._rollback()
            return {"status": "error", "message": f"Extraction failed: {e}. Changes rolled back."}
    
    # Helper methods
    
    def _find_all_usages(self, symbol: str, scope: Optional[str] = None) -> List[Dict]:
        """Find all usages of a symbol."""
        usages = []
        search_path = self.project_root / scope if scope else self.project_root
        
        for py_file in search_path.rglob("*.py"):
            if ".aureus" in str(py_file) or "__pycache__" in str(py_file):
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Use AST to find actual symbol usages (not just text matches)
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Name) and node.id == symbol:
                        usages.append({
                            "file": str(py_file.relative_to(self.project_root)),
                            "line": node.lineno,
                            "col": node.col_offset,
                            "type": "usage"
                        })
                    elif isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name == symbol:
                        usages.append({
                            "file": str(py_file.relative_to(self.project_root)),
                            "line": node.lineno,
                            "col": node.col_offset,
                            "type": "definition"
                        })
            except:
                # Fall back to simple text search if AST parsing fails
                for i, line in enumerate(content.splitlines(), 1):
                    if re.search(rf'\b{re.escape(symbol)}\b', line):
                        usages.append({
                            "file": str(py_file.relative_to(self.project_root)),
                            "line": i,
                            "col": 0,
                            "type": "unknown"
                        })
        
        return usages
    
    def _find_symbol_definition(self, symbol: str) -> Optional[Dict]:
        """Find the definition of a symbol."""
        usages = self._find_all_usages(symbol)
        for usage in usages:
            if usage.get("type") == "definition":
                return usage
        return None
    
    def _assess_refactoring_risk(self, usage_count: int) -> str:
        """Assess the risk level of a refactoring operation."""
        if usage_count <= 5:
            return "LOW"
        elif usage_count <= 20:
            return "MEDIUM"
        else:
            return "HIGH"
    
    def _preview_rename(self, old_name: str, new_name: str, usages: List[Dict], risk_level: str) -> Dict:
        """Generate preview of rename operation."""
        files_by_path = {}
        for usage in usages:
            file = usage['file']
            if file not in files_by_path:
                files_by_path[file] = []
            files_by_path[file].append(usage['line'])
        
        print("\n[*] Preview of changes:")
        for file, lines in files_by_path.items():
            print(f"  {file}: lines {', '.join(map(str, sorted(lines)))}")
        
        return {
            "status": "preview",
            "operation": "rename",
            "old_name": old_name,
            "new_name": new_name,
            "usages": len(usages),
            "files_affected": len(files_by_path),
            "risk_level": risk_level,
            "changes": files_by_path
        }
    
    def _create_backup(self, usages: List[Dict]):
        """Create backup of files before modification."""
        if self.backup_dir.exists():
            shutil.rmtree(self.backup_dir)
        self.backup_dir.mkdir(parents=True)
        
        files_to_backup = set(u['file'] for u in usages)
        
        for file in files_to_backup:
            src = self.project_root / file
            if src.exists():
                dst = self.backup_dir / file
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
        
        print(f"[*] Created backup in {self.backup_dir}")
    
    def _apply_rename(self, old_name: str, new_name: str, usages: List[Dict]) -> Set[str]:
        """Apply rename operation to all files."""
        modified_files = set()
        
        # Group usages by file
        files_usages = {}
        for usage in usages:
            file = usage['file']
            if file not in files_usages:
                files_usages[file] = []
            files_usages[file].append(usage)
        
        # Process each file
        for file, file_usages in files_usages.items():
            file_path = self.project_root / file
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Use regex with word boundaries to ensure we're replacing whole symbols
            # Sort by line number descending to avoid offset issues
            new_content = re.sub(
                rf'\b{re.escape(old_name)}\b',
                new_name,
                content
            )
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            modified_files.add(file)
        
        return modified_files
    
    def _rollback(self):
        """Rollback changes using backup."""
        if not self.backup_dir.exists():
            print("[-] No backup found to rollback")
            return
        
        for backup_file in self.backup_dir.rglob("*.py"):
            relative_path = backup_file.relative_to(self.backup_dir)
            original_file = self.project_root / relative_path
            shutil.copy2(backup_file, original_file)
        
        shutil.rmtree(self.backup_dir)
        print("[+] Rollback complete")
    
    def _extract_symbol_code(self, file_path: str, symbol: str) -> str:
        """Extract the code for a symbol from a file."""
        full_path = self.project_root / file_path
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name == symbol:
                # Extract the code for this node
                lines = content.splitlines()
                start = node.lineno - 1
                end = node.end_lineno
                return '\n'.join(lines[start:end])
        
        raise ValueError(f"Symbol '{symbol}' not found in {file_path}")
    
    def _add_symbol_to_file(self, target_path: Path, symbol_code: str):
        """Add symbol code to target file."""
        with open(target_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Add at the end of the file
        with open(target_path, 'w', encoding='utf-8') as f:
            f.write(content.rstrip() + '\n\n\n' + symbol_code + '\n')
    
    def _remove_symbol_from_file(self, file_path: str, symbol: str):
        """Remove symbol from source file."""
        full_path = self.project_root / file_path
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        lines = content.splitlines()
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name == symbol:
                # Remove these lines
                start = node.lineno - 1
                end = node.end_lineno
                new_lines = lines[:start] + lines[end:]
                
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(new_lines) + '\n')
                return
    
    def _update_imports_for_move(self, symbol: str, source_file: str, target_file: str, usages: List[Dict]):
        """Update imports in files that use the moved symbol."""
        # Convert file paths to module paths
        source_module = source_file.replace('/', '.').replace('\\', '.').replace('.py', '')
        target_module = target_file.replace('/', '.').replace('\\', '.').replace('.py', '')
        
        files_to_update = set(u['file'] for u in usages if u['file'] not in [source_file, target_file])
        
        for file in files_to_update:
            file_path = self.project_root / file
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Update import statements
            # from source_module import symbol -> from target_module import symbol
            new_content = re.sub(
                rf'from\s+{re.escape(source_module)}\s+import\s+.*{re.escape(symbol)}',
                f'from {target_module} import {symbol}',
                content
            )
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
    
    def _parse_source_reference(self, source: str) -> Tuple[Path, Tuple[int, int]]:
        """Parse source reference like 'file.py:10-20' or 'file.py:10'."""
        if ':' not in source:
            raise ValueError("Line number required for extraction (format: file.py:start-end)")
        
        parts = source.split(':', 1)  # Split only on first colon
        file_path = self.project_root / parts[0]
        
        line_spec = parts[1]
        if '-' in line_spec:
            start, end = map(int, line_spec.split('-'))
        else:
            start = end = int(line_spec)
        
        return file_path, (start, end)
    
    def _analyze_extracted_code_variables(self, code: str) -> Dict:
        """Analyze variables in extracted code to determine parameters."""
        # Simple analysis - would be more sophisticated in production
        try:
            tree = ast.parse(code)
            used_vars = set()
            assigned_vars = set()
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Name):
                    if isinstance(node.ctx, ast.Load):
                        used_vars.add(node.id)
                    elif isinstance(node.ctx, ast.Store):
                        assigned_vars.add(node.id)
            
            parameters = list(used_vars - assigned_vars)
            returns = list(assigned_vars)
            
            return {
                "parameters": parameters,
                "returns": returns[0] if len(returns) == 1 else returns if returns else None
            }
        except:
            return {"parameters": [], "returns": None}
    
    def _generate_extracted_function(self, name: str, code: str, variables: Dict) -> str:
        """Generate new function definition."""
        params = ', '.join(variables.get('parameters', []))
        indent = '    '
        
        # Indent the code
        indented_code = '\n'.join(indent + line if line.strip() else line 
                                  for line in code.splitlines())
        
        return_val = variables.get('returns')
        return_stmt = f"\n{indent}return {return_val}" if return_val else ""
        
        return f"def {name}({params}):\n{indented_code}{return_stmt}"
    
    def _generate_function_call(self, name: str, variables: Dict) -> str:
        """Generate function call to replace extracted code."""
        params = ', '.join(variables.get('parameters', []))
        return_val = variables.get('returns')
        
        if return_val:
            if isinstance(return_val, list):
                return f"    {', '.join(return_val)} = {name}({params})"
            else:
                return f"    {return_val} = {name}({params})"
        else:
            return f"    {name}({params})"
    
    def _find_function_insert_location(self, file_path: Path, current_line: int) -> int:
        """Find appropriate location to insert extracted function."""
        # Insert before the current function/class
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                    if node.lineno <= current_line <= node.end_lineno:
                        return node.lineno - 1
        except:
            pass
        
        return max(0, current_line - 5)


class ReviewCommand(BaseCommand):
    """Code review using CriticAgent."""
    
    def __init__(self, project_root: Optional[Path] = None, verbose: bool = False):
        super().__init__(project_root=project_root, verbose=verbose, dry_run=False)
        self.critic = None  # Lazy load
    
    def execute(self, args: Optional[argparse.Namespace] = None) -> Dict:
        """Execute code review command."""
        if not args:
            return self._format_error(ValueError("Missing arguments"), "Code review")
        
        target = args.target
        target_path = self.project_root / target
        
        self._validate_file_exists(target_path)
        self._verbose_print(f"Reviewing {target}")
        
        return self._handle_execution(
            self._perform_full_review,
            target_path, args.focus,
            context="Code review"
        )
    
    def _perform_full_review(self, target_path: Path, focus: Optional[str]) -> Dict:
        """Perform complete review workflow"""
        print(f"[*] Reviewing {target_path.name}...")
        
        # Read file content
        with open(target_path, 'r', encoding='utf-8') as f:
            code = f.read()
        
        # Perform review
        review_result = self._perform_review(code, str(target_path.name), focus)
        
        # Display results
        self._display_review(review_result)
        
        return self._format_success(
            "Review completed",
            file=str(target_path.name),
            issues=review_result.get("issue_count", 0),
            categories=list(review_result.get("categories", {}).keys())
        )
    
    def _perform_review(self, code: str, filename: str, focus: Optional[str]) -> Dict:
        """Perform code review analysis."""
        issues = []
        categories = {
            "quality": [],
            "security": [],
            "style": [],
            "performance": []
        }
        
        # Quality checks
        if len(code.splitlines()) > 500:
            issues.append({
                "category": "quality",
                "severity": "medium",
                "message": "File is very long (>500 lines). Consider splitting into smaller modules.",
                "line": None
            })
            categories["quality"].append("File too long")
        
        # Parse AST for deeper analysis
        try:
            tree = ast.parse(code)
            
            # Check for complex functions
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Count statements
                    statement_count = sum(1 for _ in ast.walk(node) if isinstance(_, ast.stmt))
                    if statement_count > 50:
                        issues.append({
                            "category": "quality",
                            "severity": "medium",
                            "message": f"Function '{node.name}' is too complex ({statement_count} statements)",
                            "line": node.lineno
                        })
                        categories["quality"].append(f"Complex function: {node.name}")
                
                # Security: Check for eval/exec usage
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name) and node.func.id in ['eval', 'exec']:
                        issues.append({
                            "category": "security",
                            "severity": "high",
                            "message": f"Dangerous function '{node.func.id}' usage detected",
                            "line": node.lineno
                        })
                        categories["security"].append("Dangerous function usage")
        except SyntaxError as e:
            issues.append({
                "category": "quality",
                "severity": "high",
                "message": f"Syntax error: {e}",
                "line": e.lineno
            })
        
        # Style checks
        lines = code.splitlines()
        for i, line in enumerate(lines, 1):
            if len(line) > 120:
                issues.append({
                    "category": "style",
                    "severity": "low",
                    "message": f"Line too long ({len(line)} chars, recommended: 88-120)",
                    "line": i
                })
                if "Line too long" not in categories["style"]:
                    categories["style"].append("Line too long")
            
            # Check for TODO/FIXME
            if "TODO" in line or "FIXME" in line:
                issues.append({
                    "category": "quality",
                    "severity": "low",
                    "message": "TODO/FIXME comment found",
                    "line": i
                })
        
        # Performance checks
        if "import *" in code:
            issues.append({
                "category": "style",
                "severity": "medium",
                "message": "Wildcard import detected. Import specific items instead.",
                "line": None
            })
            categories["style"].append("Wildcard import")
        
        return {
            "issue_count": len(issues),
            "issues": issues,
            "categories": categories
        }
    
    def _display_review(self, review: Dict):
        """Display review results."""
        issues = review.get("issues", [])
        
        if not issues:
            print("[+] No issues found! Code looks good.")
            return
        
        print(f"\n[*] Found {len(issues)} issue(s):\n")
        
        # Group by category
        by_category = {}
        for issue in issues:
            cat = issue["category"]
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(issue)
        
        # Display by category
        for category, cat_issues in sorted(by_category.items()):
            print(f"  {category.upper()}:")
            for issue in cat_issues:
                severity = issue["severity"].upper()
                line_info = f"Line {issue['line']}: " if issue['line'] else ""
                print(f"    [{severity}] {line_info}{issue['message']}")
            print()


class DoctorCommand(BaseCommand):
    """Environment validation and health check."""
    
    def __init__(self, project_root: Optional[Path] = None, verbose: bool = False):
        super().__init__(project_root=project_root, verbose=verbose, dry_run=False)
        self.checks: List[Dict] = []
    
    def execute(self, args: Optional[argparse.Namespace] = None) -> Dict:
        """Execute environment validation."""
        self._verbose_print("Starting environment health check")
        print("[*] Running environment health check...\n")
        
        return self._handle_execution(
            self._run_all_checks,
            context="Environment validation"
        )
    
    def _run_all_checks(self) -> Dict:
        """Run all health checks"""
        self.checks = []
        
        # Run all checks
        self._check_python_version()
        self._check_dependencies()
        self._check_configuration()
        self._check_api_keys()
        self._check_git_status()
        
        # Summary
        passed = sum(1 for c in self.checks if c["status"] == "pass")
        failed = sum(1 for c in self.checks if c["status"] == "fail")
        warnings = sum(1 for c in self.checks if c["status"] == "warning")
        
        print(f"\n[*] Summary: {passed} passed, {failed} failed, {warnings} warnings")
        
        if failed > 0:
            print("[-] Some checks failed. Please address the issues above.")
            return self._format_error(
                Exception(f"{failed} checks failed"),
                "Health check"
            )
        elif warnings > 0:
            print("[!] All critical checks passed, but there are warnings.")
            return self._format_success(
                "Health check completed with warnings",
                passed=passed, failed=failed, warnings=warnings
            )
        else:
            print("[+] All checks passed!")
            return {"status": "success", "passed": passed, "failed": failed, "warnings": warnings}
    
    def _check_python_version(self):
        """Check Python version."""
        version = sys.version_info
        required = (3, 10)
        
        if version >= required:
            self._add_check("Python Version", "pass", f"{version.major}.{version.minor}.{version.micro}")
        else:
            self._add_check(
                "Python Version",
                "fail",
                f"{version.major}.{version.minor}.{version.micro} (requires >={required[0]}.{required[1]})"
            )
    
    def _check_dependencies(self):
        """Check if required dependencies are installed."""
        required_packages = [
            "anthropic",
            "openai",
            "pytest",
            "pyyaml",
            "jinja2"
        ]
        
        missing = []
        for package in required_packages:
            try:
                __import__(package.replace("-", "_"))
            except ImportError:
                missing.append(package)
        
        if not missing:
            self._add_check("Dependencies", "pass", "All required packages installed")
        else:
            self._add_check(
                "Dependencies",
                "fail",
                f"Missing packages: {', '.join(missing)}"
            )
    
    def _check_configuration(self):
        """Check configuration files."""
        policy_file = self.project_root / "aureus-self-policy.yaml"
        
        if policy_file.exists():
            try:
                loader = PolicyLoader()
                loader.load(policy_file)
                self._add_check("Policy File", "pass", "Valid policy configuration")
            except Exception as e:
                self._add_check("Policy File", "fail", f"Invalid policy: {e}")
        else:
            self._add_check("Policy File", "warning", "No policy file found")
    
    def _check_api_keys(self):
        """Check API key configuration."""
        env_keys = ["OPENAI_API_KEY", "ANTHROPIC_API_KEY"]
        found_keys = [key for key in env_keys if os.getenv(key)]
        
        if found_keys:
            self._add_check("API Keys", "pass", f"Found: {', '.join(found_keys)}")
        else:
            self._add_check("API Keys", "warning", "No API keys configured")
    
    def _check_git_status(self):
        """Check git repository status."""
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                if result.stdout.strip():
                    self._add_check("Git Status", "warning", "Uncommitted changes detected")
                else:
                    self._add_check("Git Status", "pass", "Working directory clean")
            else:
                self._add_check("Git Status", "warning", "Not a git repository")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            self._add_check("Git Status", "warning", "Git not available")
    
    def _add_check(self, name: str, status: str, message: str):
        """Add check result."""
        self.checks.append({
            "name": name,
            "status": status,
            "message": message
        })
        
        # Display immediately
        if status == "pass":
            symbol = "[+]"
        elif status == "fail":
            symbol = "[-]"
        else:  # warning
            symbol = "[!]"
        
        print(f"{symbol} {name}: {message}")


# CLI Parsers

def add_refactor_parser(subparsers):
    """Add refactor command parser."""
    parser = subparsers.add_parser(
        "refactor",
        help="Multi-file refactoring with safety checks"
    )
    
    subparsers_refactor = parser.add_subparsers(dest="operation", required=True)
    
    # Rename
    rename_parser = subparsers_refactor.add_parser("rename", help="Rename a symbol")
    rename_parser.add_argument("old_name", help="Current symbol name")
    rename_parser.add_argument("new_name", help="New symbol name")
    rename_parser.add_argument("--preview", action="store_true", help="Preview changes without applying")
    rename_parser.add_argument("--scope", help="Limit scope to directory")
    
    # Move
    move_parser = subparsers_refactor.add_parser("move", help="Move symbol to another file")
    move_parser.add_argument("symbol", help="Symbol to move")
    move_parser.add_argument("target_file", help="Target file path")
    move_parser.add_argument("--preview", action="store_true", help="Preview changes without applying")
    
    # Extract
    extract_parser = subparsers_refactor.add_parser("extract", help="Extract code to new function")
    extract_parser.add_argument("source", help="Source reference (file:start-end)")
    extract_parser.add_argument("function_name", help="Name for new function")
    extract_parser.add_argument("--preview", action="store_true", help="Preview extraction")


def add_review_parser(subparsers):
    """Add review command parser."""
    parser = subparsers.add_parser(
        "review",
        help="Code review with quality, security, and style analysis"
    )
    parser.add_argument("target", help="File to review")
    parser.add_argument("--focus", choices=["quality", "security", "style", "all"],
                       default="all", help="Focus area for review")


def add_doctor_parser(subparsers):
    """Add doctor command parser."""
    parser = subparsers.add_parser(
        "doctor",
        help="Environment validation and health check"
    )


def handle_refactor_command(args, project_root: Path) -> int:
    """Handle refactor command execution."""
    command = RefactorCommand(project_root)
    result = command.execute(args)
    return 0 if result["status"] in ["success", "preview"] else 1


def handle_review_command(args, project_root: Path) -> int:
    """Handle review command execution."""
    command = ReviewCommand(project_root)
    result = command.execute(args)
    return 0 if result["status"] == "success" else 1


def handle_doctor_command(args, project_root: Path) -> int:
    """Handle doctor command execution."""
    command = DoctorCommand(project_root)
    result = command.execute(args)
    return 0 if result["status"] in ["success", "warning"] else 1
