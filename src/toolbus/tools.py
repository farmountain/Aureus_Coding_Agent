"""
Tool Bus - Permission-gated tool execution with rollback support

All tools must pass through:
1. Policy Gate - Permission check
2. Pricing Gate - Budget check
3. Execution - Sandboxed operation
4. Rollback - Snapshot/restore capability

Phase 1 Tools:
- FileReadTool - Read files with permissions
- FileWriteTool - Write files with rollback
- GrepSearchTool - Code search
- ShellTool - Sandboxed shell execution (Phase 2)
"""

from typing import Protocol, Any, Dict, Optional, List
from pathlib import Path
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import json


@dataclass
class ToolResult:
    """Result from tool execution"""
    success: bool
    output: Any
    tool_name: str
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            "success": self.success,
            "output": self.output,
            "tool_name": self.tool_name,
            "error": self.error,
            "metadata": self.metadata
        }


class Tool(Protocol):
    """
    Protocol for all tools in the Tool Bus
    
    All tools must implement execute() method
    """
    
    name: str
    description: str
    required_permission: str
    
    def execute(self, **kwargs) -> ToolResult:
        """
        Execute the tool with given parameters
        
        Returns:
            ToolResult with success status and output
        """
        ...


class BaseTool(ABC):
    """
    Abstract base class for tools
    
    Provides common functionality for all tools
    """
    
    def __init__(self, name: str, description: str, required_permission: str):
        self.name = name
        self.description = description
        self.required_permission = required_permission
    
    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        """Implement tool execution logic"""
        pass
    
    def _success(self, output: Any, **metadata) -> ToolResult:
        """Create success result"""
        return ToolResult(
            success=True,
            output=output,
            tool_name=self.name,
            metadata=metadata
        )
    
    def _error(self, error_message: str, **metadata) -> ToolResult:
        """Create error result"""
        return ToolResult(
            success=False,
            output=None,
            tool_name=self.name,
            error=error_message,
            metadata=metadata
        )


class FileReadTool(BaseTool):
    """
    Tool for reading files with permission checks
    
    Requires: file_read permission
    """
    
    def __init__(self, project_root: Path):
        super().__init__(
            name="file_read",
            description="Read content from files within project root",
            required_permission="file_read"
        )
        self.project_root = project_root.resolve()
    
    def execute(self, **kwargs) -> ToolResult:
        """
        Read file content
        
        Args:
            file_path: Path to file (relative or absolute)
        
        Returns:
            ToolResult with file content
        """
        file_path = kwargs.get("file_path")
        
        if not file_path:
            return self._error("file_path parameter required")
        
        try:
            path = Path(file_path)
            
            # Make absolute relative to project root
            if not path.is_absolute():
                path = self.project_root / path
            
            path = path.resolve()
            
            # Security: Ensure path is within project root
            if not self._is_within_project(path):
                return self._error(
                    f"Access denied: {path} is outside project root",
                    attempted_path=str(path)
                )
            
            # Check file exists
            if not path.exists():
                return self._error(f"File not found: {path}")
            
            if not path.is_file():
                return self._error(f"Not a file: {path}")
            
            # Read content
            content = path.read_text(encoding="utf-8")
            
            return self._success(
                output=content,
                file_path=str(path),
                size_bytes=len(content)
            )
        
        except PermissionError as e:
            return self._error(f"Permission denied: {e}")
        except Exception as e:
            return self._error(f"Error reading file: {e}")
    
    def _is_within_project(self, path: Path) -> bool:
        """Check if path is within project root"""
        try:
            path.relative_to(self.project_root)
            return True
        except ValueError:
            return False


