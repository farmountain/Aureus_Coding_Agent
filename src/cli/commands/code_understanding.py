"""
AUREUS Code Understanding Commands

CLI commands for code exploration, navigation, and analysis.
Includes: explain code, find symbols, show usages, impact analysis.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import ast
import sys
import os
import argparse
from src.cli.base_command import BaseCommand

# Configure stdout for UTF-8 on Windows
if sys.platform == 'win32':
    try:
        # Try to set console to UTF-8
        os.system('chcp 65001 > nul 2>&1')
    except:
        pass


class ExplainCodeCommand(BaseCommand):
    """Explain code using LLM and AST analysis."""
    
    def __init__(
        self,
        project_root: Optional[Path] = None,
        file_path: Optional[str] = None,
        function_name: Optional[str] = None,
        verbose: bool = False
    ):
        """
        Initialize explain code command.
        
        Args:
            project_root: Project root directory
            file_path: Path to file to explain
            function_name: Optional specific function to explain
            verbose: Show detailed analysis
        """
        super().__init__(project_root=project_root, verbose=verbose, dry_run=False)
        self.file_path = Path(file_path) if file_path else None
        self.function_name = function_name
        
    def execute(self, args: Optional[argparse.Namespace] = None) -> Dict[str, Any]:
        """
        Execute code explanation.
        
        Args:
            args: Optional parsed arguments
            
        Returns:
            Result dictionary with explanation
        """
        if not self.file_path:
            return self._format_error(ValueError("No file path specified"), "Explain code")
        
        self._validate_file_exists(self.file_path)
        self._verbose_print(f"Analyzing {self.file_path}")
        
        return self._handle_execution(
            self._perform_analysis,
            context="Code explanation"
        )
    
    def _perform_analysis(self) -> Dict[str, Any]:
        """Perform code analysis"""
        # Read source code
        source_code = self.file_path.read_text(encoding='utf-8')
        
        print(f"[*] Analyzing: {self.file_path}")
        
        try:
            # Parse AST for structure analysis
            tree = ast.parse(source_code, filename=str(self.file_path))
            
            # Extract code elements
            elements = self._extract_code_elements(tree)
            
            # If specific function requested, filter
            if self.function_name:
                elements = self._filter_function(elements, self.function_name, source_code)
                if not elements:
                    return {
                        "status": "error",
                        "message": f"Function '{self.function_name}' not found"
                    }
            
            # Generate explanation using LLM
            explanation = self._generate_explanation(
                source_code, 
                elements, 
                self.file_path
            )
            
            # Display explanation
            print(f"\n{explanation}")
            
            return {
                "status": "success",
                "message": "Code explanation generated",
                "explanation": explanation,
                "elements": elements
            }
            
        except SyntaxError as e:
            return {
                "status": "error",
                "message": f"Syntax error in file: {e}"
            }
        except Exception as e:
            if self.verbose:
                import traceback
                traceback.print_exc()
            return {
                "status": "error",
                "message": f"Analysis error: {e}"
            }
    
    def _extract_code_elements(self, tree: ast.AST) -> Dict[str, List[str]]:
        """Extract functions, classes, imports from AST."""
        elements = {
            "functions": [],
            "classes": [],
            "imports": [],
            "variables": []
        }
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                elements["functions"].append(node.name)
            elif isinstance(node, ast.ClassDef):
                elements["classes"].append(node.name)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    elements["imports"].append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    elements["imports"].append(f"{module}.{alias.name}")
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        elements["variables"].append(target.id)
        
        return elements
    
    def _filter_function(
        self, 
        elements: Dict[str, List[str]], 
        func_name: str,
        source_code: str
    ) -> Dict[str, Any]:
        """Filter to specific function."""
        if func_name not in elements["functions"]:
            return {}
        
        # Extract function source
        tree = ast.parse(source_code)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == func_name:
                func_source = ast.get_source_segment(source_code, node)
                return {
                    "type": "function",
                    "name": func_name,
                    "source": func_source,
                    "lineno": node.lineno,
                    "args": [arg.arg for arg in node.args.args]
                }
        
        return {}
    
    def _generate_explanation(
        self, 
        source_code: str, 
        elements: Dict[str, Any],
        file_path: Path
    ) -> str:
        """Generate natural language explanation."""
        # Try LLM explanation first
        try:
            from src.model_provider import OpenAIProvider, AnthropicProvider, MockProvider
            import os
            
            provider_name = os.getenv("AUREUS_MODEL_PROVIDER", "mock").lower()
            api_key = os.getenv("AUREUS_MODEL_API_KEY")
            
            if provider_name == "openai" and api_key:
                model_provider = OpenAIProvider(api_key=api_key)
            elif provider_name == "anthropic" and api_key:
                model_provider = AnthropicProvider(api_key=api_key)
            else:
                # Fallback to AST-based explanation
                return self._generate_ast_explanation(source_code, elements, file_path)
            
            # Generate explanation using LLM
            prompt = self._build_explanation_prompt(source_code, elements, file_path)
            response = model_provider.complete(prompt)
            
            return response.content
            
        except Exception as e:
            # Fallback to AST-based explanation
            if self.verbose:
                print(f"[!] LLM unavailable, using AST analysis: {e}")
            return self._generate_ast_explanation(source_code, elements, file_path)
    
    def _build_explanation_prompt(
        self, 
        source_code: str, 
        elements: Dict[str, Any],
        file_path: Path
    ) -> str:
        """Build prompt for LLM explanation."""
        if isinstance(elements, dict) and "type" in elements and elements["type"] == "function":
            # Specific function explanation
            return f"""Explain this Python function in clear, concise language:

