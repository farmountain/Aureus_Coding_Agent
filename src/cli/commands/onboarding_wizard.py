"""
Interactive Onboarding Wizard

Guides new users through AUREUS project setup with smart defaults.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass

from src.governance.policy import Policy, Budget, PolicyLoader


@dataclass
class ProjectInfo:
    """Detected project information"""
    language: str
    framework: Optional[str]
    loc: int
    file_count: int
    has_tests: bool
    has_git: bool


@dataclass
class WizardConfig:
    """Configuration collected by wizard"""
    project_name: str
    model_provider: str
    model_api_key: str
    max_loc: int
    max_files: int
    max_modules: int
    max_dependencies: int
    allow_file_delete: bool
    allow_shell_exec: bool


class OnboardingWizard:
    """
    Interactive wizard for first-time project setup.
    
    Walks user through:
    1. Project detection
    2. Model provider configuration
    3. Budget limits
    4. Permission settings
    5. Policy confirmation and save
    """
    
    def __init__(self, project_root: Path = Path.cwd(), policy_path: Path = Path(".aureus/policy.yaml")):
        self.project_root = project_root
        self.policy_path = policy_path
        self.loader = PolicyLoader()
        
    def run(self) -> Policy:
        """
        Run the complete onboarding wizard.
        
        Returns:
            Configured Policy object
        """
        self._print_header()
        
        # Step 1: Detect project
        project_info = self._detect_project()
        self._display_project_info(project_info)
        
        # Step 2: Configure model provider
        provider, api_key = self._configure_model()
        
        # Step 3: Set budget limits
        budgets = self._configure_budgets(project_info)
        
        # Step 4: Configure permissions
        permissions = self._configure_permissions()
        
        # Step 5: Confirmation
        config = WizardConfig(
            project_name=self.project_root.name,
            model_provider=provider,
            model_api_key=api_key,
            max_loc=budgets["max_loc"],
            max_files=budgets["max_files"],
            max_modules=budgets["max_modules"],
            max_dependencies=budgets["max_dependencies"],
            allow_file_delete=permissions["file_delete"],
            allow_shell_exec=permissions["shell_exec"]
        )
        
        self._display_summary(config, project_info)
        
        if not self._confirm("Create policy with these settings?"):
            print("\n❌ Setup cancelled")
            sys.exit(1)
        
        # Step 6: Create and save policy
        policy = self._create_policy(config)
        self._save_policy(policy)
        
        # Step 7: Set environment variables if needed
        if api_key:
            self._configure_environment(provider, api_key)
        
        self._print_next_steps()
        
        return policy
    
    def _print_header(self):
        """Print wizard welcome header"""
        print("\n" + "=" * 66)
        print("  🪄  AUREUS Interactive Setup Wizard")
        print("=" * 66)
        print("\nWelcome! This wizard will help you configure AUREUS for your project.")
        print("Press Ctrl+C at any time to cancel.\n")
    
    def _detect_project(self) -> ProjectInfo:
        """
        Auto-detect project characteristics.
        
        Returns:
            ProjectInfo with detected attributes
        """
        print("📊 Step 1: Analyzing project...\n")
        
        # Detect language
        language = self._detect_language()
        
        # Detect framework
        framework = self._detect_framework(language)
        
        # Count LOC
        loc = self._count_loc()
        
        # Count files
        file_count = self._count_files()
        
        # Check for tests
        has_tests = self._has_tests()
        
        # Check for git
        has_git = (self.project_root / ".git").exists()
        
        return ProjectInfo(
            language=language,
            framework=framework,
            loc=loc,
            file_count=file_count,
            has_tests=has_tests,
            has_git=has_git
        )
    
    def _detect_language(self) -> str:
        """Detect primary programming language"""
        # Count files by extension
        extensions = {}
        for ext in [".py", ".js", ".ts", ".java", ".go", ".rb", ".rs", ".cpp", ".c"]:
            count = len(list(self.project_root.rglob(f"*{ext}")))
            if count > 0:
                extensions[ext] = count
        
        if not extensions:
            return "unknown"
        
        # Return most common
        lang_map = {
            ".py": "Python",
            ".js": "JavaScript",
            ".ts": "TypeScript",
            ".java": "Java",
            ".go": "Go",
            ".rb": "Ruby",
            ".rs": "Rust",
            ".cpp": "C++",
            ".c": "C"
        }
        
        dominant = max(extensions, key=extensions.get)
        return lang_map.get(dominant, "unknown")
    
    def _detect_framework(self, language: str) -> Optional[str]:
        """Detect framework based on common files"""
        if language == "Python":
            if (self.project_root / "manage.py").exists():
                return "Django"
            if (self.project_root / "app.py").exists() or (self.project_root / "wsgi.py").exists():
                return "Flask"
            if (self.project_root / "fastapi").exists():
                return "FastAPI"
        
        elif language == "JavaScript" or language == "TypeScript":
            if (self.project_root / "package.json").exists():
                with open(self.project_root / "package.json") as f:
                    content = f.read()
                    if "react" in content:
                        return "React"
                    if "vue" in content:
                        return "Vue"
                    if "angular" in content:
                        return "Angular"
                    if "express" in content:
                        return "Express"
        
        return None
    
    def _count_loc(self) -> int:
        """Count lines of code (simple heuristic)"""
        total = 0
        extensions = [".py", ".js", ".ts", ".java", ".go", ".rb", ".rs", ".cpp", ".c"]
        
        for ext in extensions:
            for file in self.project_root.rglob(f"*{ext}"):
                # Skip common ignore patterns
                if any(part in file.parts for part in ["node_modules", ".venv", "venv", "__pycache__", "dist", "build"]):
                    continue
                
                try:
                    with open(file, "r", encoding="utf-8", errors="ignore") as f:
                        total += sum(1 for line in f if line.strip())
                except Exception:
                    continue
        
        return total
    
    def _count_files(self) -> int:
        """Count source files"""
        count = 0
        extensions = [".py", ".js", ".ts", ".java", ".go", ".rb", ".rs", ".cpp", ".c"]
        
        for ext in extensions:
            for file in self.project_root.rglob(f"*{ext}"):
                if any(part in file.parts for part in ["node_modules", ".venv", "venv", "__pycache__", "dist", "build"]):
                    continue
                count += 1
        
        return count
    
    def _has_tests(self) -> bool:
        """Check if project has tests"""
        test_dirs = ["tests", "test", "__tests__", "spec"]
        for test_dir in test_dirs:
            if (self.project_root / test_dir).exists():
                return True
        
        # Check for test files
        test_patterns = ["test_*.py", "*_test.py", "*.test.js", "*.spec.js"]
        for pattern in test_patterns:
            if list(self.project_root.rglob(pattern)):
                return True
        
        return False
    
    def _display_project_info(self, info: ProjectInfo):
        """Display detected project information"""
        print("✓ Project detected:")
        print(f"  Language:   {info.language}")
        if info.framework:
            print(f"  Framework:  {info.framework}")
        print(f"  Size:       {info.loc:,} LOC in {info.file_count} files")
        print(f"  Has tests:  {'Yes' if info.has_tests else 'No'}")
        print(f"  Has Git:    {'Yes' if info.has_git else 'No'}")
        print()
    
    def _configure_model(self) -> Tuple[str, str]:
        """
        Configure model provider.
        
        Returns:
            (provider_name, api_key)
        """
        print("🤖 Step 2: Model Provider Configuration\n")
        print("AUREUS supports 9 latest LLM models from leading providers:")
        print("\n  Anthropic Models:")
        print("    1. Claude Sonnet 4.6 (Latest, balanced, 1x cost)")
        print("    2. Claude Opus 4.6 (Highest intelligence, 3x cost)")
        print("    3. Claude Haiku 4.5 (Fast, cost-effective, 0.33x cost)")
        print("\n  Google Gemini Models:")
        print("    4. Gemini 3.1 Pro (Preview) (Advanced reasoning)")
        print("    5. Gemini 3 Pro (Preview) (Production ready)")
        print("    6. Gemini 2.5 Pro (Stable, proven)")
        print("\n  OpenAI GPT Models:")
        print("    7. GPT-5.3-Codex (Latest, code specialized)")
        print("    8. GPT-5.2-Codex (Code generation optimized)")
        print("    9. GPT-5.2 (General purpose, latest)")
        print("\n    10. Mock (for testing, no real code generation)")
        print()
        
        # Check environment first
        env_provider = os.getenv("AUREUS_MODEL_PROVIDER")
        env_key = os.getenv("AUREUS_MODEL_API_KEY")
        
        if env_provider and env_key:
            print(f"✓ Found existing configuration: {env_provider}")
            if self._confirm(f"Use {env_provider} with existing API key?"):
                return env_provider, env_key
        
        # Interactive selection
        model_map = {
            "1": ("anthropic", "claude-sonnet-4.6"),
            "2": ("anthropic", "claude-opus-4.6"),
            "3": ("anthropic", "claude-haiku-4.5"),
            "4": ("google", "gemini-3.1-pro"),
            "5": ("google", "gemini-3-pro"),
            "6": ("google", "gemini-2.5-pro"),
            "7": ("openai", "gpt-5.3-codex"),
            "8": ("openai", "gpt-5.2-codex"),
            "9": ("openai", "gpt-5.2"),
            "10": ("mock", "mock-model")
        }
        
        while True:
            choice = self._prompt("Select model [1-10]", default="1")
            
            if choice in model_map:
                provider, model_name = model_map[choice]
                
                if provider == "mock":
                    print("\n⚠️  Mock provider selected - no real code generation")
                    return "mock", ""
                
                print(f"\n✓ Selected: {model_name}")
                break
            else:
                print("  Invalid choice, please enter 1-10")
        
        # Get API key
        api_urls = {
            "openai": "https://platform.openai.com/api-keys",
            "anthropic": "https://console.anthropic.com/",
            "google": "https://makersuite.google.com/app/apikey"
        }
        
        print(f"\nEnter your {provider.upper()} API key:")
        print(f"  (Get one from: {api_urls[provider]})")
        
        api_key = self._prompt("API Key", secret=True)
        
        if not api_key:
            print("  ⚠️  No API key provided - using mock provider")
            return "mock", ""
        
        # Validate key format
        if provider == "openai" and not api_key.startswith("sk-"):
            print("  ⚠️  Warning: OpenAI keys typically start with 'sk-'")
        elif provider == "anthropic" and not api_key.startswith("sk-ant-"):
            print("  ⚠️  Warning: Anthropic keys typically start with 'sk-ant-'")
        elif provider == "google" and len(api_key) < 20:
            print("  ⚠️  Warning: Google API keys are typically 39+ characters")
        
        print(f"  ✓ {provider.upper()} configured")
        return provider, api_key
    
    def _configure_budgets(self, info: ProjectInfo) -> Dict[str, int]:
        """
        Configure budget limits with smart defaults.
        
        Args:
            info: Detected project info
        
        Returns:
            Dictionary of budget limits
        """
        print("\n📊 Step 3: Budget Limits\n")
        print("Set maximum changes AUREUS can make in a single build:")
        print()
        
        # Calculate smart defaults (3-5x current size)
        multiplier = 4
        default_loc = max(1000, info.loc * multiplier) if info.loc > 0 else 10000
        default_files = max(30, info.file_count * 3) if info.file_count > 0 else 30
        default_modules = 8
        default_deps = 20
        
        print(f"Recommended defaults (based on {info.loc:,} LOC project):")
        print(f"  Max LOC:          {default_loc:,}")
        print(f"  Max Files:        {default_files}")
        print(f"  Max Modules:      {default_modules}")
        print(f"  Max Dependencies: {default_deps}")
        print()
        
        if self._confirm("Use recommended defaults?"):
            return {
                "max_loc": default_loc,
                "max_files": default_files,
                "max_modules": default_modules,
                "max_dependencies": default_deps
            }
        
        # Custom configuration
        print("\nCustom budget configuration:")
        max_loc = self._prompt_int("Max LOC", default=default_loc)
        max_files = self._prompt_int("Max Files", default=default_files)
        max_modules = self._prompt_int("Max Modules", default=default_modules)
        max_deps = self._prompt_int("Max Dependencies", default=default_deps)
        
        return {
            "max_loc": max_loc,
            "max_files": max_files,
            "max_modules": max_modules,
            "max_dependencies": max_deps
        }
    
    def _configure_permissions(self) -> Dict[str, bool]:
        """
        Configure tool permissions.
        
        Returns:
            Dictionary of permission flags
        """
        print("\n🔒 Step 4: Permissions\n")
        print("Configure what AUREUS is allowed to do:")
        print("  - File read/write: Always allowed")
        print("  - File delete: Requires explicit permission")
        print("  - Shell commands: Requires explicit permission")
        print()
        
        allow_delete = self._confirm("Allow file deletion?", default=False)
        allow_shell = self._confirm("Allow shell command execution?", default=False)
        
        if allow_shell:
            print("  ⚠️  Warning: Shell commands can modify your system")
        
        return {
            "file_delete": allow_delete,
            "shell_exec": allow_shell
        }
    
    def _display_summary(self, config: WizardConfig, info: ProjectInfo):
        """Display configuration summary"""
        print("\n" + "=" * 66)
        print("  📋 Configuration Summary")
        print("=" * 66)
        print(f"\nProject: {config.project_name}")
        print(f"  Language: {info.language}")
        if info.framework:
            print(f"  Framework: {info.framework}")
        print(f"\nModel Provider: {config.model_provider}")
        print(f"  API Key: {'*' * 8 if config.model_api_key else 'None'}")
        print(f"\nBudget Limits:")
        print(f"  Max LOC:          {config.max_loc:,}")
        print(f"  Max Files:        {config.max_files}")
        print(f"  Max Modules:      {config.max_modules}")
        print(f"  Max Dependencies: {config.max_dependencies}")
        print(f"\nPermissions:")
        print(f"  File deletion:    {'Allowed' if config.allow_file_delete else 'Prompt required'}")
        print(f"  Shell commands:   {'Allowed' if config.allow_shell_exec else 'Prompt required'}")
        print()
    
    def _create_policy(self, config: WizardConfig) -> Policy:
        """Create Policy object from wizard config"""
        budget = Budget(
            max_loc=config.max_loc,
            max_modules=config.max_modules,
            max_files=config.max_files,
            max_dependencies=config.max_dependencies
        )
        
        policy = Policy(
            version="1.0",
            project_name=config.project_name,
            project_root=self.project_root,
            budgets=budget,
            permissions={
                "tools": {
                    "file_read": "allow",
                    "file_write": "allow",
                    "file_delete": "allow" if config.allow_file_delete else "prompt",
                    "shell_exec": "allow" if config.allow_shell_exec else "prompt"
                }
            }
        )
        
        return policy
    
    def _save_policy(self, policy: Policy):
        """Save policy to disk"""
        try:
            self.loader.save(policy, self.policy_path)
            print(f"✓ Policy saved: {self.policy_path}")
        except Exception as e:
            print(f"✗ Error saving policy: {e}")
            sys.exit(1)
    
    def _configure_environment(self, provider: str, api_key: str):
        """Configure environment variables"""
        print("\n🔧 Environment Configuration\n")
        print("To persist your API key, add these to your environment:")
        
        if sys.platform == "win32":
            print(f"\n  PowerShell:")
            print(f"    $env:AUREUS_MODEL_PROVIDER=\"{provider}\"")
            print(f"    $env:AUREUS_MODEL_API_KEY=\"{api_key}\"")
            print(f"\n  Command Prompt:")
            print(f"    set AUREUS_MODEL_PROVIDER={provider}")
            print(f"    set AUREUS_MODEL_API_KEY={api_key}")
        else:
            print(f"\n  Bash/Zsh:")
            print(f"    export AUREUS_MODEL_PROVIDER={provider}")
            print(f"    export AUREUS_MODEL_API_KEY={api_key}")
            print(f"\n  Fish:")
            print(f"    set -Ux AUREUS_MODEL_PROVIDER {provider}")
            print(f"    set -Ux AUREUS_MODEL_API_KEY {api_key}")
        
        print("\n  Or add to your shell profile (.bashrc, .zshrc, etc.)")
    
    def _print_next_steps(self):
        """Print next steps after setup"""
        print("\n" + "=" * 66)
        print("  ✅ Setup Complete!")
        print("=" * 66)
        print("\nNext steps:")
        print("  1. Try your first build:")
        print("     aureus code \"add a hello world function\"")
        print("\n  2. Check your budget:")
        print("     aureus budget")
        print("\n  3. Learn more:")
        print("     aureus --help")
        print("\nHappy coding! 🎉\n")
    
    # Helper methods
    
    def _prompt(self, message: str, default: str = "", secret: bool = False) -> str:
        """Prompt user for input"""
        if default:
            prompt_text = f"{message} [{default}]: "
        else:
            prompt_text = f"{message}: "
        
        if secret:
            import getpass
            value = getpass.getpass(prompt_text)
        else:
            value = input(prompt_text).strip()
        
        return value if value else default
    
    def _prompt_int(self, message: str, default: int) -> int:
        """Prompt user for integer input"""
        while True:
            value = self._prompt(message, default=str(default))
            try:
                return int(value)
            except ValueError:
                print(f"  Invalid input, please enter a number")
    
    def _confirm(self, message: str, default: bool = True) -> bool:
        """Prompt user for yes/no confirmation"""
        default_str = "Y/n" if default else "y/N"
        response = input(f"{message} [{default_str}]: ").strip().lower()
        
        if not response:
            return default
        
        return response in ["y", "yes"]
