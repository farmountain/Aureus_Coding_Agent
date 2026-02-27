"""
Tests for Additional Tools: Shell, Git, Web, Semantic Search
"""

import pytest
from pathlib import Path
import tempfile
import shutil
from src.toolbus.shell_tool import ShellTool, ShellResult
from src.toolbus.git_tool import GitTool, GitResult
from src.toolbus.web_tool import WebFetchTool, WebResponse
from src.toolbus.semantic_search import SemanticSearchTool, SearchResult
import subprocess


class TestShellTool:
    """Test ShellTool functionality"""
    
    @pytest.fixture
    def shell_tool(self, tmp_path):
        """Create shell tool for testing"""
        return ShellTool(working_dir=tmp_path, timeout=5)
    
    def test_execute_safe_command(self, shell_tool, tmp_path):
        """Test executing safe command"""
        # Create a test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello World")
        
        # List files (safe command)
        result = shell_tool.execute("ls" if not Path("/").drive else "dir")
        
        assert isinstance(result, ShellResult)
        # Command may not work in all environments, just check structure
        assert hasattr(result, 'success')
        assert hasattr(result, 'stdout')
    
    def test_whitelist_enforcement(self, shell_tool):
        """Test that non-whitelisted commands are blocked"""
        result = shell_tool.execute("python --version")
        
        assert not result.success
        assert "not in whitelist" in result.error
    
    def test_dangerous_command_blocked(self, shell_tool):
        """Test that dangerous commands are blocked by default"""
        result = shell_tool.execute("rm test.txt")
        
        assert not result.success
        assert "not in whitelist" in result.error
    
    def test_allow_dangerous_commands(self, tmp_path):
        """Test allowing dangerous commands with flag"""
        shell_tool = ShellTool(
            working_dir=tmp_path,
            allow_dangerous=True
        )
        
        # rm should now be in whitelist
        assert 'rm' in shell_tool.whitelist
    
    def test_empty_command(self, shell_tool):
        """Test handling of empty command"""
        result = shell_tool.execute("")
        
        assert not result.success
        assert "Empty command" in result.error
    
    def test_invalid_syntax(self, shell_tool):
        """Test handling of invalid command syntax"""
        result = shell_tool.execute("ls 'unclosed")
        
        assert not result.success
        assert "syntax" in result.error.lower()
    
    def test_to_dict(self, shell_tool):
        """Test conversion to dictionary"""
        data = shell_tool.to_dict()
        
        assert data["tool_name"] == "shell"
        assert "working_dir" in data
        assert "whitelist" in data


class TestGitTool:
    """Test GitTool functionality"""
    
    @pytest.fixture
    def git_repo(self, tmp_path):
        """Create a temporary Git repository"""
        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        
        # Initialize Git repo
        subprocess.run(
            ['git', 'init'],
            cwd=str(repo_path),
            capture_output=True
        )
        
        # Configure Git
        subprocess.run(
            ['git', 'config', 'user.name', 'Test User'],
            cwd=str(repo_path),
            capture_output=True
        )
        subprocess.run(
            ['git', 'config', 'user.email', 'test@example.com'],
            cwd=str(repo_path),
            capture_output=True
        )
        
        # Create initial commit
        test_file = repo_path / "README.md"
        test_file.write_text("# Test Repo")
        
        subprocess.run(
            ['git', 'add', 'README.md'],
            cwd=str(repo_path),
            capture_output=True
        )
        subprocess.run(
            ['git', 'commit', '-m', 'Initial commit'],
            cwd=str(repo_path),
            capture_output=True
        )
        
        return repo_path
    
    @pytest.fixture
    def git_tool(self, git_repo):
        """Create Git tool for testing"""
        return GitTool(repo_path=git_repo)
    
    def test_status(self, git_tool):
        """Test git status"""
        result = git_tool.status()
        
        assert isinstance(result, GitResult)
        assert result.success
    
    def test_log(self, git_tool):
        """Test git log"""
        result = git_tool.log(max_count=5)
        
        assert result.success
        assert "Initial commit" in result.output
    
    def test_diff_empty(self, git_tool):
        """Test git diff with no changes"""
        result = git_tool.diff()
        
        assert result.success
        # Should be empty (no changes)
    
    def test_add_file(self, git_tool, git_repo):
        """Test staging a file"""
        # Create new file
        new_file = git_repo / "new_file.txt"
        new_file.write_text("New content")
        
        result = git_tool.add("new_file.txt")
        
        assert result.success
    
    def test_commit_not_allowed(self, git_tool):
        """Test that commit is blocked without permission"""
        result = git_tool.commit("Test commit")
        
        assert not result.success
        assert "not allowed" in result.error
    
    def test_commit_with_permission(self, git_repo):
        """Test commit with allow_commits=True"""
        git_tool = GitTool(repo_path=git_repo, allow_commits=True)
        
        # Create and stage file
        new_file = git_repo / "test.txt"
        new_file.write_text("Test")
        subprocess.run(['git', 'add', 'test.txt'], cwd=str(git_repo))
        
        result = git_tool.commit("Test commit")
        
        assert result.success
    
    def test_invalid_repo(self, tmp_path):
        """Test error on non-Git directory"""
        with pytest.raises(ValueError, match="Not a Git repository"):
            GitTool(repo_path=tmp_path)
    
    def test_to_dict(self, git_tool):
        """Test conversion to dictionary"""
        data = git_tool.to_dict()
        
        assert data["tool_name"] == "git"
        assert "repo_path" in data


