"""
Skill Extension

Reusable workflow system with governance.

Skills are like functions but with:
- Cost budgets (SPK enforcement)
- Permission requirements
- Validation rules
"""

from typing import Callable, Dict, List, Optional, Any
from dataclasses import dataclass, field
from src.extensions.base import (
    Extension,
    ExtensionResult,
    ExtensionBudgetExceeded,
    ExtensionPermissionError
)


@dataclass
class Skill:
    """
    Reusable workflow definition.
    
    Skills encapsulate common workflows with governance.
    """
    name: str
    description: str
    workflow: Callable
    required_permissions: List[str] = field(default_factory=list)
    estimated_cost: float = 10.0  # Default cost estimate
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __repr__(self) -> str:
        return f"Skill(name='{self.name}', cost={self.estimated_cost})"


class SkillExtension(Extension):
    """
    Reusable workflow system with governance.
    
    Skills are registered workflows that can be executed with
    cost and permission enforcement.
    """
    
    def __init__(
        self,
        policy,
        max_cost: float = 200.0
    ):
        """
        Initialize skill extension.
        
        Args:
            policy: Governance policy
            max_cost: Maximum cost budget for all skills
        """
        super().__init__(
            name="skills",
            policy=policy,
            max_cost=max_cost,
            required_permissions=["extensions"]
        )
        
        self.skills: Dict[str, Skill] = {}
    
    def execute(self, **kwargs) -> ExtensionResult:
        """
        Execute a skill by name.
        
        Args:
            skill_name: Name of skill to execute
            **kwargs: Arguments to pass to skill workflow
        
        Returns:
            ExtensionResult with skill output
        """
        skill_name = kwargs.get("skill_name")
        
        if not skill_name:
            return self._error("skill_name parameter required")
        
        return self.execute_skill(skill_name, **kwargs)
    
    def register_skill(self, skill: Skill):
        """
        Register a skill with validation.
        
        Args:
            skill: Skill to register
        
        Raises:
            ExtensionPermissionError: If skill requires unavailable permission
            ExtensionBudgetExceeded: If skill would exceed total budget
        """
        # Validate permissions
        for perm in skill.required_permissions:
            if not self.policy.permissions.get(perm, False):
                raise ExtensionPermissionError(
                    f"Skill '{skill.name}' requires permission '{perm}' "
                    f"but it is not granted in policy"
                )
        
        # Check if registering skill would exceed budget
        # (Skills reserve their estimated cost upfront)
        if not self.check_budget(skill.estimated_cost):
            raise ExtensionBudgetExceeded(
                f"Cannot register skill '{skill.name}': "
                f"estimated cost {skill.estimated_cost} exceeds remaining budget "
                f"{self.get_budget_remaining()}"
            )
        
        # Register skill
        self.skills[skill.name] = skill
    
    def execute_skill(self, skill_name: str, **kwargs) -> ExtensionResult:
        """
        Execute a registered skill.
        
        Args:
            skill_name: Name of skill to execute
            **kwargs: Arguments to pass to skill workflow
        
        Returns:
            ExtensionResult with skill output
        """
        # Check skill exists
        skill = self.skills.get(skill_name)
        if not skill:
            return self._error(
                f"Skill '{skill_name}' not found. "
                f"Available skills: {list(self.skills.keys())}",
                metadata={"available_skills": list(self.skills.keys())}
            )
        
        # Check budget before execution
        if not self.check_budget(skill.estimated_cost):
            return self._error(
                f"Skill '{skill_name}' would exceed budget: "
                f"{skill.estimated_cost} > {self.get_budget_remaining()}",
                metadata={
                    "skill_cost": skill.estimated_cost,
                    "budget_remaining": self.get_budget_remaining()
                }
            )
        
        try:
            # Execute workflow
            output = skill.workflow(**kwargs)
            
            # Track cost (use estimated cost for now)
            # In Phase 2B, we'll measure actual cost
            actual_cost = skill.estimated_cost
            
            return self._success(
                output=output,
                cost_used=actual_cost,
                metadata={
                    "skill_name": skill.name,
                    "skill_description": skill.description,
                    "estimated_cost": skill.estimated_cost,
                    "actual_cost": actual_cost
                }
            )
        
        except Exception as e:
            return self._error(
                f"Skill '{skill_name}' failed: {e}",
                metadata={
                    "skill_name": skill.name,
                    "exception_type": type(e).__name__,
                    "exception_message": str(e)
                }
            )
    
    def list_skills(self) -> List[str]:
        """Get list of registered skill names"""
        return list(self.skills.keys())
    
    def get_skill(self, name: str) -> Optional[Skill]:
        """Get skill by name"""
        return self.skills.get(name)
    
    def unregister_skill(self, name: str) -> bool:
        """
        Unregister a skill.
        
        Args:
            name: Skill name
        
        Returns:
            True if skill was removed, False if not found
        """
        if name in self.skills:
            del self.skills[name]
            return True
        return False
