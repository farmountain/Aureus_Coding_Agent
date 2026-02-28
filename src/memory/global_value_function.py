"""
Global Value Function System

Maintains the global value function that governs all agent decisions.
Ensures local agent value functions align with global goals and don't drift.

Key concepts:
- Global Value Function: Project-level objectives and constraints
- Local Value Functions: Agent-specific utility calculations
- Alignment Checking: Validates local decisions against global goals
- Drift Detection: Monitors and corrects misalignment
"""

import json
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum


class GoalType(Enum):
    """Types of goals in the global value function"""
    CODE_QUALITY = "code_quality"
    MAINTAINABILITY = "maintainability"
    PERFORMANCE = "performance"
    SECURITY = "security"
    TESTABILITY = "testability"
    SIMPLICITY = "simplicity"
    CONSISTENCY = "consistency"


@dataclass
class GlobalGoal:
    """A goal in the global value function"""
    goal_type: GoalType
    weight: float  # 0.0 - 1.0
    threshold: float  # Minimum acceptable value
    description: str
    metrics: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "goal_type": self.goal_type.value,
            "weight": self.weight,
            "threshold": self.threshold,
            "description": self.description,
            "metrics": self.metrics
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GlobalGoal':
        data['goal_type'] = GoalType(data['goal_type'])
        return cls(**data)


@dataclass
class GlobalValueFunction:
    """
    The global value function that governs all agent decisions
    
    V_global(s, a) = Σ w_i * v_i(s, a)
    
    Where:
    - s: current state
    - a: proposed action
    - w_i: weight for goal i
    - v_i: value of action for goal i
    """
    
    version: str
    goals: List[GlobalGoal]
    constraints: Dict[str, Any]
    optimization_target: str  # "maximize_quality" | "minimize_cost" | "balance"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def evaluate(self, state: Dict[str, Any], action: Dict[str, Any]) -> float:
        """
        Evaluate an action against the global value function
        
        Returns:
            Global value score (0.0 - 1.0)
        """
        total_value = 0.0
        total_weight = 0.0
        
        for goal in self.goals:
            local_value = self._evaluate_goal(goal, state, action)
            total_value += goal.weight * local_value
            total_weight += goal.weight
        
        return total_value / total_weight if total_weight > 0 else 0.0
    
    def _evaluate_goal(self, goal: GlobalGoal, state: Dict[str, Any], action: Dict[str, Any]) -> float:
        """Evaluate action against a specific goal"""
        # Simple heuristics - can be enhanced with ML
        if goal.goal_type == GoalType.CODE_QUALITY:
            return self._evaluate_code_quality(action)
        elif goal.goal_type == GoalType.MAINTAINABILITY:
            return self._evaluate_maintainability(action)
        elif goal.goal_type == GoalType.SIMPLICITY:
            return self._evaluate_simplicity(action)
        elif goal.goal_type == GoalType.CONSISTENCY:
            return self._evaluate_consistency(action, state)
        else:
            return 0.5  # Neutral for unimplemented goals
    
    def _evaluate_code_quality(self, action: Dict[str, Any]) -> float:
        """Evaluate code quality of proposed action"""
        score = 1.0
        
        # Check for type hints
        code = action.get("code", "")
        if "->" not in code:
            score -= 0.2
        
        # Check for docstrings
        if '"""' not in code:
            score -= 0.2
        
        # Check for error handling
        if "try" not in code and "raise" not in code:
            score -= 0.1
        
        return max(0.0, score)
    
    def _evaluate_maintainability(self, action: Dict[str, Any]) -> float:
        """Evaluate maintainability"""
        score = 1.0
        code = action.get("code", "")
        lines = code.split('\n')
        
        # Penalize long files
        if len(lines) > 300:
            score -= 0.3
        
        # Penalize long functions (simple heuristic)
        max_function_lines = 0
        current_function_lines = 0
        for line in lines:
            if line.strip().startswith("def "):
                if current_function_lines > max_function_lines:
                    max_function_lines = current_function_lines
                current_function_lines = 0
            else:
                current_function_lines += 1
        
        if max_function_lines > 50:
            score -= 0.2
        
        return max(0.0, score)
    
    def _evaluate_simplicity(self, action: Dict[str, Any]) -> float:
        """Evaluate simplicity (fewer abstractions better)"""
        score = 1.0
        code = action.get("code", "")
        
        # Count classes
        class_count = code.count("class ")
        if class_count > 3:
            score -= 0.2
        
        # Count nested structures
        max_indent = max(len(line) - len(line.lstrip()) for line in code.split('\n'))
        if max_indent > 16:  # More than 4 levels
            score -= 0.2
        
        return max(0.0, score)
    
    def _evaluate_consistency(self, action: Dict[str, Any], state: Dict[str, Any]) -> float:
        """Evaluate consistency with existing code"""
        # Check if action follows patterns from existing code
        existing_patterns = state.get("patterns", [])
        action_patterns = action.get("patterns", [])
        
        if not existing_patterns:
            return 1.0
        
        overlap = len(set(existing_patterns) & set(action_patterns))
        total = len(set(existing_patterns) | set(action_patterns))
        
        return overlap / total if total > 0 else 0.5
    
    def check_threshold_violations(self, state: Dict[str, Any], action: Dict[str, Any]) -> List[str]:
        """Check if action violates any goal thresholds"""
        violations = []
        
        for goal in self.goals:
            local_value = self._evaluate_goal(goal, state, action)
            if local_value < goal.threshold:
                violations.append(
                    f"{goal.goal_type.value}: {local_value:.2f} < {goal.threshold:.2f} ({goal.description})"
                )
        
        return violations
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "goals": [g.to_dict() for g in self.goals],
            "constraints": self.constraints,
            "optimization_target": self.optimization_target,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GlobalValueFunction':
        data['goals'] = [GlobalGoal.from_dict(g) for g in data['goals']]
        return cls(**data)


