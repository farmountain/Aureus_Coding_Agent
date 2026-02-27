"""
Extension Base Classes for AUREUS

Provides foundation for constrained extension system:
- Instructions (.aureus/instructions.md)
- Skills (reusable workflows)
- Hooks (lifecycle automation)
- MCP (external tools)

All extensions are governed by SPK budget enforcement.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from dataclasses import dataclass, field
from pathlib import Path
from src.interfaces import Policy


# ============================================================================
# Exceptions
# ============================================================================

class ExtensionBudgetExceeded(Exception):
    """Raised when extension exceeds its cost budget"""
    pass


class ExtensionPermissionError(Exception):
    """Raised when extension lacks required permission"""
    pass


class ExtensionValidationError(Exception):
    """Raised when extension fails validation"""
    pass


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class ExtensionResult:
    """Result from extension execution"""
    success: bool
    output: Any
    extension_name: str
    cost_used: float
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            "success": self.success,
            "output": self.output,
            "extension_name": self.extension_name,
            "cost_used": self.cost_used,
            "error": self.error,
            "metadata": self.metadata
        }


# ============================================================================
# Base Extension Class
# ============================================================================

class Extension(ABC):
    """
    Base class for all AUREUS extensions.
    
    Extensions are constrained by:
    - SPK cost budgets (max_cost)
    - Policy permissions (policy.permissions)
    - Validation rules
    
    All extensions must implement execute() method.
    """
    
    def __init__(
        self,
        name: str,
        policy: Policy,
        max_cost: float = 100.0,
        required_permissions: Optional[list] = None
    ):
        """
        Initialize extension.
        
        Args:
            name: Extension name (unique identifier)
            policy: Governance policy
            max_cost: Maximum cost budget for this extension
            required_permissions: List of required permissions
        """
        self.name = name
        self.policy = policy
        self.max_cost = max_cost
        self.cost_used = 0.0
        self.required_permissions = required_permissions or []
        
        # Validate permissions
        self._validate_permissions()
    
    @abstractmethod
    def execute(self, **kwargs) -> ExtensionResult:
        """
        Execute extension with governance.
        
        Must be implemented by subclasses.
        
        Args:
            **kwargs: Extension-specific parameters
        
        Returns:
            ExtensionResult with success status
        
        Raises:
            ExtensionBudgetExceeded: If operation would exceed budget
            ExtensionPermissionError: If missing required permission
        """
        pass
    
    def check_budget(self, estimated_cost: float) -> bool:
        """
        Check if operation is within budget.
        
        Args:
            estimated_cost: Estimated cost of operation
        
        Returns:
            True if within budget, False otherwise
        """
        return (self.cost_used + estimated_cost) <= self.max_cost
    
    def get_budget_remaining(self) -> float:
        """Get remaining budget"""
        return max(0.0, self.max_cost - self.cost_used)
    
    def get_budget_usage_percent(self) -> float:
        """Get budget usage as percentage"""
        if self.max_cost == 0.0:
            return 0.0
        return (self.cost_used / self.max_cost) * 100.0
    
    def _validate_permissions(self):
        """Validate extension has required permissions"""
        for perm in self.required_permissions:
            if not self.policy.permissions.get(perm, False):
                raise ExtensionPermissionError(
                    f"Extension {self.name} requires permission '{perm}' "
                    f"but it is not granted in policy"
                )
    
    def _success(
        self,
        output: Any,
        cost_used: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ExtensionResult:
        """
        Create success result.
        
        Args:
            output: Extension output
            cost_used: Cost consumed by this operation
            metadata: Optional metadata
        
        Returns:
            ExtensionResult with success=True
        """
        self.cost_used += cost_used
        
        return ExtensionResult(
            success=True,
            output=output,
            extension_name=self.name,
            cost_used=cost_used,
            metadata=metadata or {}
        )
    
    def _error(
        self,
        error: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ExtensionResult:
        """
        Create error result.
        
        Args:
            error: Error message
            metadata: Optional metadata
        
        Returns:
            ExtensionResult with success=False
        """
        return ExtensionResult(
            success=False,
            output=None,
            extension_name=self.name,
            cost_used=0.0,
            error=error,
            metadata=metadata or {}
        )
    
    def __repr__(self) -> str:
        """String representation"""
        return (
            f"{self.__class__.__name__}(name='{self.name}', "
            f"cost={self.cost_used:.1f}/{self.max_cost:.1f})"
        )
