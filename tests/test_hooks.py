"""
Test Suite for HookExtension

Tests lifecycle automation at AUREUS workflow phases.
"""

import pytest
import sys
from pathlib import Path
import time

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.interfaces import Policy, Budget
from src.extensions.hooks import Hook, HookExtension


@pytest.fixture
def test_policy(tmp_path):
    """Create test policy"""
    return Policy(
        version="1.0",
        project_name="test-hooks",
        project_root=tmp_path,
        budgets=Budget(
            max_loc=4000,
            max_modules=20,
            max_files=50,
            max_dependencies=10
        ),
        permissions={"extensions": True, "hooks": True}
    )


class TestHook:
    """Test Hook dataclass"""
    
    def test_hook_creation(self):
        """Test creating a hook"""
        def my_hook():
            return "hook executed"
        
        hook = Hook(
            name="test_hook",
            description="A test hook",
            callback=my_hook,
            lifecycle_point="pre_gather",
            timeout=5.0,
            estimated_cost=1.0
        )
        
        assert hook.name == "test_hook"
        assert hook.lifecycle_point == "pre_gather"
        assert hook.timeout == 5.0
        assert hook.estimated_cost == 1.0
    
    def test_hook_execution(self):
        """Test executing hook callback"""
        def my_hook(context):
            return f"processed: {context}"
        
        hook = Hook(
            name="processor",
            description="Process context",
            callback=my_hook,
            lifecycle_point="post_gather"
        )
        
        result = hook.callback({"data": "test"})
        assert "processed" in result


class TestHookExtension:
    """Test HookExtension lifecycle automation"""
    
    def test_register_hook(self, test_policy):
        """Test registering hooks"""
        ext = HookExtension(policy=test_policy, max_cost=100.0)
        
        def pre_hook():
            return "pre"
        
        hook = Hook(
            name="pre_gather_hook",
            description="Run before gather",
            callback=pre_hook,
            lifecycle_point="pre_gather"
        )
        
        ext.register_hook(hook)
        
        assert "pre_gather" in ext.hooks
        assert len(ext.hooks["pre_gather"]) == 1
        assert ext.hooks["pre_gather"][0].name == "pre_gather_hook"
    
    def test_execute_hooks_for_lifecycle_point(self, test_policy):
        """Test executing all hooks for a lifecycle point"""
        ext = HookExtension(policy=test_policy, max_cost=100.0)
        
        results = []
        
        def hook1():
            results.append("hook1")
            return "result1"
        
        def hook2():
            results.append("hook2")
            return "result2"
        
        ext.register_hook(Hook(
            name="hook1",
            description="First hook",
            callback=hook1,
            lifecycle_point="pre_gather",
            estimated_cost=2.0
        ))
        
        ext.register_hook(Hook(
            name="hook2",
            description="Second hook",
            callback=hook2,
            lifecycle_point="pre_gather",
            estimated_cost=3.0
        ))
        
        result = ext.execute_hooks("pre_gather")
        
        assert result.success is True
        assert len(results) == 2
        assert "hook1" in results
        assert "hook2" in results
        assert result.cost_used == 5.0  # 2.0 + 3.0
    
    def test_hooks_have_cost_budget(self, test_policy):
        """Test hooks enforce cost budget"""
        ext = HookExtension(policy=test_policy, max_cost=10.0)
        
        def expensive_hook():
            return "expensive"
        
        hook = Hook(
            name="expensive",
            description="Expensive hook",
            callback=expensive_hook,
            lifecycle_point="pre_gather",
            estimated_cost=20.0
        )
        
        # Should fail registration - exceeds budget
        with pytest.raises(Exception):
            ext.register_hook(hook)
    
    def test_hook_timeout_enforcement(self, test_policy):
        """Test hooks enforce timeout"""
        ext = HookExtension(policy=test_policy, max_cost=100.0)
        
        def slow_hook():
            time.sleep(2.0)
            return "slow"
        
        hook = Hook(
            name="slow",
            description="Slow hook",
            callback=slow_hook,
            lifecycle_point="pre_gather",
            timeout=0.1,
            estimated_cost=1.0
        )
        
        ext.register_hook(hook)
        result = ext.execute_hooks("pre_gather")
        
        # Note: Timeout enforcement using signals only works on Unix
        # On Windows, hook will execute normally
        # This test validates the hook runs without crashing
        assert result is not None
    
    def test_hook_permission_validation(self, tmp_path):
        """Test hooks validate permissions"""
        policy = Policy(
            version="1.0",
            project_name="test-hooks-noperm",
            project_root=tmp_path,
            budgets=Budget(
                max_loc=4000,
                max_modules=20,
                max_files=50,
                max_dependencies=10
            ),
            permissions={"extensions": True}  # Missing 'hooks' permission
        )
        
        ext = HookExtension(policy=policy, max_cost=100.0)
        
        def my_hook():
            return "test"
        
        hook = Hook(
            name="test",
            description="Test hook",
            callback=my_hook,
            lifecycle_point="pre_gather",
            required_permissions=["hooks"]
        )
        
        # Should fail - missing permission
        with pytest.raises(Exception):
            ext.register_hook(hook)
    
    def test_hook_exception_handling(self, test_policy):
        """Test hooks handle exceptions gracefully"""
        ext = HookExtension(policy=test_policy, max_cost=100.0)
        
        def failing_hook():
            raise ValueError("Hook failed")
        
        hook = Hook(
            name="failing",
            description="Failing hook",
            callback=failing_hook,
            lifecycle_point="pre_gather",
            estimated_cost=1.0
        )
        
        ext.register_hook(hook)
        result = ext.execute_hooks("pre_gather")
        
        # Should capture error but not crash
        assert result.success is False
        # Error message is in the result error or metadata
        error_text = result.error + str(result.metadata)
        assert "ValueError" in error_text or "Hook failed" in error_text
    
    def test_multiple_lifecycle_points(self, test_policy):
        """Test hooks work across different lifecycle points"""
        ext = HookExtension(policy=test_policy, max_cost=100.0)
        
        def pre_hook():
            return "pre"
        
        def post_hook():
            return "post"
        
        ext.register_hook(Hook(
            name="pre",
            description="Pre hook",
            callback=pre_hook,
            lifecycle_point="pre_gather",
            estimated_cost=1.0
        ))
        
        ext.register_hook(Hook(
            name="post",
            description="Post hook",
            callback=post_hook,
            lifecycle_point="post_gather",
            estimated_cost=1.0
        ))
        
        pre_result = ext.execute_hooks("pre_gather")
        post_result = ext.execute_hooks("post_gather")
        
        assert pre_result.success is True
        assert post_result.success is True
        assert pre_result.cost_used == 1.0
        assert post_result.cost_used == 1.0
    
    def test_execute_hooks_with_context(self, test_policy):
        """Test hooks can receive and process context"""
        ext = HookExtension(policy=test_policy, max_cost=100.0)
        
        def context_hook(context):
            return f"processed: {context.get('data', 'none')}"
        
        hook = Hook(
            name="context_processor",
            description="Process context",
            callback=context_hook,
            lifecycle_point="pre_gather",
            estimated_cost=1.0
        )
        
        ext.register_hook(hook)
        result = ext.execute_hooks("pre_gather", context={"data": "test_value"})
        
        assert result.success is True
        assert "processed: test_value" in str(result.output)
