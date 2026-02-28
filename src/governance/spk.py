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
    
    Total Cost = (LOC × loc_weight) + (deps × dep_weight) + (abstractions × abstraction_weight) + security_cost
    
    Default weights:
    - LOC: 1.0 (baseline complexity)
    - Dependencies: 50.0 (external deps are expensive)
    - Abstractions: 20.0 (classes/interfaces add complexity)
    
    Risk multipliers for security cost:
    - low: 1.0x (no additional cost)
    - medium: 1.2x (20% increase for validation/error handling)
    - high: 1.5x (50% increase for security measures)
    - critical: 2.0x (100% increase for audit trails, encryption, etc.)
    """
    
    # Risk level multipliers
    RISK_MULTIPLIERS = {
        "low": 1.0,
        "medium": 1.2,
        "high": 1.5,
        "critical": 2.0
    }
    
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
    
    def calculate_security_cost(self, base_cost: float, risk_level: str) -> float:
        """
        Calculate security cost based on risk level
        
        Higher risk requires additional code for:
        - Input validation
        - Error handling
        - Audit logging
        - Encryption/hashing
        - Rate limiting
        - Security testing
        
        Args:
            base_cost: Base complexity cost (LOC + deps + abstractions)
            risk_level: Risk assessment from GVUFD (low/medium/high/critical)
        
        Returns:
            Additional security cost as percentage of base cost
        """
        multiplier = self.RISK_MULTIPLIERS.get(risk_level.lower(), 1.0)
        # Security cost is the additional overhead beyond baseline
        additional_cost = base_cost * (multiplier - 1.0)
        return additional_cost
    
    def calculate_total_cost(
        self,
        estimated_loc: int,
        estimated_dependencies: int,
        estimated_abstractions: int,
        risk_level: str = "low"
    ) -> tuple[float, float]:
        """
        Calculate total complexity cost including security
        
        Returns:
            Tuple of (base_cost, security_cost)
        """
        loc_cost = self.calculate_loc_cost(estimated_loc)
        dep_cost = self.calculate_dependency_cost(estimated_dependencies)
        abs_cost = self.calculate_abstraction_cost(estimated_abstractions)
        base_cost = loc_cost + dep_cost + abs_cost
        
        security_cost = self.calculate_security_cost(base_cost, risk_level)
        
        return base_cost, security_cost


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
    
    Six fallback strategies with spec-specific recommendations:
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
        
        Provides spec-specific recommendations based on:
        - Number of success criteria (scope)
        - Dependencies needed (external libs)
        - Architectural constraints (complexity)
        - Risk level (security requirements)
        
        Returns list of strategies with estimated savings
        """
        alternatives = []
        
        # Strategy 1: Reduce scope - analyze success criteria
        num_criteria = len(spec.success_criteria)
        optional_criteria = max(0, num_criteria - 2)  # Keep at least 2 critical criteria
        scope_reduction_detail = f"Remove {optional_criteria} of {num_criteria} success criteria. Keep only critical features."
        if num_criteria <= 2:
            scope_reduction_detail = "Specification already minimal. Consider simplifying requirements."
        
        alternatives.append({
            "strategy": "reduce_scope",
            "description": "Remove non-essential features from specification",
            "estimated_savings": int(budget_exceeded_by * 0.4),  # 40% savings
            "implementation": scope_reduction_detail,
            "specific_actions": [
                f"Current criteria: {num_criteria}",
                "Identify must-have vs nice-to-have features",
                "Defer enhancement features to Phase 2"
            ]
        })
        
        # Strategy 2: Simplify architecture - analyze abstractions
        num_abstractions = spec.budgets.max_new_abstractions
        reduced_abstractions = max(1, num_abstractions // 2)  # Cut abstractions in half
        arch_simplification = f"Reduce from {num_abstractions} to {reduced_abstractions} abstractions."
        if num_abstractions <= 2:
            arch_simplification = "Already using minimal abstractions. Consider procedural approach."
        
        alternatives.append({
            "strategy": "simplify_architecture",
            "description": "Use simpler patterns with fewer abstractions",
            "estimated_savings": int(budget_exceeded_by * 0.3),  # 30% savings
            "implementation": arch_simplification,
            "specific_actions": [
                f"Current abstractions: {num_abstractions}",
                "Replace class hierarchies with simple functions",
                "Avoid design patterns unless clearly beneficial"
            ]
        })
        
        # Strategy 3: Reuse existing code - check for dependencies
        reuse_detail = "Search codebase for reusable components and extend them"
        if spec.budgets.max_new_files > 5:
            reuse_detail = f"Creating {spec.budgets.max_new_files} new files suggests greenfield. Look for existing similar code."
        
        alternatives.append({
            "strategy": "reuse_existing",
            "description": "Leverage existing modules instead of creating new ones",
            "estimated_savings": int(budget_exceeded_by * 0.5),  # 50% savings
            "implementation": reuse_detail,
            "specific_actions": [
                f"Planned new files: {spec.budgets.max_new_files}",
                "Search for similar existing implementations",
                "Extend existing modules instead of creating parallel ones"
            ]
        })
        
        # Strategy 4: Defer dependencies - analyze required dependencies
        num_deps = len(spec.dependencies_needed)
        if num_deps > 0:
            dep_names = [d.name for d in spec.dependencies_needed[:3]]
            defer_detail = f"Defer {num_deps} dependencies: {', '.join(dep_names)}. Use stdlib alternatives."
        else:
            defer_detail = "No external dependencies planned (good!). Continue with stdlib."
        
        alternatives.append({
            "strategy": "defer_dependencies",
            "description": "Implement core functionality without external libraries",
            "estimated_savings": int(budget_exceeded_by * 0.25),  # 25% savings
            "implementation": defer_detail,
            "specific_actions": [
                f"Dependencies to defer: {num_deps}",
                "Use Python stdlib where possible",
                "Add dependencies only when clearly necessary"
            ]
        })
        
        # Strategy 5: Split into phases - analyze complexity
        total_loc = spec.budgets.max_loc_delta
        phase1_loc = total_loc // 3  # Phase 1 = 1/3 of original scope
        num_phases = min(3, (total_loc // 200) + 1)  # Split every 200 LOC
        
        phase_detail = f"Split {total_loc} LOC into {num_phases} phases (~{phase1_loc} LOC each)."
        
        alternatives.append({
            "strategy": "split_phases",
            "description": "Deliver functionality incrementally across multiple phases",
            "estimated_savings": int(budget_exceeded_by * 0.6),  # 60% savings (per phase)
            "implementation": phase_detail,
            "specific_actions": [
                f"Total LOC: {total_loc}, Suggested phases: {num_phases}",
                "Phase 1: Core functionality only",
                "Phase 2: Additional features",
                "Phase 3: Polish and optimization"
            ]
        })
        
        # Strategy 6: Optimize implementation - analyze risk level
        optimization_detail = "Profile and optimize critical paths to reduce LOC"
        if spec.risk_level in ["high", "critical"]:
            optimization_detail = f"High risk ({spec.risk_level}) limits optimization. Focus on correctness first."
        elif spec.budgets.max_cyclomatic_complexity > 10:
            optimization_detail = "High complexity. Simplify algorithms before optimizing."
        
        alternatives.append({
            "strategy": "optimize_implementation",
            "description": "Use more efficient algorithms and data structures",
            "estimated_savings": int(budget_exceeded_by * 0.2),  # 20% savings
            "implementation": optimization_detail,
            "specific_actions": [
                f"Risk level: {spec.risk_level}",
                f"Target complexity: {spec.budgets.max_cyclomatic_complexity}",
                "Use built-in data structures (dict, set, list)",
                "Avoid premature optimization"
            ]
        })
        
        return alternatives


class PricingKernel:
    """
    SPK Pricing Kernel - Main interface for Tier 2
    
    Calculates complexity cost, enforces budgets, generates alternatives
    Integrates risk assessment from GVUFD for security cost adjustment
    """
    
    def __init__(self):
        self.cost_model = LinearCostModel()
        self.budget_enforcer = BudgetEnforcer()
        self.alternative_generator = AlternativeGenerator()
    
    def price(self, spec: Specification, policy: Policy) -> Cost:
        """
        Price a specification against policy budget
        
        Integrates GVUFD risk assessment for security cost calculation
        
        Returns Cost object with budget status and alternatives if needed
        """
        # Extract estimates from specification budget
        estimated_loc = spec.budgets.max_loc_delta
        estimated_dependencies = spec.budgets.max_new_dependencies
        estimated_abstractions = spec.budgets.max_new_abstractions
        
        # Calculate complexity cost with risk-adjusted security cost
        base_cost, security_cost = self.cost_model.calculate_total_cost(
            estimated_loc=estimated_loc,
            estimated_dependencies=estimated_dependencies,
            estimated_abstractions=estimated_abstractions,
            risk_level=spec.risk_level  # From GVUFD specification
        )
        
        total_complexity = base_cost + security_cost
        
        # Check budget against policy budgets
        # Use total complexity for enforcement (includes security overhead)
        budget_status = self.budget_enforcer.check_budget(
            estimated_cost=estimated_loc,  # Still use LOC as primary metric
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
        
        # Create Cost object with risk-adjusted costs
        return Cost(
            loc=float(estimated_loc),
            dependencies=float(estimated_dependencies),
            abstractions=float(estimated_abstractions),
            total=total_complexity,
            security=security_cost,  # Now calculated based on risk level
            within_budget=budget_status.can_proceed,
            budget_status=budget_status.status,
            alternatives=alternatives
        )
