"""
Extension Manager

Global coordinator for all AUREUS extensions.

Responsibilities:
- Register/unregister extensions
- Enforce global extension budget (e.g., 20% of project budget)
- Track costs across all extensions
- Provide status monitoring
"""

from typing import Dict, List, Optional, Any
from src.interfaces import Policy
from src.extensions.base import Extension, ExtensionBudgetExceeded


class ExtensionManager:
    """
    Global extension coordinator.
    
    Manages lifecycle and budgets for all extensions:
    - Instructions: Persistent project-specific prompts
    - Skills: Reusable workflows
    - Hooks: Lifecycle automation
    - Future: MCP integrations
    """
    
    def __init__(
        self,
        policy: Policy,
        global_extension_budget: float = 500.0
    ):
        """
        Initialize extension manager.
        
        Args:
            policy: Governance policy
            global_extension_budget: Total budget for all extensions combined
        """
        self.policy = policy
        self.global_budget = global_extension_budget
        self.global_cost_used = 0.0
        
        # Registered extensions
        self.extensions: Dict[str, Extension] = {}
    
    def register_extension(self, name: str, extension: Extension):
        """
        Register an extension.
        
        Args:
            name: Extension identifier
            extension: Extension instance
        
        Raises:
            ExtensionBudgetExceeded: If extension would exceed global budget
            ValueError: If extension name already registered
        """
        if name in self.extensions:
            raise ValueError(f"Extension '{name}' is already registered")
        
        # Check if extension's max_cost would exceed global budget
        # (We reserve the extension's max_cost from global budget)
        total_allocated = sum(ext.max_cost for ext in self.extensions.values())
        
        if total_allocated + extension.max_cost > self.global_budget:
            raise ExtensionBudgetExceeded(
                f"Cannot register extension '{name}': "
                f"max_cost {extension.max_cost} would exceed global budget. "
                f"Allocated: {total_allocated}, "
                f"Global: {self.global_budget}, "
                f"Remaining: {self.global_budget - total_allocated}"
            )
        
        # Register extension
        self.extensions[name] = extension
    
    def unregister_extension(self, name: str) -> bool:
        """
        Unregister an extension.
        
        Args:
            name: Extension identifier
        
        Returns:
            True if extension was removed, False if not found
        """
        if name in self.extensions:
            del self.extensions[name]
            return True
        return False
    
    def get_extension(self, name: str) -> Optional[Extension]:
        """
        Get extension by name.
        
        Args:
            name: Extension identifier
        
        Returns:
            Extension instance or None if not found
        """
        return self.extensions.get(name)
    
    def list_extensions(self) -> List[str]:
        """Get list of registered extension names"""
        return list(self.extensions.keys())
    
    def get_total_cost_used(self) -> float:
        """
        Get total cost used across all extensions.
        
        Returns:
            Sum of all extension costs
        """
        return sum(ext.cost_used for ext in self.extensions.values())
    
    def get_remaining_budget(self) -> float:
        """
        Get remaining global budget.
        
        Returns:
            Global budget minus total cost used
        """
        return self.global_budget - self.get_total_cost_used()
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get status of all extensions.
        
        Returns:
            Dict with global stats and per-extension details
        """
        return {
            "global_budget": self.global_budget,
            "global_cost_used": self.get_total_cost_used(),
            "global_remaining": self.get_remaining_budget(),
            "global_usage_percent": (self.get_total_cost_used() / self.global_budget * 100)
                                    if self.global_budget > 0 else 0.0,
            "extensions": {
                name: {
                    "name": ext.name,
                    "max_cost": ext.max_cost,
                    "cost_used": ext.cost_used,
                    "remaining": ext.get_budget_remaining(),
                    "usage_percent": ext.get_budget_usage_percent()
                }
                for name, ext in self.extensions.items()
            }
        }
    
    def check_global_budget(self, estimated_cost: float) -> bool:
        """
        Check if operation would fit within global budget.
        
        Args:
            estimated_cost: Estimated cost of operation
        
        Returns:
            True if operation would fit, False otherwise
        """
        return (self.get_total_cost_used() + estimated_cost) <= self.global_budget
    
    def reset_all_costs(self):
        """
        Reset cost tracking for all extensions.
        
        WARNING: This should only be used for testing or when starting
        a new project phase. It does not affect individual extension
        budget limits.
        """
        for ext in self.extensions.values():
            ext.cost_used = 0.0
        self.global_cost_used = 0.0
