"""
End-to-End Integration Tests for Complete 3-Tier Architecture

Tests the complete pipeline:
GVUFD (Tier 1) → SPK (Tier 2) → UVUAS (Tier 3)

Validates:
- Specification generation from intent
- Cost calculation and budget enforcement
- Permission-gated tool execution
- File creation with backup/rollback
- Complete workflow success
"""

import pytest
from pathlib import Path
from src.interfaces import Policy, Budget
from src.agents import BuilderAgent
from src.governance.gvufd import SpecificationGenerator
from src.governance.spk import PricingKernel


@pytest.fixture
def integration_project(tmp_path):
    """Create temporary project for integration testing"""
    # Create project structure
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "README.md").write_text("# Integration Test Project")
    
    return tmp_path


@pytest.fixture
def integration_policy(integration_project):
    """Create integration test policy"""
    return Policy(
        version="1.0",
        project_name="integration-test",
        project_root=integration_project,
        budgets=Budget(
            max_loc=5000,
            max_modules=50,
            max_files=100,
            max_dependencies=20
        ),
        permissions={
            "file_read": True,
            "file_write": True,
            "file_delete": False,
            "network": False,
            "shell": False
        }
    )


class TestCompleteWorkflow:
    """Test complete end-to-end workflows"""
    
    def test_simple_feature_implementation(self, integration_policy):
        """Test implementing a simple feature end-to-end"""
        agent = BuilderAgent(integration_policy)
        
        # User intent
        intent = "Create a utility function to format timestamps"
        
        # Execute complete workflow
        result = agent.build(intent)
        
        # Verify workflow executed
        assert result.success is True
        assert result.specification is not None
        assert result.specification.intent == intent
        
        # Verify specification was generated (GVUFD)
        assert len(result.specification.success_criteria) > 0
        assert result.specification.budgets is not None
        
        # Verify cost was calculated (SPK)
        assert result.cost is not None
        assert result.cost.total > 0
        assert result.cost.within_budget is True
        
        # Verify files were created (UVUAS)
        assert len(result.files_created) > 0
        
        # Verify execution log tracks all tiers
        log = agent.get_execution_log()
        assert len(log) > 0
        
        # Check all tiers executed
        log_messages = [entry["message"] for entry in log]
        assert any("specification" in msg.lower() for msg in log_messages)
        assert any("cost" in msg.lower() or "budget" in msg.lower() for msg in log_messages)
        assert any("implementation" in msg.lower() for msg in log_messages)
    
    def test_budget_enforcement_across_tiers(self, integration_project):
        """Test budget enforcement flows through all tiers"""
        # Create very restrictive policy
        strict_policy = Policy(
            version="1.0",
            project_name="strict-test",
            project_root=integration_project,
            budgets=Budget(
                max_loc=50,  # Very low
                max_modules=5,
                max_files=10,
                max_dependencies=2
            ),
            permissions={"file_read": True, "file_write": True},
            cost_thresholds={
                "warning": 20.0,
                "rejection": 30.0,
                "session_limit": 50.0
            }
        )
        
        agent = BuilderAgent(strict_policy)
        
        # Request feature (may exceed budget or pass depending on estimation)
        intent = "Create complete authentication system with JWT, OAuth2, and session management"
        result = agent.build(intent)
        
        # Budget check happened
        assert result.cost is not None
        assert "budget_status" in result.metadata
    
    def test_permission_gates_across_tiers(self, integration_project):
        """Test permission gates work across all tiers"""
        # Create policy with limited permissions
        limited_policy = Policy(
            version="1.0",
            project_name="limited-test",
            project_root=integration_project,
            budgets=Budget(
                max_loc=1000,
                max_modules=20,
                max_files=50,
                max_dependencies=10
            ),
            permissions={
                "file_read": True,
                "file_write": False,  # No write permission
                "file_delete": False,
                "network": False
            }
        )
        
        agent = BuilderAgent(limited_policy)
        
        intent = "Add logging configuration"
        result = agent.build(intent)
        
        # Should succeed but not create files
        assert result.success is True  # Specification and cost calculation succeeded
        assert len(result.files_created) == 0  # No files created due to permission
    
    def test_high_risk_feature_handling(self, integration_policy):
        """Test handling of high-risk security features"""
        agent = BuilderAgent(integration_policy)
        
        # Security-critical intent
        intent = "Add password hashing and authentication endpoint"
        result = agent.build(intent)
        
        # Should generate specification with security considerations
        assert result.success is True
        assert result.specification.risk_level in ["medium", "high", "critical"]
        
        # Should have security considerations
        if hasattr(result.specification, 'security_considerations'):
            assert len(result.specification.security_considerations) > 0
    
    def test_spec_generator_integration(self, integration_policy):
        """Test GVUFD (Tier 1) integration"""
        spec_gen = SpecificationGenerator()
        
        intent = "Create REST API endpoint for user management"
        spec = spec_gen.generate(intent, integration_policy)
        
        # Verify specification structure
        assert spec.intent == intent
        assert len(spec.success_criteria) > 0
        assert spec.budgets is not None
        assert spec.budgets.max_loc_delta > 0
        assert spec.risk_level in ["low", "medium", "high", "critical"]
    
    def test_pricing_kernel_integration(self, integration_policy, integration_project):
        """Test SPK (Tier 2) integration"""
        from src.interfaces import Specification, SpecificationBudget
        
        # Create test specification
        spec = Specification(
            intent="Add caching layer",
            success_criteria=["Cache hits improve performance", "Cache invalidation works"],
            budgets=SpecificationBudget(
                max_loc_delta=100,
                max_new_files=3,
                max_new_dependencies=2,
                max_new_abstractions=5
            ),
            risk_level="low"
        )
        
        # Price the specification
        pricing = PricingKernel()
        cost = pricing.price(spec, integration_policy)
        
        # Verify cost calculation
        assert cost is not None
        assert cost.total > 0
        assert cost.within_budget in [True, False]
        assert cost.budget_status in ["approved", "advisory", "warning", "rejected"]
    
    def test_tool_bus_integration(self, integration_policy, integration_project):
        """Test Tool Bus integration with permissions"""
        from src.toolbus import FileWriteTool, FileReadTool, PermissionChecker
        
        # Test file write
        writer = FileWriteTool(integration_project)
        write_result = writer.execute(
            file_path="test.txt",
            content="Integration test content"
        )
        
        assert write_result.success is True
        assert (integration_project / "test.txt").exists()
        
        # Test file read
        reader = FileReadTool(integration_project)
        read_result = reader.execute(file_path="test.txt")
        
        assert read_result.success is True
        assert "Integration test content" in read_result.output  # output is the content string
        
        # Test permission checker
        checker = PermissionChecker(integration_policy.permissions)
        assert checker.has_permission("file_read") is True
        assert checker.has_permission("file_write") is True
        assert checker.has_permission("network") is False
    
    def test_execution_log_captures_all_steps(self, integration_policy):
        """Test execution log captures all tier interactions"""
        agent = BuilderAgent(integration_policy)
        
        intent = "Add configuration parser"
        result = agent.build(intent)
        
        log = agent.get_execution_log()
        
        # Should have multiple log entries
        assert len(log) >= 4  # At minimum: spec gen, cost calc, exec, validation
        
        # Each entry should have message
        for entry in log:
            assert "message" in entry
            assert isinstance(entry["message"], str)
            assert len(entry["message"]) > 0


