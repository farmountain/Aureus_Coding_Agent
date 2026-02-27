"""
Tests for core AUREUS interfaces and data models.
TDD: Tests written before implementation.
"""

import pytest
from pathlib import Path
from typing import Dict, Any


class TestBudget:
    """Test Budget data model."""
    
    def test_budget_creation_with_required_fields(self):
        """Budget should be created with required fields."""
        from src.interfaces import Budget
        
        budget = Budget(
            max_loc=10000,
            max_modules=8,
            max_files=30,
            max_dependencies=20
        )
        
        assert budget.max_loc == 10000
        assert budget.max_modules == 8
        assert budget.max_files == 30
        assert budget.max_dependencies == 20
    
    def test_budget_creation_with_optional_fields(self):
        """Budget should have optional fields with defaults."""
        from src.interfaces import Budget
        
        budget = Budget(
            max_loc=10000,
            max_modules=8,
            max_files=30,
            max_dependencies=20,
            max_class_loc=500,
            max_function_loc=50,
            max_inheritance_depth=2
        )
        
        assert budget.max_class_loc == 500
        assert budget.max_function_loc == 50
        assert budget.max_inheritance_depth == 2
    
    def test_budget_validation_positive_values(self):
        """Budget values must be positive."""
        from src.interfaces import Budget, ValidationError
        
        with pytest.raises(ValidationError, match="must be positive"):
            Budget(max_loc=-1, max_modules=8, max_files=30, max_dependencies=20)
    
    def test_budget_to_dict(self):
        """Budget should serialize to dict."""
        from src.interfaces import Budget
        
        budget = Budget(max_loc=10000, max_modules=8, max_files=30, max_dependencies=20)
        data = budget.to_dict()
        
        assert isinstance(data, dict)
        assert data["max_loc"] == 10000
        assert data["max_modules"] == 8
    
    def test_budget_from_dict(self):
        """Budget should deserialize from dict."""
        from src.interfaces import Budget
        
        data = {
            "max_loc": 10000,
            "max_modules": 8,
            "max_files": 30,
            "max_dependencies": 20
        }
        budget = Budget.from_dict(data)
        
        assert budget.max_loc == 10000
        assert budget.max_modules == 8


class TestForbiddenPattern:
    """Test ForbiddenPattern data model."""
    
    def test_forbidden_pattern_creation(self):
        """ForbiddenPattern should be created with required fields."""
        from src.interfaces import ForbiddenPattern
        
        pattern = ForbiddenPattern(
            name="god_object",
            description="Classes over 500 LOC",
            rule="class_loc > 500",
            severity="error"
        )
        
        assert pattern.name == "god_object"
        assert pattern.description == "Classes over 500 LOC"
        assert pattern.rule == "class_loc > 500"
        assert pattern.severity == "error"
    
    def test_forbidden_pattern_severity_validation(self):
        """Severity must be valid enum value."""
        from src.interfaces import ForbiddenPattern, ValidationError
        
        with pytest.raises(ValidationError, match="severity"):
            ForbiddenPattern(
                name="test",
                description="test",
                rule="test",
                severity="invalid"
            )
    
    def test_forbidden_pattern_auto_fix_default(self):
        """auto_fix should default to False."""
        from src.interfaces import ForbiddenPattern
        
        pattern = ForbiddenPattern(
            name="test",
            description="test",
            rule="test"
        )
        
        assert pattern.auto_fix is False


class TestPolicy:
    """Test Policy data model."""
    
    def test_policy_creation_minimal(self):
        """Policy should be created with minimal required fields."""
        from src.interfaces import Policy, Budget
        
        budget = Budget(max_loc=10000, max_modules=8, max_files=30, max_dependencies=20)
        policy = Policy(
            version="1.0",
            project_name="test-project",
            project_root=Path("/path/to/project"),
            budgets=budget,
            permissions={"tools": {"file_read": "allow"}}
        )
        
        assert policy.version == "1.0"
        assert policy.project_name == "test-project"
        assert policy.project_root == Path("/path/to/project")
        assert policy.budgets.max_loc == 10000
    
    def test_policy_with_forbidden_patterns(self):
        """Policy should store forbidden patterns."""
        from src.interfaces import Policy, Budget, ForbiddenPattern
        
        budget = Budget(max_loc=10000, max_modules=8, max_files=30, max_dependencies=20)
        patterns = [
            ForbiddenPattern(name="god_object", description="test", rule="test")
        ]
        
        policy = Policy(
            version="1.0",
            project_name="test",
            project_root=Path("/path"),
            budgets=budget,
            permissions={},
            forbidden_patterns=patterns
        )
        
        assert len(policy.forbidden_patterns) == 1
        assert policy.forbidden_patterns[0].name == "god_object"
    
    def test_policy_validation_version_format(self):
        """Policy version must match X.Y format."""
        from src.interfaces import Policy, Budget, ValidationError
        
        budget = Budget(max_loc=10000, max_modules=8, max_files=30, max_dependencies=20)
        
        with pytest.raises(ValidationError, match="version"):
            Policy(
                version="invalid",
                project_name="test",
                project_root=Path("/path"),
                budgets=budget,
                permissions={}
            )
    
    def test_policy_to_dict(self):
        """Policy should serialize to dict."""
        from src.interfaces import Policy, Budget
        
        budget = Budget(max_loc=10000, max_modules=8, max_files=30, max_dependencies=20)
        policy = Policy(
            version="1.0",
            project_name="test",
            project_root=Path("/path"),
            budgets=budget,
            permissions={"tools": {}}
        )
        
        data = policy.to_dict()
        assert isinstance(data, dict)
        assert data["version"] == "1.0"
        assert "budgets" in data


