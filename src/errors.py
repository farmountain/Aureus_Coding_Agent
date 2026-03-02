"""
AUREUS Error Catalog

Provides consistent, user-friendly error messages with:
- Unique error codes for debugging
- Clear, actionable suggestions
- Documentation links
- Structured error details

Error Code Format: CATEGORY_NNN
Categories:
- BUDGET: Budget and complexity violations
- POLICY: Policy and permission violations
- GVUFD: Specification generation errors (user-facing: "specification errors")
- SPK: Cost analysis and budget errors (user-facing: "cost analysis errors")
- TOOL: Tool execution errors
- CONTEXT: Context assembly errors
- GIT: Git operation errors
- CONFIG: Configuration errors
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from enum import Enum


class ErrorSeverity(Enum):
    """Error severity levels"""
    INFO = "info"  # Informational, non-blocking
    WARNING = "warning"  # Potential issue, continues execution
    ERROR = "error"  # Blocking error, operation failed
    CRITICAL = "critical"  # System-level failure


@dataclass
class ErrorDetails:
    """Structured error information"""
    code: str
    message: str
    severity: ErrorSeverity = ErrorSeverity.ERROR
    details: Dict[str, Any] = field(default_factory=dict)
    suggestion: Optional[str] = None
    docs_url: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)


class AUREUSError(Exception):
    """
    Base exception for all AUREUS errors.
    
    Provides structured error information with:
    - Unique error codes
    - User-friendly messages
    - Actionable suggestions
    - Documentation links
    """
    
    def __init__(
        self,
        code: str,
        message: str,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        details: Optional[Dict[str, Any]] = None,
        suggestion: Optional[str] = None,
        docs_url: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        self.error_details = ErrorDetails(
            code=code,
            message=message,
            severity=severity,
            details=details or {},
            suggestion=suggestion,
            docs_url=docs_url or f"https://aureus.dev/errors/{code}",
            context=context or {}
        )
        super().__init__(self._format_message())
    
    def _format_message(self) -> str:
        """Format error message for display"""
        parts = [
            f"[{self.error_details.code}] {self.error_details.message}"
        ]
        
        if self.error_details.details:
            parts.append("\nDetails:")
            for key, value in self.error_details.details.items():
                parts.append(f"  {key}: {value}")
        
        if self.error_details.suggestion:
            parts.append(f"\nSuggestion: {self.error_details.suggestion}")
        
        if self.error_details.docs_url:
            parts.append(f"\nDocs: {self.error_details.docs_url}")
        
        return "\n".join(parts)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "code": self.error_details.code,
            "message": self.error_details.message,
            "severity": self.error_details.severity.value,
            "details": self.error_details.details,
            "suggestion": self.error_details.suggestion,
            "docs_url": self.error_details.docs_url,
            "context": self.error_details.context
        }

    def format_for_cli(self, use_color: bool = True) -> str:
        """
        Return a rich, colour-coded string suitable for terminal display.

        Delegates to :class:`src.cli.error_display.ErrorFormatter` so the
        presentation layer stays outside the error model.

        Parameters
        ----------
        use_color:
            When True (default) emit ANSI colour codes.
            Pass False for CI/log-friendly plain-text output.
        """
        try:
            from src.cli.ui.error_display import ErrorFormatter
            return ErrorFormatter(use_color=use_color).format_aureus_error(self)
        except Exception:
            # Fallback to plain format if display module unavailable
            return self._format_message()


# ============================================================================
# Budget & Complexity Errors (BUDGET_xxx)
# ============================================================================

class BudgetExceededError(AUREUSError):
    """Raised when LOC budget is exceeded"""
    
    def __init__(self, current: int, limit: int, overage: int):
        super().__init__(
            code="BUDGET_001",
            message=f"LOC budget exceeded by {overage} lines",
            details={
                "current_loc": current,
                "budget_limit": limit,
                "overage": overage,
                "percentage": f"{(overage / limit * 100):.1f}%"
            },
            suggestion="Consider: 1) Remove unused code, 2) Simplify implementation, 3) Increase budget if justified",
        )


class FileCountExceededError(AUREUSError):
    """Raised when file count budget is exceeded"""
    
    def __init__(self, current: int, limit: int):
        super().__init__(
            code="BUDGET_002",
            message=f"File count exceeded ({current}/{limit})",
            details={"current_files": current, "max_files": limit},
            suggestion="Consolidate related functionality into fewer files or increase file budget"
        )


class DependencyBudgetExceededError(AUREUSError):
    """Raised when dependency budget is exceeded"""
    
    def __init__(self, current: int, limit: int, new_deps: List[str]):
        super().__init__(
            code="BUDGET_003",
            message=f"Dependency budget exceeded ({current}/{limit})",
            details={
                "current_dependencies": current,
                "max_dependencies": limit,
                "new_dependencies": new_deps
            },
            suggestion="Remove unnecessary dependencies or justify the additions"
        )


class ComplexityTooHighError(AUREUSError):
    """Raised when complexity score is too high"""
    
    def __init__(self, score: float, threshold: float, component: str):
        super().__init__(
            code="BUDGET_004",
            message=f"Complexity too high for {component}",
            details={
                "complexity_score": score,
                "threshold": threshold,
                "component": component
            },
            suggestion="Simplify the implementation or break into smaller components"
        )


# ============================================================================
# Policy & Permission Errors (POLICY_xxx)
# ============================================================================

class PolicyViolationError(AUREUSError):
    """Raised when policy is violated"""
    
    def __init__(self, policy_rule: str, violation: str):
        super().__init__(
            code="POLICY_001",
            message=f"Policy violation: {policy_rule}",
            details={"rule": policy_rule, "violation": violation},
            suggestion="Modify the request to comply with project policy or update policy if appropriate"
        )


class PermissionDeniedError(AUREUSError):
    """Raised when operation requires elevated permissions"""
    
    def __init__(self, operation: str, required_permission: str):
        super().__init__(
            code="POLICY_002",
            message=f"Permission denied for operation: {operation}",
            details={
                "operation": operation,
                "required_permission": required_permission
            },
            suggestion=f"Enable '{required_permission}' permission in policy configuration"
        )


class ForbiddenPatternError(AUREUSError):
    """Raised when code uses forbidden pattern"""
    
    def __init__(self, pattern: str, reason: str, location: Optional[str] = None):
        super().__init__(
            code="POLICY_003",
            message=f"Forbidden pattern detected: {pattern}",
            details={
                "pattern": pattern,
                "reason": reason,
                "location": location or "unknown"
            },
            suggestion=f"Avoid {pattern}. {reason}"
        )


# ============================================================================
# Specification Generation Errors (GVUFD_xxx)
# User-facing: "Specification errors"
# Developer context: GVUFD (Global Value Utility Function Designer)
# ============================================================================

class IntentTooVagueError(AUREUSError):
    """Raised when user intent is too vague to generate spec"""
    
    def __init__(self, intent: str, missing_details: List[str]):
        super().__init__(
            code="GVUFD_001",
            message="Intent is too vague to generate specification",
            details={
                "intent": intent,
                "missing_details": missing_details
            },
            suggestion=f"Please provide more details about: {', '.join(missing_details)}"
        )


class SpecificationGenerationError(AUREUSError):
    """Raised when spec generation fails"""
    
    def __init__(self, intent: str, reason: str):
        super().__init__(
            code="GVUFD_002",
            message="Failed to generate specification",
            details={"intent": intent, "reason": reason},
            suggestion="Try rephrasing the intent or providing more context"
        )


class AmbiguousIntentError(AUREUSError):
    """Raised when intent has multiple interpretations"""
    
    def __init__(self, intent: str, interpretations: List[str]):
        super().__init__(
            code="GVUFD_003",
            message="Intent is ambiguous",
            details={
                "intent": intent,
                "possible_interpretations": interpretations
            },
            suggestion=f"Please clarify which you mean: {', '.join(interpretations)}"
        )


# ============================================================================
# Cost Analysis Errors (SPK_xxx)
# User-facing: "Cost analysis errors"
# Developer context: SPK (Self-Pricing Kernel)
# ============================================================================

class CostCalculationError(AUREUSError):
    """Raised when cost calculation fails"""
    
    def __init__(self, reason: str, action: str):
        super().__init__(
            code="SPK_001",
            message="Failed to calculate cost",
            details={"reason": reason, "action": action},
            suggestion="Check action parameters and try again"
        )


class SessionCostLimitError(AUREUSError):
    """Raised when session cost limit is reached"""
    
    def __init__(self, current: float, limit: float):
        super().__init__(
            code="SPK_002",
            message=f"Session cost limit reached ({current:.1f}/{limit:.1f})",
            details={
                "current_cost": current,
                "session_limit": limit,
                "percentage": f"{(current / limit * 100):.1f}%"
            },
            suggestion="Start a new session or request cost limit increase"
        )


# ============================================================================
# Tool Execution Errors (TOOL_xxx)
# ============================================================================

class ToolExecutionError(AUREUSError):
    """Raised when tool execution fails"""
    
    def __init__(self, tool_name: str, reason: str, params: Optional[Dict] = None):
        super().__init__(
            code="TOOL_001",
            message=f"Tool execution failed: {tool_name}",
            details={
                "tool": tool_name,
                "reason": reason,
                "parameters": params or {}
            },
            suggestion="Check tool parameters and permissions"
        )


class ToolNotFoundError(AUREUSError):
    """Raised when requested tool doesn't exist"""
    
    def __init__(self, tool_name: str, available_tools: List[str]):
        super().__init__(
            code="TOOL_002",
            message=f"Tool not found: {tool_name}",
            details={
                "requested_tool": tool_name,
                "available_tools": available_tools
            },
            suggestion=f"Available tools: {', '.join(available_tools)}"
        )


