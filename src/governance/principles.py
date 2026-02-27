"""
Immutable Governance Principles

Core principles that define Aureus's nature and cannot be modified
by self-play or any automated process.

These principles ensure:
- Safety (sandbox enforcement)
- Transparency (human approval for high-cost changes)
- Reversibility (backup maintenance)
- Alignment (respect for user policy)
"""

from enum import Enum
from typing import Final


class GovernancePrinciple(Enum):
    """Core immutable governance principles"""
    
    # Principle 1: Always respect user policy
    RESPECT_POLICY = "respect_policy"
    
    # Principle 2: Never escape project_root sandbox
    ENFORCE_SANDBOX = "enforce_sandbox"
    
    # Principle 3: Always provide alternatives when budget exceeded
    PROVIDE_ALTERNATIVES = "provide_alternatives"
    
    # Principle 4: Human approval required for high-cost changes
    REQUIRE_HUMAN_APPROVAL = "require_human_approval"
    
    # Principle 5: All actions must be reversible
    MAINTAIN_BACKUPS = "maintain_backups"
    
    # Principle 6: Never modify immutable files
    PROTECT_IMMUTABLE = "protect_immutable"
    
    # Principle 7: Gradual cost scaling (warn before reject)
    GRADUAL_ENFORCEMENT = "gradual_enforcement"


class ImmutablePrinciples:
    """
    Immutable governance principles for Aureus
    
    These values are hardcoded and cannot be changed by:
    - Self-play
    - Configuration files
    - User policies
    - Any automated process
    
    They define what Aureus IS at its core.
    """
    
    # === SAFETY PRINCIPLES ===
    
    # Always enforce sandbox boundaries
    ENFORCE_SANDBOX: Final[bool] = True
    
    # Never allow path traversal attacks
    VALIDATE_ALL_PATHS: Final[bool] = True
    
    # Maintain file backups before modifications
    MAINTAIN_BACKUPS: Final[bool] = True
    
    # Never modify immutable files (LICENSE, sandbox.py, etc.)
    PROTECT_IMMUTABLE_FILES: Final[bool] = True
    
    # === TRANSPARENCY PRINCIPLES ===
    
    # Require human approval for high-cost changes
    REQUIRE_HUMAN_APPROVAL: Final[bool] = True
    
    # Always explain what changes will be made
    PROVIDE_EXPLANATIONS: Final[bool] = True
    
    # Show cost estimates before execution
    SHOW_COST_ESTIMATES: Final[bool] = True
    
    # === POLICY PRINCIPLES ===
    
    # Always respect user-defined policy
    RESPECT_USER_POLICY: Final[bool] = True
    
    # Never override policy without explicit user command
    NO_POLICY_OVERRIDE: Final[bool] = True
    
    # Provide alternatives when budget exceeded
    PROVIDE_ALTERNATIVES: Final[bool] = True
    
    # === REVERSIBILITY PRINCIPLES ===
    
    # All file modifications must be reversible
    ENSURE_REVERSIBILITY: Final[bool] = True
    
    # Keep modification history for rollback
    MAINTAIN_HISTORY: Final[bool] = True
    
    # Never perform destructive operations without backup
    BACKUP_BEFORE_DESTROY: Final[bool] = True
    
    # === COST THRESHOLDS ===
    
    # Base thresholds (can be adjusted by policy, but not disabled)
    # These are MINIMUM values - policy can make them stricter
    MIN_AUTO_PROCEED_THRESHOLD: Final[float] = 100.0  # Minimum LOC for auto-proceed
    MIN_PROMPT_THRESHOLD: Final[float] = 300.0        # Minimum LOC for prompting
    MIN_REJECTION_THRESHOLD: Final[float] = 1000.0    # Minimum LOC for rejection
    
    # Cost must always be calculated (cannot be disabled)
    ALWAYS_CALCULATE_COST: Final[bool] = True
    
    # === SELF-PLAY BOUNDARIES ===
    
    # Self-play can modify Aureus code
    SELF_PLAY_CAN_MODIFY_AGENT: Final[bool] = True
    
    # Self-play CANNOT modify these principles
    SELF_PLAY_CANNOT_MODIFY_PRINCIPLES: Final[bool] = True
    
    # Self-play CANNOT modify user workspace
    SELF_PLAY_CANNOT_MODIFY_WORKSPACE: Final[bool] = True
    
    # Self-play CANNOT disable safety checks
    SELF_PLAY_CANNOT_DISABLE_SAFETY: Final[bool] = True
    
    # === VALIDATION ===
    
    @staticmethod
    def validate_all_enabled() -> bool:
        """
        Validate that all safety principles are enabled
        
        This function is called on startup to ensure
        no principle has been accidentally disabled.
        
        Returns:
            True if all principles are enabled
            
        Raises:
            AssertionError: If any principle is disabled
        """
        # Safety checks
        assert ImmutablePrinciples.ENFORCE_SANDBOX is True
        assert ImmutablePrinciples.VALIDATE_ALL_PATHS is True
        assert ImmutablePrinciples.MAINTAIN_BACKUPS is True
        assert ImmutablePrinciples.PROTECT_IMMUTABLE_FILES is True
        
        # Transparency checks
        assert ImmutablePrinciples.REQUIRE_HUMAN_APPROVAL is True
        assert ImmutablePrinciples.PROVIDE_EXPLANATIONS is True
        assert ImmutablePrinciples.SHOW_COST_ESTIMATES is True
        
        # Policy checks
        assert ImmutablePrinciples.RESPECT_USER_POLICY is True
        assert ImmutablePrinciples.NO_POLICY_OVERRIDE is True
        assert ImmutablePrinciples.PROVIDE_ALTERNATIVES is True
        
        # Reversibility checks
        assert ImmutablePrinciples.ENSURE_REVERSIBILITY is True
        assert ImmutablePrinciples.MAINTAIN_HISTORY is True
        assert ImmutablePrinciples.BACKUP_BEFORE_DESTROY is True
        
        # Cost checks
        assert ImmutablePrinciples.ALWAYS_CALCULATE_COST is True
        
        # Self-play boundary checks
        assert ImmutablePrinciples.SELF_PLAY_CANNOT_MODIFY_PRINCIPLES is True
        assert ImmutablePrinciples.SELF_PLAY_CANNOT_MODIFY_WORKSPACE is True
        assert ImmutablePrinciples.SELF_PLAY_CANNOT_DISABLE_SAFETY is True
        
        return True
    
    @staticmethod
    def get_principle_description(principle: GovernancePrinciple) -> str:
        """Get human-readable description of a principle"""
        descriptions = {
            GovernancePrinciple.RESPECT_POLICY: 
                "Always honor the user's policy constraints and budgets",
            GovernancePrinciple.ENFORCE_SANDBOX:
                "Never allow file operations outside project_root sandbox",
            GovernancePrinciple.PROVIDE_ALTERNATIVES:
                "When a change exceeds budget, suggest simpler alternatives",
            GovernancePrinciple.REQUIRE_HUMAN_APPROVAL:
                "High-cost changes require explicit human confirmation",
            GovernancePrinciple.MAINTAIN_BACKUPS:
                "Always create backups before modifying files",
            GovernancePrinciple.PROTECT_IMMUTABLE:
                "Never modify immutable files (LICENSE, core principles, etc.)",
            GovernancePrinciple.GRADUAL_ENFORCEMENT:
                "Warn users before rejecting (gradual cost escalation)"
        }
        return descriptions.get(principle, "Unknown principle")


# Validate on module import
ImmutablePrinciples.validate_all_enabled()
