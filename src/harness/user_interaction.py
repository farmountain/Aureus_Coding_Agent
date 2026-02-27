"""
User Interaction System

Handles user approval checkpoints in interactive mode.
"""

from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass
import json


class UserChoice(Enum):
    """User approval choices"""
    APPROVE = "approve"
    REJECT = "reject"
    EDIT = "edit"
    SKIP = "skip"


@dataclass
class ApprovalResult:
    """Result from user approval request"""
    approved: bool
    choice: UserChoice
    reason: str = ""
    modified_content: Optional[Dict[str, Any]] = None


class UserInteraction:
    """
    User interaction and approval system.
    
    In interactive mode:
    - Displays content for user review
    - Prompts for approval/rejection/edit
    - Allows content modification
    
    In non-interactive mode:
    - Auto-approves all requests
    - No user prompts
    """
    
    def __init__(self, interactive: bool = False):
        """
        Initialize user interaction system.
        
        Args:
            interactive: Enable interactive approval checkpoints
        """
        self.interactive = interactive
    
    def request_approval(
        self,
        phase: str,
        content: Dict[str, Any],
        max_attempts: int = 3
    ) -> ApprovalResult:
        """
        Request user approval for content.
        
        Args:
            phase: Which loop phase (gather/act/verify)
            content: Content to review
            max_attempts: Maximum input attempts for invalid responses
        
        Returns:
            ApprovalResult with user's decision
        """
        # Non-interactive mode: auto-approve
        if not self.interactive:
            return ApprovalResult(
                approved=True,
                choice=UserChoice.APPROVE,
                reason="auto-approved (non-interactive mode)"
            )
        
        # Interactive mode: prompt user
        print(f"\n{'=' * 60}")
        print(f"APPROVAL REQUIRED: {phase.upper()} Phase")
        print(f"{'=' * 60}")
        print(self.format_content(content, phase))
        print(f"{'=' * 60}")
        
        attempts = 0
        while attempts < max_attempts:
            response = input("\nApprove this phase? [yes/no/edit/skip]: ").strip().lower()
            
            if response in ['yes', 'y', 'approve']:
                return ApprovalResult(
                    approved=True,
                    choice=UserChoice.APPROVE,
                    reason="user approved"
                )
            
            elif response in ['no', 'n', 'reject']:
                reason = input("Reason for rejection (optional): ").strip()
                return ApprovalResult(
                    approved=False,
                    choice=UserChoice.REJECT,
                    reason=reason or "user rejected"
                )
            
            elif response == 'edit':
                # Allow user to modify content
                modified = self._interactive_edit(content, phase)
                
                # After edit, ask again
                print("\nContent has been modified. Review changes...")
                print(self.format_content(modified, phase))
                
                confirm = input("\nApprove modified content? [yes/no]: ").strip().lower()
                if confirm in ['yes', 'y']:
                    return ApprovalResult(
                        approved=True,
                        choice=UserChoice.APPROVE,
                        reason="user approved after edit",
                        modified_content=modified
                    )
                else:
                    return ApprovalResult(
                        approved=False,
                        choice=UserChoice.REJECT,
                        reason="user rejected after edit"
                    )
            
            elif response == 'skip':
                return ApprovalResult(
                    approved=True,
                    choice=UserChoice.SKIP,
                    reason="user skipped review"
                )
            
            else:
                attempts += 1
                print(f"Invalid input. Please enter yes/no/edit/skip. ({attempts}/{max_attempts})")
        
        # Max attempts exceeded
        raise Exception(f"Max approval attempts ({max_attempts}) exceeded")
    
    def format_content(self, content: Dict[str, Any], phase: str) -> str:
        """
        Format content for user display.
        
        Args:
            content: Content to format
            phase: Phase name for context
        
        Returns:
            Formatted string for display
        """
        lines = []
        lines.append(f"\nPhase: {phase}")
        lines.append("")
        
        for key, value in content.items():
            if isinstance(value, (list, dict)):
                lines.append(f"{key}:")
                lines.append(json.dumps(value, indent=2))
            else:
                lines.append(f"{key}: {value}")
        
        return "\n".join(lines)
    
    def _interactive_edit(self, content: Dict[str, Any], phase: str) -> Dict[str, Any]:
        """
        Allow user to interactively edit content.
        
        This is a simple implementation that prints current content
        and allows key-by-key modification.
        
        Args:
            content: Original content
            phase: Phase name
        
        Returns:
            Modified content
        """
        print(f"\nInteractive Edit Mode: {phase}")
        print("Enter new values for fields (press Enter to keep current value)\n")
        
        modified = content.copy()
        
        for key, value in content.items():
            # Skip complex nested structures for now
            if isinstance(value, (dict, list)):
                continue
            
            current = str(value)
            new_value = input(f"{key} (current: {current}): ").strip()
            
            if new_value:
                # Try to preserve type
                if isinstance(value, (int, float)):
                    try:
                        modified[key] = type(value)(new_value)
                    except ValueError:
                        modified[key] = new_value
                else:
                    modified[key] = new_value
        
        return modified
    
    def display_message(self, message: str, level: str = "info"):
        """
        Display message to user.
        
        Args:
            message: Message to display
            level: Message level (info/warning/error)
        """
        if self.interactive:
            prefix = {
                "info": "ℹ",
                "warning": "⚠",
                "error": "✗"
            }.get(level, "•")
            
            print(f"{prefix} {message}")
    
    def display_progress(self, phase: str, status: str):
        """
        Display progress update.
        
        Args:
            phase: Current phase
            status: Status message
        """
        if self.interactive:
            print(f"[{phase.upper()}] {status}")
