"""
Enhanced Error Display — Sprint 1 Item 6

Provides rich, actionable error messages for the AUREUS CLI.

Goals:
- Clear error codes so users can search for help
- Specific, actionable "What to do" suggestions
- Visual hierarchy that draws the eye to the most important info
- Consistent format across all error types
- --no-color fallback for CI/log environments

Output example (AUREUS error):

  ┌─────────────────────────────────────────────────────────────┐
  │  ❌  BUDGET_001  ·  Error                                    │
  └─────────────────────────────────────────────────────────────┘

    LOC budget exceeded by 350 lines

    📊  Details
        current_loc    8,500
        budget_limit  10,000
        overage          350  (3.5% over)

    💡  What to do
        • Consider: 1) Remove unused code
        • 2) Simplify implementation
        • 3) Increase budget if justified

    📖  More info: https://aureus.dev/errors/BUDGET_001

  ─────────────────────────────────────────────────────────────
"""

import sys
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from src.errors import AUREUSError, ErrorSeverity


# ============================================================================
# ANSI Colours
# ============================================================================

class _Colors:
    """ANSI colour codes."""
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"

    RED     = "\033[91m"
    YELLOW  = "\033[93m"
    BLUE    = "\033[94m"
    CYAN    = "\033[96m"
    WHITE   = "\033[97m"
    GRAY    = "\033[90m"

    RED_BG  = "\033[41m"


# ============================================================================
# Severity metadata
# ============================================================================

_SEVERITY_META = {
    "critical": {"icon": "💥", "label": "CRITICAL", "color": _Colors.RED},
    "error":    {"icon": "❌", "label": "Error",    "color": _Colors.RED},
    "warning":  {"icon": "⚠️", "label": "Warning",  "color": _Colors.YELLOW},
    "info":     {"icon": "ℹ️", "label": "Info",     "color": _Colors.BLUE},
}


# ============================================================================
# Main formatter
# ============================================================================