@dataclass
class LocalValueFunction:
    """
    Local value function for a specific agent
    
    Must align with global value function
    """
    
    agent_id: str
    agent_role: str
    local_goals: List[str]
    alignment_score: float = 1.0
    last_validated: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def evaluate_local(self, action: Dict[str, Any]) -> float:
        """Evaluate action from local agent perspective"""
        # Agent-specific logic
        # For CodeGeneratorAgent: prioritize completeness
        # For TestWriterAgent: prioritize coverage
        # For RefactorAgent: prioritize simplicity
        return 0.8  # Placeholder
    
    def check_alignment(self, global_vf: GlobalValueFunction, state: Dict[str, Any], action: Dict[str, Any]) -> Tuple[bool, float, List[str]]:
        """
        Check if local decision aligns with global value function
        
        Returns:
            (aligned, alignment_score, drift_warnings)
        """
        global_score = global_vf.evaluate(state, action)
        local_score = self.evaluate_local(action)
        
        # Check if both agree (both high or both low)
        agreement = abs(global_score - local_score) < 0.3
        
        # Check threshold violations
        violations = global_vf.check_threshold_violations(state, action)
        
        # Calculate alignment score
        alignment = 1.0 - abs(global_score - local_score)
        self.alignment_score = alignment
        
        warnings = []
        if not agreement:
            warnings.append(f"Local/Global score mismatch: {local_score:.2f} vs {global_score:.2f}")
        
        if violations:
            warnings.extend(violations)
        
        aligned = agreement and len(violations) == 0
        
        return aligned, alignment, warnings


