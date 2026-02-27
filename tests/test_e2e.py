"""
End-to-end integration tests for AUREUS.
Tests complete workflows from CLI to policy management.
"""

import pytest
from pathlib import Path
import tempfile
import shutil
import sys


class TestE2EWorkflow:
    """Test complete AUREUS workflows."""
    
    def test_complete_init_workflow(self, tmp_path):
        """
        Test complete init workflow:
        1. Run aureus init
        2. Verify policy file created
        3. Load and validate policy
        4. Verify all required fields present
        """
        # Change to temp directory
        original_cwd = Path.cwd()
        try:
            import os
            os.chdir(tmp_path)
            
            # Import after changing directory
            from src.cli.main import InitCommand, CLIError
            from src.governance.policy import PolicyLoader
            
            # Step 1: Initialize project
            policy_path = tmp_path / ".aureus" / "policy.yaml"
            cmd = InitCommand(policy_path=policy_path, verbose=False)
            result = cmd.execute()
            
            assert result["status"] == "success"
            
            # Step 2: Verify policy file created
            assert policy_path.exists()
            
            # Step 3: Load policy
            loader = PolicyLoader()
            policy = loader.load(policy_path)
            
            # Step 4: Verify policy structure
            assert policy.version == "1.0"
            assert policy.project_name is not None
            assert policy.budgets.max_loc > 0
            assert policy.budgets.max_modules > 0
            assert "tools" in policy.permissions
            
        finally:
            os.chdir(original_cwd)
    
    def test_policy_roundtrip(self, tmp_path):
        """
        Test policy save/load roundtrip:
        1. Create policy programmatically
        2. Save to file
        3. Load from file
        4. Verify all fields match
        """
        from src.interfaces import Policy, Budget, ForbiddenPattern
        from src.governance.policy import PolicyLoader
        
        # Step 1: Create policy
        budget = Budget(
            max_loc=5000,
            max_modules=10,
            max_files=25,
            max_dependencies=15,
            max_class_loc=300,
            max_function_loc=40
        )
        
        patterns = [
            ForbiddenPattern(
                name="god_object",
                description="Classes over 300 LOC",
                rule="class_loc > 300",
                severity="error"
            )
        ]
        
        original = Policy(
            version="1.0",
            project_name="test-roundtrip",
            project_root=tmp_path,
            project_language="python",
            project_type="api",
            budgets=budget,
            forbidden_patterns=patterns,
            permissions={"tools": {"file_read": "allow"}},
            cost_thresholds={"warning": 150.0, "rejection": 600.0}
        )
        
        # Step 2: Save
        policy_file = tmp_path / "policy.yaml"
        loader = PolicyLoader()
        loader.save(original, policy_file)
        
        # Step 3: Load
        loaded = loader.load(policy_file)
        
        # Step 4: Verify
        assert loaded.version == original.version
        assert loaded.project_name == original.project_name
        assert loaded.project_language == original.project_language
        assert loaded.budgets.max_loc == original.budgets.max_loc
        assert loaded.budgets.max_class_loc == original.budgets.max_class_loc
        assert len(loaded.forbidden_patterns) == len(original.forbidden_patterns)
        assert loaded.forbidden_patterns[0].name == patterns[0].name
        assert loaded.cost_thresholds["warning"] == 150.0
    
    def test_cli_parser_integration(self):
        """
        Test CLI parser with various command combinations.
        """
        from src.cli.main import CLIParser, CLIError
        
        parser = CLIParser()
        
        # Test various valid commands
        test_cases = [
            (["init"], "init", None),
            (["code", "add authentication"], "code", "add authentication"),
            (["code", "implement feature X"], "code", "implement feature X"),
            (["status"], "status", None),
        ]
        
        for args, expected_cmd, expected_intent in test_cases:
            result = parser.parse(args)
            assert result.command == expected_cmd
            if expected_intent:
                assert result.intent == expected_intent
    
    def test_interfaces_validation(self):
        """
        Test that all validation rules work correctly.
        """
        from src.interfaces import Budget, Policy, Specification, SpecificationBudget
        from src.interfaces import ValidationError
        
        # Test Budget validation
        with pytest.raises(ValidationError):
            Budget(max_loc=-100, max_modules=5, max_files=20, max_dependencies=10)
        
        # Test Policy version validation
        budget = Budget(max_loc=10000, max_modules=8, max_files=30, max_dependencies=20)
        with pytest.raises(ValidationError, match="version"):
            Policy(
                version="invalid.version.format",
                project_name="test",
                project_root=Path("/path"),
                budgets=budget,
                permissions={}
            )
        
        # Test Specification validation
        spec_budget = SpecificationBudget(
            max_loc_delta=500,
            max_new_files=5,
            max_new_dependencies=2
        )
        
        with pytest.raises(ValidationError, match="success_criteria"):
            Specification(
                intent="test",
                success_criteria=[],  # Empty - should fail
                budgets=spec_budget,
                risk_level="low"
            )
        
        with pytest.raises(ValidationError, match="risk_level"):
            Specification(
                intent="test",
                success_criteria=["criterion 1"],
                budgets=spec_budget,
                risk_level="invalid"  # Invalid enum value
            )
    
    def test_example_policy_loading(self):
        """
        Test loading the example policy files.
        """
        from src.governance.policy import PolicyLoader
        
        example_file = Path("examples/policy-simple-api.yaml")
        if not example_file.exists():
            pytest.skip("Example file not found")
        
        loader = PolicyLoader()
        policy = loader.load(example_file)
        
        # Verify example policy structure
        assert policy.project_name == "simple-api"
        assert policy.budgets.max_loc == 5000
        assert policy.budgets.max_modules == 6
        assert len(policy.forbidden_patterns) >= 3  # At least 3 patterns
        
        # Verify specific patterns exist
        pattern_names = [p.name for p in policy.forbidden_patterns]
        assert "god_object" in pattern_names
        assert "circular_deps" in pattern_names
    
    def test_serialization_consistency(self):
        """
        Test that to_dict/from_dict are consistent for all data models.
        """
        from src.interfaces import Budget, Policy, ForbiddenPattern
        from src.interfaces import Specification, SpecificationBudget, AcceptanceTest
        
        # Test Budget
        budget = Budget(max_loc=10000, max_modules=8, max_files=30, max_dependencies=20)
        budget_dict = budget.to_dict()
        budget_restored = Budget.from_dict(budget_dict)
        assert budget_restored.max_loc == budget.max_loc
        
        # Test ForbiddenPattern
        pattern = ForbiddenPattern(name="test", description="desc", rule="rule > 5")
        pattern_dict = pattern.to_dict()
        pattern_restored = ForbiddenPattern.from_dict(pattern_dict)
        assert pattern_restored.name == pattern.name
        
        # Test AcceptanceTest
        test = AcceptanceTest(name="test_auth", description="Test authentication")
        test_dict = test.to_dict()
        test_restored = AcceptanceTest.from_dict(test_dict)
        assert test_restored.name == test.name
        
        # Test SpecificationBudget
        spec_budget = SpecificationBudget(
            max_loc_delta=500,
            max_new_files=5,
            max_new_dependencies=2
        )
        spec_budget_dict = spec_budget.to_dict()
        spec_budget_restored = SpecificationBudget.from_dict(spec_budget_dict)
        assert spec_budget_restored.max_loc_delta == spec_budget.max_loc_delta
