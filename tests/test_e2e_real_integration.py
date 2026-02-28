"""
REAL End-to-End Integration Test
Tests complete GVUFD → SPK → UVUAS pipeline with actual file creation
"""
import pytest
from pathlib import Path
import tempfile
import shutil
from src.governance.policy import PolicyLoader
from src.agents.builder import BuilderAgent
from src.model_provider import MockProvider


class TestRealE2EIntegration:
    """Test the complete pipeline actually works"""
    
    def setup_method(self):
        """Setup test workspace"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.workspace = self.test_dir / "workspace"
        self.workspace.mkdir()
        
    def teardown_method(self):
        """Cleanup"""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    def test_complete_pipeline_creates_file(self):
        """Test: User intent → File in workspace"""
        # Load policy
        policy_path = Path(".aureus/policy.yaml")
        loader = PolicyLoader()
        policy = loader.load(policy_path)
        
        # Create agent with MockProvider
        provider = MockProvider()
        agent = BuilderAgent(policy=policy, model_provider=provider)
        
        # Execute
        result = agent.build("create a simple add function")
        
        # VERIFY: Must succeed
        assert result.success is True, f"Build failed: {result.error}"
        
        # VERIFY: Must create files
        assert len(result.files_created) > 0, "No files created"
        
        # VERIFY: Files must exist
        for filepath in result.files_created:
            p = Path(filepath)
            assert p.exists(), f"File not found: {filepath}"
            assert p.stat().st_size > 0, f"File is empty: {filepath}"
        
        # VERIFY: Must be in workspace directory
        for filepath in result.files_created:
            assert "workspace" in filepath, f"File not in workspace: {filepath}"
    
    def test_gvufd_spk_integration(self):
        """Test: GVUFD spec → SPK cost (schema compatibility)"""
        policy_path = Path(".aureus/policy.yaml")
        loader = PolicyLoader()
        policy = loader.load(policy_path)
        
        provider = MockProvider()
        agent = BuilderAgent(policy=policy, model_provider=provider)
        
        result = agent.build("create hello world")
        
        # VERIFY: Specification has all required fields
        assert hasattr(result.specification, 'intent')
        assert hasattr(result.specification, 'success_criteria')
        assert hasattr(result.specification, 'budgets')
        assert hasattr(result.specification, 'risk_level')  # NOT 'risk'!
        
        # VERIFY: Cost object properly created from specification
        assert result.cost is not None
        assert result.cost.within_budget in [True, False]
        assert result.cost.budget_status in ['approved', 'advisory', 'warning', 'rejected']
    
    def test_spk_uvuas_integration(self):
        """Test: SPK cost → UVUAS implementation (budget enforcement)"""
        policy_path = Path(".aureus/policy.yaml")
        loader = PolicyLoader()
        policy = loader.load(policy_path)
        
        provider = MockProvider()
        agent = BuilderAgent(policy=policy, model_provider=provider)
        
        # Test normal case
        result = agent.build("simple function")
        assert result.cost.within_budget is True
        assert len(result.files_created) > 0
    
    def test_model_provider_format_compatibility(self):
        """Test: Model provider response → Parser (format matching)"""
        policy_path = Path(".aureus/policy.yaml")
        loader = PolicyLoader()
        policy = loader.load(policy_path)
        
        # Test MockProvider format
        mock_provider = MockProvider()
        response = mock_provider.complete("test prompt")
        
        # VERIFY: Response has Python code block
        assert "```python" in response.content, "MockProvider must return code blocks"
        assert "```" in response.content
        
        # VERIFY: Response has FILE: directive or can be parsed
        content = response.content
        assert "FILE:" in content or "def " in content or "class " in content
    
    def test_permission_system_integration(self):
        """Test: Policy permissions → Builder enforcement"""
        policy_path = Path(".aureus/policy.yaml")
        loader = PolicyLoader()
        policy = loader.load(policy_path)
        
        provider = MockProvider()
        agent = BuilderAgent(policy=policy, model_provider=provider)
        
        # VERIFY: Agent has permission checker
        assert agent.permission_checker is not None
        
        # VERIFY: file_write permission is enabled
        has_write = agent.permission_checker.has_permission("file_write")
        assert has_write is True, "file_write permission must be enabled for tests"
    
    def test_error_handling_integration(self):
        """Test: Component errors → Graceful handling"""
        policy_path = Path(".aureus/policy.yaml")
        loader = PolicyLoader()
        policy = loader.load(policy_path)
        
        # Create provider that returns bad format
        bad_provider = MockProvider(responses={"default": "Invalid response without code"})
        agent = BuilderAgent(policy=policy, model_provider=bad_provider)
        
        result = agent.build("test")
        
        # VERIFY: Should not crash, should return result with no files
        assert result is not None
        assert isinstance(result.files_created, list)


class TestSchemaValidation:
    """Validate that component interfaces match"""
    
    def test_specification_to_cost_schema(self):
        """Verify Specification fields match what SPK expects"""
        from src.interfaces import Specification, SpecificationBudget
        from src.governance.spk import PricingKernel
        from src.governance.policy import PolicyLoader
        
        # Create minimal valid spec
        spec = Specification(
            intent="test",
            success_criteria=["test"],
            budgets=SpecificationBudget(
                max_loc_delta=100,
                max_new_files=5,
                max_new_dependencies=2,
                max_new_abstractions=3
            ),
            risk_level="low"
        )
        
        # Load policy
        policy_path = Path(".aureus/policy.yaml")
        loader = PolicyLoader()
        policy = loader.load(policy_path)
        
        # VERIFY: SPK can price the specification without errors
        kernel = PricingKernel()
        cost = kernel.price(spec, policy)
        
        assert cost is not None
        assert hasattr(cost, 'within_budget')
        assert hasattr(cost, 'budget_status')