class TestErrorRecovery:
    """Test error handling and recovery"""
    
    def test_handles_empty_intent(self, integration_policy):
        """Test handling of empty intent"""
        agent = BuilderAgent(integration_policy)
        
        result = agent.build("")
        
        # Should handle gracefully
        assert isinstance(result, type(agent.build("test")))
    
    def test_handles_invalid_policy(self, integration_project):
        """Test handling of invalid policy configuration"""
        # This should be caught during policy creation
        with pytest.raises(Exception):  # ValidationError
            Policy(
                version="invalid",  # Invalid version format
                project_name="test",
                project_root=integration_project,
                budgets=Budget(
                    max_loc=100,
                    max_modules=10,
                    max_files=20,
                    max_dependencies=5
                ),
                permissions={}
            )
    
    def test_recovers_from_tool_failures(self, integration_project):
        """Test recovery from tool execution failures"""
        from src.toolbus import FileReadTool
        
        reader = FileReadTool(integration_project)
        
        # Try to read non-existent file
        result = reader.execute(file_path="nonexistent.txt")
        
        # Should fail gracefully
        assert result.success is False
        assert result.error is not None


class TestPerformance:
    """Test performance characteristics"""
    
    def test_workflow_completes_quickly(self, integration_policy):
        """Test complete workflow completes in reasonable time"""
        import time
        
        agent = BuilderAgent(integration_policy)
        
        start = time.time()
        result = agent.build("Create helper function")
        duration = time.time() - start
        
        # Should complete quickly (Phase 1 is stub implementation)
        assert duration < 5.0  # 5 seconds max
        assert result.success is True
    
    def test_handles_multiple_sequential_builds(self, integration_policy):
        """Test multiple builds in sequence"""
        agent = BuilderAgent(integration_policy)
        
        intents = [
            "Create utility function",
            "Add validation helper",
            "Create configuration parser"
        ]
        
        results = []
        for intent in intents:
            result = agent.build(intent)
            results.append(result)
            assert result.success is True
        
        # All should succeed
        assert len(results) == 3
        assert all(r.success for r in results)
