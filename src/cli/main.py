"""
AUREUS CLI - Command line interface.

Entry point for all AUREUS operations:
- init: Initialize project with policy
- code: Execute coding task
- status: Show project status
"""

import argparse
import sys
import signal
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

from src.interfaces import Policy, Budget
from src.governance.policy import PolicyLoader, PolicyLoadError
from src.cli.base_command import BaseCommand

# Global flag for graceful cancellation
_cancellation_requested = False

def _signal_handler(signum, frame):
    """Handle Ctrl+C for graceful cancellation"""
    global _cancellation_requested
    _cancellation_requested = True
    print("\n\n⚠️  Cancellation requested... finishing current operation")
    print("   Press Ctrl+C again to force quit")
    # Reset handler to allow force quit on second Ctrl+C
    signal.signal(signal.SIGINT, signal.SIG_DFL)

# Register signal handler
signal.signal(signal.SIGINT, _signal_handler)


# ============================================================================
# Exceptions
# ============================================================================

class CLIError(Exception):
    """Raised when CLI operation fails."""
    pass


# ============================================================================
# CLI Argument Parser
# ============================================================================

@dataclass
class ParsedArgs:
    """Parsed command line arguments."""
    command: str
    intent: Optional[str] = None
    policy_path: Optional[str] = None
    verbose: bool = False
    dry_run: bool = False
    stream: bool = True
    explain_target: Optional[str] = None  # For explain command: "last", "last-rejection", or decision ID
    interactive: bool = False  # For init command: interactive wizard


