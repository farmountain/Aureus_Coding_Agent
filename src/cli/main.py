"""
AUREUS CLI - Command line interface.

Entry point for all AUREUS operations:
- init: Initialize project with policy
- code: Execute coding task
- status: Show project status
"""

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

from src.interfaces import Policy, Budget
from src.governance.policy import PolicyLoader, PolicyLoadError


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


class CLIParser:
    """
    Parse AUREUS command line arguments.
    
    Commands:
    - init [--policy PATH]: Initialize project
    - code <intent> [--policy PATH]: Execute task
    - status [--policy PATH]: Show status
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
            raise CLIError("No command specified. Use: init, code, or status")
        
        command = args[0]
        
        # Parse based on command
        if command == "init":
            return self._parse_init(args[1:])
        elif command == "code":
            return self._parse_code(args[1:])
        elif command == "status":
            return self._parse_status(args[1:])
        else:
            raise CLIError(f"Unknown command: {command}")
    
    def _parse_init(self, args: List[str]) -> ParsedArgs:
        """Parse 'init' command arguments."""
        parser = argparse.ArgumentParser(prog="aureus init")
        parser.add_argument("--policy", dest="policy_path", help="Policy file path")
        parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
        
        parsed = parser.parse_args(args)
        return ParsedArgs(
            command="init",
            policy_path=parsed.policy_path,
            verbose=parsed.verbose
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
        parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
        
        parsed = parser.parse_args(remaining)
        return ParsedArgs(
            command="code",
            intent=intent,
            policy_path=parsed.policy_path,
            verbose=parsed.verbose
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

class InitCommand:
    """Initialize AUREUS project with default policy."""
    
    def __init__(self, policy_path: Optional[Path] = None, verbose: bool = False):
        self.policy_path = policy_path or Path(".aureus/policy.yaml")
        self.verbose = verbose
        self.loader = PolicyLoader()
    
    def execute(self) -> Dict[str, Any]:
        """
        Execute init command.
        
        Returns:
            Result dictionary with status
        """
        # Create default policy
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
            return {
                "status": "success",
                "message": f"Initialized policy at {self.policy_path}",
                "policy_path": str(self.policy_path)
            }
        except Exception as e:
            raise CLIError(f"Failed to initialize policy: {e}")


class CodeCommand:
    """Execute coding task with governance."""
    
    def __init__(self, intent: str, policy_path: Optional[Path] = None, verbose: bool = False):
        self.intent = intent
        self.policy_path = policy_path or Path(".aureus/policy.yaml")
        self.verbose = verbose
        self.loader = PolicyLoader()
    
    def execute(self) -> Dict[str, Any]:
        """
        Execute code command.
        
        Returns:
            Result dictionary with status
        
        Raises:
            CLIError: If policy not found or execution fails
        """
        # Load policy
        if not self.policy_path.exists():
            raise CLIError(f"Policy file not found: {self.policy_path}. Run 'aureus init' first.")
        
        try:
            policy = self.loader.load(self.policy_path)
        except PolicyLoadError as e:
            raise CLIError(f"Failed to load policy: {e}")
        
        # Implement full GVUFD -> SPK -> UVUAS pipeline
        try:
            from src.agents.builder_enhanced import BuilderEnhanced
            from src.memory.trajectory import TrajectoryStore
            from src.memory.cost_ledger import CostLedger
            from pathlib import Path
            
            # Initialize memory components
            memory_dir = Path(".aureus/memory")
            memory_dir.mkdir(parents=True, exist_ok=True)
            
            trajectory_store = TrajectoryStore(storage_dir=memory_dir / "trajectories")
            cost_ledger = CostLedger(storage_dir=memory_dir / "costs")
            
            # Initialize enhanced builder with memory
            builder = BuilderEnhanced(
                policy=policy,
                project_root=Path.cwd(),
                trajectory_store=trajectory_store,
                cost_ledger=cost_ledger
            )
            
            # Execute build with full pipeline
            result = builder.build(intent=self.intent)
            
            # Save trajectory
            session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            trajectory_store.save_trajectory(
                session_id=session_id,
                actions=builder.execution_log,
                outcome="success" if result.success else "failure"
            )
            
            return {
                "status": "success" if result.success else "failure",
                "message": f"Build completed for: {policy.project_name}",
                "intent": self.intent,
                "policy": policy.project_name,
                "files_created": result.files_created,
                "files_modified": result.files_modified,
                "tests_passed": result.tests_passed,
                "cost": result.cost.to_dict() if result.cost else None,
                "session_id": session_id
            }
        
        except Exception as e:
            # Fallback to basic execution
            return {
                "status": "error",
                "message": f"Build error: {str(e)}",
                "intent": self.intent,
                "policy": policy.project_name,
                "error": str(e)
            }


class StatusCommand:
    """Show project status and budget usage."""
    
    def __init__(self, policy_path: Optional[Path] = None, verbose: bool = False):
        self.policy_path = policy_path or Path(".aureus/policy.yaml")
        self.verbose = verbose
        self.loader = PolicyLoader()
    
    def execute(self) -> Dict[str, Any]:
        """
        Execute status command.
        
        Returns:
            Result dictionary with budget info
        """
        # Load policy
        if not self.policy_path.exists():
            raise CLIError(f"Policy file not found: {self.policy_path}")
        
        try:
            policy = self.loader.load(self.policy_path)
        except PolicyLoadError as e:
            raise CLIError(f"Failed to load policy: {e}")
        
        # Return status info
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
            cmd = InitCommand(policy_path=policy_path, verbose=args.verbose)
            return cmd.execute()
        
        elif args.command == "code":
            cmd = CodeCommand(
                intent=args.intent,
                policy_path=policy_path,
                verbose=args.verbose
            )
            return cmd.execute()
        
        elif args.command == "status":
            cmd = StatusCommand(policy_path=policy_path, verbose=args.verbose)
            return cmd.execute()
        
        else:
            raise CLIError(f"Unknown command: {args.command}")
    
    def run(self, argv: List[str]) -> int:
        """
        Main entry point for CLI.
        
        Args:
            argv: Command line arguments (including program name)
        
        Returns:
            Exit code (0 for success, 1 for error)
        """
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
            print(self.formatter.error(str(e)), file=sys.stderr)
            return 1
        except Exception as e:
            print(self.formatter.error(f"Unexpected error: {e}"), file=sys.stderr)
            return 1


def main():
    """Entry point for aureus command."""
    cli = CLI()
    sys.exit(cli.run(sys.argv))


if __name__ == "__main__":
    main()
