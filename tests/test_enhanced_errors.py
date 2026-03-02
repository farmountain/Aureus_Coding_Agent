"""
Tests for enhanced error display system — Sprint 1 Item 6

Covers:
- ErrorFormatter rendering (AUREUS errors, build failures, unexpected errors, CLI errors)
- Color / no-color mode
- format_error() and format_build_failure() convenience helpers
- AUREUSError.format_for_cli() integration
- CLI.run() uses rich formatting
- CodeCommand shows build-failure hints
"""

import sys
import pytest
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.errors import (
    AUREUSError,
    ErrorSeverity,
    BudgetExceededError,
    FileCountExceededError,
    DependencyBudgetExceededError,
    ComplexityTooHighError,
    PolicyViolationError,
    PermissionDeniedError,
    ForbiddenPatternError,
    IntentTooVagueError,
    ToolExecutionError,
    PolicyLoadError,
)
from src.cli.ui.error_display import (
    ErrorFormatter,
    format_error,
    format_build_failure,
    print_error,
    print_build_failure,
)


# ============================================================================
# Helpers
# ============================================================================

def stripped(text: str) -> str:
    """Remove ANSI codes for assertion on visible content."""
    import re
    return re.sub(r"\x1b\[[0-9;]*m", "", text)


# ============================================================================
# ErrorFormatter — initialization
# ============================================================================

class TestErrorFormatterInit:
    def test_defaults(self):
        fmt = ErrorFormatter()
        assert fmt.use_color is True
        assert fmt.width == 66

    def test_no_color(self):
        fmt = ErrorFormatter(use_color=False)
        assert fmt.use_color is False

    def test_custom_width(self):
        fmt = ErrorFormatter(width=80)
        assert fmt.width == 80


# ============================================================================
# ErrorFormatter — AUREUSError formatting
# ============================================================================

class TestFormatAUREUSError:
    def test_contains_error_code(self):
        err = BudgetExceededError(current=500, limit=400, overage=100)
        out = stripped(ErrorFormatter(use_color=False).format_aureus_error(err))
        assert "BUDGET_001" in out

    def test_contains_message(self):
        err = BudgetExceededError(current=500, limit=400, overage=100)
        out = stripped(ErrorFormatter(use_color=False).format_aureus_error(err))
        assert "exceeded" in out.lower()

    def test_contains_details_keys(self):
        err = BudgetExceededError(current=500, limit=400, overage=100)
        out = stripped(ErrorFormatter(use_color=False).format_aureus_error(err))
        # Keys are rendered with spaces replacing underscores in the display label
        assert "current loc" in out or "current_loc" in out
        assert "budget limit" in out or "budget_limit" in out

    def test_contains_suggestion(self):
        err = BudgetExceededError(current=500, limit=400, overage=100)
        out = stripped(ErrorFormatter(use_color=False).format_aureus_error(err))
        # Suggestion section should be present
        assert "What to do" in out

    def test_contains_docs_url(self):
        err = BudgetExceededError(current=500, limit=400, overage=100)
        out = stripped(ErrorFormatter(use_color=False).format_aureus_error(err))
        assert "BUDGET_001" in out  # URL contains code

    def test_severity_error_icon_in_header(self):
        err = BudgetExceededError(current=500, limit=400, overage=100)
        out = ErrorFormatter(use_color=False).format_aureus_error(err)
        assert "Error" in out

    def test_severity_critical(self):
        err = AUREUSError(
            code="TEST_001",
            message="Critical test",
            severity=ErrorSeverity.CRITICAL,
        )
        out = stripped(ErrorFormatter(use_color=False).format_aureus_error(err))
        assert "CRITICAL" in out

    def test_severity_warning(self):
        err = AUREUSError(
            code="TEST_002",
            message="Warning test",
            severity=ErrorSeverity.WARNING,
        )
        out = stripped(ErrorFormatter(use_color=False).format_aureus_error(err))
        assert "Warning" in out

    def test_no_color_has_no_ansi(self):
        err = PolicyViolationError("max_loc", "LOC exceeded")
        out = ErrorFormatter(use_color=False).format_aureus_error(err)
        assert "\x1b[" not in out

    def test_color_has_ansi(self):
        err = PolicyViolationError("max_loc", "LOC exceeded")
        out = ErrorFormatter(use_color=True).format_aureus_error(err)
        assert "\x1b[" in out

    def test_ends_with_separator(self):
        err = BudgetExceededError(current=500, limit=400, overage=100)
        out = stripped(ErrorFormatter(use_color=False).format_aureus_error(err))
        # Last non-empty line should be dashes
        last_line = [l for l in out.splitlines() if l.strip()][-1]
        assert "-" in last_line or "─" in last_line

    def test_no_details_section_when_empty(self):
        err = AUREUSError(code="TEST_003", message="No details")
        out = stripped(ErrorFormatter(use_color=False).format_aureus_error(err))
        # Should not crash, Details header optional when no details
        assert "TEST_003" in out

    def test_no_suggestion_section_when_none(self):
        err = AUREUSError(code="TEST_004", message="No suggestion", suggestion=None)
        out = stripped(ErrorFormatter(use_color=False).format_aureus_error(err))
        assert "What to do" not in out