class CLIParser:
    """
    Parse AUREUS command line arguments.
    
    Commands:
    - init [--policy PATH]: Initialize project
    - code <intent> [--policy PATH]: Execute task
    - status [--policy PATH]: Show status
    - explain [last|last-rejection|<decision-id>]: Explain decision
    """
    
    def parse(self, args: List[str]) -> ParsedArgs:
        """
        Parse command line arguments.
        
        Args:
            args: Command line arguments (without program name)
        
        Returns:
            Parsed arguments
        
        Raises:
            CLIError: If parsing fails
        """
        if len(args) == 0:
            raise CLIError("No command specified. Use: init, code, status, budget, explain, memory, history, test-gen, find, usages, impact, test, validate, lint, debug, refactor, review, doctor, adr, skills, learn")
        
        command = args[0]

        # Handle budget dashboard command
        if command == "budget":
            return self._parse_budget(args[1:])
        
        # Handle test-gen separately (delegates to test_commands.py)
        if command == "test-gen":
            from src.cli.commands.test_commands import main_test_gen
            sys.exit(main_test_gen(args[1:]))
        
        # Handle code understanding commands (Phase 2)
        if command in ["find", "usages", "impact"]:
            from src.cli.code_understanding import main_find, main_usages, main_impact
            if command == "find":
                sys.exit(main_find(args[1:]))
            elif command == "usages":
                sys.exit(main_usages(args[1:]))
            elif command == "impact":
                sys.exit(main_impact(args[1:]))
        
        # Handle testing & validation commands (Phase 3)
        if command in ["test", "validate", "lint", "debug"]:
            from src.cli.commands.test_validation import main_test, main_validate, main_lint, main_debug
            if command == "test":
                sys.exit(main_test(args[1:]))
            elif command == "validate":
                sys.exit(main_validate(args[1:]))
            elif command == "lint":
                sys.exit(main_lint(args[1:]))
            elif command == "debug":
                sys.exit(main_debug(args[1:]))
        
        # Handle refactoring & review commands (Phase 4)
        if command in ["refactor", "review", "doctor"]:
            from src.cli.refactoring_review import handle_refactor_command, handle_review_command, handle_doctor_command
            from src.cli.refactoring_review import add_refactor_parser, add_review_parser, add_doctor_parser
            
            # Create parser with subcommands
            parser = argparse.ArgumentParser(prog="aureus")
            subparsers = parser.add_subparsers(dest="command")
            
            if command == "refactor":
                add_refactor_parser(subparsers)
                parsed_args = parser.parse_args([command] + args[1:])
                project_root = Path.cwd()
                sys.exit(handle_refactor_command(parsed_args, project_root))
            elif command == "review":
                add_review_parser(subparsers)
                parsed_args = parser.parse_args([command] + args[1:])
                project_root = Path.cwd()
                sys.exit(handle_review_command(parsed_args, project_root))
            elif command == "doctor":
                add_doctor_parser(subparsers)
                parsed_args = parser.parse_args([command] + args[1:])
                project_root = Path.cwd()
                sys.exit(handle_doctor_command(parsed_args, project_root))
        
        # Handle learning & growth commands (Phase 5)
        if command in ["adr", "skills", "learn"]:
            from src.cli.learning_growth import handle_adr_command, handle_skills_command, handle_learn_command
            from src.cli.learning_growth import add_adr_parser, add_skills_parser, add_learn_parser
            
            # Create parser with subcommands
            parser = argparse.ArgumentParser(prog="aureus")
            subparsers = parser.add_subparsers(dest="command")
            
            if command == "adr":
                add_adr_parser(subparsers)
                parsed_args = parser.parse_args([command] + args[1:])
                project_root = Path.cwd()
                sys.exit(handle_adr_command(parsed_args, project_root))
            elif command == "skills":
                add_skills_parser(subparsers)
                parsed_args = parser.parse_args([command] + args[1:])
                project_root = Path.cwd()
                sys.exit(handle_skills_command(parsed_args, project_root))
            elif command == "learn":
                add_learn_parser(subparsers)
                parsed_args = parser.parse_args([command] + args[1:])
                project_root = Path.cwd()
                sys.exit(handle_learn_command(parsed_args, project_root))
        
        # Handle memory commands
        if command == "memory":
            from src.cli.commands.memory_commands import memory_commands
            # Use click's standalone_mode to handle the command
            try:
                memory_commands.main(args[1:], standalone_mode=True)
            except SystemExit as e:
                sys.exit(e.code)
        
        # Handle history commands (undo/redo stack - Sprint 1 Item 10)
        if command == "history":
            from src.cli.commands.history_commands import history_commands
            try:
                history_commands.main(args[1:], standalone_mode=True)
            except SystemExit as e:
                sys.exit(e.code)
        
        # Handle collaboration commands (Phase 6)
        if command == "collaborate":
            from src.cli.collaboration import add_collaborate_parser, handle_collaborate_command
            
            parser = argparse.ArgumentParser(prog="aureus")
            subparsers = parser.add_subparsers(dest="command")
            add_collaborate_parser(subparsers)
            parsed_args = parser.parse_args([command] + args[1:])
            sys.exit(handle_collaborate_command(parsed_args))
        
        # Parse based on command
        if command == "init":
            return self._parse_init(args[1:])
        elif command == "code":
            return self._parse_code(args[1:])
        elif command == "status":
            return self._parse_status(args[1:])
        elif command == "explain":
            return self._parse_explain(args[1:])
        else:
            raise CLIError(f"Unknown command: {command}")
    
    def _parse_init(self, args: List[str]) -> ParsedArgs:
        """Parse 'init' command arguments."""
        parser = argparse.ArgumentParser(prog="aureus init")
        parser.add_argument("--policy", dest="policy_path", help="Policy file path")
        parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
        parser.add_argument("--interactive", "-i", action="store_true", help="Interactive setup wizard")
        parser.add_argument("--force", "-f", action="store_true", help="Overwrite existing policy")
        
        parsed = parser.parse_args(args)
        return ParsedArgs(
            command="init",
            policy_path=parsed.policy_path,
            verbose=parsed.verbose,
            interactive=parsed.interactive,
            dry_run=parsed.force  # Reuse dry_run field for --force
        )
    
    def _parse_code(self, args: List[str]) -> ParsedArgs:
        """Parse 'code' command arguments."""
        if len(args) == 0:
            raise CLIError("'code' command requires an intent argument")
        
        # Extract intent (all non-option arguments)
        intent_parts = []
        remaining = []
        skip_next = False
        
        for i, arg in enumerate(args):
            if skip_next:
                skip_next = False
                continue
            if arg.startswith("-"):
                remaining.append(arg)
                # Check if next arg is the value for this option
                if i + 1 < len(args) and not args[i + 1].startswith("-"):
                    remaining.append(args[i + 1])
                    skip_next = True
            else:
                if not skip_next:
                    intent_parts.append(arg)
        
        if not intent_parts:
            raise CLIError("'code' command requires an intent argument")
        
        intent = " ".join(intent_parts)
        
        # Parse options
        parser = argparse.ArgumentParser(prog="aureus code")
        parser.add_argument("--policy", dest="policy_path", help="Policy file path")
        parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output with full error traces")
        parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing files")
        parser.add_argument("--stream", action="store_true", default=True, help="Stream output in real-time (default: ON)")
        parser.add_argument("--no-stream", dest="stream", action="store_false", help="Disable streaming for clean logs")
        
        parsed = parser.parse_args(remaining)
        return ParsedArgs(
            command="code",
            intent=intent,
            policy_path=parsed.policy_path,
            verbose=parsed.verbose,
            dry_run=parsed.dry_run,
            stream=parsed.stream
        )
    
    def _parse_status(self, args: List[str]) -> ParsedArgs:
        """Parse 'status' command arguments."""
        parser = argparse.ArgumentParser(prog="aureus status")
        parser.add_argument("--policy", dest="policy_path", help="Policy file path")
        parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

        parsed = parser.parse_args(args)
        return ParsedArgs(
            command="status",
            policy_path=parsed.policy_path,
            verbose=parsed.verbose
        )

    def _parse_budget(self, args: List[str]) -> ParsedArgs:
        """Parse 'budget' command arguments."""
        parser = argparse.ArgumentParser(
            prog="aureus budget",
            description="Show project budget usage dashboard",
        )
        parser.add_argument("--policy", dest="policy_path", help="Policy file path")
        parser.add_argument("--verbose", "-v", action="store_true",
                            help="Show per-session build history")
        parser.add_argument("--no-color", dest="no_color", action="store_true",
                            help="Disable ANSI color codes (for plain-text logs)")
        parser.add_argument("--reset", action="store_true",
                            help="Reset all budget counters (keeps policy limits)")

        parsed = parser.parse_args(args)
        return ParsedArgs(
            command="budget",
            policy_path=parsed.policy_path,
            verbose=parsed.verbose,
            # Piggy-back extra flags using the dry_run / stream fields
            dry_run=parsed.reset,
            stream=not parsed.no_color,
        )
    
    def _parse_explain(self, args: List[str]) -> ParsedArgs:
        """Parse 'explain' command arguments."""
        # Check if "explain code" subcommand
        if len(args) > 0 and args[0] == "code":
            from src.cli.code_understanding import main_explain_code
            sys.exit(main_explain_code(args[1:]))
        
        # Default target is "last" if nothing specified
        target = "last" if len(args) == 0 else args[0]
        
        return ParsedArgs(
            command="explain",
            explain_target=target,
            verbose=False
        )