class ToolValidationError(AUREUSError):
    """Raised when tool parameters are invalid"""
    
    def __init__(self, tool_name: str, invalid_params: Dict[str, str]):
        super().__init__(
            code="TOOL_003",
            message=f"Invalid parameters for tool: {tool_name}",
            details={
                "tool": tool_name,
                "invalid_parameters": invalid_params
            },
            suggestion="Check parameter types and required fields"
        )


# ============================================================================
# Context Assembly Errors (CONTEXT_xxx)
# ============================================================================

class ContextAssemblyError(AUREUSError):
    """Raised when context assembly fails"""
    
    def __init__(self, reason: str, project_path: Optional[str] = None):
        super().__init__(
            code="CONTEXT_001",
            message="Failed to assemble project context",
            details={
                "reason": reason,
                "project_path": project_path or "unknown"
            },
            suggestion="Check project path and file permissions"
        )


class IndexingError(AUREUSError):
    """Raised when repository indexing fails"""
    
    def __init__(self, reason: str, file_path: Optional[str] = None):
        super().__init__(
            code="CONTEXT_002",
            message="Failed to index repository",
            severity=ErrorSeverity.WARNING,  # Non-blocking, falls back to simple mode
            details={
                "reason": reason,
                "file_path": file_path or "multiple files"
            },
            suggestion="Indexing will be skipped. Check for syntax errors in Python files"
        )