```python
{elements['source']}
```

Provide:
1. One-sentence summary of what it does
2. Parameters and their purposes
3. Return value
4. Key logic steps
5. Any notable patterns or edge cases

Keep explanation under 200 words."""
        
        else:
            # Full file explanation
            loc = len(source_code.splitlines())
            return f"""Analyze this Python file and provide a clear explanation:

File: {file_path.name} ({loc} LOC)

```python
{source_code[:2000]}  # First 2000 chars
{'...' if len(source_code) > 2000 else ''}
```

Structure:
- Functions: {', '.join(elements.get('functions', [])[:5])}
- Classes: {', '.join(elements.get('classes', [])[:5])}
- Key imports: {', '.join(elements.get('imports', [])[:5])}

Provide:
1. One-paragraph summary (2-3 sentences)
2. Main components and their roles
3. Dependencies and integration points
4. Notable patterns or design choices
5. Potential issues or security considerations

Keep explanation under 300 words, be specific and actionable."""
    
    def _generate_ast_explanation(
        self, 
        source_code: str, 
        elements: Dict[str, Any],
        file_path: Path
    ) -> str:
        """Generate explanation from AST analysis (fallback)."""
        if isinstance(elements, dict) and "type" in elements and elements["type"] == "function":
            # Function explanation
            func = elements
            lines = [
                f"Function: {func['name']}",
                f"Location: Line {func['lineno']}",
                f"",
                f"Parameters: {', '.join(func['args']) if func['args'] else 'None'}",
                f"",
                "This function is defined in the code. Use --verbose or configure",
                "an LLM provider for detailed AI-powered explanation.",
                f"",
                f"Source Preview:",
                f"```python",
                f"{func['source'][:500]}",
                f"{'...' if len(func['source']) > 500 else ''}",
                f"```"
            ]
            return "\n".join(lines)
        
        else:
            # File explanation
            loc = len(source_code.splitlines())
            lines = [
                f"File: {file_path.name} ({loc} LOC)",
                f"",
                f"Structure:",
                f"  • Functions: {len(elements['functions'])} ({', '.join(elements['functions'][:5])}{'...' if len(elements['functions']) > 5 else ''})",
                f"  • Classes: {len(elements['classes'])} ({', '.join(elements['classes'][:3])}{'...' if len(elements['classes']) > 3 else ''})",
                f"  • Imports: {len(elements['imports'])} modules",
                f"",
                f"[i] Configure AUREUS_MODEL_PROVIDER for AI-powered analysis.",
                f"   Current: AST-based structure analysis only."
            ]
            
            return "\n".join(lines)


class FindSymbolCommand:
    """Find symbol definitions in codebase."""
    
    def __init__(self, symbol: str, verbose: bool = False):
        """
        Initialize find symbol command.
        
        Args:
            symbol: Symbol name to find
            verbose: Show detailed output
        """
        self.symbol = symbol
        self.verbose = verbose
        
    def execute(self) -> Dict[str, Any]:
        """
        Execute symbol search.
        
        Returns:
            Result dictionary with locations
        """
        print(f"[*] Searching for: {self.symbol}")
        
        try:
            from src.infrastructure.repository_indexer import RepositoryIndexer
            
            # Initialize indexer
            indexer = RepositoryIndexer(Path.cwd())
            symbol_table = indexer.index()
            
            # Find symbol
            results = self._find_in_symbol_table(symbol_table, self.symbol)
            
            if not results:
                print(f"\n[-] Symbol '{self.symbol}' not found")
                return {
                    "status": "not_found",
                    "message": f"Symbol '{self.symbol}' not found in codebase"
                }
            
            # Display results
            print(f"\n[+] Found {len(results)} location(s):\n")
            for result in results:
                print(f"  {result['file']}:{result['line']}  {result['type']} {result['name']}")
                if self.verbose and result.get('signature'):
                    print(f"    {result['signature']}")
            
            return {
                "status": "success",
                "message": f"Found {len(results)} location(s)",
                "results": results
            }
            
        except ImportError:
            return {
                "status": "error",
                "message": "Repository indexer not available"
            }
        except Exception as e:
            if self.verbose:
                import traceback
                traceback.print_exc()
            return {
                "status": "error",
                "message": f"Search error: {e}"
            }
    
    def _find_in_symbol_table(self, symbol_table, symbol_name: str) -> List[Dict[str, Any]]:
        """Find symbol in indexed symbol table."""
        results = []
        
        # Search in symbols
        for name, symbol in symbol_table.symbols.items():
            if name == symbol_name or symbol_name in name:
                results.append({
                    "file": symbol.file_path,
                    "line": symbol.lineno,
                    "type": symbol.type,
                    "name": symbol.name,
                    "signature": getattr(symbol, 'signature', None)
                })
        
        return results


class UsagesCommand:
    """Show all usages of a symbol."""
    
    def __init__(self, symbol: str, verbose: bool = False):
        """
        Initialize usages command.
        
        Args:
            symbol: Symbol name to find usages
            verbose: Show detailed output
        """
        self.symbol = symbol
        self.verbose = verbose
        
    def execute(self) -> Dict[str, Any]:
        """
        Execute usages search.
        
        Returns:
            Result dictionary with usages
        """
        print(f"[*] Finding usages of: {self.symbol}")
        
        try:
            from src.infrastructure.repository_indexer import RepositoryIndexer
            
            # Initialize indexer
            indexer = RepositoryIndexer(Path.cwd())
            symbol_table = indexer.index()
            
            # Find usages
            usages = self._find_usages(symbol_table, self.symbol)
            
            if not usages:
                print(f"\n[!] No usages found for '{self.symbol}'")
                print(f"   (Symbol may not exist or only defined, never used)")
                return {
                    "status": "not_found",
                    "message": f"No usages found for '{self.symbol}'"
                }
            
            # Group by file
            by_file = {}
            for usage in usages:
                file = usage['file']
                if file not in by_file:
                    by_file[file] = []
                by_file[file].append(usage)
            
            # Display results
            print(f"\n[+] Found {len(usages)} usage(s) across {len(by_file)} file(s):\n")
            for file, file_usages in sorted(by_file.items()):
                print(f"  {file} ({len(file_usages)} usage(s))")
                if self.verbose:
                    for usage in file_usages:
                        print(f"    Line {usage['line']}: {usage['context']}")
            
            return {
                "status": "success",
                "message": f"Found {len(usages)} usage(s)",
                "usages": usages,
                "files": list(by_file.keys())
            }
            
        except ImportError:
            return {
                "status": "error",
                "message": "Repository indexer not available"
            }
        except Exception as e:
            if self.verbose:
                import traceback
                traceback.print_exc()
            return {
                "status": "error",
                "message": f"Search error: {e}"
            }
    
    def _find_usages(self, symbol_table, symbol_name: str) -> List[Dict[str, Any]]:
        """Find all usages of symbol."""
        usages = []
        
        # Check if symbol exists
        symbol_obj = symbol_table.symbols.get(symbol_name)
        if not symbol_obj:
            return []
        
        # Look through file_symbols for references
        for file_path, symbols in symbol_table.file_symbols.items():
            if symbol_name in symbols:
                # Read file to find exact lines
                try:
                    file_content = Path(file_path).read_text(encoding='utf-8', errors='ignore')
                    for i, line in enumerate(file_content.splitlines(), 1):
                        if symbol_name in line:
                            usages.append({
                                "file": file_path,
                                "line": i,
                                "context": line.strip()[:80]
                            })
                except:
                    pass
        
        return usages


class ImpactAnalysisCommand:
    """Analyze impact of changing a symbol."""
    
    def __init__(self, symbol: str, verbose: bool = False):
        """
        Initialize impact analysis command.
        
        Args:
            symbol: Symbol to analyze
            verbose: Show detailed analysis
        """
        self.symbol = symbol
        self.verbose = verbose
        
    def execute(self) -> Dict[str, Any]:
        """
        Execute impact analysis.
        
        Returns:
            Result dictionary with impact assessment
        """
        print(f"[*] Analyzing impact of: {self.symbol}\n")
        
        try:
            from src.infrastructure.repository_indexer import RepositoryIndexer
            
            # Initialize indexer
            indexer = RepositoryIndexer(Path.cwd())
            symbol_table = indexer.index()
            
            # Find symbol definition
            symbol_obj = symbol_table.symbols.get(self.symbol)
            if not symbol_obj:
                return {
                    "status": "error",
                    "message": f"Symbol '{self.symbol}' not found"
                }
            
            # Analyze dependencies
            dependencies = self._analyze_dependencies(symbol_table, self.symbol)
            
            # Analyze dependents (what uses this symbol)
            dependents = self._analyze_dependents(symbol_table, self.symbol)
            
            # Calculate risk
            risk_level = self._calculate_risk(dependencies, dependents)
            
            # Display analysis
            print(f"Symbol: {self.symbol} ({symbol_obj.type})")
            print(f"Defined in: {symbol_obj.file_path}:{symbol_obj.lineno}\n")
            
            print(f"Direct Dependencies ({len(dependencies)}):")
            for dep in dependencies[:5]:
                print(f"  • {dep['name']} ({dep['file']})")
            if len(dependencies) > 5:
                print(f"  ... and {len(dependencies) - 5} more\n")
            else:
                print()
            
            print(f"Dependent Code ({len(dependents)} files):")
            for dep in dependents[:5]:
                print(f"  • {dep['file']} ({dep['usages']} usage(s))")
            if len(dependents) > 5:
                print(f"  ... and {len(dependents) - 5} more files\n")
            else:
                print()
            
            # Risk assessment
            risk_color = {"LOW": "[LOW]", "MEDIUM": "[MED]", "HIGH": "[HIGH]"}
            print(f"[!] Risk Assessment: {risk_color.get(risk_level, '[?]')} {risk_level}")
            print(f"    Changing this {symbol_obj.type} will affect {len(dependents)} file(s)")
            
            if risk_level == "HIGH":
                print(f"\n[*] Recommendations:")
                print(f"  • Write comprehensive tests before changes")
                print(f"  • Use aureus refactor --rename for safe renaming")
                print(f"  • Consider deprecation path if API is public")
            
            return {
                "status": "success",
                "message": "Impact analysis complete",
                "symbol": self.symbol,
                "type": symbol_obj.type,
                "file": symbol_obj.file_path,
                "dependencies": len(dependencies),
                "dependents": len(dependents),
                "risk": risk_level
            }
            
        except ImportError:
            return {
                "status": "error",
                "message": "Repository indexer not available"
            }
        except Exception as e:
            if self.verbose:
                import traceback
                traceback.print_exc()
            return {
                "status": "error",
                "message": f"Analysis error: {e}"
            }
    
    def _analyze_dependencies(self, symbol_table, symbol_name: str) -> List[Dict[str, Any]]:
        """Find what this symbol depends on."""
        dependencies = []
        
        symbol_obj = symbol_table.symbols.get(symbol_name)
        if not symbol_obj:
            return []
        
        # Get file where symbol is defined
        file_path = symbol_obj.file_path
        
        # Check dependencies
        if file_path in symbol_table.dependencies:
            for dep in symbol_table.dependencies:
                if dep.source_file == file_path and dep.symbol == symbol_name:
                    dependencies.append({
                        "name": dep.target,
                        "file": dep.target_file,
                        "type": "import"
                    })
        
        return dependencies
    
    def _analyze_dependents(self, symbol_table, symbol_name: str) -> List[Dict[str, Any]]:
        """Find what depends on this symbol."""
        dependents = {}
        
        # Find files that use this symbol
        for file_path, symbols in symbol_table.file_symbols.items():
            if symbol_name in symbols:
                # Count usages
                try:
                    content = Path(file_path).read_text(encoding='utf-8', errors='ignore')
                    count = content.count(symbol_name)
                    
                    if file_path not in dependents:
                        dependents[file_path] = 0
                    dependents[file_path] += count
                except:
                    pass
        
        return [{"file": f, "usages": count} for f, count in dependents.items()]
    
    def _calculate_risk(self, dependencies: List, dependents: List) -> str:
        """Calculate risk level of changing symbol."""
        dependent_count = len(dependents)
        usage_count = sum(d.get("usages", 0) for d in dependents)
        
        if dependent_count == 0:
            return "LOW"
        elif dependent_count <= 3 and usage_count <= 10:
            return "LOW"
        elif dependent_count <= 8 and usage_count <= 30:
            return "MEDIUM"
        else:
            return "HIGH"


# ============================================================================
# CLI Parsers
# ============================================================================

def parse_explain_args(args):
    """Parse explain code command arguments."""
    import argparse
    
    parser = argparse.ArgumentParser(
        prog="aureus explain code",
        description="Explain code using AI and static analysis"
    )
    parser.add_argument("file", help="File to explain")
    parser.add_argument("-f", "--function", help="Specific function to explain")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    
    return parser.parse_args(args)


def parse_find_args(args):
    """Parse find command arguments."""
    import argparse
    
    parser = argparse.ArgumentParser(
        prog="aureus find",
        description="Find symbol definitions in codebase"
    )
    parser.add_argument("symbol", help="Symbol name to find")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    
    return parser.parse_args(args)


def parse_usages_args(args):
    """Parse usages command arguments."""
    import argparse
    
    parser = argparse.ArgumentParser(
        prog="aureus usages",
        description="Show all usages of a symbol"
    )
    parser.add_argument("symbol", help="Symbol name to find usages")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    
    return parser.parse_args(args)


def parse_impact_args(args):
    """Parse impact command arguments."""
    import argparse
    
    parser = argparse.ArgumentParser(
        prog="aureus impact",
        description="Analyze impact of changing a symbol"
    )
    parser.add_argument("symbol", help="Symbol to analyze")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    
    return parser.parse_args(args)


# ============================================================================
# Main Entry Points
# ============================================================================

def main_explain_code(args):
    """Main entry point for explain code command."""
    parsed = parse_explain_args(args)
    
    cmd = ExplainCodeCommand(
        file_path=parsed.file,
        function_name=parsed.function,
        verbose=parsed.verbose
    )
    
    result = cmd.execute()
    
    if result["status"] == "success":
        return 0
    else:
        print(f"\n[-] {result['message']}", file=sys.stderr)
        return 1


def main_find(args):
    """Main entry point for find command."""
    parsed = parse_find_args(args)
    
    cmd = FindSymbolCommand(
        symbol=parsed.symbol,
        verbose=parsed.verbose
    )
    
    result = cmd.execute()
    
    return 0 if result["status"] == "success" else 1


def main_usages(args):
    """Main entry point for usages command."""
    parsed = parse_usages_args(args)
    
    cmd = UsagesCommand(
        symbol=parsed.symbol,
        verbose=parsed.verbose
    )
    
    result = cmd.execute()
    
    return 0 if result["status"] == "success" else 1


def main_impact(args):
    """Main entry point for impact command."""
    parsed = parse_impact_args(args)
    
    cmd = ImpactAnalysisCommand(
        symbol=parsed.symbol,
        verbose=parsed.verbose
    )
    
    result = cmd.execute()
    
    return 0 if result["status"] == "success" else 1
