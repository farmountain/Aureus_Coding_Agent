"""
Three-Tier Coordination Protocol

Coordinates the tight integration between:
1. GVUFD (Semantic Compiler): Intent → Goals + Spec
2. SPK (Self-Pricing Kernel): Spec Candidates → Value-Aligned Selection
3. UVUAS (Agent Swarm): Execution with Claude Code Loop (Context → Execute → Reflect)

This is NOT a pipeline - it's a coordinated system where each tier informs the others:
- GVUFD extracts goals from intent and updates global value function
- SPK evaluates specs based on value alignment (not just cost)
- UVUAS executes with continuous alignment checking and reflection
- Feedback from UVUAS can trigger GVUFD re-specification or SPK re-evaluation
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import re

from src.interfaces import Policy, Specification, Cost, AcceptanceTest, SpecificationBudget
from src.governance.gvufd import SpecificationGenerator
from src.governance.spk import PricingKernel
from src.memory.global_value_function import GlobalValueMemory, GoalType


@dataclass
class IntentGoals:
    """Goals extracted from user intent"""
    explicit_goals: List[str]  # Direct mentions: "simple", "production-ready"
    implied_goals: Dict[GoalType, float]  # Weight adjustments
    optimization_target: str  # "maximize_quality", "balance", "maximize_speed"
    constraints: List[str]  # Hard constraints from intent


class IntentGoalExtractor:
    """
    Extracts goals and constraints from natural language intent.
    
    This is what makes GVUFD "semantic" - it maps natural language to formal goals.
    """
    
    # Keywords that signal goal priorities
    QUALITY_KEYWORDS = ["production", "robust", "reliable", "enterprise", "quality"]
    SIMPLICITY_KEYWORDS = ["simple", "minimal", "basic", "straightforward", "quick"]
    MAINTAINABILITY_KEYWORDS = ["maintainable", "clean", "readable", "documented"]
    PERFORMANCE_KEYWORDS = ["fast", "efficient", "optimized", "high-performance"]
    TESTABILITY_KEYWORDS = ["tested", "test coverage", "tdd", "testable"]
    
    def extract(self, intent: str) -> IntentGoals:
        """
        Parse intent and extract goal adjustments.
        
        Examples:
        - "create a simple calculator" → increase simplicity weight
        - "build a production-ready API" → increase quality + testability
        - "quick prototype of..." → maximize speed, reduce quality requirements
        """
        intent_lower = intent.lower()
        
        explicit_goals = []
        implied_goals = {}
        optimization_target = "balance"  # Default
        constraints = []
        
        # Detect quality emphasis
        if any(kw in intent_lower for kw in self.QUALITY_KEYWORDS):
            explicit_goals.append("high_quality")
            implied_goals[GoalType.CODE_QUALITY] = 0.35  # Increase from 0.30
            implied_goals[GoalType.TESTABILITY] = 0.15  # Increase from 0.10
            optimization_target = "maximize_quality"
        
        # Detect simplicity emphasis
        if any(kw in intent_lower for kw in self.SIMPLICITY_KEYWORDS):
            explicit_goals.append("simplicity")
            implied_goals[GoalType.SIMPLICITY] = 0.30  # Increase from 0.20
            implied_goals[GoalType.CODE_QUALITY] = 0.20  # Reduce from 0.30
            if optimization_target == "balance":
                optimization_target = "maximize_speed"
        
        # Detect maintainability emphasis
        if any(kw in intent_lower for kw in self.MAINTAINABILITY_KEYWORDS):
            explicit_goals.append("maintainability")
            implied_goals[GoalType.MAINTAINABILITY] = 0.30  # Increase from 0.25
        
        # Detect performance emphasis
        if any(kw in intent_lower for kw in self.PERFORMANCE_KEYWORDS):
            explicit_goals.append("performance")
            constraints.append("optimize_for_performance")
        
        # Detect testability emphasis
        if any(kw in intent_lower for kw in self.TESTABILITY_KEYWORDS):
            explicit_goals.append("testability")
            implied_goals[GoalType.TESTABILITY] = 0.15  # Increase from 0.10
        
        # Extract hard constraints
        if "no dependencies" in intent_lower or "zero dependencies" in intent_lower:
            constraints.append("no_external_dependencies")
        
        if "no classes" in intent_lower or "functional" in intent_lower:
            constraints.append("no_classes")
        
        return IntentGoals(
            explicit_goals=explicit_goals,
            implied_goals=implied_goals,
            optimization_target=optimization_target,
            constraints=constraints
        )


class SpecEvaluator:
    """
    Evaluates specification candidates using global value function.
    
    This is what makes SPK "value-aware" - it selects based on alignment, not just cost.
    """
    
    def __init__(self, global_value_memory: GlobalValueMemory):
        self.global_value_memory = global_value_memory
    
    def evaluate_spec(self, spec: Specification) -> float:
        """
        Evaluate how well a specification aligns with global goals.
        
        Returns:
            Alignment score (0.0 - 1.0)
        """
        global_vf = self.global_value_memory.get_global_value_function()
        
        # Convert spec to action representation
        action = {
            "type": "specification",
            "estimated_loc": spec.budgets.max_loc_delta,
            "dependencies": len(spec.dependencies_needed) if hasattr(spec, 'dependencies_needed') else 0,
            "abstractions": spec.budgets.max_new_abstractions,
            "risk_level": spec.risk_level,
            "has_tests": len(spec.acceptance_tests) > 0
        }
        
        # Current state (project context)
        state = {
            "project_loc": 9618,  # TODO: Get from project analyzer
            "existing_patterns": []
        }
        
        # Evaluate
        score = global_vf.evaluate(state, action)
        
        return score
    
    def select_best_spec(
        self, 
        candidates: List[Tuple[Specification, Cost]]
    ) -> Tuple[Specification, Cost, float]:
        """
        Select specification with highest value alignment that fits budget.
        
        Args:
            candidates: List of (spec, cost) tuples
        
        Returns:
            (best_spec, cost, alignment_score)
        """
        best_spec = None
        best_cost = None
        best_score = -1.0
        
        for spec, cost in candidates:
            if not cost.within_budget:
                continue
            
            score = self.evaluate_spec(spec)
            
            if score > best_score:
                best_score = score
                best_spec = spec
                best_cost = cost
        
        return best_spec, best_cost, best_score


class ClaudeCodeLoop:
    """
    Implements Context → Execute → Reflect pattern for agent execution.
    
    This is what makes UVUAS "reflective" - continuous alignment checking.
    """
    
    def __init__(self, global_value_memory: GlobalValueMemory, workspace_root: Path):
        self.global_value_memory = global_value_memory
        self.workspace_root = workspace_root
    
    def gather_context(self, intent: str, spec: Specification) -> Dict[str, Any]:
        """
        Phase 1: Gather context from workspace
        
        Looks for:
        - Similar existing files
        - Coding patterns
        - Style conventions
        - Related implementations
        """
        context = {
            "intent": intent,
            "specification": spec,
            "existing_files": [],
            "patterns": [],
            "style_guide": {}
        }
        
        # Scan workspace for relevant files
        if self.workspace_root.exists():
            # Simple keyword matching (can be enhanced with semantic search)
            keywords = self._extract_keywords(intent)
            
            for py_file in self.workspace_root.rglob("*.py"):
                if any(kw in py_file.name.lower() for kw in keywords):
                    try:
                        content = py_file.read_text()
                        context["existing_files"].append({
                            "path": str(py_file),
                            "content": content[:500]  # Preview
                        })
                    except:
                        pass
        
        return context
    
    def execute_with_alignment(
        self, 
        agent_id: str,
        task: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Tuple[Any, bool, List[str]]:
        """
        Phase 2: Execute task with continuous alignment checking
        
        Returns:
            (result, aligned, warnings)
        """
        # Execute task (actual implementation in agent)
        result = task  # Placeholder
        
        # Check alignment
        action = {
            "type": "task_execution",
            "agent_id": agent_id,
            "task_type": task.get("type"),
            "context": context
        }
        
        state = {
            "workspace_size": len(context.get("existing_files", [])),
            "project_loc": 9618
        }
        
        aligned, warnings = self.global_value_memory.validate_agent_action(
            agent_id=agent_id,
            action=action,
            state=state
        )
        
        return result, aligned, warnings
    
    def reflect_and_refine(
        self,
        result: Any,
        aligned: bool,
        warnings: List[str]
    ) -> Tuple[bool, Optional[str]]:
        """
        Phase 3: Reflect on result and decide if refinement needed
        
        Returns:
            (should_refine, refinement_instruction)
        """
        if aligned and not warnings:
            return False, None
        
        # Build refinement instruction
        refinement = "Please refine the result to address:\n"
        for warning in warnings:
            refinement += f"- {warning}\n"
        
        return True, refinement
    
    def _extract_keywords(self, intent: str) -> List[str]:
        """Extract keywords from intent for file matching"""
        # Simple word extraction
        words = re.findall(r'\b\w{4,}\b', intent.lower())
        return [w for w in words if w not in ['create', 'build', 'make', 'implement']]


class ThreeTierCoordinator:
    """
    Coordinates the complete flow: GVUFD → SPK → UVUAS with tight integration.
    
    Flow:
    1. Intent arrives
    2. GVUFD: Extract goals → Update global value function → Generate spec
    3. SPK: Generate spec variants → Evaluate by value alignment → Select best
    4. UVUAS: Context → Execute → Reflect (with alignment checking at each step)
    5. Feedback: If misaligned, loop back to GVUFD for re-specification
    """
    
    def __init__(
        self,
        policy: Policy,
        global_value_memory: GlobalValueMemory,
        workspace_root: Path
    ):
        self.policy = policy
        self.global_value_memory = global_value_memory
        self.workspace_root = workspace_root
        
        # Initialize tier components
        self.intent_extractor = IntentGoalExtractor()
        self.spec_generator = SpecificationGenerator()
        self.spec_evaluator = SpecEvaluator(global_value_memory)
        self.pricing_kernel = PricingKernel()
        self.claude_loop = ClaudeCodeLoop(global_value_memory, workspace_root)
        
        # Register coordinator with global value function
        self.global_value_memory.register_agent(
            agent_id="uvuas_coordinator",
            agent_role="coordination",
            local_goals=["coordination", "alignment", "integration"]
        )
    
    def coordinate(self, intent: str) -> Dict[str, Any]:
        """
        Execute coordinated 3-tier flow.
        
        Returns:
            Coordination result with spec, cost, alignment, execution results
        """
        result = {
            "intent": intent,
            "goals_extracted": None,
            "spec": None,
            "spec_candidates": [],
            "selected_spec": None,
            "cost": None,
            "alignment_score": 0.0,
            "execution_result": None,
            "coordination_log": []
        }
        
        # ====================================================================
        # TIER 1: GVUFD - Intent → Goals + Spec
        # ====================================================================
        
        self._log(result, "TIER 1: GVUFD - Extracting goals from intent")
        
        # Extract goals from intent
        intent_goals = self.intent_extractor.extract(intent)
        result["goals_extracted"] = intent_goals
        
        self._log(result, f"Extracted goals: {intent_goals.explicit_goals}")
        self._log(result, f"Optimization target: {intent_goals.optimization_target}")
        
        # Update global value function with intent-derived goals
        if intent_goals.implied_goals:
            for goal_type, new_weight in intent_goals.implied_goals.items():
                self.global_value_memory.update_global_goal(goal_type, new_weight)
                self._log(result, f"Updated {goal_type.value} weight to {new_weight}")
        
        # Update optimization target
        global_vf = self.global_value_memory.get_global_value_function()
        global_vf.optimization_target = intent_goals.optimization_target
        self._log(result, f"Set optimization target: {intent_goals.optimization_target}")
        
        # Generate base specification
        base_spec = self.spec_generator.generate(intent, self.policy)
        result["spec"] = base_spec
        
        # ====================================================================
        # TIER 2: SPK - Spec Variants → Value-Aligned Selection
        # ====================================================================
        
        self._log(result, "TIER 2: SPK - Evaluating specification candidates")
        
        # Generate spec variants (base + alternatives)
        spec_candidates = []
        
        # Candidate 1: Base spec
        base_cost = self.pricing_kernel.price(base_spec, self.policy)
        spec_candidates.append((base_spec, base_cost))
        self._log(result, f"Base spec: {base_cost.total} cost, budget OK: {base_cost.within_budget}")
        
        # Candidate 2: Simpler variant (if base is complex)
        if base_spec.budgets.max_loc_delta > 100:
            simple_spec = self._create_simpler_variant(base_spec)
            simple_cost = self.pricing_kernel.price(simple_spec, self.policy)
            spec_candidates.append((simple_spec, simple_cost))
            self._log(result, f"Simple variant: {simple_cost.total} cost")
        
        # Candidate 3: More robust variant
        robust_spec = self._create_robust_variant(base_spec)
        robust_cost = self.pricing_kernel.price(robust_spec, self.policy)
        spec_candidates.append((robust_spec, robust_cost))
        self._log(result, f"Robust variant: {robust_cost.total} cost")
        
        result["spec_candidates"] = spec_candidates
        
        # Evaluate candidates by value alignment
        selected_spec, selected_cost, alignment_score = self.spec_evaluator.select_best_spec(
            spec_candidates
        )
        
        if selected_spec is None:
            self._log(result, "ERROR: No spec candidate fits budget")
            result["error"] = "All spec candidates exceed budget"
            return result
        
        result["selected_spec"] = selected_spec
        result["cost"] = selected_cost
        result["alignment_score"] = alignment_score
        
        self._log(result, f"Selected spec with alignment score: {alignment_score:.2f}")
        
        # ====================================================================
        # TIER 3: UVUAS - Claude Code Loop (Context → Execute → Reflect)
        # ====================================================================
        
        self._log(result, "TIER 3: UVUAS - Executing with Claude Code loop")
        
        # Phase 1: Gather context
        context = self.claude_loop.gather_context(intent, selected_spec)
        self._log(result, f"Context: Found {len(context['existing_files'])} relevant files")
        
        # Phase 2: Execute with alignment checking
        task = {
            "type": "code_generation",
            "spec": selected_spec,
            "goals": intent_goals.explicit_goals
        }
        
        execution_result, aligned, warnings = self.claude_loop.execute_with_alignment(
            agent_id="uvuas_coordinator",
            task=task,
            context=context
        )
        
        result["execution_result"] = execution_result
        result["aligned"] = aligned
        result["warnings"] = warnings
        
        if warnings:
            self._log(result, f"Warnings: {', '.join(warnings)}")
        
        # Phase 3: Reflect and decide if refinement needed
        should_refine, refinement_instruction = self.claude_loop.reflect_and_refine(
            execution_result, aligned, warnings
        )
        
        if should_refine:
            self._log(result, f"Refinement needed: {refinement_instruction}")
            result["refinement_needed"] = True
            result["refinement_instruction"] = refinement_instruction
        else:
            self._log(result, "Execution aligned with global goals")
        
        return result
    
    def _create_simpler_variant(self, base_spec: Specification) -> Specification:
        """Create a simpler variant of the specification"""
        # Reduce LOC estimate by 30%
        simple_budget = SpecificationBudget(
            max_loc_delta=int(base_spec.budgets.max_loc_delta * 0.7),
            max_new_files=base_spec.budgets.max_new_files,
            max_new_dependencies=max(0, base_spec.budgets.max_new_dependencies - 1),
            max_new_abstractions=max(1, base_spec.budgets.max_new_abstractions - 1),
            max_cyclomatic_complexity=base_spec.budgets.max_cyclomatic_complexity
        )
        
        return Specification(
            intent=base_spec.intent + " (simplified)",
            success_criteria=base_spec.success_criteria[:3],  # Fewer criteria
            budgets=simple_budget,
            risk_level="low",
            dependencies_needed=base_spec.dependencies_needed[:1] if base_spec.dependencies_needed else [],  # Fewer deps
            forbidden_patterns=base_spec.forbidden_patterns,
            acceptance_tests=base_spec.acceptance_tests[:2]  # Fewer tests
        )
    
    def _create_robust_variant(self, base_spec: Specification) -> Specification:
        """Create a more robust variant with better quality"""
        # Increase LOC estimate by 20% for better error handling
        robust_budget = SpecificationBudget(
            max_loc_delta=int(base_spec.budgets.max_loc_delta * 1.2),
            max_new_files=base_spec.budgets.max_new_files,
            max_new_dependencies=base_spec.budgets.max_new_dependencies,
            max_new_abstractions=base_spec.budgets.max_new_abstractions + 1,
            max_cyclomatic_complexity=base_spec.budgets.max_cyclomatic_complexity
        )
        
        # Add quality-focused success criteria
        enhanced_criteria = base_spec.success_criteria + [
            "Has comprehensive error handling",
            "Includes type hints",
            "Has docstrings"
        ]
        
        return Specification(
            intent=base_spec.intent + " (production-ready)",
            success_criteria=enhanced_criteria,
            budgets=robust_budget,
            risk_level="medium",
            dependencies_needed=base_spec.dependencies_needed,
            forbidden_patterns=base_spec.forbidden_patterns,
            acceptance_tests=base_spec.acceptance_tests + [
                AcceptanceTest(
                    name="error_handling_test",
                    description="Verify error handling for edge cases and invalid inputs",
                    test_type="integration",
                    priority="high"
                )
            ]
        )
    
    def _log(self, result: Dict[str, Any], message: str):
        """Add message to coordination log"""
        result["coordination_log"].append(message)
        print(f"[3-TIER] {message}")
