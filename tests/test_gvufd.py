"""
Tests for GVUFD (Tier 1) - Specification Generator.
TDD: Tests written before implementation.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch


class TestSpecificationGenerator:
    """Test GVUFD specification generation from intent."""
    
    def test_generate_spec_from_simple_intent(self):
        """GVUFD should generate specification from simple intent."""
        from src.governance.gvufd import SpecificationGenerator
        from src.interfaces import Policy, Budget, Specification
        
        # Setup
        budget = Budget(max_loc=10000, max_modules=8, max_files=30, max_dependencies=20)
        policy = Policy(
            version="1.0",
            project_name="test",
            project_root=Path("/path"),
            budgets=budget,
            permissions={}
        )
        
        generator = SpecificationGenerator()
        spec = generator.generate(
            intent="Add user authentication with email/password",
            policy=policy
        )
        
        # Verify specification structure
        assert isinstance(spec, Specification)
        assert spec.intent == "Add user authentication with email/password"
        assert len(spec.success_criteria) > 0
        assert spec.risk_level in ["low", "medium", "high", "critical"]
        assert spec.budgets.max_loc_delta > 0
    
    def test_generate_spec_with_security_intent(self):
        """GVUFD should detect security-related intents and set high risk."""
        from src.governance.gvufd import SpecificationGenerator
        from src.interfaces import Policy, Budget
        
        budget = Budget(max_loc=10000, max_modules=8, max_files=30, max_dependencies=20)
        policy = Policy(
            version="1.0",
            project_name="test",
            project_root=Path("/path"),
            budgets=budget,
            permissions={}
        )
        
        generator = SpecificationGenerator()
        spec = generator.generate(
            intent="Implement payment processing with credit cards",
            policy=policy
        )
        
        # Security-sensitive features should have high risk
        assert spec.risk_level in ["high", "critical"]
        assert len(spec.security_considerations) > 0
    
    def test_generate_allocates_budget(self):
        """GVUFD should allocate appropriate budgets from policy."""
        from src.governance.gvufd import SpecificationGenerator
        from src.interfaces import Policy, Budget
        
        budget = Budget(max_loc=5000, max_modules=8, max_files=30, max_dependencies=20)
        policy = Policy(
            version="1.0",
            project_name="test",
            project_root=Path("/path"),
            budgets=budget,
            permissions={}
        )
        
        generator = SpecificationGenerator()
        spec = generator.generate(intent="Add logging module", policy=policy)
        
        # Budget should be allocated but within policy limits
        assert spec.budgets.max_loc_delta <= budget.max_loc
        assert spec.budgets.max_new_files <= budget.max_files
    
    def test_generate_creates_success_criteria(self):
        """GVUFD should generate testable success criteria."""
        from src.governance.gvufd import SpecificationGenerator
        from src.interfaces import Policy, Budget
        
        budget = Budget(max_loc=10000, max_modules=8, max_files=30, max_dependencies=20)
        policy = Policy(
            version="1.0",
            project_name="test",
            project_root=Path("/path"),
            budgets=budget,
            permissions={}
        )
        
        generator = SpecificationGenerator()
        spec = generator.generate(
            intent="Add user registration endpoint",
            policy=policy
        )
        
        # Should have multiple success criteria
        assert len(spec.success_criteria) >= 2
        # Should be specific and testable
        for criterion in spec.success_criteria:
            assert len(criterion) > 10  # Not trivial
    
    def test_generate_respects_forbidden_patterns(self):
        """GVUFD should include policy forbidden patterns in spec."""
        from src.governance.gvufd import SpecificationGenerator
        from src.interfaces import Policy, Budget, ForbiddenPattern
        
        budget = Budget(max_loc=10000, max_modules=8, max_files=30, max_dependencies=20)
        patterns = [
            ForbiddenPattern(
                name="god_object",
                description="Classes over 300 LOC",
                rule="class_loc > 300"
            )
        ]
        
        policy = Policy(
            version="1.0",
            project_name="test",
            project_root=Path("/path"),
            budgets=budget,
            permissions={},
            forbidden_patterns=patterns
        )
        
        generator = SpecificationGenerator()
        spec = generator.generate(intent="Add feature", policy=policy)
        
        # Forbidden patterns should be included
        assert "god_object" in spec.forbidden_patterns


class TestProjectAnalyzer:
    """Test project analysis for intelligent defaults."""
    
    def test_analyze_python_project(self, tmp_path):
        """ProjectAnalyzer should detect Python project characteristics."""
        from src.governance.gvufd import ProjectAnalyzer
        
        # Create dummy Python project structure
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("# Main file\n" * 50)
        (tmp_path / "tests").mkdir()
        (tmp_path / "requirements.txt").write_text("flask==2.0.0\npytest==7.0.0\n")
        
        analyzer = ProjectAnalyzer()
        profile = analyzer.analyze(tmp_path)
        
        assert profile.language == "python"
        assert profile.has_tests is True
        assert profile.current_files > 0
    
    def test_analyze_empty_project(self, tmp_path):
        """ProjectAnalyzer should handle empty/new projects."""
        from src.governance.gvufd import ProjectAnalyzer
        
        analyzer = ProjectAnalyzer()
        profile = analyzer.analyze(tmp_path)
        
        # Should provide sensible defaults
        assert profile.current_loc >= 0
        assert profile.project_type in ["unknown", "new"]


class TestBudgetAllocator:
    """Test intelligent budget allocation."""
    
    def test_allocate_for_small_feature(self):
        """BudgetAllocator should allocate small budgets for simple features."""
        from src.governance.gvufd import BudgetAllocator
        from src.interfaces import Budget
        
        policy_budget = Budget(
            max_loc=10000,
            max_modules=8,
            max_files=30,
            max_dependencies=20
        )
        
        allocator = BudgetAllocator(policy_budget)
        
        # Use a simple intent that will be classified as 'low' complexity
        complexity = allocator.estimate_complexity("Add helper function for string formatting")
        spec_budget = allocator.allocate(
            intent="Add helper function for string formatting",
            complexity=complexity
        )
        
        # Low complexity feature = small budget (15% of 10000 = 1500)
        assert spec_budget.max_loc_delta <= 1500
        assert spec_budget.max_new_files <= 5
    
    def test_allocate_for_large_feature(self):
        """BudgetAllocator should allocate larger budgets for complex features."""
        from src.governance.gvufd import BudgetAllocator
        from src.interfaces import Budget
        
        policy_budget = Budget(
            max_loc=10000,
            max_modules=8,
            max_files=30,
            max_dependencies=20
        )
        
        allocator = BudgetAllocator(policy_budget)
        spec_budget = allocator.allocate(
            intent="Implement complete authentication system with OAuth2",
            complexity="high"
        )
        
        # Complex feature = larger budget
        assert spec_budget.max_loc_delta > 300
        assert spec_budget.max_new_files > 2
    
    def test_allocate_respects_policy_limits(self):
        """BudgetAllocator should never exceed policy limits."""
        from src.governance.gvufd import BudgetAllocator
        from src.interfaces import Budget
        
        policy_budget = Budget(
            max_loc=1000,  # Small policy limit
            max_modules=3,
            max_files=10,
            max_dependencies=5
        )
        
        allocator = BudgetAllocator(policy_budget)
        spec_budget = allocator.allocate(
            intent="Implement large feature",
            complexity="high"
        )
        
        # Should not exceed policy
        assert spec_budget.max_loc_delta <= policy_budget.max_loc
        assert spec_budget.max_new_files <= policy_budget.max_files
