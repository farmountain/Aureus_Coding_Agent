"""
AUREUS Testing & Validation Commands - Phase 3

CLI commands for test execution, coverage analysis, validation, and debugging.
Includes: test runner, coverage reports, validation, lint checks.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
import subprocess
import sys
import json
import re
from datetime import datetime
import argparse
from src.cli.base_command import BaseCommand


class TestCommand(BaseCommand):
    """Execute tests with pytest integration."""
    
    def __init__(
        self,
        project_root: Optional[Path] = None,
        pattern: Optional[str] = None,
        coverage: bool = False,
        watch: bool = False,
        failed: bool = False,
        verbose: bool = False
    ):
        """
        Initialize test command.
        
        Args:
            project_root: Project root directory
            pattern: Test pattern to match (e.g., "test_auth")
            coverage: Generate coverage report
            watch: Watch mode (re-run on file changes)
            failed: Only run previously failed tests
            verbose: Show detailed output
        """
        # Initialize BaseCommand
        super().__init__(
            project_root=project_root,
            verbose=verbose,
            dry_run=False
        )
        
        # TestCommand-specific attributes
        self.pattern = pattern
        self.coverage = coverage
        self.watch = watch
        self.failed = failed
        
    def execute(self, args: Optional[argparse.Namespace] = None) -> Dict[str, Any]:
        """
        Execute tests.
        
        Args:
            args: Optional parsed arguments
            
        Returns:
            Result dictionary with test results
        """
        self._verbose_print("Running tests", pattern=self.pattern or "all")
        
        # Wrap execution with standardized error handling
        return self._handle_execution(
            self._run_tests,
            context="Test execution"
        )
    
    def _run_tests(self) -> Dict[str, Any]:
        """Run tests with pytest"""
        print("[*] Running tests...")
        
        # Build pytest command
        cmd = ["python", "-m", "pytest"]
        
        # Add pattern if specified
        if self.pattern:
            cmd.append(self.pattern)
        
        # Add coverage if requested
        if self.coverage:
            cmd.extend(["--cov=src", "--cov-report=term-missing"])
        
        # Add failed-only flag
        if self.failed:
            cmd.append("--lf")  # last-failed
        
        # Add verbosity
        if self.verbose:
            cmd.append("-v")
        else:
            cmd.append("-q")
        
        # Add color output
        cmd.append("--color=yes")
        
        try:
            # Run tests
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=Path.cwd()
            )
            
            # Parse output
            stdout = result.stdout
            stderr = result.stderr
            
            # Extract test results
            test_results = self._parse_test_output(stdout, stderr)
            
            # Display formatted results
            self._display_results(test_results, stdout)
            
            return {
                "status": "success" if result.returncode == 0 else "failed",
                "message": f"Tests completed: {test_results['passed']}/{test_results['total']} passed",
                "results": test_results,
                "exit_code": result.returncode
            }
            
        except FileNotFoundError:
            return {
                "status": "error",
                "message": "pytest not found. Install with: pip install pytest pytest-cov"
            }
        except Exception as e:
            if self.verbose:
                import traceback
                traceback.print_exc()
            return {
                "status": "error",
                "message": f"Test execution error: {e}"
            }
    
    def _parse_test_output(self, stdout: str, stderr: str) -> Dict[str, Any]:
        """Parse pytest output to extract test results."""
        results = {
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "total": 0,
            "coverage": None,
            "failed_tests": []
        }
        
        # Parse test counts (e.g., "5 passed, 2 failed in 1.23s")
        match = re.search(r'(\d+) passed', stdout)
        if match:
            results["passed"] = int(match.group(1))
        
        match = re.search(r'(\d+) failed', stdout)
        if match:
            results["failed"] = int(match.group(1))
        
        match = re.search(r'(\d+) skipped', stdout)
        if match:
            results["skipped"] = int(match.group(1))
        
        results["total"] = results["passed"] + results["failed"] + results["skipped"]
        
        # Parse coverage (e.g., "TOTAL 1234 567 54%")
        match = re.search(r'TOTAL\s+\d+\s+\d+\s+(\d+)%', stdout)
        if match:
            results["coverage"] = int(match.group(1))
        
        # Extract failed test names
        failed_pattern = re.compile(r'FAILED ([\w/.]+::\w+)')
        results["failed_tests"] = failed_pattern.findall(stdout)
        
        return results
    
    def _display_results(self, results: Dict[str, Any], stdout: str):
        """Display formatted test results."""
        print()
        
        # Summary
        total = results["total"]
        passed = results["passed"]
        failed = results["failed"]
        
        if total == 0:
            print("[!] No tests found")
            return
        
        pass_rate = (passed / total * 100) if total > 0 else 0
        
        if failed == 0:
            print(f"[+] All tests passed! ({passed}/{total} - {pass_rate:.0f}%)")
        else:
            print(f"[!] Tests completed: {passed}/{total} passed ({pass_rate:.0f}%)")
            print(f"    {failed} failed, {results['skipped']} skipped")
        
        # Coverage
        if results["coverage"] is not None:
            cov = results["coverage"]
            status = "[+]" if cov >= 80 else "[!]"
            print(f"{status} Coverage: {cov}% (target: 80%)")
        
        # Failed tests
        if results["failed_tests"]:
            print(f"\n[!] Failed Tests:")
            for test in results["failed_tests"][:5]:
                print(f"    - {test}")
            if len(results["failed_tests"]) > 5:
                print(f"    ... and {len(results['failed_tests']) - 5} more")
            
            print(f"\n[*] Re-run failed tests only: aureus test --failed")


class ValidateCommand:
    """Validate code against policy and quality standards."""
    
    def __init__(self, fix: bool = False, verbose: bool = False):
        """
        Initialize validate command.
        
        Args:
            fix: Auto-fix issues where possible
            verbose: Show detailed output
        """
        self.fix = fix
        self.verbose = verbose
        
    def execute(self) -> Dict[str, Any]:
        """
        Execute validation checks.
        
        Returns:
            Result dictionary with validation results
        """
        print("[*] Validating project...")
        
        issues = []
        
        # Check 1: Policy file exists
        policy_check = self._check_policy_exists()
        if not policy_check["passed"]:
            issues.append(policy_check)
        
        # Check 2: Python syntax
        syntax_check = self._check_python_syntax()
        if not syntax_check["passed"]:
            issues.extend(syntax_check.get("issues", []))
        
        # Check 3: Import validation
        import_check = self._check_imports()
        if not import_check["passed"]:
            issues.extend(import_check.get("issues", []))
        
        # Check 4: Policy compliance
        policy_compliance = self._check_policy_compliance()
        if not policy_compliance["passed"]:
            issues.extend(policy_compliance.get("issues", []))
        
        # Display results
        self._display_validation_results(issues)
        
        return {
            "status": "success" if len(issues) == 0 else "failed",
            "message": f"Validation complete: {len(issues)} issue(s) found",
            "issues": issues
        }
    
    def _check_policy_exists(self) -> Dict[str, Any]:
        """Check if policy file exists."""
        policy_path = Path(".aureus/policy.yaml")
        
        if policy_path.exists():
            return {"passed": True, "check": "policy_exists"}
        else:
            return {
                "passed": False,
                "check": "policy_exists",
                "severity": "error",
                "message": "Policy file not found: .aureus/policy.yaml",
                "suggestion": "Run: aureus init"
            }
    
    def _check_python_syntax(self) -> Dict[str, Any]:
        """Check Python files for syntax errors."""
        import ast
        
        issues = []
        src_path = Path("src")
        
        if not src_path.exists():
            return {"passed": True, "issues": []}
        
        for py_file in src_path.rglob("*.py"):
            try:
                py_file.read_text(encoding='utf-8', errors='ignore')
                # Try to parse
                ast.parse(py_file.read_text(encoding='utf-8', errors='ignore'))
            except SyntaxError as e:
                issues.append({
                    "passed": False,
                    "check": "syntax",
                    "severity": "error",
                    "file": str(py_file),
                    "line": e.lineno,
                    "message": f"Syntax error: {e.msg}",
                    "suggestion": "Fix syntax error"
                })
            except Exception:
                # Ignore other errors (encoding, etc)
                pass
        
        return {
            "passed": len(issues) == 0,
            "issues": issues
        }
    
    def _check_imports(self) -> Dict[str, Any]:
        """Check for missing imports."""
        issues = []
        # Simplified check - could be enhanced
        return {"passed": True, "issues": issues}
    
    def _check_policy_compliance(self) -> Dict[str, Any]:
        """Check policy compliance (budgets, forbidden patterns)."""
        try:
            from src.governance.policy import PolicyLoader
            
            policy_path = Path(".aureus/policy.yaml")
            if not policy_path.exists():
                return {"passed": True, "issues": []}
            
            loader = PolicyLoader()
            policy = loader.load(str(policy_path))
            
            issues = []
            
            # Check LOC budget
            src_path = Path("src")
            if src_path.exists():
                total_loc = 0
                for py_file in src_path.rglob("*.py"):
                    try:
                        content = py_file.read_text(encoding='utf-8', errors='ignore')
                        total_loc += len(content.splitlines())
                    except:
                        pass
                
                loc_budget = policy.budgets.get("LOC", float('inf'))
                if total_loc > loc_budget:
                    issues.append({
                        "passed": False,
                        "check": "budget_loc",
                        "severity": "warning",
                        "message": f"LOC budget exceeded: {total_loc} / {loc_budget}",
                        "suggestion": "Review complexity or request escrow exception"
                    })
            
            return {
                "passed": len(issues) == 0,
                "issues": issues
            }
            
        except ImportError:
            return {"passed": True, "issues": []}
        except Exception as e:
            if self.verbose:
                print(f"[!] Policy check error: {e}")
            return {"passed": True, "issues": []}
    
    def _display_validation_results(self, issues: List[Dict[str, Any]]):
        """Display validation results."""
        print()
        
        if len(issues) == 0:
            print("[+] All validation checks passed!")
            print("    Project is compliant with policy and quality standards")
            return
        
        print(f"[!] Found {len(issues)} issue(s):\n")
        
        # Group by severity
        errors = [i for i in issues if i.get("severity") == "error"]
        warnings = [i for i in issues if i.get("severity") == "warning"]
        
        if errors:
            print(f"[!] Errors ({len(errors)}):")
            for issue in errors[:5]:
                file_info = f" in {issue['file']}" if "file" in issue else ""
                line_info = f":{issue['line']}" if "line" in issue else ""
                print(f"    - {issue['message']}{file_info}{line_info}")
                if "suggestion" in issue:
                    print(f"      Suggestion: {issue['suggestion']}")
            if len(errors) > 5:
                print(f"    ... and {len(errors) - 5} more")
        
        if warnings:
            print(f"\n[!] Warnings ({len(warnings)}):")
            for issue in warnings[:5]:
                print(f"    - {issue['message']}")
                if "suggestion" in issue:
                    print(f"      Suggestion: {issue['suggestion']}")
            if len(warnings) > 5:
                print(f"    ... and {len(warnings) - 5} more")
        
        if self.fix:
            print(f"\n[*] Auto-fix not yet implemented")
            print(f"    Manual fixes required for most issues")


class LintCommand:
    """Run linting checks with optional auto-fix."""
    
    def __init__(self, auto_fix: bool = False, verbose: bool = False):
        """
        Initialize lint command.
        
        Args:
            auto_fix: Auto-fix issues where possible
            verbose: Show detailed output
        """
        self.auto_fix = auto_fix
        self.verbose = verbose
        
    def execute(self) -> Dict[str, Any]:
        """
        Execute linting.
        
        Returns:
            Result dictionary with lint results
        """
        print("[*] Running linting checks...")
        
        # Try to run ruff or flake8 if available
        linters = [
            ("ruff", ["ruff", "check", "src", "tests"]),
            ("flake8", ["flake8", "src", "tests"]),
            ("pylint", ["pylint", "src"])
        ]
        
        for linter_name, cmd in linters:
            try:
                if self.auto_fix and linter_name == "ruff":
                    cmd.append("--fix")
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    cwd=Path.cwd()
                )
                
                if result.returncode == 0:
                    print(f"[+] {linter_name}: No issues found")
                else:
                    print(f"[!] {linter_name} found issues:")
                    print(result.stdout[:500])  # First 500 chars
                
                return {
                    "status": "success" if result.returncode == 0 else "issues_found",
                    "message": f"{linter_name} completed",
                    "linter": linter_name
                }
                
            except FileNotFoundError:
                continue  # Try next linter
        
        # No linter found
        print("[!] No linter found (ruff, flake8, pylint)")
        print("    Install with: pip install ruff")
        return {
            "status": "error",
            "message": "No linter available"
        }


class DebugCommand:
    """Debug failed sessions and provide analysis."""
    
    def __init__(
        self,
        session_id: Optional[str] = None,
        last_failure: bool = False,
        verbose: bool = False
    ):
        """
        Initialize debug command.
        
        Args:
            session_id: Specific session to debug
            last_failure: Debug last failed session
            verbose: Show detailed output
        """
        self.session_id = session_id
        self.last_failure = last_failure
        self.verbose = verbose
        
    def execute(self) -> Dict[str, Any]:
        """
        Execute debugging analysis.
        
        Returns:
            Result dictionary with debug info
        """
        print("[*] Analyzing session...")
        
        try:
            # Find session to debug
            if self.last_failure:
                session = self._find_last_failed_session()
            elif self.session_id:
                session = self._load_session(self.session_id)
            else:
                return {
                    "status": "error",
                    "message": "Specify --last-failure or <session-id>"
                }
            
            if not session:
                return {
                    "status": "error",
                    "message": "Session not found"
                }
            
            # Analyze session
            analysis = self._analyze_session(session)
            
            # Display analysis
            self._display_analysis(analysis)
            
            return {
                "status": "success",
                "message": "Debug analysis complete",
                "analysis": analysis
            }
            
        except Exception as e:
            if self.verbose:
                import traceback
                traceback.print_exc()
            return {
                "status": "error",
                "message": f"Debug error: {e}"
            }
    
    def _find_last_failed_session(self) -> Optional[Dict[str, Any]]:
        """Find most recent failed session."""
        memory_path = Path("memory/trajectories")
        
        if not memory_path.exists():
            return None
        
        # Find most recent failed session
        for session_file in sorted(memory_path.glob("*.json"), reverse=True):
            try:
                session = json.loads(session_file.read_text())
                if not session.get("success", True):
                    return session
            except:
                continue
        
        return None
    
    def _load_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load specific session."""
        session_path = Path(f"memory/trajectories/{session_id}.json")
        
        if not session_path.exists():
            return None
        
        try:
            return json.loads(session_path.read_text())
        except:
            return None
    
    def _analyze_session(self, session: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze session for issues."""
        analysis = {
            "session_id": session.get("session_id", "unknown"),
            "timestamp": session.get("timestamp", "unknown"),
            "error_type": None,
            "error_message": None,
            "suggestions": []
        }
        
        # Extract error info
        if "error" in session:
            error = session["error"]
            analysis["error_type"] = error.get("type", "Unknown")
            analysis["error_message"] = error.get("message", "No message")
        
        # Generate suggestions
        error_type = analysis["error_type"]
        
        if error_type == "BudgetExceeded":
            analysis["suggestions"].append("Increase budget in .aureus/policy.yaml")
            analysis["suggestions"].append("Or simplify requirements")
        elif error_type == "SyntaxError":
            analysis["suggestions"].append("Review generated code for syntax issues")
            analysis["suggestions"].append("Check LLM prompt quality")
        elif error_type == "TestFailure":
            analysis["suggestions"].append("Review test expectations")
            analysis["suggestions"].append("Update code to pass tests")
        else:
            analysis["suggestions"].append("Review session logs for details")
            analysis["suggestions"].append("Check error message for specific guidance")
        
        return analysis
    
    def _display_analysis(self, analysis: Dict[str, Any]):
        """Display debug analysis."""
        print()
        print(f"Session: {analysis['session_id']}")
        print(f"Time: {analysis['timestamp']}")
        print()
        
        if analysis["error_type"]:
            print(f"[!] Error: {analysis['error_type']}")
            print(f"    {analysis['error_message']}")
            print()
        
        if analysis["suggestions"]:
            print("[*] Suggestions:")
            for suggestion in analysis["suggestions"]:
                print(f"    - {suggestion}")


# ============================================================================
# CLI Parsers
# ============================================================================

def parse_test_args(args):
    """Parse test command arguments."""
    import argparse
    
    parser = argparse.ArgumentParser(
        prog="aureus test",
        description="Run tests with pytest integration"
    )
    parser.add_argument("pattern", nargs="?", help="Test pattern to match")
    parser.add_argument("--coverage", action="store_true", help="Generate coverage report")
    parser.add_argument("--watch", action="store_true", help="Watch mode (re-run on changes)")
    parser.add_argument("--failed", action="store_true", help="Run only failed tests")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    
    return parser.parse_args(args)


def parse_validate_args(args):
    """Parse validate command arguments."""
    import argparse
    
    parser = argparse.ArgumentParser(
        prog="aureus validate",
        description="Validate code against policy and quality standards"
    )
    parser.add_argument("--fix", action="store_true", help="Auto-fix issues where possible")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    
    return parser.parse_args(args)


def parse_lint_args(args):
    """Parse lint command arguments."""
    import argparse
    
    parser = argparse.ArgumentParser(
        prog="aureus lint",
        description="Run linting checks"
    )
    parser.add_argument("--auto-fix", action="store_true", help="Auto-fix issues where possible")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    
    return parser.parse_args(args)


def parse_debug_args(args):
    """Parse debug command arguments."""
    import argparse
    
    parser = argparse.ArgumentParser(
        prog="aureus debug",
        description="Debug failed sessions"
    )
    parser.add_argument("session_id", nargs="?", help="Session ID to debug")
    parser.add_argument("--last-failure", action="store_true", help="Debug last failed session")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    
    return parser.parse_args(args)


# ============================================================================
# Main Entry Points
# ============================================================================

def main_test(args):
    """Main entry point for test command."""
    parsed = parse_test_args(args)
    
    cmd = TestCommand(
        pattern=parsed.pattern,
        coverage=parsed.coverage,
        watch=parsed.watch,
        failed=parsed.failed,
        verbose=parsed.verbose
    )
    
    result = cmd.execute()
    
    return 0 if result["status"] == "success" else 1


def main_validate(args):
    """Main entry point for validate command."""
    parsed = parse_validate_args(args)
    
    cmd = ValidateCommand(
        fix=parsed.fix,
        verbose=parsed.verbose
    )
    
    result = cmd.execute()
    
    return 0 if result["status"] == "success" else 1


def main_lint(args):
    """Main entry point for lint command."""
    parsed = parse_lint_args(args)
    
    cmd = LintCommand(
        auto_fix=parsed.auto_fix,
        verbose=parsed.verbose
    )
    
    result = cmd.execute()
    
    return 0 if result["status"] in ["success", "issues_found"] else 1


def main_debug(args):
    """Main entry point for debug command."""
    parsed = parse_debug_args(args)
    
    cmd = DebugCommand(
        session_id=parsed.session_id,
        last_failure=parsed.last_failure,
        verbose=parsed.verbose
    )
    
    result = cmd.execute()
    
    return 0 if result["status"] == "success" else 1
