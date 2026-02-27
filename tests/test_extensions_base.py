"""
Test Suite for Extension Base Classes

Tests the foundation for AUREUS extension system with SPK budget enforcement.
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.interfaces import Policy, Budget
from src.governance.spk import PricingKernel


@pytest.fixture
def test_policy(tmp_path):
    """Create test policy with extension budgets"""
    return Policy(
        version="1.0",
        project_name="test-extensions",
        project_root=tmp_path,
        budgets=Budget(
            max_loc=5000,
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
def pricing_kernel():
    """Create pricing kernel for cost calculations"""
    return PricingKernel()


class TestExtensionBase:
    """Test Extension base class"""
    
    def test_extension_initialization(self, test_policy):
        """Test extension initializes with policy and budget"""
        from src.extensions.base import Extension
        
        class TestExtension(Extension):
            def execute(self, **kwargs):
                return self._success("test")
        
        ext = TestExtension(
            name="test_ext",
            policy=test_policy,
            max_cost=100.0
        )
        
        assert ext.name == "test_ext"
        assert ext.policy == test_policy
        assert ext.max_cost == 100.0
        assert ext.cost_used == 0.0
    
    def test_extension_budget_checking(self, test_policy):
        """Test extension budget enforcement"""
        from src.extensions.base import Extension
        
        class TestExtension(Extension):
            def execute(self, **kwargs):
                return self._success("test")
        
        ext = TestExtension(name="test", policy=test_policy, max_cost=50.0)
        
        # Within budget
        assert ext.check_budget(30.0) is True
        
        # At budget limit
        assert ext.check_budget(50.0) is True
        
        # Over budget
        assert ext.check_budget(51.0) is False
        
        # After using some budget
        ext.cost_used = 40.0
        assert ext.check_budget(10.0) is True
        assert ext.check_budget(11.0) is False
    
    def test_extension_cost_tracking(self, test_policy):
        """Test extension tracks cost usage"""
        from src.extensions.base import Extension
        
        class TestExtension(Extension):
            def execute(self, **kwargs):
                self.cost_used += 25.0
                return self._success("test")
        
        ext = TestExtension(name="test", policy=test_policy, max_cost=100.0)
        
        # Initial cost
        assert ext.cost_used == 0.0
        
        # Execute and track cost
        ext.execute()
        assert ext.cost_used == 25.0
        
        # Execute again
        ext.execute()
        assert ext.cost_used == 50.0
    
    def test_extension_budget_exceeded_error(self, test_policy):
        """Test extension raises error when budget exceeded"""
        from src.extensions.base import Extension, ExtensionBudgetExceeded
        
        class TestExtension(Extension):
            def execute(self, **kwargs):
                cost = kwargs.get("cost", 10.0)
                if not self.check_budget(cost):
                    raise ExtensionBudgetExceeded(
                        f"Extension {self.name} would exceed budget: {cost} > {self.max_cost - self.cost_used}"
                    )
                self.cost_used += cost
                return self._success("test")
        
        ext = TestExtension(name="test", policy=test_policy, max_cost=50.0)
        
        # Should succeed within budget
        result = ext.execute(cost=30.0)
        assert result.success is True
        
        # Should fail when exceeding budget
        with pytest.raises(ExtensionBudgetExceeded):
            ext.execute(cost=30.0)  # Total would be 60.0 > 50.0
    
    def test_extension_result_dataclass(self):
        """Test ExtensionResult dataclass"""
        from src.extensions.base import ExtensionResult
        
        result = ExtensionResult(
            success=True,
            output="test output",
            extension_name="test_ext",
            cost_used=25.0
        )
        
        assert result.success is True
        assert result.output == "test output"
        assert result.extension_name == "test_ext"
        assert result.cost_used == 25.0
        assert result.error is None
        
        # Test serialization
        data = result.to_dict()
        assert isinstance(data, dict)
        assert data["success"] is True
        assert data["output"] == "test output"
    
    def test_extension_error_result(self, test_policy):
        """Test extension error handling"""
        from src.extensions.base import Extension
        
        class TestExtension(Extension):
            def execute(self, **kwargs):
                if kwargs.get("fail"):
                    return self._error("Test error")
                return self._success("test")
        
        ext = TestExtension(name="test", policy=test_policy, max_cost=100.0)
        
        # Success case
        result = ext.execute(fail=False)
        assert result.success is True
        assert result.error is None
        
        # Error case
        result = ext.execute(fail=True)
        assert result.success is False
        assert result.error == "Test error"
    
    def test_extension_metadata_tracking(self, test_policy):
        """Test extension tracks metadata"""
        from src.extensions.base import Extension
        
        class TestExtension(Extension):
            def execute(self, **kwargs):
                return self._success(
                    "test",
                    metadata={"foo": "bar", "count": 42}
                )
        
        ext = TestExtension(name="test", policy=test_policy, max_cost=100.0)
        
        result = ext.execute()
        assert result.metadata["foo"] == "bar"
        assert result.metadata["count"] == 42
    
    def test_extension_requires_policy(self):
        """Test extension requires policy parameter"""
        from src.extensions.base import Extension
        
        class TestExtension(Extension):
            def execute(self, **kwargs):
                return self._success("test")
        
        # Should require policy
        with pytest.raises(TypeError):
            TestExtension(name="test", max_cost=100.0)  # Missing policy


class TestExtensionBudgetExceeded:
    """Test ExtensionBudgetExceeded exception"""
    
    def test_exception_message(self):
        """Test exception has clear message"""
        from src.extensions.base import ExtensionBudgetExceeded
        
        exc = ExtensionBudgetExceeded("Budget exceeded: 150.0 > 100.0")
        
        assert "Budget exceeded" in str(exc)
        assert "150.0" in str(exc)
        assert "100.0" in str(exc)
    
    def test_exception_is_raised(self):
        """Test exception can be raised and caught"""
        from src.extensions.base import ExtensionBudgetExceeded
        
        with pytest.raises(ExtensionBudgetExceeded) as exc_info:
            raise ExtensionBudgetExceeded("Test budget error")
        
        assert "Test budget error" in str(exc_info.value)
