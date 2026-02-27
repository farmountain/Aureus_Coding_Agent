"""
Test Suite for ExtensionManager

Tests global extension coordination and budget enforcement.
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.interfaces import Policy, Budget
from src.extensions import (
    Extension,
    ExtensionResult,
    InstructionExtension,
    SkillExtension,
    HookExtension
)
from src.extensions.manager import ExtensionManager


@pytest.fixture
def test_policy(tmp_path):
    """Create test policy"""
    return Policy(
        version="1.0",
        project_name="test-manager",
        project_root=tmp_path,
        budgets=Budget(
            max_loc=4000,
            max_modules=20,
            max_files=50,
            max_dependencies=10
        ),
        permissions={
            "extensions": True,
            "hooks": True,
            "skills": True,
            "file_read": True,
            "file_write": True
        }
    )


class TestExtensionManager:
    """Test ExtensionManager global coordination"""
    
    def test_manager_initialization(self, test_policy):
        """Test creating extension manager"""
        manager = ExtensionManager(
            policy=test_policy,
            global_extension_budget=100.0
        )
        
        assert manager.policy == test_policy
        assert manager.global_budget == 100.0
        assert manager.global_cost_used == 0.0
        assert len(manager.extensions) == 0
    
    def test_register_extension(self, test_policy):
        """Test registering extensions"""
        manager = ExtensionManager(policy=test_policy, global_extension_budget=200.0)
        
        skills = SkillExtension(policy=test_policy, max_cost=50.0)
        manager.register_extension("skills", skills)
        
        assert "skills" in manager.extensions
        assert manager.extensions["skills"] == skills
    
    def test_global_budget_enforcement(self, test_policy):
        """Test global budget limits all extensions"""
        manager = ExtensionManager(policy=test_policy, global_extension_budget=100.0)
        
        # Register extension with cost that would exceed global budget
        skills = SkillExtension(policy=test_policy, max_cost=150.0)
        
        # Should fail - extension max_cost exceeds global budget
        with pytest.raises(Exception):
            manager.register_extension("skills", skills)
    
    def test_track_extension_costs(self, test_policy, tmp_path):
        """Test manager tracks costs across extensions"""
        manager = ExtensionManager(policy=test_policy, global_extension_budget=200.0)
        
        # Create instruction file
        instructions_file = tmp_path / ".aureus" / "instructions.md"
        instructions_file.parent.mkdir(exist_ok=True)
        instructions_file.write_text("Test instructions")
        
        # Register and use extension
        instructions = InstructionExtension(policy=test_policy, max_cost=50.0)
        manager.register_extension("instructions", instructions)
        
        # Execute extension
        result = instructions.execute()
        
        # Manager should track the cost
        assert manager.get_total_cost_used() > 0.0
        assert manager.get_remaining_budget() < 200.0
    
    def test_list_extensions(self, test_policy):
        """Test listing registered extensions"""
        manager = ExtensionManager(policy=test_policy, global_extension_budget=200.0)
        
        skills = SkillExtension(policy=test_policy, max_cost=50.0)
        hooks = HookExtension(policy=test_policy, max_cost=50.0)
        
        manager.register_extension("skills", skills)
        manager.register_extension("hooks", hooks)
        
        extensions = manager.list_extensions()
        
        assert "skills" in extensions
        assert "hooks" in extensions
        assert len(extensions) == 2
    
    def test_get_extension_status(self, test_policy):
        """Test getting status for all extensions"""
        manager = ExtensionManager(policy=test_policy, global_extension_budget=200.0)
        
        skills = SkillExtension(policy=test_policy, max_cost=50.0)
        manager.register_extension("skills", skills)
        
        status = manager.get_status()
        
        assert status["global_budget"] == 200.0
        assert status["global_cost_used"] == 0.0
        assert "extensions" in status
        assert "skills" in status["extensions"]
    
    def test_unregister_extension(self, test_policy):
        """Test unregistering extensions"""
        manager = ExtensionManager(policy=test_policy, global_extension_budget=200.0)
        
        skills = SkillExtension(policy=test_policy, max_cost=50.0)
        manager.register_extension("skills", skills)
        
        assert "skills" in manager.extensions
        
        manager.unregister_extension("skills")
        
        assert "skills" not in manager.extensions
    
    def test_budget_allocation_across_extensions(self, test_policy):
        """Test budget is properly allocated across multiple extensions"""
        manager = ExtensionManager(policy=test_policy, global_extension_budget=200.0)
        
        # Register multiple extensions
        skills = SkillExtension(policy=test_policy, max_cost=80.0)
        hooks = HookExtension(policy=test_policy, max_cost=80.0)
        
        manager.register_extension("skills", skills)
        manager.register_extension("hooks", hooks)
        
        # Total allocated should not exceed global budget
        total_allocated = skills.max_cost + hooks.max_cost
        assert total_allocated == 160.0
        assert total_allocated <= manager.global_budget