class HotFileNotFoundError(AUREUSError):
    """Raised when specified hot file doesn't exist"""
    
    def __init__(self, file_path: str, available_files: List[str]):
        super().__init__(
            code="CONTEXT_003",
            message=f"Hot file not found: {file_path}",
            details={
                "requested_file": file_path,
                "similar_files": available_files[:5]  # Show top 5 similar
            },
            suggestion="Check file path or remove from hot files configuration"
        )


# ============================================================================
# Git Operation Errors (GIT_xxx)
# ============================================================================

class GitOperationError(AUREUSError):
    """Raised when git operation fails"""
    
    def __init__(self, operation: str, reason: str):
        super().__init__(
            code="GIT_001",
            message=f"Git operation failed: {operation}",
            details={"operation": operation, "reason": reason},
            suggestion="Check git repository state and permissions"
        )


class DirtyWorkingTreeError(AUREUSError):
    """Raised when git working tree has uncommitted changes"""
    
    def __init__(self, uncommitted_files: List[str]):
        super().__init__(
            code="GIT_002",
            message="Working tree has uncommitted changes",
            severity=ErrorSeverity.WARNING,
            details={
                "uncommitted_files": uncommitted_files,
                "count": len(uncommitted_files)
            },
            suggestion="Commit or stash changes before proceeding"
        )