class FileWriteTool(BaseTool):
    """
    Tool for writing files with rollback support
    
    Requires: file_write permission
    Creates backup before writing for rollback
    """
    
    def __init__(self, project_root: Path):
        super().__init__(
            name="file_write",
            description="Write content to files within project root",
            required_permission="file_write"
        )
        self.project_root = project_root.resolve()
        self.backup_dir = project_root / ".aureus" / "backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def execute(self, **kwargs) -> ToolResult:
        """
        Write content to file
        
        Args:
            file_path: Path to file (relative or absolute)
            content: Content to write
            create_backup: Whether to create backup (default: True)
        
        Returns:
            ToolResult with write status
        """
        file_path = kwargs.get("file_path")
        content = kwargs.get("content")
        create_backup = kwargs.get("create_backup", True)
        
        if not file_path:
            return self._error("file_path parameter required")
        
        if content is None:
            return self._error("content parameter required")
        
        try:
            path = Path(file_path)
            
            # Make absolute relative to project root
            if not path.is_absolute():
                path = self.project_root / path
            
            path = path.resolve()
            
            # Security: Ensure path is within project root
            if not self._is_within_project(path):
                return self._error(
                    f"Access denied: {path} is outside project root",
                    attempted_path=str(path)
                )
            
            # Create backup if file exists
            backup_path = None
            if create_backup and path.exists():
                backup_path = self._create_backup(path)
            
            # Create parent directories
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write content
            path.write_text(content, encoding="utf-8")
            
            return self._success(
                output=f"Successfully wrote {len(content)} bytes",
                file_path=str(path),
                backup_path=str(backup_path) if backup_path else None,
                size_bytes=len(content)
            )
        
        except PermissionError as e:
            return self._error(f"Permission denied: {e}")
        except Exception as e:
            return self._error(f"Error writing file: {e}")
    
    def _is_within_project(self, path: Path) -> bool:
        """Check if path is within project root"""
        try:
            path.relative_to(self.project_root)
            return True
        except ValueError:
            return False
    
    def _create_backup(self, path: Path) -> Path:
        """Create backup of file"""
        import shutil
        from datetime import datetime
        
        # Generate backup filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{path.name}.{timestamp}.bak"
        backup_path = self.backup_dir / backup_name
        
        # Copy file to backup
        shutil.copy2(path, backup_path)
        
        return backup_path


class GrepSearchTool(BaseTool):
    """
    Tool for searching code patterns (grep-like)
    
    Requires: file_read permission
    """
    
    def __init__(self, project_root: Path):
        super().__init__(
            name="grep_search",
            description="Search for patterns in files",
            required_permission="file_read"
        )
        self.project_root = project_root.resolve()
    
    def execute(self, **kwargs) -> ToolResult:
        """
        Search for pattern in files
        
        Args:
            pattern: Text pattern to search for
            file_pattern: Glob pattern for files (default: "**/*.py")
            case_sensitive: Case sensitive search (default: True)
            max_results: Maximum results to return (default: 100)
        
        Returns:
            ToolResult with list of matches
        """
        pattern = kwargs.get("pattern")
        file_pattern = kwargs.get("file_pattern", "**/*.py")
        case_sensitive = kwargs.get("case_sensitive", True)
        max_results = kwargs.get("max_results", 100)
        
        if not pattern:
            return self._error("pattern parameter required")
        
        try:
            matches = []
            files_searched = 0
            
            # Search pattern
            search_pattern = pattern if case_sensitive else pattern.lower()
            
            # Iterate matching files
            for file_path in self.project_root.glob(file_pattern):
                if not file_path.is_file():
                    continue
                
                files_searched += 1
                
                try:
                    content = file_path.read_text(encoding="utf-8")
                    lines = content.split("\n")
                    
                    for line_num, line in enumerate(lines, 1):
                        search_line = line if case_sensitive else line.lower()
                        
                        if search_pattern in search_line:
                            matches.append({
                                "file": str(file_path.relative_to(self.project_root)),
                                "line": line_num,
                                "content": line.strip()
                            })
                            
                            if len(matches) >= max_results:
                                break
                
                except Exception:
                    # Skip files that can't be read
                    continue
                
                if len(matches) >= max_results:
                    break
            
            return self._success(
                output=matches,
                files_searched=files_searched,
                matches_found=len(matches)
            )
        
        except Exception as e:
            return self._error(f"Error during search: {e}")


class PermissionChecker:
    """
    Checks if tools have required permissions according to policy
    """
    
    def __init__(self, policy_permissions: Dict[str, bool]):
        """
        Initialize with policy permissions
        
        Args:
            policy_permissions: Dict mapping permission names to allowed status
        """
        self.permissions = policy_permissions
    
    def has_permission(self, permission: str) -> bool:
        """
        Check if permission is granted
        
        Args:
            permission: Permission name (e.g., "file_read", "file_write")
        
        Returns:
            True if permission granted
        """
        return self.permissions.get(permission, False)
    
    def check_tool_permission(self, tool: Tool) -> bool:
        """
        Check if tool has required permission
        
        Args:
            tool: Tool instance
        
        Returns:
            True if tool can execute
        """
        return self.has_permission(tool.required_permission)
