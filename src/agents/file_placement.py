"""
File Placement Intelligence - Smart file organization based on project conventions

Analyzes project structure and places generated files in appropriate locations
following established patterns and conventions.
"""

from pathlib import Path
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass
import re


@dataclass
class ProjectStructure:
    """Detected project structure and conventions"""
    
    # Project type detection
    has_src_dir: bool = False
    has_lib_dir: bool = False
    has_app_dir: bool = False
    has_tests_dir: bool = False
    
    # Python-specific
    is_package: bool = False  # Has __init__.py
    uses_flat_layout: bool = True  # No src/ directory
    
    # Detected patterns
    primary_code_dir: Optional[Path] = None
    test_dir: Optional[Path] = None
    
    # Naming conventions
    uses_underscores: bool = True  # snake_case vs camelCase
    prefers_plural_dirs: bool = True  # tests vs test
    
    def to_dict(self) -> Dict:
        """Serialize to dictionary"""
        return {
            "has_src_dir": self.has_src_dir,
            "has_lib_dir": self.has_lib_dir,
            "has_app_dir": self.has_app_dir,
            "has_tests_dir": self.has_tests_dir,
            "is_package": self.is_package,
            "uses_flat_layout": self.uses_flat_layout,
            "primary_code_dir": str(self.primary_code_dir) if self.primary_code_dir else None,
            "test_dir": str(self.test_dir) if self.test_dir else None,
            "uses_underscores": self.uses_underscores,
            "prefers_plural_dirs": self.prefers_plural_dirs
        }


class FileRoleClassifier:
    """Classify file types and their purposes"""
    
    # Keywords that indicate file roles
    TEST_KEYWORDS = ["test_", "_test", "test", "tests", "spec", "specs"]
    CONFIG_KEYWORDS = ["config", "settings", "setup", "conftest"]
    MODEL_KEYWORDS = ["model", "schema", "entity", "domain"]
    CONTROLLER_KEYWORDS = ["controller", "handler", "view", "route", "api", "endpoint"]
    SERVICE_KEYWORDS = ["service", "manager", "repository", "dao"]
    UTIL_KEYWORDS = ["util", "helper", "tool", "common"]
    
    @classmethod
    def classify(cls, filename: str, intent: str) -> str:
        """
        Classify file role based on filename and intent
        
        Args:
            filename: Name of file to create
            intent: User intent description
        
        Returns:
            Role classification: test | config | model | controller | service | util | main
        """
        filename_lower = filename.lower()
        intent_lower = intent.lower()
        
        # Check test
        if any(kw in filename_lower for kw in cls.TEST_KEYWORDS):
            return "test"
        if any(kw in intent_lower for kw in ["test", "unit test", "integration test"]):
            return "test"
        
        # Check config
        if any(kw in filename_lower for kw in cls.CONFIG_KEYWORDS):
            return "config"
        
        # Check model/domain
        if any(kw in filename_lower for kw in cls.MODEL_KEYWORDS):
            return "model"
        if any(kw in intent_lower for kw in ["model", "schema", "entity", "data structure"]):
            return "model"
        
        # Check controller/api
        if any(kw in filename_lower for kw in cls.CONTROLLER_KEYWORDS):
            return "controller"
        if any(kw in intent_lower for kw in ["api", "endpoint", "route", "controller", "handler"]):
            return "controller"
        
        # Check service/business logic
        if any(kw in filename_lower for kw in cls.SERVICE_KEYWORDS):
            return "service"
        if any(kw in intent_lower for kw in ["service", "business logic", "manager"]):
            return "service"
        
        # Check utility
        if any(kw in filename_lower for kw in cls.UTIL_KEYWORDS):
            return "util"
        if any(kw in intent_lower for kw in ["utility", "helper", "tool"]):
            return "util"
        
        # Default to main application code
        return "main"


