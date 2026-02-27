"""
Git Tool - Version Control Operations

Provides safe Git operations:
- Repository status
- Commit history
- Diffs
- Staging operations
"""

import subprocess
from typing import Dict, Any, Optional, List
from pathlib import Path
from dataclasses import dataclass


@dataclass
class GitResult:
    """Result of Git operation"""
    success: bool
    output: str
    error: Optional[str] = None


class GitTool:
    """
    Git operations tool for version control
    
    Provides safe Git commands for code analysis and tracking:
    - Status checking
    - Commit history
    - Diff generation
    - Blame analysis
    """
    
    # Safe Git commands (read-only or staging)
    SAFE_COMMANDS = {
        'status', 'log', 'diff', 'show', 'blame', 'branch',
        'add', 'reset', 'checkout', 'stash'
    }
    
    # Dangerous commands (modify history)
    DANGEROUS_COMMANDS = {
        'commit', 'push', 'pull', 'fetch', 'merge', 'rebase', 'reset --hard'
    }
    
    def __init__(
        self,
        repo_path: Path,
        allow_commits: bool = False,
        timeout: int = 30
    ):
        """
        Initialize Git tool
        
        Args:
            repo_path: Path to Git repository
            allow_commits: Allow commit operations
            timeout: Command timeout in seconds
        """
        self.repo_path = Path(repo_path)
        self.allow_commits = allow_commits
        self.timeout = timeout
        
        # Verify it's a Git repo
        if not (self.repo_path / '.git').exists():
            raise ValueError(f"Not a Git repository: {repo_path}")
    
    def status(self) -> GitResult:
        """
        Get repository status
        
        Returns:
            GitResult with status information
        """
        return self._run_git(['status', '--short'])
    
    def log(
        self,
        max_count: int = 10,
        oneline: bool = True
    ) -> GitResult:
        """
        Get commit history
        
        Args:
            max_count: Maximum number of commits
            oneline: Use one-line format
            
        Returns:
            GitResult with commit log
        """
        cmd = ['log', f'--max-count={max_count}']
        if oneline:
            cmd.append('--oneline')
        
        return self._run_git(cmd)
    
    def diff(
        self,
        file_path: Optional[str] = None,
        staged: bool = False
    ) -> GitResult:
        """
        Get diff of changes
        
        Args:
            file_path: Specific file to diff (None = all files)
            staged: Show staged changes only
            
        Returns:
            GitResult with diff output
        """
        cmd = ['diff']
        if staged:
            cmd.append('--cached')
        if file_path:
            cmd.append(file_path)
        
        return self._run_git(cmd)
    
    def show(self, commit: str = 'HEAD') -> GitResult:
        """
        Show commit details
        
        Args:
            commit: Commit reference (default: HEAD)
            
        Returns:
            GitResult with commit details
        """
        return self._run_git(['show', commit])
    
    def blame(self, file_path: str) -> GitResult:
        """
        Show line-by-line authorship
        
        Args:
            file_path: File to analyze
            
        Returns:
            GitResult with blame information
        """
        return self._run_git(['blame', file_path])
    
    def add(self, file_path: str) -> GitResult:
        """
        Stage file for commit
        
        Args:
            file_path: File to stage
            
        Returns:
            GitResult with operation status
        """
        return self._run_git(['add', file_path])
    
    def commit(
        self,
        message: str,
        author: Optional[str] = None
    ) -> GitResult:
        """
        Commit staged changes
        
        Args:
            message: Commit message
            author: Author override (format: "Name <email>")
            
        Returns:
            GitResult with commit status
        """
        if not self.allow_commits:
            return GitResult(
                success=False,
                output="",
                error="Commit operations not allowed"
            )
        
        cmd = ['commit', '-m', message]
        if author:
            cmd.extend(['--author', author])
        
        return self._run_git(cmd)
    
    def branch(self, list_all: bool = False) -> GitResult:
        """
        List branches
        
        Args:
            list_all: Include remote branches
            
        Returns:
            GitResult with branch list
        """
        cmd = ['branch']
        if list_all:
            cmd.append('-a')
        
        return self._run_git(cmd)
    
    def _run_git(self, args: List[str]) -> GitResult:
        """
        Run Git command with safety checks
        
        Args:
            args: Git command arguments
            
        Returns:
            GitResult with command output
        """
        if not args:
            return GitResult(
                success=False,
                output="",
                error="Empty Git command"
            )
        
        # Check if command is safe
        cmd_name = args[0]
        if cmd_name not in self.SAFE_COMMANDS and not self.allow_commits:
            return GitResult(
                success=False,
                output="",
                error=f"Git command '{cmd_name}' not allowed"
            )
        
        # Execute Git command
        try:
            result = subprocess.run(
                ['git'] + args,
                cwd=str(self.repo_path),
                capture_output=True,
                text=True,
                timeout=self.timeout,
                check=False
            )
            
            return GitResult(
                success=result.returncode == 0,
                output=result.stdout,
                error=result.stderr if result.returncode != 0 else None
            )
            
        except subprocess.TimeoutExpired:
            return GitResult(
                success=False,
                output="",
                error=f"Git command timed out after {self.timeout} seconds"
            )
        except Exception as e:
            return GitResult(
                success=False,
                output="",
                error=f"Git execution error: {e}"
            )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "tool_name": "git",
            "repo_path": str(self.repo_path),
            "allow_commits": self.allow_commits,
            "timeout": self.timeout
        }