class TestSpecification:
    """Test Specification data model (GVUFD output)."""
    
    def test_specification_creation(self):
        """Specification should be created with required fields."""
        from src.interfaces import Specification, SpecificationBudget
        
        budget = SpecificationBudget(
            max_loc_delta=500,
            max_new_files=5,
            max_new_dependencies=2
        )
        
        spec = Specification(
            intent="Add user authentication",
            success_criteria=["Users can login", "Passwords are hashed"],
            budgets=budget,
            risk_level="medium"
        )
        
        assert spec.intent == "Add user authentication"
        assert len(spec.success_criteria) == 2
        assert spec.budgets.max_loc_delta == 500
        assert spec.risk_level == "medium"
    
    def test_specification_requires_success_criteria(self):
        """Specification must have at least one success criterion."""
        from src.interfaces import Specification, SpecificationBudget, ValidationError
        
        budget = SpecificationBudget(max_loc_delta=500, max_new_files=5, max_new_dependencies=2)
        
        with pytest.raises(ValidationError, match="success_criteria"):
            Specification(
                intent="Test",
                success_criteria=[],
                budgets=budget,
                risk_level="low"
            )
    
    def test_specification_risk_level_validation(self):
        """Risk level must be valid enum."""
        from src.interfaces import Specification, SpecificationBudget, ValidationError
        
        budget = SpecificationBudget(max_loc_delta=500, max_new_files=5, max_new_dependencies=2)
        
        with pytest.raises(ValidationError, match="risk_level"):
            Specification(
                intent="Test",
                success_criteria=["Test"],
                budgets=budget,
                risk_level="invalid"
            )
    
    def test_specification_with_acceptance_tests(self):
        """Specification can include acceptance tests."""
        from src.interfaces import Specification, SpecificationBudget, AcceptanceTest
        
        budget = SpecificationBudget(max_loc_delta=500, max_new_files=5, max_new_dependencies=2)
        tests = [
            AcceptanceTest(
                name="test_login",
                description="User can login",
                test_type="integration",
                priority="high"
            )
        ]
        
        spec = Specification(
            intent="Add auth",
            success_criteria=["Login works"],
            budgets=budget,
            risk_level="medium",
            acceptance_tests=tests
        )
        
        assert len(spec.acceptance_tests) == 1
        assert spec.acceptance_tests[0].name == "test_login"


class TestCostModel:
    """Test CostModel interface."""
    
    def test_cost_model_calculate_method(self):
        """CostModel should have calculate method."""
        from src.interfaces import CostModel, Cost
        
        # CostModel is abstract, so we test with a concrete implementation
        class SimpleCostModel(CostModel):
            def calculate(self, spec, context) -> Cost:
                return Cost(loc=100.0, dependencies=50.0, abstractions=25.0, total=175.0)
        
        model = SimpleCostModel()
        cost = model.calculate(None, None)
        
        assert cost.total == 175.0
        assert cost.loc == 100.0
    
    def test_cost_creation_and_comparison(self):
        """Cost should support comparison operations."""
        from src.interfaces import Cost
        
        cost1 = Cost(loc=100.0, dependencies=50.0, abstractions=25.0, total=175.0)
        cost2 = Cost(loc=200.0, dependencies=50.0, abstractions=25.0, total=275.0)
        
        assert cost1.total < cost2.total
        assert cost2.total > cost1.total


class TestValidationError:
    """Test ValidationError exception."""
    
    def test_validation_error_message(self):
        """ValidationError should carry message."""
        from src.interfaces import ValidationError
        
        error = ValidationError("Test error message")
        assert str(error) == "Validation error: Test error message"
    
    def test_validation_error_with_field(self):
        """ValidationError can specify field."""
        from src.interfaces import ValidationError
        
        error = ValidationError("Invalid value", field="max_loc")
        assert "max_loc" in str(error)
