"""
Core AUREUS interfaces and data models.

This module defines the foundational data structures and protocols
for the 3-tier architecture:
- Policy: Governance configuration
- Specification: GVUFD output (intent -> formal spec)
- Cost: SPK output (complexity pricing)
- Agent/Tool: Execution protocols
"""

from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional, Any, Protocol
from abc import ABC, abstractmethod
import re


# ============================================================================
# Exceptions
# ============================================================================

class ValidationError(Exception):
    """Raised when data validation fails."""
    
    def __init__(self, message: str, field: Optional[str] = None):
        self.field = field
        if field:
            super().__init__(f"Validation error in '{field}': {message}")
        else:
            super().__init__(f"Validation error: {message}")


# ============================================================================
# Budget Models
# ============================================================================

@dataclass
class Budget:
    """
    Architectural complexity budgets for a project.
    
    Enforces hard limits on:
    - Lines of code
    - Number of modules
    - Number of files
    - External dependencies
    - Class/function size
    - Inheritance depth
    """
    
    # Required fields
    max_loc: int
    max_modules: int
    max_files: int
    max_dependencies: int
    
    # Optional fields with defaults
    max_class_loc: int = 500
    max_function_loc: int = 50
    max_inheritance_depth: int = 2
    
    def __post_init__(self):
        """Validate budget constraints."""
        self._validate()
    
    def _validate(self):
        """Ensure all budget values are positive."""
        for field_name in ['max_loc', 'max_modules', 'max_files', 'max_dependencies',
                           'max_class_loc', 'max_function_loc', 'max_inheritance_depth']:
            value = getattr(self, field_name)
            if value <= 0:
                raise ValidationError(f"{field_name} must be positive", field=field_name)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Budget':
        """Deserialize from dictionary."""
        return cls(**data)


@dataclass
class SpecificationBudget:
    """
    Budgets for a specific implementation task (GVUFD output).
    
    Defines resource limits for a single feature/task:
    - Delta LOC (new lines added)
    - New files created
    - New dependencies added
    - New abstractions (classes/interfaces)
    """
    
    max_loc_delta: int
    max_new_files: int
    max_new_dependencies: int
    max_new_abstractions: int = 5
    max_cyclomatic_complexity: int = 10
    
    def __post_init__(self):
        """Validate specification budget."""
        for field_name in ['max_loc_delta', 'max_new_files', 'max_new_dependencies',
                           'max_new_abstractions', 'max_cyclomatic_complexity']:
            value = getattr(self, field_name)
            if value < 0:
                raise ValidationError(f"{field_name} cannot be negative", field=field_name)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SpecificationBudget':
        """Deserialize from dictionary."""
        return cls(**data)


# ============================================================================
# Pattern Models
# ============================================================================

@dataclass
class ForbiddenPattern:
    """
    A forbidden code pattern with detection rule.
    
    Patterns are governance constraints that trigger errors/warnings
    when detected during code analysis.
    """
    
    name: str
    description: str
    rule: str
    severity: str = "error"
    auto_fix: bool = False
    
    def __post_init__(self):
        """Validate pattern definition."""
        valid_severities = ["error", "warning", "info"]
        if self.severity not in valid_severities:
            raise ValidationError(
                f"severity must be one of {valid_severities}",
                field="severity"
            )
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ForbiddenPattern':
        """Deserialize from dictionary."""
        return cls(**data)


# ============================================================================
# Policy Model (Tier 0: Configuration)
# ============================================================================