class ProjectStructureAnalyzer:
    """Analyze project structure to determine file placement conventions"""
    
    def __init__(self, project_root: Path):
        """
        Initialize analyzer
        
        Args:
            project_root: Root directory of project
        """
        self.project_root = project_root
    
    def analyze(self) -> ProjectStructure:
        """
        Analyze project and detect structure
        
        Returns:
            ProjectStructure with detected conventions
        """
        structure = ProjectStructure()
        
        if not self.project_root.exists():
            return structure
        
        # Check for common directory patterns
        structure.has_src_dir = (self.project_root / "src").exists()
        structure.has_lib_dir = (self.project_root / "lib").exists()
        structure.has_app_dir = (self.project_root / "app").exists()
        
        # Check for test directories
        test_dirs = ["tests", "test", "spec", "specs"]
        for test_dir_name in test_dirs:
            test_path = self.project_root / test_dir_name
            if test_path.exists():
                structure.has_tests_dir = True
                structure.test_dir = test_path
                structure.prefers_plural_dirs = test_dir_name.endswith("s")
                break
        
        # Determine layout (flat vs src layout)
        structure.uses_flat_layout = not structure.has_src_dir
        
        # Check if it's a package (has __init__.py)
        init_files = list(self.project_root.glob("**/__init__.py"))
        structure.is_package = len(init_files) > 0
        
        # Determine primary code directory
        # Special case: if we're IN the Aureus project, don't use src/ for generated code
        is_aureus_project = "Aureus_Coding_Agent" in str(self.project_root)
        
        if structure.has_src_dir and not is_aureus_project:
            structure.primary_code_dir = self.project_root / "src"
        elif structure.has_lib_dir:
            structure.primary_code_dir = self.project_root / "lib"
        elif structure.has_app_dir:
            structure.primary_code_dir = self.project_root / "app"
        else:
            # Look for directory with most Python files
            # (will return None for Aureus project due to filtering)
            structure.primary_code_dir = self._find_primary_code_dir()
        
        # Analyze naming conventions (snake_case vs camelCase)
        py_files = list(self.project_root.glob("**/*.py"))
        underscore_count = sum(1 for f in py_files if "_" in f.stem)
        structure.uses_underscores = underscore_count > len(py_files) / 2
        
        return structure
    
    def _find_primary_code_dir(self) -> Optional[Path]:
        """Find directory with most Python files (excluding tests and aureus itself)"""
        py_files_by_dir: Dict[Path, int] = {}
        
        for py_file in self.project_root.glob("**/*.py"):
            # Skip test files
            if any(test_kw in py_file.stem.lower() for test_kw in ["test_", "_test"]):
                continue
            
            # Skip venv/virtualenv
            if any(part in ["venv", "env", ".venv", "virtualenv", "__pycache__"] for part in py_file.parts):
                continue
            
            # Skip aureus's own src directory if we're IN the aureus project
            # This prevents generated files from going into src/ when testing
            if "Aureus_Coding_Agent" in str(self.project_root) and "src" in py_file.parts:
                continue
            
            # Count files per directory
            parent = py_file.parent
            py_files_by_dir[parent] = py_files_by_dir.get(parent, 0) + 1
        
        if not py_files_by_dir:
            return None
        
        # Return directory with most files
        primary_dir = max(py_files_by_dir.items(), key=lambda x: x[1])[0]
        
        # Don't use src/ if it looks like we're in Aureus project itself
        if "Aureus_Coding_Agent" in str(self.project_root) and "src" in primary_dir.parts:
            return None
        
        return primary_dir


