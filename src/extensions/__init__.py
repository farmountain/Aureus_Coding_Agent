"""
AUREUS Extension System

Constrained extension architecture for:
- Instructions (persistent prompts)
- Skills (reusable workflows)
- Hooks (lifecycle automation)
- MCP integration (future)

All extensions are governed by SPK budgets.
"""

from src.extensions.base import (
    Extension,
    ExtensionResult,
    ExtensionBudgetExceeded,
    ExtensionPermissionError,
    ExtensionValidationError
)

from src.extensions.instructions import InstructionExtension
from src.extensions.skills import Skill, SkillExtension
from src.extensions.hooks import Hook, HookExtension, LIFECYCLE_POINTS
from src.extensions.manager import ExtensionManager

__all__ = [
    "Extension",
    "ExtensionResult",
    "ExtensionBudgetExceeded",
    "ExtensionPermissionError",
    "ExtensionValidationError",
    "InstructionExtension",
    "Skill",
    "SkillExtension",
    "Hook",
    "HookExtension",
    "LIFECYCLE_POINTS",
    "ExtensionManager"
]