@dataclass
class Policy:
    """
    AUREUS governance policy configuration.
    
    Defines project-level constraints:
    - Version and metadata
    - Complexity budgets
    - Forbidden patterns
    - Tool permissions
    - Cost thresholds
    """
    
    # Required fields
    version: str
    project_name: str
    project_root: Path
    budgets: Budget
    permissions: Dict[str, Any]
    
    # Optional fields
    project_language: Optional[str] = None
    project_type: Optional[str] = None
    forbidden_patterns: List[ForbiddenPattern] = field(default_factory=list)
    cost_thresholds: Dict[str, float] = field(default_factory=lambda: {
        "warning": 100.0,
        "rejection": 500.0,
        "session_limit": 2000.0
    })
    simplification_config: Dict[str, Any] = field(default_factory=lambda: {
        "trigger_at_budget_percent": 85,
        "mandatory": True,
        "target_reduction": 0.2
    })
    
    def __post_init__(self):
        """Validate policy configuration."""
        self._validate()
    
    def _validate(self):
        """Ensure policy is valid."""
        # Validate version format (X.Y)
        if not re.match(r'^\d+\.\d+$', self.version):
            raise ValidationError(
                "version must match format X.Y (e.g., '1.0')",
                field="version"
            )
        
        # Validate project_root is a Path
        if not isinstance(self.project_root, Path):
            raise ValidationError(
                "project_root must be a Path object",
                field="project_root"
            )
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        data = {
            "version": self.version,
            "project": {
                "name": self.project_name,
                "root": str(self.project_root),
                "language": self.project_language,
                "type": self.project_type
            },
            "budgets": self.budgets.to_dict(),
            "forbidden_patterns": [p.to_dict() for p in self.forbidden_patterns],
            "permissions": self.permissions,
            "cost_thresholds": self.cost_thresholds,
            "simplification": self.simplification_config
        }
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Policy':
        """Deserialize from dictionary."""
        project = data.get("project", {})
        return cls(
            version=data["version"],
            project_name=project["name"],
            project_root=Path(project["root"]),
            project_language=project.get("language"),
            project_type=project.get("type"),
            budgets=Budget.from_dict(data["budgets"]),
            forbidden_patterns=[
                ForbiddenPattern.from_dict(p)
                for p in data.get("forbidden_patterns", [])
            ],
            permissions=data["permissions"],
            cost_thresholds=data.get("cost_thresholds", {}),
            simplification_config=data.get("simplification", {})
        )


# ============================================================================
# Specification Model (Tier 1: GVUFD Output)
# ============================================================================

@dataclass
class AcceptanceTest:
    """A test case to verify specification success."""
    
    name: str
    description: str
    test_type: str = "integration"  # unit | integration | e2e
    priority: str = "high"  # critical | high | medium | low
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AcceptanceTest':
        """Deserialize from dictionary."""
        return cls(**data)


@dataclass
class Dependency:
    """A required external dependency."""
    
    name: str
    justification: str
    version: Optional[str] = None
    alternatives_considered: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Dependency':
        """Deserialize from dictionary."""
        return cls(**data)