class ErrorFormatter:
    """
    Renders AUREUS errors as rich, structured CLI output.

    Parameters
    ----------
    use_color:
        When True (default) emit ANSI colour codes.  Pass False for CI/logs.
    width:
        Box width in characters (default 66).
    """

    BOX_WIDTH = 66
    INDENT    = "    "  # 4-space indent for body lines

    def __init__(self, use_color: bool = True, width: int = 66):
        self.use_color = use_color
        self.width = width

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def format_aureus_error(self, error: "AUREUSError") -> str:
        """
        Format a structured AUREUSError for CLI display.

        Renders: code box → message → details section → suggestion section →
                 docs link → separator.
        """
        from src.errors import ErrorSeverity  # local import to avoid circularity

        sev_key = error.error_details.severity.value.lower()
        meta = _SEVERITY_META.get(sev_key, _SEVERITY_META["error"])

        title = (
            f"{meta['icon']}  {error.error_details.code}  ·  {meta['label']}"
        )
        lines: List[str] = []
        lines.append(self._box(title, meta["color"]))
        lines.append("")

        # Primary message
        lines.append(f"{self.INDENT}{self._bold(error.error_details.message)}")
        lines.append("")

        # Details section
        if error.error_details.details:
            lines.append(f"{self.INDENT}{self._colored('📊', _Colors.CYAN)}  {self._bold('Details')}")
            for key, value in error.error_details.details.items():
                label = key.replace("_", " ").rjust(20)
                lines.append(f"{self.INDENT}    {self._dim(label)}  {value}")
            lines.append("")

        # Suggestion section
        if error.error_details.suggestion:
            lines.append(f"{self.INDENT}{self._colored('💡', _Colors.YELLOW)}  {self._bold('What to do')}")
            for suggestion_line in error.error_details.suggestion.splitlines():
                stripped = suggestion_line.strip()
                if stripped:
                    if not stripped.startswith("•") and not stripped.startswith("-"):
                        stripped = f"• {stripped}"
                    lines.append(f"{self.INDENT}    {stripped}")
            lines.append("")

        # Docs link
        if error.error_details.docs_url:
            lines.append(
                f"{self.INDENT}{self._dim('📖  More info:')} "
                f"{self._colored(error.error_details.docs_url, _Colors.CYAN)}"
            )
            lines.append("")

        lines.append(self._separator())
        return "\n".join(lines)

    def format_build_failure(
        self,
        error_message: str,
        alternatives: Optional[List[Dict[str, Any]]] = None,
        budget_status: Optional[str] = None,
    ) -> str:
        """
        Format a build failure (result.success == False) with diagnostic hints.

        Shown after every failed `aureus code` run.
        """
        meta = _SEVERITY_META["error"]
        title = f"{meta['icon']}  BUILD FAILED"

        lines: List[str] = []
        lines.append(self._box(title, meta["color"]))
        lines.append("")

        # Error summary
        summary = error_message.splitlines()[0] if error_message else "Build did not complete"
        lines.append(f"{self.INDENT}{self._bold(summary)}")
        lines.append("")

        # Budget-exceeded alternatives
        if alternatives:
            lines.append(
                f"{self.INDENT}{self._colored('🔀', _Colors.CYAN)}  "
                f"{self._bold(f'Planner suggests {len(alternatives)} alternative(s)')}"
            )
            for idx, alt in enumerate(alternatives[:4], start=1):
                desc = alt.get("description", alt.get("strategy", "alternative approach"))
                savings = alt.get("estimated_savings")
                savings_str = f"  (saves ~{savings} pts)" if savings else ""
                lines.append(f"{self.INDENT}    {idx}. {desc}{savings_str}")
            lines.append("")

        # Standard diagnostic hints
        lines.append(f"{self.INDENT}{self._colored('💡', _Colors.YELLOW)}  {self._bold('Diagnostic steps')}")

        hints = [
            "Run with --verbose to see the full execution log",
            "Run 'aureus explain last' to see the last decision",
            "Run 'aureus explain last-rejection' for rejection details",
            "Run 'aureus budget' to check remaining capacity",
        ]
        if budget_status and "exceed" in budget_status.lower():
            hints.insert(0, "Try splitting the intent into smaller tasks")
        elif budget_status and "reject" in budget_status.lower():
            hints.insert(0, "Simplify the intent or increase policy budgets")

        for hint in hints:
            lines.append(f"{self.INDENT}    • {hint}")
        lines.append("")

        lines.append(self._separator())
        return "\n".join(lines)

    def format_unexpected_error(self, error: Exception) -> str:
        """
        Format an unexpected (non-AUREUS) exception with helpful guidance.
        """
        meta = _SEVERITY_META["critical"]
        title = f"{meta['icon']}  UNEXPECTED ERROR"

        error_type = type(error).__name__
        error_msg  = str(error) or "(no message)"

        lines: List[str] = []
        lines.append(self._box(title, meta["color"]))
        lines.append("")

        lines.append(
            f"{self.INDENT}{self._bold(error_type)}: "
            f"{self._dim(error_msg[:120])}"
        )
        lines.append("")

        lines.append(
            f"{self.INDENT}{self._colored('💡', _Colors.YELLOW)}  {self._bold('What you can do')}"
        )
        hints = [
            "Check network connectivity and API key settings",
            "Run with --verbose for the full stack trace",
            "Run 'aureus doctor' for environment diagnostics",
            "Check the error catalog: https://aureus.dev/errors",
        ]
        # Tailor hints to common errors
        if "api" in error_msg.lower() or "key" in error_msg.lower():
            hints.insert(0, "Verify AUREUS_MODEL_API_KEY is set correctly")
        elif "permission" in error_msg.lower() or "access" in error_msg.lower():
            hints.insert(0, "Check file permissions in your project directory")
        elif "not found" in error_msg.lower() or "no such file" in error_msg.lower():
            hints.insert(0, "Run 'aureus init' to create missing configuration files")
        elif "connection" in error_msg.lower() or "timeout" in error_msg.lower():
            hints.insert(0, "Check network connectivity and model provider status")

        for hint in hints:
            lines.append(f"{self.INDENT}    • {hint}")
        lines.append("")

        lines.append(self._separator())
        return "\n".join(lines)

    def format_cli_error(self, message: str) -> str:
        """
        Format a plain CLIError (configuration/usage error).
        """
        meta = _SEVERITY_META["error"]
        title = f"{meta['icon']}  USAGE ERROR"

        lines: List[str] = []
        lines.append(self._box(title, meta["color"]))
        lines.append("")

        for msg_line in message.splitlines():
            stripped = msg_line.strip()
            if stripped:
                lines.append(f"{self.INDENT}{stripped}")
        lines.append("")

        # Check for common patterns and add targeted hints
        hints = []
        msg_lower = message.lower()
        if "policy file not found" in msg_lower or "run 'aureus init'" in msg_lower:
            hints = [
                "Run 'aureus init' to create the default policy",
                "Or pass --policy <path> to specify a custom policy file",
            ]
        elif "unknown command" in msg_lower:
            hints = [
                "Run 'aureus --help' to see all available commands",
                "Commands: init, code, status, budget, explain, test, review...",
            ]
        elif "failed to load policy" in msg_lower:
            hints = [
                "Check YAML syntax in your .aureus/policy.yaml",
                "Run 'aureus init' to regenerate a valid policy file",
            ]

        if hints:
            lines.append(
                f"{self.INDENT}{self._colored('💡', _Colors.YELLOW)}  {self._bold('Hint')}"
            )
            for hint in hints:
                lines.append(f"{self.INDENT}    • {hint}")
            lines.append("")

        lines.append(self._separator())
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Convenience dispatcher
    # ------------------------------------------------------------------

    def format(self, error: Exception) -> str:
        """
        Format any exception.

        - AUREUSError  → rich structured display
        - CLIError     → usage error with hints
        - Other        → unexpected error with diagnostics
        """
        # Import here to avoid circular imports
        try:
            from src.errors import AUREUSError as _AUREUSError
            from src.cli.main import CLIError as _CLIError
        except ImportError:
            return self.format_unexpected_error(error)

        if isinstance(error, _AUREUSError):
            return self.format_aureus_error(error)
        elif isinstance(error, _CLIError):
            return self.format_cli_error(str(error))
        else:
            return self.format_unexpected_error(error)

    # ------------------------------------------------------------------
    # Rendering helpers
    # ------------------------------------------------------------------

    def _box(self, title: str, title_color: str = "") -> str:
        """Render the top title box."""
        inner = f"  {title}  "
        # Strip ANSI for width calculation (rough: icon is 2 chars wide on most terminals)
        visible_len = len(title) + 4 + 2  # leading/trailing spaces + border
        pad = max(self.width - visible_len, 0)
        fill = " " * pad

        if self.use_color:
            colored_title = f"{title_color}{_Colors.BOLD}{title}{_Colors.RESET}"
            top = f"  ┌{'─' * (self.width - 4)}┐"
            mid = f"  │  {colored_title}{fill}  │"
            bot = f"  └{'─' * (self.width - 4)}┘"
        else:
            top = f"  +{'-' * (self.width - 4)}+"
            mid = f"  |  {title}{fill}  |"
            bot = f"  +{'-' * (self.width - 4)}+"

        return f"{top}\n{mid}\n{bot}"

    def _separator(self) -> str:
        if self.use_color:
            return f"  {_Colors.DIM}{'─' * (self.width - 4)}{_Colors.RESET}"
        return f"  {'-' * (self.width - 4)}"

    def _bold(self, text: str) -> str:
        if self.use_color:
            return f"{_Colors.BOLD}{text}{_Colors.RESET}"
        return text

    def _dim(self, text: str) -> str:
        if self.use_color:
            return f"{_Colors.DIM}{text}{_Colors.RESET}"
        return text

    def _colored(self, text: str, color: str) -> str:
        if self.use_color:
            return f"{color}{text}{_Colors.RESET}"
        return text