# ============================================================================
# CLI Output Formatter
# ============================================================================

class CLIFormatter:
    """
    Format CLI output for terminal display.
    
    Provides consistent formatting for:
    - Success messages
    - Error messages
    - Info messages
    - Tables
    """
    
    def success(self, message: str) -> str:
        """Format success message."""
        return f"✓ SUCCESS: {message}"
    
    def error(self, message: str) -> str:
        """Format error message."""
        return f"✗ ERROR: {message}"
    
    def info(self, message: str) -> str:
        """Format info message."""
        return f"ℹ {message}"
    
    def warning(self, message: str) -> str:
        """Format warning message."""
        return f"⚠ WARNING: {message}"
    
    def table(self, headers: List[str], rows: List[List[str]]) -> str:
        """
        Format tabular data.
        
        Args:
            headers: Column headers
            rows: Data rows
        
        Returns:
            Formatted table string
        """
        # Calculate column widths
        col_widths = [len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                col_widths[i] = max(col_widths[i], len(str(cell)))
        
        # Build table
        lines = []
        
        # Header
        header_line = " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers))
        lines.append(header_line)
        lines.append("-" * len(header_line))
        
        # Rows
        for row in rows:
            row_line = " | ".join(str(cell).ljust(col_widths[i]) for i, cell in enumerate(row))
            lines.append(row_line)
        
        return "\n".join(lines)


# ============================================================================
# Command Implementations
# ============================================================================

class InitCommand(BaseCommand):
    """Initialize AUREUS project with default policy."""
    
    def __init__(
        self,
        project_root: Optional[Path] = None,
        policy_path: Optional[Path] = None,
        verbose: bool = False,
        interactive: bool = False
    ):
        super().__init__(project_root=project_root, verbose=verbose, dry_run=False)
        self.policy_path = policy_path or (self.project_root / ".aureus/policy.yaml")
        self.interactive = interactive
        self.loader = PolicyLoader()
    
    def execute(self, args: Optional[argparse.Namespace] = None) -> Dict[str, Any]:
        """
        Execute init command.
        
        Args:
            args: Optional parsed arguments
            
        Returns:
            Result dictionary with status
        """
        self._verbose_print("Initializing AUREUS project")
        
        return self._handle_execution(
            self._perform_init,
            context="Project initialization"
        )
    
    def _perform_init(self) -> Dict[str, Any]:
        """Perform initialization"""
        # Check if policy already exists
        if self.policy_path.exists() and not self.interactive:
            raise CLIError(
                f"Policy already exists at {self.policy_path}\n"
                f"  Use --force to overwrite, or --interactive to reconfigure"
            )
        
        # Interactive wizard mode
        if self.interactive:
            from src.cli.onboarding_wizard import OnboardingWizard
            wizard = OnboardingWizard(
                project_root=Path.cwd(),
                policy_path=self.policy_path
            )
            policy = wizard.run()
            
            return {
                "status": "success",
                "message": f"Interactive setup complete",
                "policy_path": str(self.policy_path)
            }
        
        # Non-interactive mode: create default policy
        budget = Budget(
            max_loc=10000,
            max_modules=8,
            max_files=30,
            max_dependencies=20
        )
        
        policy = Policy(
            version="1.0",
            project_name=Path.cwd().name,
            project_root=Path.cwd(),
            budgets=budget,
            permissions={
                "tools": {
                    "file_read": "allow",
                    "file_write": "allow",
                    "file_delete": "prompt",
                    "shell_exec": "prompt"
                }
            }
        )
        
        # Save policy
        try:
            self.loader.save(policy, self.policy_path)
            print(f"✓ Initialized policy at {self.policy_path}")
            print(f"  Max LOC: {budget.max_loc:,} | Files: {budget.max_files} | Deps: {budget.max_dependencies}")
            print(f"\n💡 Tip: Run 'aureus init --interactive' for guided setup")
            return {
                "status": "success",
                "message": f"Initialized policy at {self.policy_path}",
                "policy_path": str(self.policy_path)
            }
        except Exception as e:
            raise CLIError(f"Failed to initialize policy: {e}")


class CodeCommand(BaseCommand):
    """Execute coding task with governance."""
    
    def __init__(
        self,
        intent: str,
        project_root: Optional[Path] = None,
        policy_path: Optional[Path] = None,
        verbose: bool = False,
        dry_run: bool = False,
        stream: bool = True
    ):
        super().__init__(project_root=project_root, verbose=verbose, dry_run=dry_run)
        self.intent = intent
        self.policy_path = policy_path or (self.project_root / ".aureus/policy.yaml")
        self.stream = stream
        self.loader = PolicyLoader()
    
    def execute(self, args: Optional[argparse.Namespace] = None) -> Dict[str, Any]:
        """
        Execute code command.
        
        Args:
            args: Optional parsed arguments
            
        Returns:
            Result dictionary with status
        
        Raises:
            CLIError: If policy not found or execution fails
        """
        global _cancellation_requested
        
        # Check for cancellation
        if _cancellation_requested:
            return self._format_error(Exception("Cancelled by user"), "Code generation")
        
        # Dry-run mode notification
        if self.dry_run:
            self._dry_run_print("Code generation - no files will be modified")
            print("🔍 DRY-RUN MODE: No files will be modified\n")
        
        self._validate_file_exists(self.policy_path)
        self._verbose_print(f"Loading policy from {self.policy_path}")
        
        return self._handle_execution(
            self._execute_build,
            context="Code generation"
        )
    
    def _execute_build(self) -> Dict[str, Any]:
        """Execute the actual build"""
        # Load policy
        try:
            policy = self.loader.load(self.policy_path)
        except PolicyLoadError as e:
            raise CLIError(f"Failed to load policy: {e}")
        
        # Implement full GVUFD -> SPK -> UVUAS pipeline
        try:
            from src.agents.builder import BuilderAgent
            from src.model_provider import ModelProviderFactory, TaskType
            from pathlib import Path
            import os
            
            # Initialize memory directory
            memory_dir = Path(".aureus/memory")
            memory_dir.mkdir(parents=True, exist_ok=True)
            
            # Create model provider using intelligent factory
            # Supports environment configuration (AUREUS_MODEL_PROVIDER, AUREUS_MODEL_API_KEY)
            # and task-based routing via ModelSelector
            try:
                # For code generation tasks, prefer balanced quality/speed
                model_provider = ModelProviderFactory.create_for_task(
                    task_type=TaskType.CODE_GENERATION,
                    workspace_root=Path.cwd()
                )
                print(f"🤖 Using {model_provider.model_name} for code generation")
                
            except ValueError as e:
                # Fallback to environment-based selection on error
                print(f"⚠️  Model selection failed: {e}")
                model_provider = ModelProviderFactory.create(workspace_root=Path.cwd())
                
                if model_provider.model_name == "mock-model":
                    print("⚠️  Using MockProvider (no actual code generation)")
                    print("   Set AUREUS_MODEL_PROVIDER=openai or anthropic with AUREUS_MODEL_API_KEY to enable real LLM")
                else:
                    print(f"🤖 Using {model_provider.model_name}")
            
            # Initialize unified builder with optional memory features
            # Enable memory tracking if not using MockProvider
            enable_memory = model_provider.model_name != "mock-model"
            
            builder = BuilderAgent(
                policy=policy,
                model_provider=model_provider,
                enable_memory=enable_memory,
                storage_dir=memory_dir
            )
            
            if enable_memory:
                print("📝 Memory tracking enabled (trajectory, cost ledger, pattern learning)")
            
            # Setup streaming callback if enabled
            if self.stream:
                def on_token(token: str):
                    """Stream tokens as they arrive"""
                    if not _cancellation_requested:
                        print(token, end="", flush=True)
                
                # Monkey-patch streaming support (will enhance builder later)
                builder._stream_callback = on_token
            
            # Execute build with full pipeline
            print(f"\n🎯 Intent: {self.intent}")
            print("⚙️  Processing...\n")
            
            # Create progress indicator for 3-tier pipeline
            progress = None
            if self.stream:  # Only show progress in stream mode
                try:
                    from src.cli.ui.progress_indicators import MultiPhaseProgress
                    phases = ["Specification", "Cost Analysis", "Code Generation"]
                    progress = MultiPhaseProgress(phases, use_color=True)
                    print("")  # Add spacing before progress bars
                except ImportError:
                    pass  # Progress indicators optional
            
            result = builder.build(intent=self.intent, progress_callback=progress)
            
            # Finish progress display
            if progress:
                print("")  # Add spacing after progress bars

            # Record budget consumption for dashboard
            try:
                from src.cli.budget_dashboard import BudgetDashboard
                dashboard = BudgetDashboard(Path.cwd(), policy)
                dashboard.record_build(
                    result,
                    intent=self.intent,
                    session_id=getattr(builder, "current_session_id", None),
                )
            except Exception:
                pass  # Budget tracking must never break the build

            # Check if cancelled during build
            if _cancellation_requested:
                print("\n⚠️  Build cancelled")
                return {"status": "cancelled", "message": "Operation cancelled by user"}
            
            # Dry-run: show what would be done without writing
            if self.dry_run:
                print("\n📄 Files that would be created/modified:")
                if hasattr(result, 'files_created'):
                    for f in result.files_created:
                        print(f"  + {f}")
                if hasattr(result, 'files_modified'):
                    for f in result.files_modified:
                        print(f"  ~ {f}")
                print("\n✅ Dry-run complete (no files written)")
                return {
                    "status": "dry-run",
                    "message": "Dry-run completed - no files modified",
                    "would_create": result.files_created if hasattr(result, 'files_created') else [],
                    "would_modify": result.files_modified if hasattr(result, 'files_modified') else []
                }
            
            # Show execution log for debugging
            if self.verbose or not result.success:
                print("\n📋 Execution Log:")
                for entry in builder.execution_log:
                    print(f"  - {entry}")

            # Show detailed error trace in verbose mode
            if self.verbose and hasattr(result, 'error') and result.error:
                print("\n🔍 Detailed Error Trace:")
                import traceback
                print(traceback.format_exc())

            # Show rich build-failure message when build fails
            if not result.success:
                error_msg = result.error if hasattr(result, 'error') and result.error else "Build did not complete"
                budget_status = None
                alternatives = None
                if hasattr(result, 'cost') and result.cost:
                    budget_status = getattr(result.cost, 'budget_status', None)
                    alternatives = getattr(result.cost, 'alternatives', None)
                try:
                    from src.cli.ui.error_display import format_build_failure
                    print(format_build_failure(
                        error_msg,
                        alternatives=alternatives,
                        budget_status=budget_status,
                        use_color=self.stream,
                    ))
                except Exception:
                    pass  # Never break output

            # Show compact budget summary after each build
            try:
                from src.cli.budget_dashboard import BudgetDashboard
                dashboard = BudgetDashboard(Path.cwd(), policy)
                print(dashboard.format_post_build_summary(use_color=self.stream))
            except Exception:
                pass  # Must never break build output
            
            return {
                "status": "success" if result.success else "failure",
                "message": result.message if hasattr(result, 'message') else "Build completed",
                "files_created": result.files_created if hasattr(result, 'files_created') else [],
                "files_modified": result.files_modified if hasattr(result, 'files_modified') else [],
                "cost": result.cost if hasattr(result, 'cost') else 0.0
            }
        
        except Exception as e:
            # Show rich error message for AUREUSError, plain for others
            try:
                from src.errors import AUREUSError
                from src.cli.ui.error_display import ErrorFormatter
                fmt = ErrorFormatter(use_color=self.stream)
                if isinstance(e, AUREUSError):
                    print(fmt.format_aureus_error(e))
                else:
                    print(fmt.format_unexpected_error(e))
            except Exception:
                pass  # Last-resort fallback
            return {
                "status": "error",
                "message": f"Build error: {str(e)}",
                "intent": self.intent,
                "policy": getattr(policy, "project_name", "unknown"),
                "error": str(e)
            }


class StatusCommand(BaseCommand):
    """Show project status and budget usage."""

    def __init__(
        self,
        project_root: Optional[Path] = None,
        policy_path: Optional[Path] = None,
        verbose: bool = False
    ):
        super().__init__(project_root=project_root, verbose=verbose, dry_run=False)
        self.policy_path = policy_path or (self.project_root / ".aureus/policy.yaml")
        self.loader = PolicyLoader()

    def execute(self, args: Optional[argparse.Namespace] = None) -> Dict[str, Any]:
        """
        Execute status command.

        Args:
            args: Optional parsed arguments
            
        Returns:
            Result dictionary with budget info
        """
        self._validate_file_exists(self.policy_path)
        self._verbose_print(f"Loading policy from {self.policy_path}")
        
        return self._handle_execution(
            self._show_status,
            context="Status display"
        )
    
    def _show_status(self) -> Dict[str, Any]:
        """Show project status"""
        # Load policy
        try:
            policy = self.loader.load(self.policy_path)
        except PolicyLoadError as e:
            raise CLIError(f"Failed to load policy: {e}")

        # Print budget dashboard inline
        try:
            from src.cli.budget_dashboard import BudgetDashboard
            dashboard = BudgetDashboard(Path.cwd(), policy)
            print(dashboard.format_dashboard(verbose=self.verbose))
        except Exception:
            pass  # Never break status

        return {
            "status": "success",
            "message": f"Project: {policy.project_name}",
            "budgets": {
                "max_loc": policy.budgets.max_loc,
                "max_files": policy.budgets.max_files,
                "max_modules": policy.budgets.max_modules,
                "max_dependencies": policy.budgets.max_dependencies,
            },
        }


class BudgetCommand(BaseCommand):
    """
    Display the full budget dashboard.

    Sub-options:
    - default: show progress bars for all metrics
    - --verbose / -v: also show per-session build history
    - --no-color: plain-text output (good for CI logs)
    - --reset: clear all usage counters (keeps policy limits)
    """

    def __init__(
        self,
        project_root: Optional[Path] = None,
        policy_path: Optional[Path] = None,
        verbose: bool = False,
        use_color: bool = True,
        reset: bool = False,
    ):
        super().__init__(project_root=project_root, verbose=verbose, dry_run=False)
        self.policy_path = policy_path or (self.project_root / ".aureus/policy.yaml")
        self.use_color = use_color
        self.reset = reset
        self.loader = PolicyLoader()

    def execute(self, args: Optional[argparse.Namespace] = None) -> Dict[str, Any]:
        """Execute budget command."""
        self._verbose_print("Loading budget dashboard")
        
        return self._handle_execution(
            self._show_budget,
            context="Budget dashboard"
        )
    
    def _show_budget(self) -> Dict[str, Any]:
        """Show budget dashboard"""
        from src.cli.budget_dashboard import BudgetDashboard

        # Load policy (optional — dashboard has safe defaults)
        policy = None
        if self.policy_path.exists():
            try:
                policy = self.loader.load(self.policy_path)
            except PolicyLoadError:
                pass

        dashboard = BudgetDashboard(self.project_root, policy)

        if self.reset:
            dashboard.reset()
            return self._format_success("Budget counters reset. All usage cleared.")

        print(dashboard.format_dashboard(
            use_color=self.use_color,
            verbose=self.verbose,
        ))

        return {
            "status": "success",
            "message": "",   # dashboard already printed inline
        }


class ExplainCommand(BaseCommand):
    """Explain agent decisions for transparency."""
    
    def __init__(
        self,
        target: str,
        project_root: Optional[Path] = None,
        verbose: bool = False
    ):
        """
        Initialize explain command.
        
        Args:
            target: What to explain ("last", "last-rejection", decision ID, or "list")
            project_root: Project root directory
            verbose: Verbose output
        """
        super().__init__(project_root=project_root, verbose=verbose, dry_run=False)
        self.target = target
    
    def execute(self, args: Optional[argparse.Namespace] = None) -> Dict[str, Any]:
        """
        Execute explain command.
        
        Args:
            args: Optional parsed arguments
            
        Returns:
            Result dictionary with explanation
        """
        self._verbose_print(f"Explaining target: {self.target}")
        
        return self._handle_execution(
            self._get_explanation,
            context="Explanation"
        )
    
    def _get_explanation(self) -> Dict[str, Any]:
        """Get explanation for target"""
        from src.harness.explainer import Explainer
        
        explainer = Explainer()
        
        # Handle different targets
        if self.target == "list":
            explanation = explainer.list_recent_decisions(limit=20)
        elif self.target == "last":
            explanation = explainer.explain_last_decision()
            if explanation is None:
                explanation = "No recent decisions found. Run 'aureus code <intent>' to generate decisions."
        elif self.target == "last-rejection":
            explanation = explainer.explain_last_rejection()
            if explanation is None:
                explanation = "No recent rejections found."
        else:
            # Treat as decision ID
            explanation = explainer.explain_decision(self.target)
            if explanation is None:
                explanation = f"Decision not found: {self.target}\nUse 'aureus explain list' to see available decisions."
        
        return {
            "status": "success",
            "message": explanation
        }
        return {
            "status": "success",
            "project": policy.project_name,
            "budgets": {
                "max_loc": policy.budgets.max_loc,
                "max_modules": policy.budgets.max_modules,
                "max_files": policy.budgets.max_files,
                "max_dependencies": policy.budgets.max_dependencies
            }
        }


# ============================================================================
# Main CLI Orchestrator
# ============================================================================

class CLI:
    """
    Main CLI orchestrator.
    
    Parses arguments, dispatches to command handlers,
    and formats output.
    """
    
    def __init__(self):
        self.formatter = CLIFormatter()
    
    def execute(self, args: ParsedArgs) -> Dict[str, Any]:
        """
        Execute parsed command.
        
        Args:
            args: Parsed command line arguments
        
        Returns:
            Result dictionary
        
        Raises:
            CLIError: If command execution fails
        """
        policy_path = Path(args.policy_path) if args.policy_path else None
        
        if args.command == "init":
            cmd = InitCommand(
                policy_path=policy_path,
                verbose=args.verbose,
                interactive=getattr(args, 'interactive', False)
            )
            return cmd.execute()
        
        elif args.command == "code":
            cmd = CodeCommand(
                intent=args.intent,
                policy_path=policy_path,
                verbose=args.verbose,
                dry_run=args.dry_run,
                stream=args.stream
            )
            return cmd.execute()
        
        elif args.command == "status":
            cmd = StatusCommand(policy_path=policy_path, verbose=args.verbose)
            return cmd.execute()

        elif args.command == "budget":
            cmd = BudgetCommand(
                policy_path=policy_path,
                verbose=args.verbose,
                use_color=args.stream,    # --no-color sets stream=False
                reset=args.dry_run,       # --reset piggy-backs on dry_run
            )
            return cmd.execute()

        elif args.command == "explain":
            cmd = ExplainCommand(target=args.explain_target, verbose=args.verbose)
            return cmd.execute()
        
        else:
            raise CLIError(
                f"Unknown command: {args.command}\n"
                f"  Available commands: init, code, status, budget, explain, memory, test, validate, lint, debug,\n"
                f"                      find, usages, impact, test-gen, refactor, review, doctor,\n"
                f"                      adr, skills, learn, collaborate"
            )
    
    def run(self, argv: List[str]) -> int:
        """
        Main entry point for CLI.
        
        Args:
            argv: Command line arguments (including program name)
        
        Returns:
            Exit code (0 for success, 1 for error)
        """
        # Detect --no-color / --no-stream early for error formatting
        use_color = "--no-color" not in argv and "--no-stream" not in argv

        try:
            # Parse arguments
            parser = CLIParser()
            args = parser.parse(argv[1:])  # Skip program name
            
            # Execute command
            result = self.execute(args)
            
            # Print success
            if result.get("message"):
                print(self.formatter.success(result["message"]))
            
            return 0
        
        except CLIError as e:
            from src.cli.ui.error_display import ErrorFormatter
            fmt = ErrorFormatter(use_color=use_color)
            print(fmt.format_cli_error(str(e)), file=sys.stderr)
            return 1
        except Exception as e:
            from src.errors import AUREUSError
            from src.cli.ui.error_display import ErrorFormatter
            fmt = ErrorFormatter(use_color=use_color)
            if isinstance(e, AUREUSError):
                print(fmt.format_aureus_error(e), file=sys.stderr)
            else:
                print(fmt.format_unexpected_error(e), file=sys.stderr)
            return 1


def main():
    """Entry point for aureus command."""
    cli = CLI()
    sys.exit(cli.run(sys.argv))


if __name__ == "__main__":
    main()
