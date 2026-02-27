"""
SPK (Self-Pricing Kernel) - Tier 2 of AUREUS Semantic Compiler

The SPK is the optimizer and cost analyzer in the 3-tier architecture:
- GVUFD (Tier 1): Intent → Specification
- SPK (Tier 2): Specification → Cost (with budget enforcement)
- UVUAS (Tier 3): Cost-approved specification → Implementation

SPK performs:
1. Cost calculation (LOC, dependencies, abstractions)
2. Budget enforcement (70%/85%/100% thresholds)
3. Alternative generation (6 fallback strategies)
4. Risk assessment integration

Like a compiler optimizer, SPK minimizes complexity cost while ensuring constraints.
"""

from dataclasses import dataclass
from typing import List, Dict, Any
from src.interfaces import Specification, Cost, Budget, Policy


@dataclass
class BudgetStatus:
    """Budget enforcement status"""
    status: str  # "approved", "advisory", "warning", "rejected"
    usage_percentage: float
    can_proceed: bool
    message: str


class LinearCostModel:
    """
    Linear cost model for complexity calculation
    
    Total Cost = (LOC × loc_weight) + (deps × dep_weight) + (abstractions × abstraction_weight)
    
    Default weights:
    - LOC: 1.0 (baseline complexity)
    - Dependencies: 50.0 (external deps are expensive)
    - Abstractions: 20.0 (classes/interfaces add complexity)
    """
    
    def __init__(
        self,
        loc_weight: float = 1.0,
        dependency_weight: float = 50.0,
        abstraction_weight: float = 20.0
    ):
        self.loc_weight = loc_weight
        self.dependency_weight = dependency_weight
        self.abstraction_weight = abstraction_weight
    
    def calculate_loc_cost(self, estimated_loc: int) -> float:
        """Calculate complexity cost for lines of code"""
        return float(estimated_loc) * self.loc_weight
    
    def calculate_dependency_cost(self, estimated_dependencies: int) -> float:
        """Calculate complexity cost for external dependencies"""
        return float(estimated_dependencies) * self.dependency_weight
    
    def calculate_abstraction_cost(self, estimated_abstractions: int) -> float:
        """Calculate complexity cost for abstractions (classes, interfaces)"""
        return float(estimated_abstractions) * self.abstraction_weight
    
    def calculate_total_cost(
        self,
        estimated_loc: int,
        estimated_dependencies: int,
        estimated_abstractions: int
    ) -> float:
        """Calculate total complexity cost"""
        loc_cost = self.calculate_loc_cost(estimated_loc)
        dep_cost = self.calculate_dependency_cost(estimated_dependencies)
        abs_cost = self.calculate_abstraction_cost(estimated_abstractions)
        return loc_cost + dep_cost + abs_cost


class BudgetEnforcer:
    """
    Enforces budget constraints with three thresholds:
    
    - Advisory (70%): Gentle warning, proceed allowed
    - Warning (85%): Strong warning, justification recommended
    - Rejection (100%): Hard limit, execution blocked
    """
    
    def __init__(
        self,
        advisory_threshold: float = 0.70,
        warning_threshold: float = 0.85,
        rejection_threshold: float = 1.00
    ):
        self.advisory_threshold = advisory_threshold
        self.warning_threshold = warning_threshold
        self.rejection_threshold = rejection_threshold
    
    def check_budget(self, estimated_cost: float, budget_limit: float) -> BudgetStatus:
        """
        Check if estimated cost is within budget
        
        Returns BudgetStatus with enforcement decision
        """
        if budget_limit == 0:
            # Avoid division by zero
            return BudgetStatus(
                status="rejected",
                usage_percentage=100.0,
                can_proceed=False,
                message="Budget limit is zero"
            )
        
        usage_percentage = (estimated_cost / budget_limit) * 100.0
        usage_ratio = estimated_cost / budget_limit
        
        if usage_ratio > self.rejection_threshold:
            return BudgetStatus(
                status="rejected",
                usage_percentage=usage_percentage,
                can_proceed=False,
                message=f"Budget exceeded: {usage_percentage:.1f}% of limit. Operation rejected."
            )
        elif usage_ratio > self.warning_threshold:
            return BudgetStatus(
                status="warning",
                usage_percentage=usage_percentage,
                can_proceed=True,
                message=f"Warning: {usage_percentage:.1f}% of budget. Justification recommended."
            )
        elif usage_ratio > self.advisory_threshold:
            return BudgetStatus(
                status="advisory",
                usage_percentage=usage_percentage,
                can_proceed=True,
                message=f"Advisory: {usage_percentage:.1f}% of budget. Consider alternatives."
            )
        else:
            return BudgetStatus(
                status="approved",
                usage_percentage=usage_percentage,
                can_proceed=True,
                message=f"Within budget: {usage_percentage:.1f}% used."
            )


