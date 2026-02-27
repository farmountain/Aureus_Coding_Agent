"""
Tests for Tool Bus - Permission-gated tools

Tests:
- FileReadTool: Reading files within project root
- FileWriteTool: Writing files with backup
- GrepSearchTool: Searching code patterns
- PermissionChecker: Policy-based permission enforcement
"""

import pytest
from pathlib import Path
import tempfile
import shutil
from src.toolbus import (
    FileReadTool,
    FileWriteTool,
    GrepSearchTool,
    PermissionChecker,
    ToolResult
)


@pytest.fixture
def temp_project():
    """Create temporary project directory"""
    temp_dir = Path(tempfile.mkdtemp())
    
    # Create test files
    (temp_dir / "test.txt").write_text("Hello World")
    (temp_dir / "code.py").write_text("def hello():\n    return 'world'\n")
    (temp_dir / "subdir").mkdir()
    (temp_dir / "subdir" / "nested.txt").write_text("Nested file content")
    
    yield temp_dir
    
    # Cleanup
    shutil.rmtree(temp_dir)


class TestFileReadTool:
    """Test file reading with permissions"""
    
    def test_read_file_success(self, temp_project):
        """Test successful file read"""
        tool = FileReadTool(temp_project)
        
        result = tool.execute(file_path="test.txt")
        
        assert result.success is True
        assert result.output == "Hello World"
        assert result.tool_name == "file_read"
        assert result.error is None
    
    def test_read_file_with_absolute_path(self, temp_project):
        """Test reading with absolute path"""
        tool = FileReadTool(temp_project)
        absolute_path = temp_project / "test.txt"
        
        result = tool.execute(file_path=str(absolute_path))
        
        assert result.success is True
        assert result.output == "Hello World"
    
    def test_read_nested_file(self, temp_project):
        """Test reading file in subdirectory"""
        tool = FileReadTool(temp_project)
        
        result = tool.execute(file_path="subdir/nested.txt")
        
        assert result.success is True
        assert result.output == "Nested file content"
    
    def test_read_file_not_found(self, temp_project):
        """Test reading nonexistent file"""
        tool = FileReadTool(temp_project)
        
        result = tool.execute(file_path="nonexistent.txt")
        
        assert result.success is False
        assert "not found" in result.error.lower()
    
    def test_read_file_outside_project_denied(self, temp_project):
        """Test that reading outside project root is denied"""
        tool = FileReadTool(temp_project)
        
        # Try to read file outside project
        result = tool.execute(file_path="../../../etc/passwd")
        
        assert result.success is False
        assert "outside project root" in result.error.lower()
    
    def test_read_file_missing_parameter(self, temp_project):
        """Test execution without file_path parameter"""
        tool = FileReadTool(temp_project)
        
        result = tool.execute()
        
        assert result.success is False
        assert "required" in result.error.lower()


class TestFileWriteTool:
    """Test file writing with backup"""
    
    def test_write_new_file(self, temp_project):
        """Test writing new file"""
        tool = FileWriteTool(temp_project)
        
        result = tool.execute(
            file_path="new_file.txt",
            content="New content"
        )
        
        assert result.success is True
        assert (temp_project / "new_file.txt").exists()
        assert (temp_project / "new_file.txt").read_text() == "New content"
    
    def test_write_overwrites_existing_file(self, temp_project):
        """Test overwriting existing file"""
        tool = FileWriteTool(temp_project)
        
        result = tool.execute(
            file_path="test.txt",
            content="Updated content"
        )
        
        assert result.success is True
        assert (temp_project / "test.txt").read_text() == "Updated content"
    
    def test_write_creates_backup(self, temp_project):
        """Test that backup is created"""
        tool = FileWriteTool(temp_project)
        
        original_content = (temp_project / "test.txt").read_text()
        
        result = tool.execute(
            file_path="test.txt",
            content="Modified"
        )
        
        assert result.success is True
        assert result.metadata.get("backup_path") is not None
        
        # Backup should exist and contain original content
        backup_path = Path(result.metadata["backup_path"])
        assert backup_path.exists()
        assert backup_path.read_text() == original_content
    
    def test_write_without_backup(self, temp_project):
        """Test writing without creating backup"""
        tool = FileWriteTool(temp_project)
        
        result = tool.execute(
            file_path="test.txt",
            content="No backup",
            create_backup=False
        )
        
        assert result.success is True
        assert result.metadata.get("backup_path") is None
    
    def test_write_creates_parent_directories(self, temp_project):
        """Test that parent directories are created"""
        tool = FileWriteTool(temp_project)
        
        result = tool.execute(
            file_path="deep/nested/path/file.txt",
            content="Deep file"
        )
        
        assert result.success is True
        assert (temp_project / "deep" / "nested" / "path" / "file.txt").exists()
    
    def test_write_outside_project_denied(self, temp_project):
        """Test that writing outside project root is denied"""
        tool = FileWriteTool(temp_project)
        
        result = tool.execute(
            file_path="../../../tmp/malicious.txt",
            content="Malicious"
        )
        
        assert result.success is False
        assert "outside project root" in result.error.lower()
    
    def test_write_missing_content_parameter(self, temp_project):
        """Test execution without content parameter"""
        tool = FileWriteTool(temp_project)
        
        result = tool.execute(file_path="test.txt")
        
        assert result.success is False
        assert "required" in result.error.lower()


