"""
Shell Tool - Sandboxed Shell Command Execution

Provides safe execution of shell commands with:
- Command whitelisting
- Path sandboxing
- Timeout protection
- Resource limits
"""

import subprocess
import shlex
from typing import Dict, Any, Optional, List
from pathlib import Path
from dataclasses import dataclass


@dataclass
class ShellResult:
    """Result of shell command execution"""
    success: bool
    stdout: str
    stderr: str
    returncode: int
    error: Optional[str] = None


class ShellTool:
    """
    Sandboxed shell command execution tool
    
    Executes shell commands with safety constraints:
    - Command whitelist (only allowed commands)
    - Working directory sandboxing
    - Timeout limits
    - Output size limits
    """
    
    # Default whitelist of safe commands
    DEFAULT_WHITELIST = {
        'ls', 'dir', 'pwd', 'cd', 'cat', 'head', 'tail', 'grep',
        'find', 'echo', 'wc', 'sort', 'uniq', 'diff', 'git'
    }
    
    # Commands that modify filesystem (require explicit permission)
    DANGEROUS_COMMANDS = {
        'rm', 'del', 'mv', 'cp', 'mkdir', 'rmdir', 'chmod', 'chown'
    }
    
    def __init__(
        self,
        working_dir: Path,
        whitelist: Optional[set] = None,
        allow_dangerous: bool = False,
        timeout: int = 30,
        max_output_size: int = 1024 * 1024  # 1MB
    ):
        """
        Initialize shell tool
        
        Args:
            working_dir: Working directory for command execution
            whitelist: Set of allowed commands (None = use default)
            allow_dangerous: Allow dangerous filesystem commands
            timeout: Command timeout in seconds
            max_output_size: Maximum output size in bytes
        """
        self.working_dir = Path(working_dir)
        self.whitelist = whitelist or self.DEFAULT_WHITELIST.copy()
        if allow_dangerous:
            self.whitelist.update(self.DANGEROUS_COMMANDS)
        self.timeout = timeout
        self.max_output_size = max_output_size
        
        # Ensure working directory exists
        self.working_dir.mkdir(parents=True, exist_ok=True)
    
    def execute(self, command: str) -> ShellResult:
        """
        Execute a shell command with safety checks
        
        Args:
            command: Shell command to execute
            
        Returns:
            ShellResult with execution outcome
        """
        # Parse command
        try:
            parts = shlex.split(command)
        except ValueError as e:
            return ShellResult(
                success=False,
                stdout="",
                stderr="",
                returncode=-1,
                error=f"Invalid command syntax: {e}"
            )
        
        if not parts:
            return ShellResult(
                success=False,
                stdout="",
                stderr="",
                returncode=-1,
                error="Empty command"
            )
        
        # Check whitelist
        cmd_name = parts[0]
        if cmd_name not in self.whitelist:
            return ShellResult(
                success=False,
                stdout="",
                stderr="",
                returncode=-1,
                error=f"Command '{cmd_name}' not in whitelist"
            )
        
        # Validate paths don't escape working directory
        if not self._validate_paths(parts):
            return ShellResult(
                success=False,
                stdout="",
                stderr="",
                returncode=-1,
                error="Command attempts to access paths outside working directory"
            )
        
        # Execute command
        try:
            result = subprocess.run(
                parts,
                cwd=str(self.working_dir),
                capture_output=True,
                text=True,
                timeout=self.timeout,
                check=False  # Don't raise on non-zero exit
            )
            
            # Check output size
            stdout = result.stdout[:self.max_output_size]
            stderr = result.stderr[:self.max_output_size]
            
            if len(result.stdout) > self.max_output_size:
                stderr += f"\n[Output truncated at {self.max_output_size} bytes]"
            
            return ShellResult(
                success=result.returncode == 0,
                stdout=stdout,
                stderr=stderr,
                returncode=result.returncode
            )
            
        except subprocess.TimeoutExpired:
            return ShellResult(
                success=False,
                stdout="",
                stderr="",
                returncode=-1,
                error=f"Command timed out after {self.timeout} seconds"
            )
        except Exception as e:
            return ShellResult(
                success=False,
                stdout="",
                stderr="",
                returncode=-1,
                error=f"Execution error: {e}"
            )
    
    def _validate_paths(self, parts: List[str]) -> bool:
        """
        Validate that command doesn't access paths outside working directory
        
        Args:
            parts: Command parts from shlex.split
            
        Returns:
            True if paths are safe, False otherwise
        """
        for part in parts[1:]:  # Skip command name
            # Check if part looks like a path
            if '/' in part or '\\' in part or part.startswith('.'):
                try:
                    # Resolve path relative to working directory
                    path = (self.working_dir / part).resolve()
                    # Check if it's within working directory
                    if not str(path).startswith(str(self.working_dir.resolve())):
                        return False
                except Exception:
                    # If we can't resolve, be safe and reject
                    return False
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "tool_name": "shell",
            "working_dir": str(self.working_dir),
            "whitelist": list(self.whitelist),
            "timeout": self.timeout,
            "max_output_size": self.max_output_size
        }