class FilePlacementEngine:
    """
    Intelligent file placement based on project structure analysis
    
    Places generated files in appropriate locations following project conventions:
    - Tests go in tests/ or test/
    - Source code goes in src/ or lib/ or root
    - Respects existing directory structure
    - Creates subdirectories as needed
    """
    
    def __init__(self, project_root: Path):
        """
        Initialize placement engine
        
        Args:
            project_root: Root directory of project
        """
        self.project_root = project_root
        self.analyzer = ProjectStructureAnalyzer(project_root)
        self.structure = self.analyzer.analyze()
    
    def determine_file_path(
        self,
        filename: str,
        intent: str,
        suggested_path: Optional[str] = None
    ) -> Path:
        """
        Determine optimal file path based on project structure
        
        Args:
            filename: Name of file to create
            intent: User intent (helps classify file role)
            suggested_path: Optional suggested path from LLM
        
        Returns:
            Path where file should be created
        """
        # Classify file role
        role = FileRoleClassifier.classify(filename, intent)
        
        # If LLM provided a path, validate and use if safe
        if suggested_path:
            target_path = self._validate_suggested_path(suggested_path)
            if target_path:
                return target_path
        
        # Determine base directory based on role
        if role == "test":
            base_dir = self._get_test_directory()
        elif role == "config":
            base_dir = self.project_root  # Configs at root
        else:
            base_dir = self._get_code_directory()
        
        # Handle subdirectories based on role
        if role == "model":
            subdir = self._get_models_directory(base_dir)
        elif role == "controller":
            subdir = self._get_controllers_directory(base_dir)
        elif role == "service":
            subdir = self._get_services_directory(base_dir)
        elif role == "util":
            subdir = self._get_utils_directory(base_dir)
        else:
            subdir = base_dir
        
        return subdir / filename
    
    def _validate_suggested_path(self, suggested_path: str) -> Optional[Path]:
        """
        Validate suggested path for security
        
        Rejects:
        - Absolute paths
        - Parent directory traversal (..)
        - Paths outside project root
        
        Returns:
            Validated path or None if invalid
        """
        try:
            path = Path(suggested_path)
            
            # Reject absolute paths
            if path.is_absolute():
                return None
            
            # Reject parent traversal
            if ".." in path.parts:
                return None
            
            # If suggested path is just a filename (no directory), don't use it
            # Let the role-based placement handle it
            if len(path.parts) == 1:
                return None
            
            # Construct full path
            full_path = self.project_root / path
            
            # Ensure it's within project root
            try:
                full_path.relative_to(self.project_root)
                return full_path
            except ValueError:
                return None
        
        except Exception:
            return None
    
    def _get_test_directory(self) -> Path:
        """Get test directory (tests/ or test/)"""
        if self.structure.test_dir:
            return self.structure.test_dir
        
        # Create tests directory using plural convention
        test_dir_name = "tests" if self.structure.prefers_plural_dirs else "test"
        test_dir = self.project_root / test_dir_name
        test_dir.mkdir(parents=True, exist_ok=True)
        return test_dir
    
    def _get_code_directory(self) -> Path:
        """Get primary code directory"""
        # Always use workspace/ for backward compatibility and safety
        # Don't pollute existing code directories with generated files
        workspace_dir = self.project_root / "workspace"
        workspace_dir.mkdir(parents=True, exist_ok=True)
        return workspace_dir
    
    def _get_models_directory(self, base_dir: Path) -> Path:
        """Get models directory"""
        # Check for existing models directory
        candidates = ["models", "model", "domain", "entities"]
        for candidate in candidates:
            dir_path = base_dir / candidate
            if dir_path.exists():
                return dir_path
        
        # Create new models directory
        models_dir = base_dir / ("models" if self.structure.prefers_plural_dirs else "model")
        models_dir.mkdir(parents=True, exist_ok=True)
        return models_dir
    
    def _get_controllers_directory(self, base_dir: Path) -> Path:
        """Get controllers directory"""
        candidates = ["controllers", "controller", "handlers", "api", "routes"]
        for candidate in candidates:
            dir_path = base_dir / candidate
            if dir_path.exists():
                return dir_path
        
        # Create controllers directory
        controllers_dir = base_dir / ("controllers" if self.structure.prefers_plural_dirs else "controller")
        controllers_dir.mkdir(parents=True, exist_ok=True)
        return controllers_dir
    
    def _get_services_directory(self, base_dir: Path) -> Path:
        """Get services directory"""
        candidates = ["services", "service", "business", "logic"]
        for candidate in candidates:
            dir_path = base_dir / candidate
            if dir_path.exists():
                return dir_path
        
        # Create services directory
        services_dir = base_dir / ("services" if self.structure.prefers_plural_dirs else "service")
        services_dir.mkdir(parents=True, exist_ok=True)
        return services_dir
    
    def _get_utils_directory(self, base_dir: Path) -> Path:
        """Get utilities directory"""
        candidates = ["utils", "util", "helpers", "common"]
        for candidate in candidates:
            dir_path = base_dir / candidate
            if dir_path.exists():
                return dir_path
        
        # Create utils directory
        utils_dir = base_dir / ("utils" if self.structure.prefers_plural_dirs else "util")
        utils_dir.mkdir(parents=True, exist_ok=True)
        return utils_dir
    
    def get_structure_summary(self) -> Dict:
        """Get summary of detected project structure"""
        return self.structure.to_dict()
