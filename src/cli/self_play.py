"""
Enhanced CLI with Self-Play Mode and Memory Commands

Extends the main CLI with:
- --self-play flag for self-improvement mode
- Memory command integration
- Authorization validation
"""

from pathlib import Path
from typing import Optional
import os
from src.interfaces import Policy
from src.governance.policy import PolicyLoader
from src.security import Sandbox, SandboxViolation
from src.governance.principles import ImmutablePrinciples


class SelfPlayAuthorizationError(Exception):
    """Raised when self-play authorization fails"""
    pass


class SelfPlayMode:
    """
    Manages self-play mode operations
    
    Self-play mode allows Aureus to improve itself by modifying
    its own source code under governance constraints.
    """
    
    def __init__(self):
        self.aureus_policy_path = Sandbox.AUREUS_ROOT / "aureus-self-policy.yaml"
    
    def is_authorized(self) -> bool:
        """
        Check if self-play mode is authorized
        
        Checks:
        1. AUREUS_SELF_PLAY environment variable
        2. Aureus self-policy exists
        3. All immutable principles intact
        
        Returns:
            True if authorized
        """
        # Check environment variable
        if not os.environ.get('AUREUS_SELF_PLAY', '').lower() in ['true', '1', 'yes']:
            return False
        
        # Check self-policy exists
        if not self.aureus_policy_path.exists():
            return False
        
        # Validate immutable principles
        try:
            ImmutablePrinciples.validate_all_enabled()
        except AssertionError:
            return False
        
        return True
    
    def load_self_policy(self) -> Policy:
        """
        Load Aureus's self-governance policy
        
        Returns:
            Aureus self-policy
            
        Raises:
            SelfPlayAuthorizationError: If not authorized
        """
        if not self.is_authorized():
            raise SelfPlayAuthorizationError(
                "Self-play mode not authorized. Set AUREUS_SELF_PLAY=true and ensure "
                "aureus-self-policy.yaml exists."
            )
        
        loader = PolicyLoader()
        policy = loader.load(self.aureus_policy_path)
        
        # Validate policy is for Aureus itself
        if not policy.project_root.resolve() == Sandbox.AUREUS_ROOT:
            raise SelfPlayAuthorizationError(
                f"Self-policy project_root must be Aureus root: {Sandbox.AUREUS_ROOT}"
            )
        
        return policy
    
    def validate_modification(self, path: Path) -> bool:
        """
        Validate that path can be modified in self-play mode
        
        Args:
            path: Path to validate
            
        Returns:
            True if allowed
            
        Raises:
            SandboxViolation: If modification not allowed
        """
        return Sandbox.validate_modification(path, is_self_play=True)
    
    def get_improvement_areas(self) -> list[str]:
        """
        Get areas where Aureus can improve itself
        
        Returns:
            List of improvement areas from self-policy
        """
        policy = self.load_self_policy()
        
        # Extract from policy if available
        if hasattr(policy, 'self_play') and 'improvement_areas' in policy.self_play:
            return policy.self_play['improvement_areas']
        
        # Default improvement areas
        return [
            "Cost estimation accuracy",
            "Plan decomposition quality",
            "Memory pattern recognition",
            "Alternative generation",
            "Performance optimization",
            "Test coverage improvement"
        ]


def validate_self_play_environment() -> tuple[bool, str]:
    """
    Validate environment for self-play mode
    
    Returns:
        Tuple of (is_valid, message)
    """
    self_play = SelfPlayMode()
    
    # Check authorization
    if not self_play.is_authorized():
        return False, "Self-play not authorized. Set AUREUS_SELF_PLAY=true"
    
    # Check all tests pass
    import subprocess
    result = subprocess.run(
        ['pytest', 'tests/', '-q'],
        cwd=str(Sandbox.AUREUS_ROOT),
        capture_output=True
    )
    
    if result.returncode != 0:
        return False, "All tests must pass before self-play mode"
    
    # Check immutable principles
    try:
        ImmutablePrinciples.validate_all_enabled()
    except AssertionError as e:
        return False, f"Immutable principles validation failed: {e}"
    
    return True, "Self-play environment validated"


def get_self_play_status() -> dict:
    """
    Get current self-play status
    
    Returns:
        Dictionary with status information
    """
    self_play = SelfPlayMode()
    
    return {
        'authorized': self_play.is_authorized(),
        'policy_exists': self_play.aureus_policy_path.exists(),
        'principles_intact': _check_principles_intact(),
        'aureus_root': str(Sandbox.AUREUS_ROOT),
        'improvement_areas': self_play.get_improvement_areas() if self_play.is_authorized() else []
    }


def _check_principles_intact() -> bool:
    """Check if immutable principles are intact"""
    try:
        ImmutablePrinciples.validate_all_enabled()
        return True
    except AssertionError:
        return False
