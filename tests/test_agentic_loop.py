"""
Test Suite for Agentic Loop

Tests the explicit Gather/Act/Verify loop with Tier 1/2 gates.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.interfaces import Policy, Budget, Specification
from src.harness.agentic_loop import AgenticLoop, LoopPhase, LoopResult


@pytest.fixture
def test_policy(tmp_path):
    """Create test policy"""
    return Policy(
        version="1.0",
        project_name="test-loop",
        project_root=tmp_path,
        budgets=Budget(
            max_loc=4000,
            max_modules=20,
            max_files=50,
            max_dependencies=10
        ),
        permissions={
            "file_read": True,
            "file_write": True,
            "extensions": True
        }
    )


@pytest.fixture
def mock_gvufd():
    """Mock GVUFD generator"""
    from src.interfaces import SpecificationBudget
    
    gvufd = Mock()
    gvufd.generate_spec.return_value = Specification(
        intent="Add hello function",
        success_criteria=["Function returns 'Hello'"],
        budgets=SpecificationBudget(
            max_loc_delta=100,
            max_new_files=2,
            max_new_dependencies=1,
            max_new_abstractions=2
        ),
        risk_level="low",
        acceptance_tests=["test_hello_returns_hello"]
    )
    return gvufd


@pytest.fixture
def mock_spk():
    """Mock SPK pricing kernel"""
    spk = Mock()
    spk.price_changes.return_value = Mock(
        within_budget=True,
        total_cost=50.0,
        breakdown={"loc": 30.0, "complexity": 20.0}
    )
    return spk


class TestAgenticLoop:
    """Test AgenticLoop orchestration"""
    
    def test_loop_initialization(self, test_policy, mock_gvufd, mock_spk):
        """Test creating agentic loop"""
        loop = AgenticLoop(
            policy=test_policy,
            gvufd=mock_gvufd,
            spk=mock_spk,
            interactive_mode=False
        )
        
        assert loop.policy == test_policy
        assert loop.gvufd == mock_gvufd
        assert loop.spk == mock_spk
        assert loop.interactive_mode is False
        assert loop.current_phase is None
    
    def test_gather_phase(self, test_policy, mock_gvufd, mock_spk):
        """Test gather context phase"""
        loop = AgenticLoop(
            policy=test_policy,
            gvufd=mock_gvufd,
            spk=mock_spk
        )
        
        result = loop.gather_context("Add hello function")
        
        assert result.success is True
        assert result.phase == LoopPhase.GATHER
        assert result.specification is not None
        assert loop.current_phase == LoopPhase.GATHER
        
        # GVUFD should have been called
        mock_gvufd.generate_spec.assert_called_once()
    
    def test_act_phase_requires_gather(self, test_policy, mock_gvufd, mock_spk):
        """Test act phase requires gather first"""
        loop = AgenticLoop(
            policy=test_policy,
            gvufd=mock_gvufd,
            spk=mock_spk
        )
        
        # Try to act without gathering
        result = loop.act_on_plan()
        
        assert result.success is False
        assert "must gather context first" in result.error.lower()
    
    def test_act_phase_with_budget_check(self, test_policy, mock_gvufd, mock_spk):
        """Test act phase enforces SPK budget"""
        loop = AgenticLoop(
            policy=test_policy,
            gvufd=mock_gvufd,
            spk=mock_spk
        )
        
        # Gather first
        loop.gather_context("Add hello function")
        
        # Act
        result = loop.act_on_plan()
        
        assert result.success is True
        assert result.phase == LoopPhase.ACT
        assert loop.current_phase == LoopPhase.ACT
        
        # SPK should have been called
        mock_spk.price_changes.assert_called()
    
    def test_act_phase_fails_when_over_budget(self, test_policy, mock_gvufd, mock_spk):
        """Test act phase rejects over-budget changes"""
        # Make SPK reject changes
        mock_spk.price_changes.return_value = Mock(
            within_budget=False,
            total_cost=5000.0,
            breakdown={"loc": 5000.0}
        )
        
        loop = AgenticLoop(
            policy=test_policy,
            gvufd=mock_gvufd,
            spk=mock_spk
        )
        
        # Gather and try to act
        loop.gather_context("Add massive feature")
        result = loop.act_on_plan()
        
        assert result.success is False
        assert "budget" in result.error.lower()
    
    def test_verify_phase(self, test_policy, mock_gvufd, mock_spk):
        """Test verify phase"""
        loop = AgenticLoop(
            policy=test_policy,
            gvufd=mock_gvufd,
            spk=mock_spk
        )
        
        # Gather and act first
        loop.gather_context("Add hello function")
        loop.act_on_plan()
        
        # Verify
        result = loop.verify_changes()
        
        assert result.success is True
        assert result.phase == LoopPhase.VERIFY
        assert loop.current_phase == LoopPhase.VERIFY
    
    def test_full_loop_execution(self, test_policy, mock_gvufd, mock_spk):
        """Test complete loop: gather → act → verify"""
        loop = AgenticLoop(
            policy=test_policy,
            gvufd=mock_gvufd,
            spk=mock_spk
        )
        
        # Execute full loop
        intent = "Add hello function"
        
        # Gather
        gather_result = loop.gather_context(intent)
        assert gather_result.success is True
        
        # Act
        act_result = loop.act_on_plan()
        assert act_result.success is True
        
        # Verify
        verify_result = loop.verify_changes()
        assert verify_result.success is True
        
        # Loop should be complete
        assert loop.is_complete()
    
    def test_loop_reset(self, test_policy, mock_gvufd, mock_spk):
        """Test resetting loop state"""
        loop = AgenticLoop(
            policy=test_policy,
            gvufd=mock_gvufd,
            spk=mock_spk
        )
        
        # Execute partial loop
        loop.gather_context("Add hello function")
        assert loop.current_phase == LoopPhase.GATHER
        
        # Reset
        loop.reset()
        
        assert loop.current_phase is None
        assert not loop.is_complete()
    
    def test_interactive_mode_flag(self, test_policy, mock_gvufd, mock_spk):
        """Test interactive mode is respected"""
        loop_interactive = AgenticLoop(
            policy=test_policy,
            gvufd=mock_gvufd,
            spk=mock_spk,
            interactive_mode=True
        )
        
        loop_non_interactive = AgenticLoop(
            policy=test_policy,
            gvufd=mock_gvufd,
            spk=mock_spk,
            interactive_mode=False
        )
        
        assert loop_interactive.interactive_mode is True
        assert loop_non_interactive.interactive_mode is False
