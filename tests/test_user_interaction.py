"""
Test Suite for User Interaction System

Tests approval checkpoints and interactive mode.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch
from io import StringIO

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.harness.user_interaction import UserInteraction, ApprovalResult, UserChoice


class TestUserInteraction:
    """Test user interaction and approval system"""
    
    def test_auto_approve_in_non_interactive_mode(self):
        """Test auto-approval when not interactive"""
        ui = UserInteraction(interactive=False)
        
        result = ui.request_approval(
            phase="gather",
            content={"spec": "test"}
        )
        
        assert result.approved is True
        assert result.choice == UserChoice.APPROVE
        assert result.reason == "auto-approved (non-interactive mode)"
    
    @patch('builtins.input', return_value='yes')
    def test_user_approves_in_interactive_mode(self, mock_input):
        """Test user approval in interactive mode"""
        ui = UserInteraction(interactive=True)
        
        result = ui.request_approval(
            phase="gather",
            content={"spec": "test"}
        )
        
        assert result.approved is True
        assert result.choice == UserChoice.APPROVE
    
    @patch('builtins.input', return_value='no')
    def test_user_rejects_in_interactive_mode(self, mock_input):
        """Test user rejection in interactive mode"""
        ui = UserInteraction(interactive=True)
        
        result = ui.request_approval(
            phase="gather",
            content={"spec": "test"}
        )
        
        assert result.approved is False
        assert result.choice == UserChoice.REJECT
    
    @patch('builtins.input', side_effect=['edit', 'new_value', 'yes'])
    def test_user_edits_then_approves(self, mock_input):
        """Test user editing content then approving"""
        ui = UserInteraction(interactive=True)
        
        result = ui.request_approval(
            phase="gather",
            content={"spec": "test"}
        )
        
        assert result.approved is True
        assert result.choice == UserChoice.APPROVE
        assert result.modified_content is not None
    
    @patch('builtins.input', return_value='invalid')
    def test_invalid_input_prompts_again(self, mock_input):
        """Test invalid input handling"""
        ui = UserInteraction(interactive=True)
        
        # Mock will return 'invalid' repeatedly, should eventually timeout or fail
        # For now, we'll accept that it prompts multiple times
        with pytest.raises(Exception):
            ui.request_approval(
                phase="gather",
                content={"spec": "test"},
                max_attempts=2
            )
    
    def test_format_content_for_display(self):
        """Test content formatting for user review"""
        ui = UserInteraction(interactive=False)
        
        content = {
            "specification": "Add function",
            "success_criteria": ["Works"],
            "cost": 50.0
        }
        
        formatted = ui.format_content(content, phase="gather")
        
        assert "gather" in formatted.lower()
        assert "specification" in formatted.lower()
        assert "50.0" in formatted