class TestGrepSearchTool:
    """Test code search functionality"""
    
    def test_search_finds_pattern(self, temp_project):
        """Test searching for pattern in files"""
        tool = GrepSearchTool(temp_project)
        
        result = tool.execute(
            pattern="Hello",
            file_pattern="**/*.txt"  # Search in .txt files
        )
        
        assert result.success is True
        assert len(result.output) >= 1
        assert any("Hello" in match["content"] for match in result.output)
    
    def test_search_in_python_files(self, temp_project):
        """Test searching only in Python files"""
        tool = GrepSearchTool(temp_project)
        
        result = tool.execute(
            pattern="def",
            file_pattern="**/*.py"
        )
        
        assert result.success is True
        assert len(result.output) >= 1
        # All matches should be from .py files
        assert all(match["file"].endswith(".py") for match in result.output)
    
    def test_search_case_insensitive(self, temp_project):
        """Test case-insensitive search"""
        tool = GrepSearchTool(temp_project)
        
        result = tool.execute(
            pattern="HELLO",
            case_sensitive=False
        )
        
        assert result.success is True
        assert len(result.output) >= 1
    
    def test_search_respects_max_results(self, temp_project):
        """Test that max_results limit is respected"""
        # Create multiple files
        for i in range(20):
            (temp_project / f"file{i}.txt").write_text("pattern match")
        
        tool = GrepSearchTool(temp_project)
        
        result = tool.execute(
            pattern="pattern",
            max_results=5
        )
        
        assert result.success is True
        assert len(result.output) <= 5
    
    def test_search_no_matches(self, temp_project):
        """Test search with no matches"""
        tool = GrepSearchTool(temp_project)
        
        result = tool.execute(pattern="ThisWillNotMatch12345")
        
        assert result.success is True
        assert len(result.output) == 0
    
    def test_search_missing_pattern(self, temp_project):
        """Test execution without pattern parameter"""
        tool = GrepSearchTool(temp_project)
        
        result = tool.execute()
        
        assert result.success is False
        assert "required" in result.error.lower()


class TestPermissionChecker:
    """Test permission enforcement"""
    
    def test_has_permission_granted(self):
        """Test checking granted permission"""
        permissions = {"file_read": True, "file_write": True}
        checker = PermissionChecker(permissions)
        
        assert checker.has_permission("file_read") is True
        assert checker.has_permission("file_write") is True
    
    def test_has_permission_denied(self):
        """Test checking denied permission"""
        permissions = {"file_read": True, "file_write": False}
        checker = PermissionChecker(permissions)
        
        assert checker.has_permission("file_write") is False
    
    def test_has_permission_not_in_policy(self):
        """Test checking permission not in policy (default deny)"""
        permissions = {"file_read": True}
        checker = PermissionChecker(permissions)
        
        assert checker.has_permission("shell_exec") is False
    
    def test_check_tool_permission_allowed(self, temp_project):
        """Test tool permission check when allowed"""
        permissions = {"file_read": True}
        checker = PermissionChecker(permissions)
        tool = FileReadTool(temp_project)
        
        assert checker.check_tool_permission(tool) is True
    
    def test_check_tool_permission_denied(self, temp_project):
        """Test tool permission check when denied"""
        permissions = {"file_read": False}
        checker = PermissionChecker(permissions)
        tool = FileReadTool(temp_project)
        
        assert checker.check_tool_permission(tool) is False