@dataclass
class Specification:
    """
    Formal specification generated by GVUFD (Tier 1).
    
    Transforms user intent into:
    - Success criteria (testable conditions)
    - Resource budgets (complexity limits)
    - Constraints (forbidden patterns, architecture)
    - Tests (acceptance criteria)
    - Risk assessment
    """
    
    # Required fields
    intent: str
    success_criteria: List[str]
    budgets: SpecificationBudget
    risk_level: str  # low | medium | high | critical
    
    # Optional fields
    forbidden_patterns: List[str] = field(default_factory=list)
    acceptance_tests: List[AcceptanceTest] = field(default_factory=list)
    security_considerations: List[str] = field(default_factory=list)
    architectural_constraints: List[str] = field(default_factory=list)
    dependencies_needed: List[Dependency] = field(default_factory=list)
    estimated_cost: Optional[Dict[str, float]] = None
    
    def __post_init__(self):
        """Validate specification."""
        self._validate()
    
    def _validate(self):
        """Ensure specification is valid."""
        # Must have at least one success criterion
        if not self.success_criteria or len(self.success_criteria) == 0:
            raise ValidationError(
                "Must have at least one success criterion",
                field="success_criteria"
            )
        
        # Validate risk level
        valid_risk_levels = ["low", "medium", "high", "critical"]
        if self.risk_level not in valid_risk_levels:
            raise ValidationError(
                f"risk_level must be one of {valid_risk_levels}",
                field="risk_level"
            )
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "intent": self.intent,
            "success_criteria": self.success_criteria,
            "budgets": self.budgets.to_dict(),
            "risk_level": self.risk_level,
            "forbidden_patterns": self.forbidden_patterns,
            "acceptance_tests": [t.to_dict() for t in self.acceptance_tests],
            "security_considerations": self.security_considerations,
            "architectural_constraints": self.architectural_constraints,
            "dependencies_needed": [d.to_dict() for d in self.dependencies_needed],
            "estimated_cost": self.estimated_cost
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Specification':
        """Deserialize from dictionary."""
        return cls(
            intent=data["intent"],
            success_criteria=data["success_criteria"],
            budgets=SpecificationBudget.from_dict(data["budgets"]),
            risk_level=data["risk_level"],
            forbidden_patterns=data.get("forbidden_patterns", []),
            acceptance_tests=[
                AcceptanceTest.from_dict(t)
                for t in data.get("acceptance_tests", [])
            ],
            security_considerations=data.get("security_considerations", []),
            architectural_constraints=data.get("architectural_constraints", []),
            dependencies_needed=[
                Dependency.from_dict(d)
                for d in data.get("dependencies_needed", [])
            ],
            estimated_cost=data.get("estimated_cost")
        )


# ============================================================================
# Cost Model (Tier 2: SPK Output)
# ============================================================================

@dataclass
class Cost:
    """
    Complexity cost calculation from SPK (Tier 2).
    
    Breaks down total cost into components:
    - LOC: Lines of code cost
    - Dependencies: External library cost
    - Abstractions: Class/interface cost
    - Security: Risk-adjusted cost
    
    SPK enhancements (Phase 1):
    - Budget enforcement results
    - Alternative suggestions when over budget
    """
    
    # Core cost metrics
    loc: float
    dependencies: float
    abstractions: float
    total: float
    security: float = 0.0
    
    # SPK budget enforcement (Phase 1 additions)
    within_budget: bool = True
    budget_status: str = "approved"  # approved | advisory | warning | rejected
    alternatives: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Cost':
        """Deserialize from dictionary."""
        return cls(**data)


class CostModel(ABC):
    """
    Abstract base class for cost calculation (Tier 2: SPK).
    
    Implementations calculate complexity cost for specifications,
    enabling budget enforcement and alternative comparison.
    """
    
    @abstractmethod
    def calculate(self, spec: Specification, context: Dict[str, Any]) -> Cost:
        """
        Calculate complexity cost for a specification.
        
        Args:
            spec: Specification to price
            context: Project context (current state, history)
        
        Returns:
            Cost breakdown with total
        """
        pass


# ============================================================================
# Agent Protocol (Tier 3: UVUAS)
# ============================================================================

class Agent(Protocol):
    """
    Agent protocol for UVUAS execution layer (Tier 3).
    
    Agents implement specific roles:
    - Planner: Decomposes spec into tasks
    - Builder: Generates code
    - Tester: Verifies implementation
    - Critic: Detects violations
    - Reflexion: Simplifies code
    """
    
    name: str
    
    def execute(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute agent's role on a task.
        
        Args:
            task: Task specification
            context: Execution context
        
        Returns:
            Result with status and artifacts
        """
        ...


# ============================================================================
# Tool Protocol (Infrastructure)
# ============================================================================

class Tool(Protocol):
    """
    Tool protocol for controlled operations.
    
    Tools provide governed access to:
    - File system (read/write/delete)
    - Shell execution
    - Git operations
    - Web fetch
    """
    
    name: str
    permission_required: str
    
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute tool operation with permission check.
        
        Args:
            params: Operation parameters
        
        Returns:
            Result with status and output
        """
        ...
