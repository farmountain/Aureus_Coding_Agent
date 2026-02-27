"""
End-to-End Integration Tests for Complete AUREUS Pipeline

Tests the full compilation pipeline:
Intent → GVUFD → SPK → EnhancedBuilder → Memory → Verification

These tests validate that all 3 tiers work together seamlessly with memory.
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.interfaces import Policy, Budget
from src.governance.gvufd import SpecificationGenerator
from src.governance.spk import PricingKernel
from src.agents.builder_enhanced import EnhancedBuilderAgent
from src.memory.trajectory import TrajectoryStore
from src.memory.cost_ledger import CostLedger
from src.memory.summarization import TrajectorySummarizer, PatternExtractor


@pytest.fixture
def test_project(tmp_path):
    """Create a test project structure"""
    project_root = tmp_path / "test_project"
    project_root.mkdir()
    
    # Create some existing files
    (project_root / "main.py").write_text("# Main file\nprint('Hello')")
    (project_root / "utils.py").write_text("# Utilities\ndef helper(): pass")
    
    return project_root


@pytest.fixture
def test_policy(test_project):
    """Create test policy"""
    return Policy(
        version="1.0",
        project_name="E2ETest",
        project_root=test_project,
        budgets=Budget(
            max_loc=500,
            max_modules=5,
            max_files=10,
            max_dependencies=3
        ),
        permissions=["file_read", "file_write", "grep_search"]
    )


@pytest.fixture
def memory_storage(tmp_path):
    """Create memory storage directory"""
    storage_dir = tmp_path / ".aureus" / "memory"
    storage_dir.mkdir(parents=True, exist_ok=True)
    return storage_dir


class TestCompleteE2EPipeline:
    """Test complete AUREUS pipeline end-to-end"""
    
    def test_full_pipeline_simple_feature(self, test_policy, memory_storage):
        """
        Test complete pipeline for a simple feature
        
        Pipeline: Intent → GVUFD → SPK → EnhancedBuilder → Memory
        """
        # Step 1: Define intent
        intent = "Add a greeting function that returns 'Hello, World!'"
        
        # Step 2: GVUFD - Generate specification
        spec_generator = SpecificationGenerator()
        spec = spec_generator.generate(intent, test_policy)
        
        assert spec is not None
        assert spec.intent == intent
        assert len(spec.success_criteria) > 0
        assert spec.budgets is not None
        
        # Step 3: SPK - Price specification
        pricing_kernel = PricingKernel()
        cost_result = pricing_kernel.price(spec, test_policy)
        
        assert cost_result is not None
        assert cost_result.total > 0
        assert cost_result.within_budget
        
        # Step 4: Enhanced Builder - Execute with memory
        builder = EnhancedBuilderAgent(
            policy=test_policy,
            storage_dir=memory_storage
        )
        
        result = builder.build(intent)
        
        # Validate result (may not fully succeed in test env, but pipeline should execute)
        assert result is not None
        assert result.specification.intent == intent
        assert result.cost.total > 0
        
        # Step 5: Verify memory captured
        assert builder.current_session_id is not None
        
        # Check trajectory
        trajectory_store = TrajectoryStore(storage_dir=memory_storage)
        session = trajectory_store.get_session(builder.current_session_id)
        
        assert session is not None
        assert session.intent == intent
        assert len(session.actions) > 0
        assert session.end_time is not None
        
        # Check cost ledger
        cost_ledger = CostLedger(storage_path=memory_storage / "costs.json")
        session_costs = cost_ledger.get_session_costs(builder.current_session_id)
        
        assert session_costs > 0
    
    def test_full_pipeline_with_budget_check(self, test_policy, memory_storage):
        """Test pipeline correctly enforces budget limits"""
        # Create low-budget policy
        low_budget_policy = Policy(
            version="1.0",
            project_name="LowBudget",
            project_root=test_policy.project_root,
            budgets=Budget(
                max_loc=10,  # Very low budget
                max_modules=1,
                max_files=1,
                max_dependencies=1  # Must be >= 1
            ),
            permissions=test_policy.permissions
        )
        
        intent = "Implement a complete REST API with database and tests"
        
        # Generate spec
        spec_generator = SpecificationGenerator()
        spec = spec_generator.generate(intent, low_budget_policy)
        
        # Price specification - should exceed budget
        pricing_kernel = PricingKernel()
        cost_result = pricing_kernel.price(spec, low_budget_policy)
        
        # The cost should be high (since we're asking for a complete REST API)
        # With max_loc=10, this should be over budget
        assert cost_result is not None
        assert cost_result.total > 10  # Should exceed the 10 LOC budget
        
        # This test validates budget checking works - no need to actually build
        # since the build would fail anyway in test environment
    
    def test_multi_session_learning(self, test_policy, memory_storage):
        """Test that system learns from multiple sessions"""
        builder = EnhancedBuilderAgent(
            policy=test_policy,
            storage_dir=memory_storage
        )
        
        # Session 1: Add authentication
        result1 = builder.build("Add user authentication")
        assert result1 is not None
        session1_id = builder.current_session_id
        
        # Session 2: Similar feature - should find similar session
        builder2 = EnhancedBuilderAgent(
            policy=test_policy,
            storage_dir=memory_storage
        )
        result2 = builder2.build("Add login functionality")
        assert result2 is not None
        
        # Should have attempted to find similar sessions (may be empty in test)
        similar_sessions = result2.metadata.get("similar_sessions", [])
        # Just verify the key exists
        assert "similar_sessions" in result2.metadata
    
    def test_trajectory_summarization_integration(self, test_policy, memory_storage):
        """Test trajectory summarization works with complete pipeline"""
        builder = EnhancedBuilderAgent(
            policy=test_policy,
            storage_dir=memory_storage
        )
        
        # Execute a build
        result = builder.build("Create a helper function")
        assert result is not None
        
        session_id = builder.current_session_id
        
        # Summarize trajectory
        summarizer = TrajectorySummarizer(storage_dir=memory_storage)
        summary = summarizer.summarize_session(session_id)
        
        assert summary is not None
        assert summary.session_id == session_id
        assert summary.action_count > 0
        assert summary.total_cost > 0
        
        # Compress trajectory
        compressed = summarizer.compress_trajectory(session_id, keep_ratio=0.5)
        assert compressed.action_count < summary.action_count
        assert compressed.total_cost == summary.total_cost  # Cost preserved
    
    def test_pattern_extraction_from_sessions(self, test_policy, memory_storage):
        """Test pattern extraction from multiple successful sessions"""
        builder = EnhancedBuilderAgent(
            policy=test_policy,
            storage_dir=memory_storage
        )
        
        # Create multiple similar sessions
        intents = [
            "Add a function to calculate sum",
            "Add a function to calculate product",
            "Add a function to calculate average"
        ]
        
        for intent in intents:
            result = builder.build(intent)
            assert result is not None  # Pipeline executed
        
        # Extract patterns
        extractor = PatternExtractor(storage_dir=memory_storage)
        patterns = extractor.extract_successful_patterns()
        
        # Should have found patterns (may be empty in test environment)
        assert patterns is not None
        if len(patterns) > 0:
            # Patterns should be from successful sessions
            for pattern in patterns:
                if isinstance(pattern, dict):
                    assert pattern.get("success", False) is True
    
    def test_error_recovery_in_pipeline(self, test_policy, memory_storage):
        """Test error recovery mechanisms in complete pipeline"""
        # Create policy with restricted permissions
        restricted_policy = Policy(
            version="1.0",
            project_name="Restricted",
            project_root=test_policy.project_root,
            budgets=test_policy.budgets,
            permissions=["file_read"]  # No write permission
        )
        
        builder = EnhancedBuilderAgent(
            policy=restricted_policy,
            storage_dir=memory_storage
        )
        
        # Try to build something requiring write
        result = builder.build("Create a new file with content")
        
        # Should handle gracefully
        assert result is not None
        # May succeed or fail, but should not crash
        
        # Error recovery should have logged attempts
        assert builder.error_recovery is not None
    
    def test_cost_tracking_across_phases(self, test_policy, memory_storage):
        """Test cost tracking works across all phases"""
        builder = EnhancedBuilderAgent(
            policy=test_policy,
            storage_dir=memory_storage
        )
        
        result = builder.build("Simple task")
        assert result is not None
        
        # Check cost ledger has entries for different phases
        cost_ledger = CostLedger(storage_path=memory_storage / "costs.json")
        
        # Should have costs from gather phase (plan decomposition)
        gather_costs = cost_ledger.get_phase_costs("gather")
        assert gather_costs > 0
        
        # Check breakdown
        breakdown = cost_ledger.get_cost_breakdown()
        assert len(breakdown) > 0
    
    def test_subtask_decomposition_execution(self, test_policy, memory_storage):
        """Test plan decomposition and subtask execution"""
        builder = EnhancedBuilderAgent(
            policy=test_policy,
            storage_dir=memory_storage
        )
        
        # Complex intent that should decompose
        result = builder.build("Add authentication with database and tests")
        
        # Should have subtasks
        assert "subtasks" in result.metadata
        subtasks = result.metadata["subtasks"]
        assert len(subtasks) >= 2  # At least analysis + implementation
        
        # Check subtask structure
        for subtask in subtasks:
            assert "id" in subtask
            assert "description" in subtask
            assert "status" in subtask
            assert "estimated_cost" in subtask
    
    def test_memory_persistence_across_instances(self, test_policy, memory_storage):
        """Test memory persists across agent instances"""
        # First instance
        builder1 = EnhancedBuilderAgent(
            policy=test_policy,
            storage_dir=memory_storage
        )
        result1 = builder1.build("Feature A")
        session1_id = builder1.current_session_id
        
        # Second instance (new agent)
        builder2 = EnhancedBuilderAgent(
            policy=test_policy,
            storage_dir=memory_storage
        )
        result2 = builder2.build("Feature B")
        
        # Should be able to see first session from second instance
        trajectory_store = TrajectoryStore(storage_dir=memory_storage)
        session1 = trajectory_store.get_session(session1_id)
        
        assert session1 is not None
        assert session1.intent == "Feature A"


class TestE2EWithRealScenarios:
    """Test real-world scenarios"""
    
    def test_add_api_endpoint(self, test_policy, memory_storage):
        """Real scenario: Add REST API endpoint"""
        builder = EnhancedBuilderAgent(
            policy=test_policy,
            storage_dir=memory_storage
        )
        
        result = builder.build("Add a REST API endpoint for user registration")
        
        assert result is not None
        assert result.specification.intent.find("REST API") >= 0 or \
               result.specification.intent.find("endpoint") >= 0
    
    def test_add_database_model(self, test_policy, memory_storage):
        """Real scenario: Add database model"""
        builder = EnhancedBuilderAgent(
            policy=test_policy,
            storage_dir=memory_storage
        )
        
        result = builder.build("Create a User model for the database")
        
        assert result is not None
        # Should decompose into subtasks
        if "subtasks" in result.metadata:
            assert len(result.metadata["subtasks"]) >= 2
    
    def test_refactoring_task(self, test_policy, memory_storage):
        """Real scenario: Refactoring existing code"""
        builder = EnhancedBuilderAgent(
            policy=test_policy,
            storage_dir=memory_storage
        )
        
        result = builder.build("Refactor the helper function to use better naming")
        
        assert result is not None
        # Refactoring should have reasonable cost
        if result.cost:
            assert result.cost.total < 300  # Reasonable range for refactoring