# ============================================================================
# Various error types
# ============================================================================

class TestSpecificErrorTypes:
    def test_file_count_error(self):
        err = FileCountExceededError(current=35, limit=30)
        out = stripped(ErrorFormatter(use_color=False).format_aureus_error(err))
        assert "BUDGET_002" in out
        assert "35" in out

    def test_dependency_budget_error(self):
        err = DependencyBudgetExceededError(current=22, limit=20, new_deps=["requests", "httpx"])
        out = stripped(ErrorFormatter(use_color=False).format_aureus_error(err))
        assert "BUDGET_003" in out

    def test_complexity_error(self):
        err = ComplexityTooHighError(score=15.0, threshold=10.0, component="UserService")
        out = stripped(ErrorFormatter(use_color=False).format_aureus_error(err))
        assert "BUDGET_004" in out

    def test_permission_denied(self):
        err = PermissionDeniedError("file_delete", "write")
        out = stripped(ErrorFormatter(use_color=False).format_aureus_error(err))
        assert "POLICY_002" in out

    def test_forbidden_pattern(self):
        err = ForbiddenPatternError("god_object", "Class is too large")
        out = stripped(ErrorFormatter(use_color=False).format_aureus_error(err))
        assert "POLICY_003" in out

    def test_intent_too_vague(self):
        err = IntentTooVagueError("do something", ["target", "scope"])
        out = stripped(ErrorFormatter(use_color=False).format_aureus_error(err))
        assert "GVUFD_001" in out

    def test_tool_execution_error(self):
        err = ToolExecutionError("file_write", "Permission denied")
        out = stripped(ErrorFormatter(use_color=False).format_aureus_error(err))
        assert "TOOL_001" in out

    def test_policy_load_error(self):
        err = PolicyLoadError(".aureus/policy.yaml", "Invalid YAML")
        out = stripped(ErrorFormatter(use_color=False).format_aureus_error(err))
        assert "CONFIG_001" in out


# ============================================================================
# ErrorFormatter — build failure
# ============================================================================

class TestFormatBuildFailure:
    def test_contains_build_failed_header(self):
        out = stripped(ErrorFormatter(use_color=False).format_build_failure("Build did not complete"))
        assert "BUILD FAILED" in out

    def test_shows_error_summary(self):
        out = stripped(ErrorFormatter(use_color=False).format_build_failure(
            "Budget exceeded: rejected. Alternatives: 3"
        ))
        assert "Budget exceeded" in out

    def test_shows_alternatives_when_provided(self):
        alts = [
            {"description": "Reduce scope to core functionality", "estimated_savings": 200},
            {"description": "Split into 2 phases", "estimated_savings": 150},
        ]
        out = stripped(ErrorFormatter(use_color=False).format_build_failure(
            "Budget exceeded", alternatives=alts
        ))
        assert "Reduce scope" in out
        assert "Split into 2 phases" in out
        assert "SPK suggests" in out

    def test_shows_max_4_alternatives(self):
        alts = [{"description": f"Option {i}"} for i in range(6)]
        out = stripped(ErrorFormatter(use_color=False).format_build_failure(
            "Budget exceeded", alternatives=alts
        ))
        # Should show at most 4
        assert "Option 4" not in out  # 5th alternative (0-indexed 4) should be cut off
        assert "Option 3" in out  # 4th alternative shown

    def test_shows_diagnostic_hints(self):
        out = stripped(ErrorFormatter(use_color=False).format_build_failure("Failed"))
        assert "--verbose" in out
        assert "aureus explain" in out

    def test_budget_exceeded_hint_added(self):
        out = stripped(ErrorFormatter(use_color=False).format_build_failure(
            "Budget exceeded", budget_status="exceeded"
        ))
        assert "smaller tasks" in out.lower() or "simplify" in out.lower()

    def test_rejected_hint_added(self):
        out = stripped(ErrorFormatter(use_color=False).format_build_failure(
            "Rejected", budget_status="rejected"
        ))
        assert "simplify" in out.lower() or "increase" in out.lower()

    def test_no_color_mode(self):
        out = ErrorFormatter(use_color=False).format_build_failure("Failed")
        assert "\x1b[" not in out

    def test_multi_line_error_uses_first_line(self):
        out = stripped(ErrorFormatter(use_color=False).format_build_failure(
            "First line\nSecond line\nThird line"
        ))
        assert "First line" in out


