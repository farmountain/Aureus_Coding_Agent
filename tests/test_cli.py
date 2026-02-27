"""
Tests for CLI entry point.
TDD: Tests written before implementation.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys


class TestCLIParser:
    """Test command line argument parsing."""
    
    def test_parse_init_command(self):
        """CLI should parse 'aureus init' command."""
        from src.cli.main import CLIParser
        
        parser = CLIParser()
        args = parser.parse(["init"])
        
        assert args.command == "init"
    
    def test_parse_code_command_with_intent(self):
        """CLI should parse 'aureus code <intent>' command."""
        from src.cli.main import CLIParser
        
        parser = CLIParser()
        args = parser.parse(["code", "add user authentication"])
        
        assert args.command == "code"
        assert args.intent == "add user authentication"
    
    def test_parse_status_command(self):
        """CLI should parse 'aureus status' command."""
        from src.cli.main import CLIParser
        
        parser = CLIParser()
        args = parser.parse(["status"])
        
        assert args.command == "status"
    
    def test_parse_with_policy_path_option(self):
        """CLI should parse --policy option."""
        from src.cli.main import CLIParser
        
        parser = CLIParser()
        args = parser.parse(["code", "test", "--policy", "/path/to/policy.yaml"])
        
        assert args.policy_path == "/path/to/policy.yaml"
    
    def test_parse_with_verbose_flag(self):
        """CLI should parse --verbose flag."""
        from src.cli.main import CLIParser
        
        parser = CLIParser()
        args = parser.parse(["code", "test", "--verbose"])
        
        assert args.verbose is True
    
    def test_parse_missing_intent_for_code(self):
        """CLI should require intent for 'code' command."""
        from src.cli.main import CLIParser, CLIError
        
        parser = CLIParser()
        with pytest.raises(CLIError, match="intent"):
            parser.parse(["code"])


class TestCLIFormatter:
    """Test CLI output formatting."""
    
    def test_format_success_message(self):
        """Formatter should format success messages."""
        from src.cli.main import CLIFormatter
        
        formatter = CLIFormatter()
        output = formatter.success("Operation completed")
        
        assert "✓" in output or "SUCCESS" in output.upper()
        assert "Operation completed" in output
    
    def test_format_error_message(self):
        """Formatter should format error messages."""
        from src.cli.main import CLIFormatter
        
        formatter = CLIFormatter()
        output = formatter.error("Something went wrong")
        
        assert "✗" in output or "ERROR" in output.upper()
        assert "Something went wrong" in output
    
    def test_format_info_message(self):
        """Formatter should format info messages."""
        from src.cli.main import CLIFormatter
        
        formatter = CLIFormatter()
        output = formatter.info("Processing request...")
        
        assert "Processing request..." in output
    
    def test_format_table(self):
        """Formatter should format tabular data."""
        from src.cli.main import CLIFormatter
        
        formatter = CLIFormatter()
        headers = ["Name", "Value"]
        rows = [["Item 1", "100"], ["Item 2", "200"]]
        
        output = formatter.table(headers, rows)
        
        assert "Name" in output
        assert "Value" in output
        assert "Item 1" in output


class TestCLI:
    """Test main CLI orchestrator."""
    
    @patch('src.cli.main.InitCommand')
    def test_execute_init_command(self, mock_init_cmd):
        """CLI should execute init command."""
        from src.cli.main import CLI
        
        # Setup mock
        mock_instance = Mock()
        mock_init_cmd.return_value = mock_instance
        mock_instance.execute.return_value = {"status": "success"}
        
        cli = CLI()
        args = Mock(command="init", policy_path=None, verbose=False)
        result = cli.execute(args)
        
        assert result["status"] == "success"
        mock_instance.execute.assert_called_once()
    
    @patch('src.cli.main.CodeCommand')
    def test_execute_code_command(self, mock_code_cmd):
        """CLI should execute code command."""
        from src.cli.main import CLI
        
        # Setup mock
        mock_instance = Mock()
        mock_code_cmd.return_value = mock_instance
        mock_instance.execute.return_value = {"status": "success"}
        
        cli = CLI()
        args = Mock(command="code", intent="add feature", policy_path=None, verbose=False)
        result = cli.execute(args)
        
        assert result["status"] == "success"
        mock_instance.execute.assert_called_once()
    
    @patch('src.cli.main.StatusCommand')
    def test_execute_status_command(self, mock_status_cmd):
        """CLI should execute status command."""
        from src.cli.main import CLI
        
        # Setup mock
        mock_instance = Mock()
        mock_status_cmd.return_value = mock_instance
        mock_instance.execute.return_value = {"status": "success"}
        
        cli = CLI()
        args = Mock(command="status", policy_path=None, verbose=False)
        result = cli.execute(args)
        
        assert result["status"] == "success"
        mock_instance.execute.assert_called_once()
    
    def test_execute_unknown_command(self):
        """CLI should raise error for unknown commands."""
        from src.cli.main import CLI, CLIError
        
        cli = CLI()
        args = Mock(command="unknown", policy_path=None, verbose=False)
        
        with pytest.raises(CLIError, match="Unknown command"):
            cli.execute(args)


class TestInitCommand:
    """Test 'init' command implementation."""
    
    @patch('src.cli.main.PolicyLoader')
    def test_init_creates_default_policy(self, mock_loader):
        """Init command should create default policy."""
        from src.cli.main import InitCommand
        
        mock_loader_instance = Mock()
        mock_loader.return_value = mock_loader_instance
        
        cmd = InitCommand(policy_path=None, verbose=False)
        result = cmd.execute()
        
        assert result["status"] == "success"
        # Should call save method
        assert mock_loader_instance.save.called or "policy" in result
    
    def test_init_with_custom_path(self):
        """Init command should use custom policy path."""
        from src.cli.main import InitCommand
        
        cmd = InitCommand(policy_path=Path("/custom/policy.yaml"), verbose=False)
        result = cmd.execute()
        
        assert "policy_path" in result or "message" in result


class TestCodeCommand:
    """Test 'code' command implementation."""
    
    def test_code_requires_policy(self):
        """Code command should require policy to exist."""
        from src.cli.main import CodeCommand, CLIError
        
        cmd = CodeCommand(intent="test", policy_path=Path("/nonexistent/policy.yaml"), verbose=False)
        
        # Should fail if policy doesn't exist
        with pytest.raises(CLIError, match="policy"):
            cmd.execute()
    
    @patch('src.cli.main.PolicyLoader')
    @patch('pathlib.Path.exists')
    def test_code_loads_policy(self, mock_exists, mock_loader):
        """Code command should load policy."""
        from src.cli.main import CodeCommand
        from src.interfaces import Policy, Budget
        
        # Setup mocks
        mock_exists.return_value = True
        
        budget = Budget(max_loc=10000, max_modules=8, max_files=30, max_dependencies=20)
        policy = Policy(
            version="1.0",
            project_name="test",
            project_root=Path("/path"),
            budgets=budget,
            permissions={}
        )
        
        mock_loader_instance = Mock()
        mock_loader_instance.load.return_value = policy
        mock_loader.return_value = mock_loader_instance
        
        cmd = CodeCommand(intent="add feature", policy_path=Path("/path/policy.yaml"), verbose=False)
        result = cmd.execute()
        
        assert mock_loader_instance.load.called


class TestStatusCommand:
    """Test 'status' command implementation."""
    
    @patch('src.cli.main.PolicyLoader')
    @patch('pathlib.Path.exists')
    def test_status_shows_budget_usage(self, mock_exists, mock_loader):
        """Status command should show budget usage."""
        from src.cli.main import StatusCommand
        from src.interfaces import Policy, Budget
        
        # Setup mocks
        mock_exists.return_value = True
        
        budget = Budget(max_loc=10000, max_modules=8, max_files=30, max_dependencies=20)
        policy = Policy(
            version="1.0",
            project_name="test",
            project_root=Path("/path"),
            budgets=budget,
            permissions={}
        )
        
        mock_loader_instance = Mock()
        mock_loader_instance.load.return_value = policy
        mock_loader.return_value = mock_loader_instance
        
        cmd = StatusCommand(policy_path=Path("/path/policy.yaml"), verbose=False)
        result = cmd.execute()
        
        assert "budgets" in result or "status" in result
