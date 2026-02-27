"""
Policy YAML loader and validator.

Handles:
- Loading policy from YAML files
- Validating against schema
- Saving policy to YAML
- Error reporting with context
"""

import yaml
from pathlib import Path
from typing import List, Dict, Any
from src.interfaces import Policy, Budget, ForbiddenPattern, ValidationError


class PolicyLoadError(Exception):
    """Raised when policy loading fails."""
    pass


class PolicyValidator:
    """
    Validates policy dictionaries against schema requirements.
    
    Checks:
    - Required fields present
    - Valid value types
    - Budget constraints
    - Version format
    """
    
    REQUIRED_FIELDS = {
        "version": str,
        "project": dict,
        "budgets": dict,
        "permissions": dict
    }
    
    REQUIRED_PROJECT_FIELDS = {
        "name": str,
        "root": str
    }
    
    REQUIRED_BUDGET_FIELDS = {
        "max_loc": int,
        "max_modules": int,
        "max_files": int,
        "max_dependencies": int
    }
    
    def validate(self, policy_dict: Dict[str, Any]) -> List[str]:
        """
        Validate policy dictionary.
        
        Args:
            policy_dict: Dictionary to validate
        
        Returns:
            List of error messages (empty if valid)
        """
        errors = []
        
        # Check top-level required fields
        for field, expected_type in self.REQUIRED_FIELDS.items():
            if field not in policy_dict:
                errors.append(f"Missing required field: {field}")
            elif not isinstance(policy_dict[field], expected_type):
                errors.append(f"Field '{field}' must be {expected_type.__name__}")
        
        if errors:
            return errors
        
        # Validate project section
        project = policy_dict.get("project", {})
        for field, expected_type in self.REQUIRED_PROJECT_FIELDS.items():
            if field not in project:
                errors.append(f"Missing required field: project.{field}")
            elif not isinstance(project[field], expected_type):
                errors.append(f"Field 'project.{field}' must be {expected_type.__name__}")
        
        # Validate budgets section
        budgets = policy_dict.get("budgets", {})
        for field, expected_type in self.REQUIRED_BUDGET_FIELDS.items():
            if field not in budgets:
                errors.append(f"Missing required field: budgets.{field}")
            elif not isinstance(budgets[field], expected_type):
                errors.append(f"Field 'budgets.{field}' must be {expected_type.__name__}")
            elif budgets[field] <= 0:
                errors.append(f"Field 'budgets.{field}' must be positive")
        
        return errors


class PolicyLoader:
    """
    Loads and saves AUREUS policies from/to YAML files.
    
    Features:
    - YAML parsing with error handling
    - Schema validation
    - Path resolution
    - Type conversion
    """
    
    def __init__(self):
        self.validator = PolicyValidator()
    
    def load(self, path: Path) -> Policy:
        """
        Load policy from YAML file.
        
        Args:
            path: Path to policy YAML file
        
        Returns:
            Validated Policy object
        
        Raises:
            PolicyLoadError: If loading or validation fails
        """
        # Check file exists
        if not path.exists():
            raise PolicyLoadError(f"Policy file not found: {path}")
        
        # Parse YAML
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise PolicyLoadError(f"Invalid YAML syntax: {e}")
        except Exception as e:
            raise PolicyLoadError(f"Failed to read file: {e}")
        
        if not isinstance(data, dict):
            raise PolicyLoadError("Policy file must contain a YAML dictionary")
        
        # Validate structure
        errors = self.validator.validate(data)
        if errors:
            error_msg = "Policy validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
            raise PolicyLoadError(error_msg)
        
        # Convert to Policy object
        try:
            policy = self._dict_to_policy(data)
        except ValidationError as e:
            raise PolicyLoadError(f"Policy validation error: {e}")
        except Exception as e:
            raise PolicyLoadError(f"Failed to create Policy object: {e}")
        
        return policy
    
    def save(self, policy: Policy, path: Path) -> None:
        """
        Save policy to YAML file.
        
        Args:
            policy: Policy object to save
            path: Destination file path
        
        Raises:
            PolicyLoadError: If saving fails
        """
        try:
            data = policy.to_dict()
            
            # Ensure parent directory exists
            path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, 'w', encoding='utf-8') as f:
                yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)
        except Exception as e:
            raise PolicyLoadError(f"Failed to save policy: {e}")
    
    def _dict_to_policy(self, data: Dict[str, Any]) -> Policy:
        """
        Convert dictionary to Policy object.
        
        Args:
            data: Validated policy dictionary
        
        Returns:
            Policy object
        """
        # Parse project section
        project = data["project"]
        
        # Parse budgets
        budget_data = data["budgets"]
        budgets = Budget(
            max_loc=budget_data["max_loc"],
            max_modules=budget_data["max_modules"],
            max_files=budget_data["max_files"],
            max_dependencies=budget_data["max_dependencies"],
            max_class_loc=budget_data.get("max_class_loc", 500),
            max_function_loc=budget_data.get("max_function_loc", 50),
            max_inheritance_depth=budget_data.get("max_inheritance_depth", 2)
        )
        
        # Parse forbidden patterns
        patterns = []
        for pattern_data in data.get("forbidden_patterns", []):
            pattern = ForbiddenPattern(
                name=pattern_data["name"],
                description=pattern_data["description"],
                rule=pattern_data["rule"],
                severity=pattern_data.get("severity", "error"),
                auto_fix=pattern_data.get("auto_fix", False)
            )
            patterns.append(pattern)
        
        # Create Policy object
        policy = Policy(
            version=data["version"],
            project_name=project["name"],
            project_root=Path(project["root"]),
            project_language=project.get("language"),
            project_type=project.get("type"),
            budgets=budgets,
            forbidden_patterns=patterns,
            permissions=data["permissions"],
            cost_thresholds=data.get("cost_thresholds", {
                "warning": 100.0,
                "rejection": 500.0,
                "session_limit": 2000.0
            }),
            simplification_config=data.get("simplification", {
                "trigger_at_budget_percent": 85,
                "mandatory": True,
                "target_reduction": 0.2
            })
        )
        
        return policy
