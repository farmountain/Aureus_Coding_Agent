"""
Security and Sandbox Enforcement

Provides explicit separation between:
- Aureus agent code (this codebase)
- User workspace code (governed by policy)

Enforces boundaries for:
- Normal operations (user workspace only)
- Self-play mode (Aureus code only)
"""

from pathlib import Path
from typing import Optional
import os
from dataclasses import dataclass


@dataclass
class SandboxViolation(Exception):
    """Raised when sandbox boundary is violated"""
    path: Path
    reason: str
    
    def __str__(self):
        return f"Sandbox violation for {self.path}: {self.reason}"


class Sandbox:
    """
    Enforces code separation between Aureus agent and user workspace
    
    Key Boundaries:
    - Aureus code: /aureus/src/, /aureus/tests/, /aureus/docs/
    - User workspace: {policy.project_root}/
    - Immutable files: LICENSE, principles.py, sandbox.py
    
    Validation:
    - Normal mode: Can only modify user workspace
    - Self-play mode: Can only modify Aureus code (except immutable)
    """
    
    # Root directory of Aureus agent codebase
    AUREUS_ROOT = Path(__file__).parent.parent.parent.resolve()
    
    # Immutable files that cannot be modified even in self-play
    IMMUTABLE_FILES = {
        "LICENSE",
        "COPYRIGHT",
        "principles.py",
        "sandbox.py",
        "pyproject.toml"  # Requires manual review
    }
    
    # Immutable directories (never modify)
    IMMUTABLE_DIRS = {
        ".git",
        ".github",
        "__pycache__"
    }
    
    @staticmethod
    def is_aureus_code(path: Path) -> bool:
        """
        Check if path is Aureus agent code
        
        Args:
            path: Path to check
            
        Returns:
            True if path is within Aureus codebase
        """
        try:
            resolved = path.resolve()
            resolved.relative_to(Sandbox.AUREUS_ROOT)
            return True
        except (ValueError, OSError):
            return False
    
    @staticmethod
    def is_user_workspace(path: Path, project_root: Path) -> bool:
        """
        Check if path is in user workspace
        
        Args:
            path: Path to check
            project_root: User's project root from policy
            
        Returns:
            True if path is in user workspace (and not Aureus code)
        """
        try:
            resolved = path.resolve()
            project_resolved = project_root.resolve()
            
            # Must be within project_root
            resolved.relative_to(project_resolved)
            
            # Must NOT be Aureus code
            if Sandbox.is_aureus_code(resolved):
                return False
            
            return True
        except (ValueError, OSError):
            return False
    
    @staticmethod
    def is_immutable(path: Path) -> bool:
        """
        Check if path is immutable (cannot be modified even in self-play)
        
        Args:
            path: Path to check
            
        Returns:
            True if path is immutable
        """
        # Check filename
        if path.name in Sandbox.IMMUTABLE_FILES:
            return True
        
        # Check if in immutable directory
        for immutable_dir in Sandbox.IMMUTABLE_DIRS:
            try:
                path.relative_to(Sandbox.AUREUS_ROOT / immutable_dir)
                return True
            except ValueError:
                continue
        
        return False
    
    @staticmethod
    def validate_path_in_workspace(
        path: Path,
        project_root: Path
    ) -> Path:
        """
        Validate path is within workspace and return resolved path
        
        Args:
            path: Path to validate (can be relative)
            project_root: Workspace root
            
        Returns:
            Resolved absolute path
            
        Raises:
            SandboxViolation: If path escapes workspace
        """
        # Resolve relative to project_root
        if not path.is_absolute():
            path = project_root / path
        
        resolved = path.resolve()
        project_resolved = project_root.resolve()
        
        try:
            resolved.relative_to(project_resolved)
        except ValueError:
            raise SandboxViolation(
                path=resolved,
                reason=f"Path escapes workspace root: {project_resolved}"
            )
        
        # Ensure not trying to modify Aureus code in normal mode
        if Sandbox.is_aureus_code(resolved):
            raise SandboxViolation(
                path=resolved,
                reason="Cannot modify Aureus agent code from user workspace"
            )
        
        return resolved
    
    @staticmethod
    def validate_modification(
        path: Path,
        project_root: Optional[Path] = None,
        is_self_play: bool = False
    ) -> bool:
        """
        Validate if path modification is allowed
        
        Args:
            path: Path to modify
            project_root: User workspace root (None for self-play)
            is_self_play: Is this Aureus self-improvement?
            
        Returns:
            True if modification allowed
            
        Raises:
            SandboxViolation: If modification not allowed
        """
        resolved = path.resolve()
        
        # Check immutable first (applies to all modes)
        if Sandbox.is_immutable(resolved):
            raise SandboxViolation(
                path=resolved,
                reason=f"File {resolved.name} is immutable"
            )
        
        if is_self_play:
            # Self-play mode: Can only modify Aureus code
            if not Sandbox.is_aureus_code(resolved):
                raise SandboxViolation(
                    path=resolved,
                    reason="Self-play mode can only modify Aureus agent code"
                )
            
            # Validate within allowed Aureus directories
            allowed_dirs = ["src", "tests", "docs", "examples", "config"]
            in_allowed_dir = any(
                str(resolved).startswith(str(Sandbox.AUREUS_ROOT / d))
                for d in allowed_dirs
            )
            
            if not in_allowed_dir:
                raise SandboxViolation(
                    path=resolved,
                    reason=f"Self-play can only modify: {', '.join(allowed_dirs)}"
                )
        else:
            # Normal mode: Can only modify user workspace
            if project_root is None:
                raise SandboxViolation(
                    path=resolved,
                    reason="project_root required for non-self-play mode"
                )
            
            if not Sandbox.is_user_workspace(resolved, project_root):
                raise SandboxViolation(
                    path=resolved,
                    reason=f"Path must be within project root: {project_root}"
                )
        
        return True
    
    @staticmethod
    def get_aureus_metadata_dir(project_root: Path) -> Path:
        """
        Get Aureus metadata directory for a workspace
        
        Args:
            project_root: User workspace root
            
        Returns:
            Path to .aureus directory
        """
        return project_root / ".aureus"
    
    @staticmethod
    def ensure_metadata_dir(project_root: Path) -> Path:
        """
        Ensure .aureus metadata directory exists
        
        Args:
            project_root: User workspace root
            
        Returns:
            Path to .aureus directory
        """
        metadata_dir = Sandbox.get_aureus_metadata_dir(project_root)
        metadata_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        (metadata_dir / "memory").mkdir(exist_ok=True)
        (metadata_dir / "backups").mkdir(exist_ok=True)
        (metadata_dir / "patterns").mkdir(exist_ok=True)
        
        return metadata_dir


# Convenience functions for common checks

def validate_file_read(path: Path, project_root: Path) -> Path:
    """Validate file read is allowed"""
    return Sandbox.validate_path_in_workspace(path, project_root)


def validate_file_write(
    path: Path,
    project_root: Path,
    is_self_play: bool = False
) -> Path:
    """Validate file write is allowed"""
    resolved = path if path.is_absolute() else project_root / path
    Sandbox.validate_modification(resolved, project_root, is_self_play)
    return resolved.resolve()


def is_safe_path(path: Path, project_root: Path) -> bool:
    """Check if path is safe to access"""
    try:
        Sandbox.validate_path_in_workspace(path, project_root)
        return True
    except SandboxViolation:
        return False