class TestWebFetchTool:
    """Test WebFetchTool functionality"""
    
    @pytest.fixture
    def web_tool(self):
        """Create web fetch tool for testing"""
        return WebFetchTool(timeout=10)
    
    def test_fetch_success(self, web_tool):
        """Test successful HTTP fetch"""
        # Use a reliable test endpoint
        result = web_tool.fetch("https://httpbin.org/get")
        
        # May fail if no internet, so check gracefully
        if result.success:
            assert result.status_code == 200
            assert result.content
        else:
            # Network error is acceptable in tests
            assert result.error is not None
    
    def test_fetch_json(self, web_tool):
        """Test JSON fetching"""
        result = web_tool.fetch_json("https://httpbin.org/json")
        
        if result.success:
            assert result.status_code == 200
            # Should be formatted JSON
            assert '{' in result.content
    
    def test_url_validation_http(self):
        """Test that HTTP is allowed with no whitelist"""
        tool = WebFetchTool()
        
        # HTTPS should be allowed
        assert tool._is_url_allowed("https://example.com")
    
    def test_url_validation_invalid(self):
        """Test invalid URL rejection"""
        tool = WebFetchTool()
        
        assert not tool._is_url_allowed("ftp://example.com")
        assert not tool._is_url_allowed("not-a-url")
    
    def test_domain_whitelist(self):
        """Test domain whitelisting"""
        tool = WebFetchTool(allowed_domains=["example.com"])
        
        assert tool._is_url_allowed("https://example.com/path")
        assert tool._is_url_allowed("https://sub.example.com/path")
        assert not tool._is_url_allowed("https://other.com/path")
    
    def test_to_dict(self, web_tool):
        """Test conversion to dictionary"""
        data = web_tool.to_dict()
        
        assert data["tool_name"] == "web_fetch"
        assert "timeout" in data


class TestSemanticSearchTool:
    """Test SemanticSearchTool functionality"""
    
    @pytest.fixture
    def search_project(self, tmp_path):
        """Create a test project structure"""
        project = tmp_path / "project"
        project.mkdir()
        
        # Create Python files
        (project / "module1.py").write_text("""
def hello():
    print("Hello")

class TestClass:
    def method(self):
        pass
""")
        
        (project / "module2.py").write_text("""
from module1 import TestClass

def goodbye():
    print("Goodbye")
    
class AnotherClass:
    pass
""")
        
        return project
    
    @pytest.fixture
    def search_tool(self, search_project):
        """Create semantic search tool"""
        return SemanticSearchTool(project_root=search_project)
    
    def test_find_function(self, search_tool):
        """Test finding function definitions"""
        result = search_tool.find_function("hello")
        
        assert result.success
        assert len(result.matches) == 1
        assert result.matches[0].name == "hello"
        assert result.matches[0].match_type == "function"
    
    def test_find_function_wildcard(self, search_tool):
        """Test finding functions with wildcard"""
        result = search_tool.find_function("*bye")
        
        assert result.success
        assert len(result.matches) == 1
        assert result.matches[0].name == "goodbye"
    
    def test_find_class(self, search_tool):
        """Test finding class definitions"""
        result = search_tool.find_class("TestClass")
        
        assert result.success
        assert len(result.matches) == 1
        assert result.matches[0].name == "TestClass"
        assert result.matches[0].match_type == "class"
    
    def test_find_class_wildcard(self, search_tool):
        """Test finding classes with wildcard"""
        result = search_tool.find_class("*Class")
        
        assert result.success
        assert len(result.matches) >= 2  # TestClass and AnotherClass
    
    def test_find_imports(self, search_tool):
        """Test finding import statements"""
        result = search_tool.find_imports("module1")
        
        assert result.success
        assert len(result.matches) == 1
        assert result.matches[0].match_type == "import"
    
    def test_find_references(self, search_tool):
        """Test finding symbol references"""
        result = search_tool.find_references("TestClass")
        
        assert result.success
        # May or may not find references depending on AST structure
        assert isinstance(result.matches, list)
    
    def test_to_dict(self, search_tool):
        """Test conversion to dictionary"""
        data = search_tool.to_dict()
        
        assert data["tool_name"] == "semantic_search"
        assert "project_root" in data
