"""
Tests for Policy YAML loader.
TDD: Tests written before implementation.
"""

import pytest
import yaml
from pathlib import Path
import tempfile
import os


class TestPolicyLoader:
    """Test PolicyLoader for YAML parsing and validation."""
    
    def test_load_valid_policy(self, tmp_path):
        """PolicyLoader should load valid YAML policy."""
        from src.governance.policy import PolicyLoader
        
        # Create valid policy YAML
        policy_yaml = """
version: "1.0"
project:
  name: "test-project"
  root: "/path/to/project"
  language: "python"
  type: "api"
budgets:
  max_loc: 10000
  max_modules: 8
  max_files: 30
  max_dependencies: 20
permissions:
  tools:
    file_read: allow
    file_write: allow
"""
        policy_file = tmp_path / "policy.yaml"
        policy_file.write_text(policy_yaml)
        
        loader = PolicyLoader()
        policy = loader.load(policy_file)
        
        assert policy.version == "1.0"
        assert policy.project_name == "test-project"
        assert policy.budgets.max_loc == 10000
    
    def test_load_with_forbidden_patterns(self, tmp_path):
        """PolicyLoader should parse forbidden patterns."""
        from src.governance.policy import PolicyLoader
        
        policy_yaml = """
version: "1.0"
project:
  name: "test"
  root: "/path"
budgets:
  max_loc: 10000
  max_modules: 8
  max_files: 30
  max_dependencies: 20
permissions:
  tools: {}
forbidden_patterns:
  - name: "god_object"
    description: "Classes over 500 LOC"
    rule: "class_loc > 500"
    severity: "error"
"""
        policy_file = tmp_path / "policy.yaml"
        policy_file.write_text(policy_yaml)
        
        loader = PolicyLoader()
        policy = loader.load(policy_file)
        
        assert len(policy.forbidden_patterns) == 1
        assert policy.forbidden_patterns[0].name == "god_object"
    
    def test_load_missing_file(self):
        """PolicyLoader should raise error for missing file."""
        from src.governance.policy import PolicyLoader, PolicyLoadError
        
        loader = PolicyLoader()
        with pytest.raises(PolicyLoadError, match="not found"):
            loader.load(Path("/nonexistent/policy.yaml"))
    
    def test_load_invalid_yaml(self, tmp_path):
        """PolicyLoader should raise error for invalid YAML."""
        from src.governance.policy import PolicyLoader, PolicyLoadError
        
        invalid_yaml = "invalid: yaml: content: [unclosed"
        policy_file = tmp_path / "policy.yaml"
        policy_file.write_text(invalid_yaml)
        
        loader = PolicyLoader()
        with pytest.raises(PolicyLoadError, match="YAML"):
            loader.load(policy_file)
    
    def test_load_missing_required_field(self, tmp_path):
        """PolicyLoader should raise error for missing required fields."""
        from src.governance.policy import PolicyLoader, PolicyLoadError
        
        # Missing 'budgets' field
        policy_yaml = """
version: "1.0"
project:
  name: "test"
  root: "/path"
permissions:
  tools: {}
"""
        policy_file = tmp_path / "policy.yaml"
        policy_file.write_text(policy_yaml)
        
        loader = PolicyLoader()
        with pytest.raises(PolicyLoadError, match="required field"):
            loader.load(policy_file)
    
    def test_load_invalid_version_format(self, tmp_path):
        """PolicyLoader should raise error for invalid version format."""
        from src.governance.policy import PolicyLoader, PolicyLoadError
        
        policy_yaml = """
version: "invalid"
project:
  name: "test"
  root: "/path"
budgets:
  max_loc: 10000
  max_modules: 8
  max_files: 30
  max_dependencies: 20
permissions:
  tools: {}
"""
        policy_file = tmp_path / "policy.yaml"
        policy_file.write_text(policy_yaml)
        
        loader = PolicyLoader()
        with pytest.raises(PolicyLoadError, match="version"):
            loader.load(policy_file)
    
    def test_load_with_cost_thresholds(self, tmp_path):
        """PolicyLoader should parse cost thresholds."""
        from src.governance.policy import PolicyLoader
        
        policy_yaml = """
version: "1.0"
project:
  name: "test"
  root: "/path"
budgets:
  max_loc: 10000
  max_modules: 8
  max_files: 30
  max_dependencies: 20
permissions:
  tools: {}
cost_thresholds:
  warning: 200.0
  rejection: 800.0
  session_limit: 3000.0
"""
        policy_file = tmp_path / "policy.yaml"
        policy_file.write_text(policy_yaml)
        
        loader = PolicyLoader()
        policy = loader.load(policy_file)
        
        assert policy.cost_thresholds["warning"] == 200.0
        assert policy.cost_thresholds["rejection"] == 800.0
    
    def test_save_policy(self, tmp_path):
        """PolicyLoader should save policy to YAML."""
        from src.governance.policy import PolicyLoader
        from src.interfaces import Policy, Budget
        
        budget = Budget(max_loc=10000, max_modules=8, max_files=30, max_dependencies=20)
        policy = Policy(
            version="1.0",
            project_name="test",
            project_root=Path("/path"),
            budgets=budget,
            permissions={"tools": {"file_read": "allow"}}
        )
        
        policy_file = tmp_path / "saved_policy.yaml"
        loader = PolicyLoader()
        loader.save(policy, policy_file)
        
        # Load it back
        loaded = loader.load(policy_file)
        assert loaded.version == "1.0"
        assert loaded.project_name == "test"
    
    def test_load_from_example_file(self):
        """PolicyLoader should load the example policy file."""
        from src.governance.policy import PolicyLoader
        
        # Load the actual example file
        example_file = Path("examples/policy-simple-api.yaml")
        if not example_file.exists():
            pytest.skip("Example file not found")
        
        loader = PolicyLoader()
        policy = loader.load(example_file)
        
        assert policy.project_name == "simple-api"
        assert policy.budgets.max_loc == 5000
        assert len(policy.forbidden_patterns) > 0


class TestPolicyValidator:
    """Test PolicyValidator for schema validation."""
    
    def test_validate_valid_policy_dict(self):
        """PolicyValidator should validate correct policy dict."""
        from src.governance.policy import PolicyValidator
        
        policy_dict = {
            "version": "1.0",
            "project": {
                "name": "test",
                "root": "/path"
            },
            "budgets": {
                "max_loc": 10000,
                "max_modules": 8,
                "max_files": 30,
                "max_dependencies": 20
            },
            "permissions": {
                "tools": {}
            }
        }
        
        validator = PolicyValidator()
        errors = validator.validate(policy_dict)
        assert len(errors) == 0
    
    def test_validate_missing_required_field(self):
        """PolicyValidator should detect missing required fields."""
        from src.governance.policy import PolicyValidator
        
        policy_dict = {
            "version": "1.0",
            "project": {
                "name": "test"
                # Missing 'root'
            }
        }
        
        validator = PolicyValidator()
        errors = validator.validate(policy_dict)
        assert len(errors) > 0
        assert any("required" in err.lower() for err in errors)
    
    def test_validate_invalid_budget_value(self):
        """PolicyValidator should detect invalid budget values."""
        from src.governance.policy import PolicyValidator
        
        policy_dict = {
            "version": "1.0",
            "project": {"name": "test", "root": "/path"},
            "budgets": {
                "max_loc": -1000,  # Invalid: negative
                "max_modules": 8,
                "max_files": 30,
                "max_dependencies": 20
            },
            "permissions": {"tools": {}}
        }
        
        validator = PolicyValidator()
        errors = validator.validate(policy_dict)
        assert len(errors) > 0