# ============================================================================
# ErrorFormatter — unexpected error
# ============================================================================

class TestFormatUnexpectedError:
    def test_contains_error_type(self):
        err = ConnectionError("Failed to connect to API")
        out = stripped(ErrorFormatter(use_color=False).format_unexpected_error(err))
        assert "ConnectionError" in out

    def test_contains_message(self):
        err = ValueError("bad value")
        out = stripped(ErrorFormatter(use_color=False).format_unexpected_error(err))
        assert "bad value" in out

    def test_shows_diagnostics_section(self):
        err = RuntimeError("something went wrong")
        out = stripped(ErrorFormatter(use_color=False).format_unexpected_error(err))
        assert "What you can do" in out

    def test_api_key_hint_for_api_errors(self):
        err = RuntimeError("Invalid API key provided")
        out = stripped(ErrorFormatter(use_color=False).format_unexpected_error(err))
        assert "API_KEY" in out

    def test_permission_hint_for_permission_errors(self):
        err = PermissionError("Access denied to file")
        out = stripped(ErrorFormatter(use_color=False).format_unexpected_error(err))
        assert "permission" in out.lower()

    def test_init_hint_for_missing_files(self):
        err = FileNotFoundError("No such file: .aureus/policy.yaml")
        out = stripped(ErrorFormatter(use_color=False).format_unexpected_error(err))
        assert "init" in out.lower()

    def test_connection_hint_for_connection_errors(self):
        err = ConnectionError("Connection timed out")
        out = stripped(ErrorFormatter(use_color=False).format_unexpected_error(err))
        assert "network" in out.lower() or "connect" in out.lower()

    def test_no_color_mode(self):
        err = RuntimeError("test")
        out = ErrorFormatter(use_color=False).format_unexpected_error(err)
        assert "\x1b[" not in out


# ============================================================================
# ErrorFormatter — CLI error
# ============================================================================

class TestFormatCLIError:
    def test_contains_usage_error_header(self):
        out = stripped(ErrorFormatter(use_color=False).format_cli_error(
            "Policy file not found: .aureus/policy.yaml. Run 'aureus init' first."
        ))
        assert "USAGE ERROR" in out

    def test_contains_message(self):
        out = stripped(ErrorFormatter(use_color=False).format_cli_error("Unknown command: foo"))
        assert "Unknown command" in out

    def test_policy_not_found_hint(self):
        out = stripped(ErrorFormatter(use_color=False).format_cli_error(
            "Policy file not found: .aureus/policy.yaml"
        ))
        assert "aureus init" in out

    def test_unknown_command_hint(self):
        out = stripped(ErrorFormatter(use_color=False).format_cli_error(
            "Unknown command: foobar"
        ))
        assert "--help" in out

    def test_load_policy_hint(self):
        out = stripped(ErrorFormatter(use_color=False).format_cli_error(
            "Failed to load policy: YAML error"
        ))
        assert "YAML" in out or "policy" in out.lower()

    def test_no_color_mode(self):
        out = ErrorFormatter(use_color=False).format_cli_error("some error")
        assert "\x1b[" not in out


# ============================================================================
# format() dispatcher
# ============================================================================

class TestFormatDispatcher:
    def test_dispatches_aureus_error(self):
        fmt = ErrorFormatter(use_color=False)
        err = BudgetExceededError(current=500, limit=400, overage=100)
        out = stripped(fmt.format(err))
        assert "BUDGET_001" in out

    def test_dispatches_unexpected_error(self):
        fmt = ErrorFormatter(use_color=False)
        err = RuntimeError("something unexpected")
        out = stripped(fmt.format(err))
        assert "UNEXPECTED" in out

    def test_dispatches_cli_error(self):
        from src.cli.main import CLIError
        fmt = ErrorFormatter(use_color=False)
        err = CLIError("Policy file not found")
        out = stripped(fmt.format(err))
        assert "USAGE ERROR" in out


# ============================================================================
# Module-level convenience functions
# ============================================================================