class AlternativeGenerator:
    """
    Generates alternative strategies when budget is exceeded
    
    Six fallback strategies:
    1. Reduce scope - Remove non-essential features
    2. Simplify architecture - Fewer abstractions
    3. Reuse existing - Leverage existing code
    4. Defer dependencies - Minimize external libs
    5. Split phases - Incremental delivery
    6. Optimize implementation - Algorithmic improvements
    """
    
    def generate_alternatives(
        self,
        spec: Specification,
        budget_exceeded_by: int
    ) -> List[Dict[str, Any]]:
        """
        Generate alternative approaches to fit within budget
        
        Returns list of strategies with estimated savings
        """
        alternatives = []
        
        # Strategy 1: Reduce scope
        alternatives.append({
            "strategy": "reduce_scope",
            "description": "Remove non-essential features from specification",
            "estimated_savings": int(budget_exceeded_by * 0.4),  # 40% savings
            "implementation": "Review success criteria and remove optional requirements"
        })
        
        # Strategy 2: Simplify architecture
        alternatives.append({
            "strategy": "simplify_architecture",
            "description": "Use simpler patterns with fewer abstractions",
            "estimated_savings": int(budget_exceeded_by * 0.3),  # 30% savings
            "implementation": "Replace complex patterns with straightforward implementations"
        })
        
        # Strategy 3: Reuse existing code
        alternatives.append({
            "strategy": "reuse_existing",
            "description": "Leverage existing modules instead of creating new ones",
            "estimated_savings": int(budget_exceeded_by * 0.5),  # 50% savings
            "implementation": "Search codebase for reusable components and extend them"
        })
        
        # Strategy 4: Defer dependencies
        alternatives.append({
            "strategy": "defer_dependencies",
            "description": "Implement core functionality without external libraries",
            "estimated_savings": int(budget_exceeded_by * 0.25),  # 25% savings
            "implementation": "Use stdlib instead of external dependencies where possible"
        })
        
        # Strategy 5: Split into phases
        alternatives.append({
            "strategy": "split_phases",
            "description": "Deliver functionality incrementally across multiple phases",
            "estimated_savings": int(budget_exceeded_by * 0.6),  # 60% savings (per phase)
            "implementation": "Create Phase 1 with core features, defer enhancements"
        })
        
        # Strategy 6: Optimize implementation
        alternatives.append({
            "strategy": "optimize_implementation",
            "description": "Use more efficient algorithms and data structures",
            "estimated_savings": int(budget_exceeded_by * 0.2),  # 20% savings
            "implementation": "Profile and optimize critical paths to reduce LOC"
        })
        
        return alternatives


class PricingKernel:
    """
    SPK Pricing Kernel - Main interface for Tier 2
    
    Calculates complexity cost, enforces budgets, generates alternatives
    """
    
    def __init__(self):
        self.cost_model = LinearCostModel()
        self.budget_enforcer = BudgetEnforcer()
        self.alternative_generator = AlternativeGenerator()
    
    def price(self, spec: Specification, policy: Policy) -> Cost:
        """
        Price a specification against policy budget
        
        Returns Cost object with budget status and alternatives if needed
        """
        # Extract estimates from specification budget
        estimated_loc = spec.budgets.max_loc_delta  # Use max_loc_delta field
        estimated_dependencies = spec.budgets.max_new_dependencies  # Use max_new_dependencies field
        
        # Estimate abstractions from spec budget
        estimated_abstractions = spec.budgets.max_new_abstractions
        
        # Calculate total complexity cost
        total_complexity = self.cost_model.calculate_total_cost(
            estimated_loc=estimated_loc,
            estimated_dependencies=estimated_dependencies,
            estimated_abstractions=estimated_abstractions
        )
        
        # Check budget against policy budgets (note: policy.budgets)
        budget_status = self.budget_enforcer.check_budget(
            estimated_cost=estimated_loc,  # Use LOC as primary budget metric
            budget_limit=policy.budgets.max_loc
        )
        
        # Generate alternatives if over budget
        alternatives = []
        if not budget_status.can_proceed:
            budget_exceeded_by = estimated_loc - policy.budgets.max_loc
            alternatives = self.alternative_generator.generate_alternatives(
                spec=spec,
                budget_exceeded_by=budget_exceeded_by
            )
        
        # Create Cost object with SPK budget enforcement results
        return Cost(
            loc=float(estimated_loc),
            dependencies=float(estimated_dependencies),
            abstractions=float(estimated_abstractions),
            total=total_complexity,
            security=0.0,  # No security cost calculation in Phase 1
            within_budget=budget_status.can_proceed,
            budget_status=budget_status.status,
            alternatives=alternatives
        )
