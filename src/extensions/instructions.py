"""
Instruction Extension

Loads persistent instructions from .aureus/instructions.md

Instructions are injected into every AUREUS session but cost-limited by SPK.
Similar to Claude Code's CLAUDE.md file.
"""

from pathlib import Path
from typing import Optional
from src.extensions.base import Extension, ExtensionResult, ExtensionBudgetExceeded


class InstructionExtension(Extension):
    """
    Persistent instructions extension.
    
    Loads instructions from .aureus/instructions.md and injects them
    into agent context. Instructions count toward extension budget.
    
    Similar to Claude Code's CLAUDE.md file.
    """
    
    def __init__(
        self,
        policy,
        instructions_path: Optional[Path] = None,
        max_cost: float = 100.0
    ):
        """
        Initialize instruction extension.
        
        Args:
            policy: Governance policy
            instructions_path: Path to instructions file (default: .aureus/instructions.md)
            max_cost: Maximum cost budget for instructions
        """
        super().__init__(
            name="instructions",
            policy=policy,
            max_cost=max_cost,
            required_permissions=["file_read", "extensions"]
        )
        
        # Default to .aureus/instructions.md if not specified
        if instructions_path is None:
            instructions_path = policy.project_root / ".aureus" / "instructions.md"
        
        self.instructions_path = Path(instructions_path)
        self._cached_instructions: Optional[str] = None
    
    def execute(self, **kwargs) -> ExtensionResult:
        """
        Load and return instructions.
        
        Returns:
            ExtensionResult with instructions as output
        
        Raises:
            ExtensionBudgetExceeded: If instructions exceed budget
        """
        try:
            # Track cost before loading
            cost_before = self.cost_used
            
            instructions = self.load_instructions()
            
            # Calculate actual cost used by this operation
            cost_used = self.cost_used - cost_before
            
            # Get file info for metadata
            file_size = self.instructions_path.stat().st_size if self.instructions_path.exists() else 0
            
            return self._success(
                output=instructions,
                cost_used=cost_used,
                metadata={
                    "file_path": str(self.instructions_path),
                    "file_size": file_size,
                    "cached": cost_used == 0.0  # Cached if no cost
                }
            )
        
        except FileNotFoundError:
            return self._error(
                f"Instructions file not found: {self.instructions_path}",
                metadata={"file_path": str(self.instructions_path)}
            )
        
        except ExtensionBudgetExceeded as e:
            return self._error(
                str(e),
                metadata={"file_path": str(self.instructions_path)}
            )
    
    def load_instructions(self) -> str:
        """
        Load instructions from file with cost tracking.
        
        Instructions are cached after first load to avoid repeated cost.
        
        Returns:
            Instructions content as string
        
        Raises:
            ExtensionBudgetExceeded: If instructions exceed budget
            FileNotFoundError: If file doesn't exist
        """
        # Return cached if available
        if self._cached_instructions is not None:
            return self._cached_instructions
        
        # Check file exists
        if not self.instructions_path.exists():
            raise FileNotFoundError(f"Instructions file not found: {self.instructions_path}")
        
        # Read content
        content = self.instructions_path.read_text(encoding="utf-8")
        
        # Calculate cost (simple: 0.01 per character)
        cost = len(content) * 0.01
        
        # Check budget
        if not self.check_budget(cost):
            raise ExtensionBudgetExceeded(
                f"Instructions file too large: {cost:.1f} > {self.get_budget_remaining():.1f} "
                f"(budget: {self.max_cost:.1f}, used: {self.cost_used:.1f})"
            )
        
        # Track cost
        self.cost_used += cost
        
        # Cache for future use
        self._cached_instructions = content
        
        return content
    
    def get_instructions(self) -> Optional[str]:
        """
        Get cached instructions without loading from file.
        
        Returns:
            Cached instructions or None if not loaded yet
        """
        return self._cached_instructions
    
    def clear_cache(self):
        """Clear cached instructions (forces reload on next access)"""
        self._cached_instructions = None
    
    def reload_instructions(self) -> str:
        """
        Reload instructions from file (bypasses cache).
        
        Note: This will count toward budget again!
        
        Returns:
            Fresh instructions content
        
        Raises:
            ExtensionBudgetExceeded: If reload would exceed budget
        """
        self.clear_cache()
        return self.load_instructions()