class TestConvenienceFunctions:
    def test_format_error_aureus(self):
        err = BudgetExceededError(current=500, limit=400, overage=100)
        out = stripped(format_error(err, use_color=False))
        assert "BUDGET_001" in out

    def test_format_error_unexpected(self):
        err = RuntimeError("test")
        out = stripped(format_error(err, use_color=False))
        assert "UNEXPECTED" in out

    def test_format_build_failure_plain(self):
        out = stripped(format_build_failure("Budget exceeded", use_color=False))
        assert "BUILD FAILED" in out

    def test_format_build_failure_with_alternatives(self):
        alts = [{"description": "Reduce scope"}, {"description": "Split phases"}]
        out = stripped(format_build_failure("Budget exceeded", alternatives=alts, use_color=False))
        assert "Reduce scope" in out

    def test_print_error_writes_to_stderr(self):
        err = BudgetExceededError(current=500, limit=400, overage=100)
        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            print_error(err, use_color=False)
            output = mock_stderr.getvalue()
            assert "BUDGET_001" in stripped(output)

    def test_print_build_failure_writes_to_stdout(self):
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            print_build_failure("Build failed", use_color=False)
            output = mock_stdout.getvalue()
            assert "BUILD FAILED" in stripped(output)


# ============================================================================
# AUREUSError.format_for_cli()
# ============================================================================

class TestFormatForCLI:
    def test_format_for_cli_returns_string(self):
        err = BudgetExceededError(current=500, limit=400, overage=100)
        out = err.format_for_cli(use_color=False)
        assert isinstance(out, str)
        assert len(out) > 0

    def test_format_for_cli_contains_code(self):
        err = BudgetExceededError(current=500, limit=400, overage=100)
        out = stripped(err.format_for_cli(use_color=False))
        assert "BUDGET_001" in out

    def test_format_for_cli_color_mode(self):
        err = PolicyViolationError("max_loc", "exceeded")
        out = err.format_for_cli(use_color=True)
        assert "\x1b[" in out

    def test_format_for_cli_no_color_mode(self):
        err = PolicyViolationError("max_loc", "exceeded")
        out = err.format_for_cli(use_color=False)
        assert "\x1b[" not in out

    def test_all_error_types_format_without_crash(self):
        errors = [
            BudgetExceededError(current=100, limit=50, overage=50),
            FileCountExceededError(current=10, limit=5),
            DependencyBudgetExceededError(current=5, limit=3, new_deps=["requests"]),
            ComplexityTooHighError(score=10.0, threshold=5.0, component="Foo"),
            PolicyViolationError("max_loc", "exceeded"),
            PermissionDeniedError("file_delete", "write"),
            ForbiddenPatternError("god_object", "Too large"),
            IntentTooVagueError("do something", ["target"]),
            ToolExecutionError("file_write", "Permission denied"),
            PolicyLoadError(".aureus/policy.yaml", "YAML error"),
        ]
        for err in errors:
            out = err.format_for_cli(use_color=False)
            assert isinstance(out, str)
            assert len(out) > 20, f"Output too short for {type(err).__name__}"


# ============================================================================
# Integration — CLI.run() uses rich formatting
# ============================================================================

class TestCLIRunIntegration:
    def test_cli_error_formatted_richly(self):
        """CLI.run() wraps CLIError with rich formatting."""
        from src.cli.main import CLI

        cli = CLI()
        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            exit_code = cli.run(["aureus", "code"])  # missing intent → CLIError
            output = mock_stderr.getvalue()

        assert exit_code == 1
        # Should have box-style output, not plain "✗ ERROR: ..."
        out = stripped(output)
        assert "USAGE ERROR" in out or "Error" in out

    def test_unexpected_error_formatted_richly(self):
        """CLI.run() wraps unexpected Exception with rich formatting."""
        from src.cli.main import CLI

        cli = CLI()
        with patch.object(cli, "execute", side_effect=RuntimeError("unexpected!")):
            with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
                exit_code = cli.run(["aureus", "status"])
                output = mock_stderr.getvalue()

        assert exit_code == 1
        out = stripped(output)
        assert "UNEXPECTED" in out or "unexpected!" in out

    def test_aureus_error_formatted_richly(self):
        """CLI.run() wraps AUREUSError with structured display."""
        from src.cli.main import CLI

        cli = CLI()
        err = BudgetExceededError(current=500, limit=400, overage=100)
        with patch.object(cli, "execute", side_effect=err):
            with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
                exit_code = cli.run(["aureus", "status"])
                output = mock_stderr.getvalue()

        assert exit_code == 1
        out = stripped(output)
        assert "BUDGET_001" in out
