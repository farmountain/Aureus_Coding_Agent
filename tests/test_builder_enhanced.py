"""
Test Suite for Enhanced Builder Agent with Memory Integration

Tests plan decomposition, memory integration, and error recovery.
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.builder_enhanced import (
    EnhancedBuilderAgent,
    PlanDecomposer,
    SubTask,
    TaskStatus,
    ErrorRecoveryManager
)
from src.interfaces import Policy, Budget
from src.memory.trajectory import TrajectoryStore, ActionRecord
from src.memory.cost_ledger import CostLedger


@pytest.fixture
def temp_storage(tmp_path):
    """Create temporary storage directory"""
    storage_dir = tmp_path / ".aureus" / "memory"
    storage_dir.mkdir(parents=True, exist_ok=True)
    return storage_dir


@pytest.fixture
def sample_policy(tmp_path):
    """Create sample policy"""
    return Policy(
        version="0.1",
        project_name="TestProject",
        project_root=tmp_path,
        budgets=Budget(
            max_loc=1000,
            max_modules=10,
            max_files=20,
            max_dependencies=5
        ),
        permissions=["file_read", "file_write", "grep_search"]
    )


class TestPlanDecomposer:
    """Test plan decomposition"""
    
    def test_decompose_simple_intent(self, sample_policy):
        """Test decomposing a simple intent"""
        decomposer = PlanDecomposer(policy=sample_policy)
        
        subtasks = decomposer.decompose(
            intent="Add authentication to the API"
        )
        
        assert len(subtasks) > 0
        assert all(isinstance(task, SubTask) for task in subtasks)
        assert all(task.status == TaskStatus.PENDING for task in subtasks)
    
    def test_subtask_structure(self, sample_policy):
        """Test subtask has required fields"""
        decomposer = PlanDecomposer(policy=sample_policy)
        
        subtasks = decomposer.decompose(intent="Build user registration")
        
        for task in subtasks:
            assert task.id is not None
            assert task.description != ""
            assert task.estimated_cost >= 0
            assert task.dependencies is not None
    
    def test_task_dependencies(self, sample_policy):
        """Test tasks have proper dependency ordering"""
        decomposer = PlanDecomposer(policy=sample_policy)
        
        subtasks = decomposer.decompose(
            intent="Create API with database and tests"
        )
        
        # Check that later tasks may depend on earlier ones
        task_ids = {task.id for task in subtasks}
        for task in subtasks:
            for dep_id in task.dependencies:
                assert dep_id in task_ids
    
    def test_estimate_costs(self, sample_policy):
        """Test cost estimation for subtasks"""
        decomposer = PlanDecomposer(policy=sample_policy)
        
        subtasks = decomposer.decompose(intent="Implement feature X")
        
        total_cost = sum(task.estimated_cost for task in subtasks)
        assert total_cost > 0
        assert total_cost < sample_policy.budgets.max_loc


class TestEnhancedBuilderAgent:
    """Test enhanced builder agent"""
    
    def test_agent_initialization(self, sample_policy, temp_storage):
        """Test creating enhanced agent with memory"""
        agent = EnhancedBuilderAgent(
            policy=sample_policy,
            storage_dir=temp_storage
        )
        
        assert agent.policy == sample_policy
        assert agent.trajectory_store is not None
        assert agent.cost_ledger is not None
    
    def test_build_with_plan_decomposition(self, sample_policy, temp_storage):
        """Test build decomposes plan into subtasks"""
        agent = EnhancedBuilderAgent(
            policy=sample_policy,
            storage_dir=temp_storage
        )
        
        result = agent.build(intent="Add user login")
        
        # Check decomposition happened
        assert "subtasks" in result.metadata
        assert len(result.metadata["subtasks"]) > 0
    
    def test_build_tracks_trajectory(self, sample_policy, temp_storage):
        """Test build records trajectory"""
        agent = EnhancedBuilderAgent(
            policy=sample_policy,
            storage_dir=temp_storage
        )
        
        result = agent.build(intent="Test feature")
        
        # Check trajectory was created
        assert agent.current_session_id is not None
        
        # Verify trajectory stored
        session = agent.trajectory_store.get_session(agent.current_session_id)
        assert session is not None
        assert session.intent == "Test feature"
        assert len(session.actions) > 0
    
    def test_build_tracks_costs(self, sample_policy, temp_storage):
        """Test build records costs to ledger"""
        agent = EnhancedBuilderAgent(
            policy=sample_policy,
            storage_dir=temp_storage
        )
        
        result = agent.build(intent="Simple task")
        
        # Check costs were recorded
        session_costs = agent.cost_ledger.get_session_costs(agent.current_session_id)
        assert session_costs > 0
    
    def test_build_learns_from_history(self, sample_policy, temp_storage):
        """Test agent uses past sessions for context"""
        agent = EnhancedBuilderAgent(
            policy=sample_policy,
            storage_dir=temp_storage
        )
        
        # First build
        result1 = agent.build(intent="Add login feature")
        
        # Second similar build should reference first
        agent2 = EnhancedBuilderAgent(
            policy=sample_policy,
            storage_dir=temp_storage
        )
        result2 = agent2.build(intent="Add authentication")
        
        # Check that similar sessions were found
        assert "similar_sessions" in result2.metadata
    
    def test_subtask_execution(self, sample_policy, temp_storage):
        """Test subtask execution tracking"""
        agent = EnhancedBuilderAgent(
            policy=sample_policy,
            storage_dir=temp_storage
        )
        
        result = agent.build(intent="Multi-step feature")
        
        # Check subtask statuses were updated
        subtasks = result.metadata.get("subtasks", [])
        completed = [t for t in subtasks if t["status"] == "completed"]
        assert len(completed) > 0


class TestErrorRecoveryManager:
    """Test error recovery mechanisms"""
    
    def test_record_error(self):
        """Test recording an error"""
        recovery = ErrorRecoveryManager(max_retries=3)
        
        recovery.record_error(
            operation="file_write",
            error="Permission denied",
            context={"file": "test.py"}
        )
        
        assert recovery.get_error_count("file_write") == 1
    
    def test_should_retry(self):
        """Test retry decision"""
        recovery = ErrorRecoveryManager(max_retries=3)
        
        # First attempt
        assert recovery.should_retry("test_op")
        
        # Record errors
        for i in range(3):
            recovery.record_error("test_op", "error")
        
        # Should not retry after max attempts
        assert not recovery.should_retry("test_op")
    
    def test_suggest_recovery(self):
        """Test recovery suggestion"""
        recovery = ErrorRecoveryManager(max_retries=3)
        
        recovery.record_error(
            operation="file_write",
            error="Permission denied",
            context={}
        )
        
        suggestion = recovery.suggest_recovery("file_write")
        assert suggestion is not None
        assert "suggestion" in suggestion
    
    def test_reset_errors(self):
        """Test error counter reset"""
        recovery = ErrorRecoveryManager(max_retries=3)
        
        recovery.record_error("test_op", "error")
        assert recovery.get_error_count("test_op") == 1
        
        recovery.reset_errors("test_op")
        assert recovery.get_error_count("test_op") == 0
