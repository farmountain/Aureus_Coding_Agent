"""
GVUFD (Tier 1) - Global Value Utility Function Designer.

Converts natural language intent into bounded specifications with:
- Success criteria
- Budget allocation
- Risk assessment
- Forbidden patterns
- Acceptance tests

Phase 1: Rule-based generation (no LLM required for MVP)
Phase 2+: LLM-enhanced with learning
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Dict, Any
import re

from src.interfaces import (
    Policy, Specification, SpecificationBudget,
    AcceptanceTest, Dependency
)


# ============================================================================
# Project Analysis
# ============================================================================

@dataclass
class ProjectProfile:
    """Profile of a project for intelligent policy generation."""
    
    language: str = "unknown"
    project_type: str = "unknown"
    current_loc: int = 0
    current_files: int = 0
    current_modules: int = 0
    dependencies: int = 0
    has_tests: bool = False
    architecture_style: str = "unknown"


class ProjectAnalyzer:
    """
    Analyzes project structure to generate intelligent defaults.
    
    Phase 1: Simple file-based detection
    Phase 2+: AST analysis, git history, pattern detection
    """
    
    def analyze(self, project_root: Path) -> ProjectProfile:
        """
        Analyze project and return profile.
        
        Args:
            project_root: Path to project root
        
        Returns:
            ProjectProfile with detected characteristics
        """
        profile = ProjectProfile()
        
        if not project_root.exists():
            return profile
        
        # Detect language
        profile.language = self._detect_language(project_root)
        
        # Count files and LOC
        profile.current_files = self._count_files(project_root, profile.language)
        profile.current_loc = self._count_loc(project_root, profile.language)
        
        # Detect tests
        profile.has_tests = self._has_tests(project_root)
        
        # Detect project type
        profile.project_type = self._detect_project_type(project_root)
        
        return profile
    
    def _detect_language(self, root: Path) -> str:
        """Detect primary programming language."""
        # Check for language-specific files
        if list(root.glob("**/*.py")):
            return "python"
        elif list(root.glob("**/*.ts")) or list(root.glob("**/*.js")):
            return "typescript"
        elif list(root.glob("**/*.rs")):
            return "rust"
        return "unknown"
    
    def _count_files(self, root: Path, language: str) -> int:
        """Count source files."""
        extensions = {
            "python": "*.py",
            "typescript": "*.ts",
            "javascript": "*.js",
            "rust": "*.rs"
        }
        
        pattern = extensions.get(language, "*.*")
        return len(list(root.glob(f"**/{pattern}")))
    
    def _count_loc(self, root: Path, language: str) -> int:
        """Count lines of code (rough estimate)."""
        extensions = {
            "python": "*.py",
            "typescript": "*.ts",
            "javascript": "*.js",
            "rust": "*.rs"
        }
        
        pattern = extensions.get(language, "*.*")
        total_lines = 0
        
        for file in root.glob(f"**/{pattern}"):
            try:
                total_lines += len(file.read_text(encoding='utf-8').splitlines())
            except:
                pass
        
        return total_lines
    
    def _has_tests(self, root: Path) -> bool:
        """Check if project has tests."""
        test_indicators = ["test", "tests", "spec", "__tests__"]
        return any((root / name).exists() for name in test_indicators)
    
    def _detect_project_type(self, root: Path) -> str:
        """Detect project type from structure."""
        # Check for web framework indicators
        if (root / "app.py").exists() or (root / "wsgi.py").exists():
            return "api"
        if (root / "package.json").exists():
            return "web"
        if (root / "setup.py").exists() or (root / "pyproject.toml").exists():
            return "library"
        
        # Default
        return "new" if self._count_files(root, "python") == 0 else "unknown"


# ============================================================================
# Budget Allocation
# ============================================================================

class BudgetAllocator:
    """
    Intelligently allocate budgets for specifications.
    
    Phase 1: Rule-based allocation
    Phase 2+: Learned from historical data
    """
    
    COMPLEXITY_MULTIPLIERS = {
        "trivial": 0.05,   # Helper functions, small changes
        "low": 0.15,       # Single feature, well-defined
        "medium": 0.30,    # Multiple files, moderate complexity
        "high": 0.50,      # System-wide changes, high complexity
        "critical": 0.75   # Major refactor, architectural changes
    }
    
    def __init__(self, policy_budget):
        self.policy_budget = policy_budget
    
    def allocate(self, intent: str, complexity: str = "medium") -> SpecificationBudget:
        """
        Allocate budget for a specification.
        
        Args:
            intent: User intent string
            complexity: Estimated complexity level
        
        Returns:
            SpecificationBudget with allocated limits
        """
        # Get multiplier
        multiplier = self.COMPLEXITY_MULTIPLIERS.get(complexity, 0.30)
        
        # Allocate as percentage of policy budget
        return SpecificationBudget(
            max_loc_delta=int(self.policy_budget.max_loc * multiplier),
            max_new_files=max(1, int(self.policy_budget.max_files * multiplier)),
            max_new_dependencies=max(0, int(self.policy_budget.max_dependencies * multiplier)),
            max_new_abstractions=5,
            max_cyclomatic_complexity=10
        )
    
    def estimate_complexity(self, intent: str) -> str:
        """
        Estimate complexity from intent string.
        
        Phase 1: Simple keyword matching
        Phase 2+: LLM-based estimation
        """
        intent_lower = intent.lower()
        
        # High complexity indicators
        if any(word in intent_lower for word in [
            "authentication", "payment", "security", "oauth", "database migration",
            "refactor system", "redesign", "architecture"
        ]):
            return "high"
        
        # Medium complexity indicators
        if any(word in intent_lower for word in [
            "api", "endpoint", "feature", "module", "integration", "service"
        ]):
            return "medium"
        
        # Low complexity indicators
        if any(word in intent_lower for word in [
            "function", "helper", "utility", "format", "parse", "validate"
        ]):
            return "low"
        
        # Default
        return "medium"


# ============================================================================
# Specification Generator
# ============================================================================

class SpecificationGenerator:
    """
    Main GVUFD component - generates specifications from intent.
    
    Phase 1: Rule-based generation
    Phase 2+: LLM-enhanced with learning
    """
    
    def __init__(self):
        self.project_analyzer = ProjectAnalyzer()
    
    def generate(
        self,
        intent: str,
        policy: Policy,
        project_root: Optional[Path] = None
    ) -> Specification:
        """
        Generate specification from user intent.
        
        Args:
            intent: Natural language intent
            policy: Project policy with budgets and constraints
            project_root: Optional project root for context
        
        Returns:
            Specification with success criteria and budgets
        """
        # Allocate budget
        allocator = BudgetAllocator(policy.budgets)
        complexity = allocator.estimate_complexity(intent)
        spec_budget = allocator.allocate(intent, complexity)
        
        # Assess risk
        risk_level = self._assess_risk(intent)
        
        # Generate success criteria
        success_criteria = self._generate_success_criteria(intent)
        
        # Extract forbidden patterns from policy
        forbidden_patterns = [p.name for p in policy.forbidden_patterns]
        
        # Generate security considerations
        security_considerations = self._generate_security_considerations(intent)
        
        # Create specification
        spec = Specification(
            intent=intent,
            success_criteria=success_criteria,
            budgets=spec_budget,
            risk_level=risk_level,
            forbidden_patterns=forbidden_patterns,
            security_considerations=security_considerations,
            acceptance_tests=self._generate_acceptance_tests(intent)
        )
        
        return spec
    
    def _assess_risk(self, intent: str) -> str:
        """
        Assess risk level of intent.
        
        Returns: "low", "medium", "high", or "critical"
        """
        intent_lower = intent.lower()
        
        # Critical risk indicators
        if any(word in intent_lower for word in [
            "payment", "credit card", "password reset", "admin", "sudo"
        ]):
            return "critical"
        
        # High risk indicators
        if any(word in intent_lower for word in [
            "authentication", "authorization", "security", "encryption",
            "database", "migration", "production"
        ]):
            return "high"
        
        # Medium risk indicators
        if any(word in intent_lower for word in [
            "api", "endpoint", "user data", "storage", "cache"
        ]):
            return "medium"
        
        # Default low risk
        return "low"
    
    def _generate_success_criteria(self, intent: str) -> List[str]:
        """
        Generate testable success criteria from intent.
        
        Phase 1: Template-based generation
        Phase 2+: LLM-generated
        """
        criteria = []
        
        # Add basic criterion
        criteria.append(f"Implement: {intent}")
        
        # Add type-specific criteria based on keywords
        intent_lower = intent.lower()
        
        if "authentication" in intent_lower or "login" in intent_lower:
            criteria.extend([
                "User can authenticate with valid credentials",
                "Invalid credentials are rejected",
                "Password is securely hashed"
            ])
        
        if "api" in intent_lower or "endpoint" in intent_lower:
            criteria.extend([
                "Endpoint returns correct status codes",
                "Response format matches specification",
                "Error cases are handled properly"
            ])
        
        if "test" in intent_lower:
            criteria.extend([
                "Tests cover happy path",
                "Tests cover error cases",
                "All tests pass"
            ])
        
        # Default criteria if none matched
        if len(criteria) == 1:
            criteria.extend([
                "Implementation is complete and functional",
                "Code follows project conventions"
            ])
        
        return criteria
    
    def _generate_security_considerations(self, intent: str) -> List[str]:
        """Generate security considerations if needed."""
        considerations = []
        intent_lower = intent.lower()
        
        if "password" in intent_lower:
            considerations.append("Use bcrypt or argon2 for password hashing")
        
        if "payment" in intent_lower or "credit card" in intent_lower:
            considerations.append("Use PCI-DSS compliant payment processor")
            considerations.append("Never store raw credit card numbers")
            considerations.append("Implement tokenization for payment data")
        
        if "api" in intent_lower or "endpoint" in intent_lower:
            considerations.append("Validate all input parameters")
            considerations.append("Implement rate limiting")
        
        if "database" in intent_lower or "sql" in intent_lower:
            considerations.append("Use parameterized queries to prevent SQL injection")
        
        if "authentication" in intent_lower:
            considerations.append("Implement secure session management")
            considerations.append("Use HTTPS for authentication endpoints")
        
        return considerations
    
    def _generate_acceptance_tests(self, intent: str) -> List[AcceptanceTest]:
        """Generate acceptance test templates."""
        tests = []
        
        # Always add basic test
        tests.append(AcceptanceTest(
            name=f"test_{intent[:30].replace(' ', '_').lower()}",
            description=f"Verify that {intent} works correctly",
            test_type="integration",
            priority="high"
        ))
        
        return tests