class GlobalValueMemory:
    """
    Enhanced memory system that maintains global value function
    and ensures all agent decisions align with it
    """
    
    def __init__(self, memory_file: Optional[Path] = None):
        self.memory_file = memory_file or Path(".aureus") / "global_value_memory.json"
        self.global_vf: Optional[GlobalValueFunction] = None
        self.agent_vfs: Dict[str, LocalValueFunction] = {}
        self.alignment_history: List[Dict[str, Any]] = []
        self.drift_events: List[Dict[str, Any]] = []
        self._load()
    
    def _load(self):
        """Load global value function and history"""
        if self.memory_file.exists():
            try:
                with open(self.memory_file, 'r') as f:
                    data = json.load(f)
                    if "global_value_function" in data:
                        self.global_vf = GlobalValueFunction.from_dict(data["global_value_function"])
                    self.alignment_history = data.get("alignment_history", [])
                    self.drift_events = data.get("drift_events", [])
            except Exception as e:
                print(f"Warning: Could not load global value memory: {e}")
                self._initialize_default()
        else:
            self._initialize_default()
    
    def _initialize_default(self):
        """Initialize default global value function"""
        self.global_vf = GlobalValueFunction(
            version="1.0",
            goals=[
                GlobalGoal(
                    goal_type=GoalType.CODE_QUALITY,
                    weight=0.3,
                    threshold=0.7,
                    description="Code must have type hints, docstrings, and error handling",
                    metrics=["type_hint_coverage", "docstring_coverage"]
                ),
                GlobalGoal(
                    goal_type=GoalType.MAINTAINABILITY,
                    weight=0.25,
                    threshold=0.6,
                    description="Code must be maintainable with reasonable complexity",
                    metrics=["cyclomatic_complexity", "lines_per_function"]
                ),
                GlobalGoal(
                    goal_type=GoalType.SIMPLICITY,
                    weight=0.2,
                    threshold=0.5,
                    description="Prefer simple solutions over complex ones",
                    metrics=["abstraction_count", "nesting_depth"]
                ),
                GlobalGoal(
                    goal_type=GoalType.CONSISTENCY,
                    weight=0.15,
                    threshold=0.6,
                    description="Follow existing codebase patterns",
                    metrics=["pattern_similarity"]
                ),
                GlobalGoal(
                    goal_type=GoalType.TESTABILITY,
                    weight=0.1,
                    threshold=0.5,
                    description="Code must be testable",
                    metrics=["test_coverage"]
                )
            ],
            constraints={
                "max_loc": 500,
                "max_complexity": 10,
                "min_test_coverage": 0.8
            },
            optimization_target="balance"
        )
    
    def _save(self):
        """Save global value function and history"""
        try:
            self.memory_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.memory_file, 'w') as f:
                json.dump({
                    "version": "1.0",
                    "last_updated": datetime.now().isoformat(),
                    "global_value_function": self.global_vf.to_dict() if self.global_vf else None,
                    "alignment_history": self.alignment_history[-100:],  # Keep last 100
                    "drift_events": self.drift_events[-50:]  # Keep last 50
                }, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save global value memory: {e}")
    
    def register_agent(self, agent_id: str, agent_role: str, local_goals: List[str]):
        """Register an agent with its local value function"""
        self.agent_vfs[agent_id] = LocalValueFunction(
            agent_id=agent_id,
            agent_role=agent_role,
            local_goals=local_goals
        )
    
    def validate_agent_action(
        self,
        agent_id: str,
        action: Dict[str, Any],
        state: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        Validate agent action against global value function
        
        Returns:
            (approved, warnings)
        """
        if not self.global_vf:
            return True, []
        
        agent_vf = self.agent_vfs.get(agent_id)
        if not agent_vf:
            return True, ["Agent not registered"]
        
        # Check alignment
        aligned, alignment_score, warnings = agent_vf.check_alignment(
            self.global_vf, state, action
        )
        
        # Record alignment
        self.alignment_history.append({
            "timestamp": datetime.now().isoformat(),
            "agent_id": agent_id,
            "action": action.get("type", "unknown"),
            "aligned": aligned,
            "alignment_score": alignment_score,
            "warnings": warnings
        })
        
        # Detect drift
        if alignment_score < 0.5:
            self.drift_events.append({
                "timestamp": datetime.now().isoformat(),
                "agent_id": agent_id,
                "alignment_score": alignment_score,
                "warnings": warnings
            })
            warnings.insert(0, f"⚠️ DRIFT DETECTED: Alignment score {alignment_score:.2f} < 0.5")
        
        self._save()
        
        return aligned, warnings
    
    def get_global_value_function(self) -> GlobalValueFunction:
        """Get the global value function"""
        if not self.global_vf:
            self._initialize_default()
        return self.global_vf
    
    def update_global_goal(self, goal_type: GoalType, weight: float):
        """Update weight of a global goal"""
        if not self.global_vf:
            return
        
        for goal in self.global_vf.goals:
            if goal.goal_type == goal_type:
                goal.weight = weight
                self.global_vf.updated_at = datetime.now().isoformat()
                self._save()
                break
    
    def get_alignment_statistics(self) -> Dict[str, Any]:
        """Get alignment statistics"""
        if not self.alignment_history:
            return {}
        
        total = len(self.alignment_history)
        aligned = sum(1 for h in self.alignment_history if h["aligned"])
        avg_score = sum(h["alignment_score"] for h in self.alignment_history) / total
        
        return {
            "total_actions": total,
            "aligned_actions": aligned,
            "alignment_rate": aligned / total,
            "avg_alignment_score": avg_score,
            "drift_events": len(self.drift_events),
            "last_drift": self.drift_events[-1] if self.drift_events else None
        }
