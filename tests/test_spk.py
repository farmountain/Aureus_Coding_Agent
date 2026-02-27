"""
Tests for SPK (Self-Pricing Kernel) - Tier 2

SPK is the cost optimizer in the 3-tier semantic compiler.
It calculates complexity costs, enforces budgets, and generates alternatives.

Test Coverage:
- LinearCostModel: LOC, dependencies, abstractions pricing
- BudgetEnforcer: 70%/85%/100% threshold enforcement
- AlternativeGenerator: 6 fallback strategies
- PricingKernel: End-to-end cost calculation and budget checking
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.interfaces import Specification, Cost, Budget, Policy, SpecificationBudget
from src.governance.spk import (
    LinearCostModel,
    BudgetEnforcer,
    AlternativeGenerator,
    PricingKernel,
    BudgetStatus,
)


class TestLinearCostModel:
    """Test the linear cost calculation model"""

    def test_loc_cost_calculation(self):
        """Test LOC complexity cost calculation"""
        model = LinearCostModel(loc_weight=1.0, dependency_weight=50.0, abstraction_weight=20.0)
        
        # 500 LOC should cost 500 complexity units
        cost = model.calculate_loc_cost(500)
        assert cost == 500.0
        
        # 0 LOC should cost 0
        cost = model.calculate_loc_cost(0)
        assert cost == 0.0

    def test_dependency_cost_calculation(self):
        """Test dependency complexity cost calculation"""
        model = LinearCostModel(loc_weight=1.0, dependency_weight=50.0, abstraction_weight=20.0)
        
        # 3 dependencies should cost 150 complexity units (3 * 50)
        cost = model.calculate_dependency_cost(3)
        assert cost == 150.0
        
        # 0 dependencies should cost 0
        cost = model.calculate_dependency_cost(0)
        assert cost == 0.0

    def test_abstraction_cost_calculation(self):
        """Test abstraction complexity cost calculation"""
        model = LinearCostModel(loc_weight=1.0, dependency_weight=50.0, abstraction_weight=20.0)
        
        # 5 abstractions (classes/interfaces) should cost 100 units (5 * 20)
        cost = model.calculate_abstraction_cost(5)
        assert cost == 100.0
        
        # 0 abstractions should cost 0
        cost = model.calculate_abstraction_cost(0)
        assert cost == 0.0

    def test_total_cost_calculation(self):
        """Test total complexity cost combines all factors"""
        model = LinearCostModel(loc_weight=1.0, dependency_weight=50.0, abstraction_weight=20.0)
        
        # Total: 500 LOC + 3 deps + 5 abstractions = 500 + 150 + 100 = 750
        cost = model.calculate_total_cost(
            estimated_loc=500,
            estimated_dependencies=3,
            estimated_abstractions=5
        )
        assert cost == 750.0

    def test_configurable_weights(self):
        """Test that cost model weights are configurable"""
        # Custom weights for different complexity priorities
        model = LinearCostModel(loc_weight=2.0, dependency_weight=100.0, abstraction_weight=50.0)
        
        # Total: 500*2 + 3*100 + 5*50 = 1000 + 300 + 250 = 1550
        cost = model.calculate_total_cost(
            estimated_loc=500,
            estimated_dependencies=3,
            estimated_abstractions=5
        )
        assert cost == 1550.0


class TestBudgetEnforcer:
    """Test budget threshold enforcement"""

    def test_within_budget(self):
        """Test operation within budget (< 70%)"""
        enforcer = BudgetEnforcer(
            advisory_threshold=0.70,  # 70%
            warning_threshold=0.85,   # 85%
            rejection_threshold=1.00  # 100%
        )
        
        budget = Budget(max_loc=1000, max_dependencies=10, max_modules=5, max_files=25)
        estimated_cost = 500  # 50% of budget
        
        status = enforcer.check_budget(estimated_cost, budget.max_loc)
        
        assert status.status == "approved"
        assert status.usage_percentage == 50.0
        assert status.can_proceed is True
        assert "within budget" in status.message.lower()

    def test_advisory_threshold(self):
        """Test advisory threshold (70-85%)"""
        enforcer = BudgetEnforcer(
            advisory_threshold=0.70,
            warning_threshold=0.85,
            rejection_threshold=1.00
        )
        
        budget = Budget(max_loc=1000, max_dependencies=10, max_modules=5, max_files=25)
        estimated_cost = 750  # 75% of budget
        
        status = enforcer.check_budget(estimated_cost, budget.max_loc)
        
        assert status.status == "advisory"
        assert status.usage_percentage == 75.0
        assert status.can_proceed is True
        assert "advisory" in status.message.lower()

    def test_warning_threshold(self):
        """Test warning threshold (85-100%)"""
        enforcer = BudgetEnforcer(
            advisory_threshold=0.70,
            warning_threshold=0.85,
            rejection_threshold=1.00
        )
        
        budget = Budget(max_loc=1000, max_dependencies=10, max_modules=5, max_files=25)
        estimated_cost = 900  # 90% of budget
        
        status = enforcer.check_budget(estimated_cost, budget.max_loc)
        
        assert status.status == "warning"
        assert status.usage_percentage == 90.0
        assert status.can_proceed is True  # Still allowed but requires justification
        assert "warning" in status.message.lower()

    def test_rejection_threshold(self):
        """Test rejection threshold (> 100%)"""
        enforcer = BudgetEnforcer(
            advisory_threshold=0.70,
            warning_threshold=0.85,
            rejection_threshold=1.00
        )
        
        budget = Budget(max_loc=1000, max_dependencies=10, max_modules=5, max_files=25)
        estimated_cost = 1200  # 120% of budget
        
        status = enforcer.check_budget(estimated_cost, budget.max_loc)
        
        assert status.status == "rejected"
        assert status.usage_percentage == 120.0
        assert status.can_proceed is False
        assert "rejected" in status.message.lower()

    def test_exact_budget_limit(self):
        """Test exact budget limit (100%)"""
        enforcer = BudgetEnforcer(
            advisory_threshold=0.70,
            warning_threshold=0.85,
            rejection_threshold=1.00
        )
        
        budget = Budget(max_loc=1000, max_dependencies=10, max_modules=5, max_files=25)
        estimated_cost = 1000  # Exactly 100%
        
        status = enforcer.check_budget(estimated_cost, budget.max_loc)
        
        # At exactly 100%, should be warning, not rejected
        assert status.status == "warning"
        assert status.usage_percentage == 100.0
        assert status.can_proceed is True


class TestAlternativeGenerator:
    """Test alternative suggestion generation"""

    def test_generate_alternatives_for_over_budget(self):
        """Test that alternatives are generated when over budget"""
        generator = AlternativeGenerator()
        
        spec = Specification(
            intent="Add REST API with authentication",
            success_criteria=["API responds", "Auth works"],
            forbidden_patterns=[],
            budgets=SpecificationBudget(max_loc_delta=1200, max_new_files=5, max_new_dependencies=3, max_new_abstractions=10),
            acceptance_tests=[],
            risk_level="high"
        )
        
        alternatives = generator.generate_alternatives(spec, budget_exceeded_by=200)
        
        # Should generate multiple strategies
        assert len(alternatives) >= 3
        
        # All strategies should have descriptions
        for alt in alternatives:
            assert len(alt["strategy"]) > 0
            assert len(alt["description"]) > 0
            assert "estimated_savings" in alt

    def test_reduce_scope_strategy(self):
        """Test reduce scope alternative strategy"""
        generator = AlternativeGenerator()
        
        spec = Specification(
            intent="Add REST API with authentication and logging",
            success_criteria=["API works", "Auth works", "Logs work"],
            forbidden_patterns=[],
            budgets=SpecificationBudget(max_loc_delta=1200, max_new_files=5, max_new_dependencies=3, max_new_abstractions=10),
            acceptance_tests=[],
            risk_level="high"
        )
        
        alternatives = generator.generate_alternatives(spec, budget_exceeded_by=200)
        
        # Should include "reduce scope" strategy
        strategies = [alt["strategy"] for alt in alternatives]
        assert "reduce_scope" in strategies

    def test_simplify_architecture_strategy(self):
        """Test simplify architecture alternative"""
        generator = AlternativeGenerator()
        
        spec = Specification(
            intent="Add REST API with microservices architecture",
            success_criteria=["API works"],
            forbidden_patterns=[],
            budgets=SpecificationBudget(max_loc_delta=1500, max_new_files=8, max_new_dependencies=5, max_new_abstractions=15),
            acceptance_tests=[],
            risk_level="high"
        )
        
        alternatives = generator.generate_alternatives(spec, budget_exceeded_by=300)
        
        # Should include "simplify architecture" strategy
        strategies = [alt["strategy"] for alt in alternatives]
        assert "simplify_architecture" in strategies

    def test_all_six_strategies_available(self):
        """Test that all 6 strategies can be generated"""
        generator = AlternativeGenerator()
        
        spec = Specification(
            intent="Complex feature with many requirements",
            success_criteria=["Feature works"] * 10,
            forbidden_patterns=[],
            budgets=SpecificationBudget(max_loc_delta=2000, max_new_files=10, max_new_dependencies=8, max_new_abstractions=20),
            acceptance_tests=[],
            risk_level="critical"
        )
        
        alternatives = generator.generate_alternatives(spec, budget_exceeded_by=500)
        
        strategies = [alt["strategy"] for alt in alternatives]
        
        # All 6 strategies should be present
        expected_strategies = [
            "reduce_scope",
            "simplify_architecture",
            "reuse_existing",
            "defer_dependencies",
            "split_phases",
            "optimize_implementation"
        ]
        
        for strategy in expected_strategies:
            assert strategy in strategies, f"Missing strategy: {strategy}"


class TestPricingKernel:
    """Test the complete SPK pricing kernel"""

    def test_price_specification(self):
        """Test end-to-end specification pricing"""
        kernel = PricingKernel()
        
        spec = Specification(
            intent="Add a simple REST API endpoint",
            success_criteria=["Endpoint responds with 200"],
            forbidden_patterns=[],
            budgets=SpecificationBudget(max_loc_delta=500, max_new_files=3, max_new_dependencies=2, max_new_abstractions=5),
            acceptance_tests=["test_endpoint_returns_200"],
            risk_level="low"
        )
        
        policy = Policy(
            version="1.0",
            project_name="test-api",
            project_root=Path("."),
            budgets=Budget(max_loc=1000, max_dependencies=10, max_modules=5, max_files=25),
            permissions={"file_write": True, "file_read": True}
        )
        
        cost = kernel.price(spec, policy)
        
        # Should return a Cost object
        assert isinstance(cost, Cost)
        assert cost.loc == 500
        assert cost.dependencies == 2
        assert cost.abstractions >= 0
        assert cost.total > 0
        assert cost.within_budget is True

    def test_reject_over_budget_specification(self):
        """Test that over-budget specifications are rejected"""
        kernel = PricingKernel()
        
        spec = Specification(
            intent="Add massive feature",
            success_criteria=["Feature works"],
            forbidden_patterns=[],
            budgets=SpecificationBudget(max_loc_delta=1500, max_new_files=8, max_new_dependencies=6, max_new_abstractions=15),
            acceptance_tests=[],
            risk_level="critical"
        )
        
        policy = Policy(
            version="1.0",
            project_name="test-api",
            project_root=Path("."),
            budgets=Budget(max_loc=1000, max_dependencies=5, max_modules=3, max_files=15),
            permissions={"file_write": True, "file_read": True}
        )
        
        cost = kernel.price(spec, policy)
        
        # Should be over budget
        assert cost.within_budget is False
        assert len(cost.alternatives) > 0  # Should provide alternatives

    def test_alternatives_provided_when_over_budget(self):
        """Test that alternatives are provided for over-budget specs"""
        kernel = PricingKernel()
        
        spec = Specification(
            intent="Add complex feature",
            success_criteria=["Feature works"],
            forbidden_patterns=[],
            budgets=SpecificationBudget(max_loc_delta=1200, max_new_files=6, max_new_dependencies=4, max_new_abstractions=12),
            acceptance_tests=[],
            risk_level="high"
        )
        
        policy = Policy(
            version="1.0",
            project_name="test-api",
            project_root=Path("."),
            budgets=Budget(max_loc=1000, max_dependencies=5, max_modules=3, max_files=15),
            permissions={"file_write": True, "file_read": True}
        )
        
        cost = kernel.price(spec, policy)
        
        # Should provide alternatives
        assert len(cost.alternatives) >= 3
        assert all("strategy" in alt for alt in cost.alternatives)
        assert all("description" in alt for alt in cost.alternatives)