# ============================================================================
# Module-level convenience helpers
# ============================================================================

# Default formatter instances
_formatter_color   = ErrorFormatter(use_color=True)
_formatter_nocolor = ErrorFormatter(use_color=False)


def format_error(error: Exception, use_color: bool = True) -> str:
    """
    Format any exception for CLI display.

    Parameters
    ----------
    error:
        The exception to format.
    use_color:
        Whether to emit ANSI colour codes.

    Returns
    -------
    str
        Ready-to-print error string.
    """
    formatter = _formatter_color if use_color else _formatter_nocolor
    return formatter.format(error)


def format_build_failure(
    error_message: str,
    alternatives: Optional[List[Dict[str, Any]]] = None,
    budget_status: Optional[str] = None,
    use_color: bool = True,
) -> str:
    """
    Format a failed build result for CLI display.

    Parameters
    ----------
    error_message:
        The result.error string from a failed BuildResult.
    alternatives:
        Optional list of Planner alternative dicts.
    budget_status:
        Optional budget_status string from Cost object.
    use_color:
        Whether to emit ANSI colour codes.
    """
    formatter = _formatter_color if use_color else _formatter_nocolor
    return formatter.format_build_failure(error_message, alternatives, budget_status)


def print_error(error: Exception, use_color: bool = True) -> None:
    """Print formatted error to stderr."""
    print(format_error(error, use_color=use_color), file=sys.stderr)


def print_build_failure(
    error_message: str,
    alternatives: Optional[List[Dict[str, Any]]] = None,
    budget_status: Optional[str] = None,
    use_color: bool = True,
) -> None:
    """Print formatted build failure to stdout."""
    print(format_build_failure(
        error_message, alternatives, budget_status, use_color=use_color
    ))
