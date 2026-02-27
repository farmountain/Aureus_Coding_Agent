"""
Test Suite for SkillExtension

Tests reusable workflow system with governance.
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.interfaces import Policy, Budget


@pytest.fixture
def test_policy(tmp_path):
    """Create test policy"""
    return Policy(
        version="1.0",
        project_name="test-skills",
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


class TestSkill:
    """Test Skill dataclass"""
    
    def test_skill_creation(self):
        """Test creating a skill"""
        from src.extensions.skills import Skill
        
        def test_workflow(**kwargs):
            return f"Processed: {kwargs.get('input', 'none')}"
        
        skill = Skill(
            name="test_skill",
            description="A test skill",
            workflow=test_workflow,
            required_permissions=["file_read"]
        )
        
        assert skill.name == "test_skill"
        assert skill.description == "A test skill"
        assert skill.workflow == test_workflow
        assert "file_read" in skill.required_permissions
    
    def test_skill_execution(self):
        """Test skill workflow execution"""
        from src.extensions.skills import Skill
        
        def workflow(**kwargs):
            value = kwargs.get("value", 0)
            return value * 2
        
        skill = Skill(
            name="doubler",
            description="Doubles a value",
            workflow=workflow
        )
        
        result = skill.workflow(value=5)
        assert result == 10


class TestSkillExtension:
    """Test SkillExtension functionality"""
    
    def test_register_skill(self, test_policy):
        """Test registering a skill"""
        from src.extensions.skills import SkillExtension, Skill
        
        def workflow(**kwargs):
            return "test output"
        
        skill = Skill(
            name="test_skill",
            description="Test",
            workflow=workflow
        )
        
        ext = SkillExtension(policy=test_policy)
        ext.register_skill(skill)
        
        assert "test_skill" in ext.skills
        assert ext.skills["test_skill"] == skill
    
    def test_execute_skill(self, test_policy):
        """Test executing a registered skill"""
        from src.extensions.skills import SkillExtension, Skill
        
        def workflow(**kwargs):
            return f"Processed: {kwargs.get('data', 'none')}"
        
        skill = Skill(
            name="processor",
            description="Processes data",
            workflow=workflow
        )
        
        ext = SkillExtension(policy=test_policy)
        ext.register_skill(skill)
        
        result = ext.execute_skill("processor", data="test_data")
        
        assert result.success is True
        assert "Processed: test_data" in result.output
    
    def test_skill_has_cost_budget(self, test_policy):
        """Test skills have cost budgets"""
        from src.extensions.skills import SkillExtension, Skill
        
        def workflow(**kwargs):
            return "output"
        
        skill = Skill(
            name="test_skill",
            description="Test",
            workflow=workflow,
            estimated_cost=50.0
        )
        
        ext = SkillExtension(policy=test_policy, max_cost=100.0)
        ext.register_skill(skill)
        
        # Skill should have cost budget
        assert skill.estimated_cost == 50.0
        
        # Executing should track cost
        result = ext.execute_skill("test_skill")
        assert result.cost_used <= 50.0
    
    def test_skill_permission_validation(self, test_policy):
        """Test skill permission requirements validated"""
        from src.extensions.skills import SkillExtension, Skill
        from src.extensions.base import ExtensionPermissionError
        
        def workflow(**kwargs):
            return "output"
        
        # Skill requires permission not in policy
        skill = Skill(
            name="test_skill",
            description="Test",
            workflow=workflow,
            required_permissions=["network"]  # Not granted in test_policy
        )
        
        ext = SkillExtension(policy=test_policy)
        
        # Should fail validation
        with pytest.raises(ExtensionPermissionError):
            ext.register_skill(skill)
    
    def test_skill_execution_tracks_cost(self, test_policy):
        """Test skill execution tracks cost"""
        from src.extensions.skills import SkillExtension, Skill
        
        def workflow(**kwargs):
            return "output"
        
        skill = Skill(
            name="test_skill",
            description="Test",
            workflow=workflow,
            estimated_cost=25.0
        )
        
        ext = SkillExtension(policy=test_policy, max_cost=100.0)
        ext.register_skill(skill)
        
        # Initial cost
        assert ext.cost_used == 0.0
        
        # Execute skill
        ext.execute_skill("test_skill")
        
        # Cost should be tracked
        assert ext.cost_used > 0.0
        assert ext.cost_used <= 25.0
    
    def test_skill_not_found_error(self, test_policy):
        """Test executing non-existent skill fails gracefully"""
        from src.extensions.skills import SkillExtension
        
        ext = SkillExtension(policy=test_policy)
        
        result = ext.execute_skill("nonexistent_skill")
        
        assert result.success is False
        assert "not found" in result.error.lower()
    
    def test_skill_workflow_exception_handling(self, test_policy):
        """Test skill handles workflow exceptions"""
        from src.extensions.skills import SkillExtension, Skill
        
        def failing_workflow(**kwargs):
            raise ValueError("Workflow error")
        
        skill = Skill(
            name="failing_skill",
            description="Fails",
            workflow=failing_workflow
        )
        
        ext = SkillExtension(policy=test_policy)
        ext.register_skill(skill)
        
        result = ext.execute_skill("failing_skill")
        
        assert result.success is False
        assert "error" in result.error.lower()