class RollbackError(AUREUSError):
    """Raised when rollback operation fails"""
    
    def __init__(self, reason: str, commit_hash: Optional[str] = None):
        super().__init__(
            code="GIT_003",
            message="Failed to rollback changes",
            severity=ErrorSeverity.CRITICAL,
            details={
                "reason": reason,
                "target_commit": commit_hash or "unknown"
            },
            suggestion="Manual recovery may be required. Check git log and status"
        )


# ============================================================================
# Configuration Errors (CONFIG_xxx)
# ============================================================================

class PolicyLoadError(AUREUSError):
    """Raised when policy file cannot be loaded"""
    
    def __init__(self, file_path: str, reason: str):
        super().__init__(
            code="CONFIG_001",
            message=f"Failed to load policy file",
            details={
                "file_path": file_path,
                "reason": reason
            },
            suggestion="Check policy file syntax and path"
        )


class InvalidConfigurationError(AUREUSError):
    """Raised when configuration is invalid"""
    
    def __init__(self, field: str, value: Any, reason: str):
        super().__init__(
            code="CONFIG_002",
            message=f"Invalid configuration: {field}",
            details={
                "field": field,
                "value": str(value),
                "reason": reason
            },
            suggestion=f"Fix '{field}' in configuration. {reason}"
        )


class MissingRequiredConfigError(AUREUSError):
    """Raised when required configuration is missing"""
    
    def __init__(self, missing_fields: List[str]):
        super().__init__(
            code="CONFIG_003",
            message="Required configuration fields missing",
            details={"missing_fields": missing_fields},
            suggestion=f"Add required fields to configuration: {', '.join(missing_fields)}"
        )


# ============================================================================
# Error Catalog Registry
# ============================================================================

ERROR_CATALOG = {
    # Budget errors
    "BUDGET_001": "LOC budget exceeded",
    "BUDGET_002": "File count exceeded",
    "BUDGET_003": "Dependency budget exceeded",
    "BUDGET_004": "Complexity too high",
    
    # Policy errors
    "POLICY_001": "Policy violation",
    "POLICY_002": "Permission denied",
    "POLICY_003": "Forbidden pattern detected",
    
    # GVUFD errors
    "GVUFD_001": "Intent too vague",
    "GVUFD_002": "Specification generation failed",
    "GVUFD_003": "Ambiguous intent",
    
    # SPK errors
    "SPK_001": "Cost calculation failed",
    "SPK_002": "Session cost limit reached",
    
    # Tool errors
    "TOOL_001": "Tool execution failed",
    "TOOL_002": "Tool not found",
    "TOOL_003": "Tool parameter validation failed",
    
    # Context errors
    "CONTEXT_001": "Context assembly failed",
    "CONTEXT_002": "Repository indexing failed",
    "CONTEXT_003": "Hot file not found",
    
    # Git errors
    "GIT_001": "Git operation failed",
    "GIT_002": "Dirty working tree",
    "GIT_003": "Rollback failed",
    
    # Config errors
    "CONFIG_001": "Policy load failed",
    "CONFIG_002": "Invalid configuration",
    "CONFIG_003": "Missing required configuration",
}


def get_error_description(code: str) -> str:
    """Get short description for error code"""
    return ERROR_CATALOG.get(code, "Unknown error")


def list_all_errors() -> Dict[str, str]:
    """List all error codes and descriptions"""
    return ERROR_CATALOG.copy()
