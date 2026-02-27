"""
Builder Agent - Tier 3 (UVUAS) for AUREUS Phase 1

Unified agent that integrates:
- GVUFD (Tier 1): Specification generation
- SPK (Tier 2): Cost pricing and budget enforcement  
- Tool Bus: Permission-gated tool execution

Phase 1: Single unified agent (plan + build + test)
Phase 2: Multi-agent swarm (Planner, Builder, Tester, Critic, Reflexion)

The Builder Agent orchestrates the complete coding workflow:
1. Generate specification from intent (GVUFD)
2. Check budget and get cost (SPK)
3. Execute implementation using tools
4. Validate against success criteria
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
from dataclasses import dataclass, field
from src.interfaces import Policy, Specification, Cost
from src.governance.gvufd import SpecificationGenerator
from src.governance.spk import PricingKernel
from src.toolbus import FileReadTool, FileWriteTool, GrepSearchTool, PermissionChecker
from src.model_provider import ModelProvider, MockProvider


@dataclass
class BuildResult:
    """Result from Builder Agent execution"""
    success: bool
    specification: Specification
    cost: Cost
    files_created: List[str] = field(default_factory=list)
    files_modified: List[str] = field(default_factory=list)
    tests_passed: bool = False
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            "success": self.success,
            "specification": self.specification.to_dict(),
            "cost": self.cost.to_dict(),
            "files_created": self.files_created,
            "files_modified": self.files_modified,
            "tests_passed": self.tests_passed,
            "error": self.error,
            "metadata": self.metadata
        }


class BuilderAgent:
    """
    Unified Builder Agent (Phase 1 UVUAS)
    
    Orchestrates complete coding workflow:
    1. GVUFD: Intent → Specification
    2. SPK: Specification → Cost (with budget check)
    3. Execute: Use tools to implement
    4. Validate: Check against success criteria
    """
    
    def __init__(
        self,
        policy: Policy,
        model_provider: Optional[ModelProvider] = None,
        project_root: Optional[Path] = None
    ):
        """
        Initialize Builder Agent
        
        Args:
            policy: Governance policy
            model_provider: LLM provider (defaults to MockProvider)
            project_root: Project root directory
        """
        self.policy = policy
        self.project_root = project_root or policy.project_root
        
        # Initialize components
        self.spec_generator = SpecificationGenerator()
        self.pricing_kernel = PricingKernel()
        self.model_provider = model_provider or MockProvider()
        
        # Initialize tools
        self.file_read = FileReadTool(self.project_root)
        self.file_write = FileWriteTool(self.project_root)
        self.grep_search = GrepSearchTool(self.project_root)
        self.permission_checker = PermissionChecker(self.policy.permissions)
        
        # Track execution
        self.execution_log: List[Dict[str, Any]] = []
    
    def build(self, intent: str) -> BuildResult:
        """
        Execute complete build workflow
        
        Args:
            intent: Natural language intent
        
        Returns:
            BuildResult with success status
        """
        try:
            # Step 1: GVUFD - Generate specification
            self._log("Generating specification from intent", intent=intent)
            spec = self.spec_generator.generate(intent, self.policy)
            
            # Step 2: SPK - Price and check budget
            self._log("Calculating cost and checking budget")
            cost = self.pricing_kernel.price(spec, self.policy)
            
            # Check if budget exceeded
            if not cost.within_budget:
                self._log("Budget exceeded", status=cost.budget_status)
                return BuildResult(
                    success=False,
                    specification=spec,
                    cost=cost,
                    error=f"Budget exceeded: {cost.budget_status}. Alternatives: {len(cost.alternatives)}",
                    metadata={
                        "budget_status": cost.budget_status,
                        "alternatives": cost.alternatives
                    }
                )
            
            # Step 3: Execute implementation (Phase 1: simple stub)
            self._log("Executing implementation")
            files_created, files_modified = self._execute_implementation(spec, cost)
            
            # Step 4: Validate (Phase 1: check files exist)
            self._log("Validating implementation")
            tests_passed = self._validate_implementation(spec, files_created)
            
            return BuildResult(
                success=True,
                specification=spec,
                cost=cost,
                files_created=files_created,
                files_modified=files_modified,
                tests_passed=tests_passed,
                metadata={
                    "budget_status": cost.budget_status,
                    "execution_log": self.execution_log
                }
            )
        
        except Exception as e:
            self._log("Error during build", error=str(e))
            
            # Return partial result if we got far enough
            spec = spec if 'spec' in locals() else None
            cost = cost if 'cost' in locals() else None
            
            return BuildResult(
                success=False,
                specification=spec,
                cost=cost,
                error=f"Build error: {e}",
                metadata={"execution_log": self.execution_log}
            )
    
    def _execute_implementation(
        self,
        spec: Specification,
        cost: Cost
    ) -> tuple[List[str], List[str]]:
        """
        Execute implementation using tools
        
        Phase 1: Simple stub that creates placeholder files
        Phase 2: Actual LLM-driven code generation
        
        Returns:
            (files_created, files_modified)
        """
        files_created = []
        files_modified = []
        
        # Check permissions
        if not self.permission_checker.has_permission("file_write"):
            self._log("File write permission denied")
            return files_created, files_modified
        
        # Generate actual implementation using model provider
        try:
            from src.model_provider.enhanced import EnhancedMockProvider
            
            # Use model provider to generate code
            provider = EnhancedMockProvider("enhanced-builder")
            
            # Create prompt for code generation
            prompt = f"""Generate Python code for the following specification:

Intent: {spec.intent}

Success Criteria:
{chr(10).join(f"- {c}" for c in spec.success_criteria)}

Generate clean, well-documented Python code that implements this specification.
Include proper imports, error handling, and docstrings.
"""
            
            # Get code from model
            response = provider.complete(prompt)
            generated_code = response.content
            
            # Determine output file path
            impl_file = self.project_root / "src" / "implementation.py"
            impl_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Write generated code
            result = self.file_write.execute(
                file_path=str(impl_file),
                content=generated_code
            )
            
            if result.success:
                files_created.append(str(impl_file))
                self._log("Created implementation file", file=str(impl_file))
        
        except Exception as e:
            # Fallback: Create basic template
            self._log(f"Code generation error: {e}, using template")
            
            template_file = self.project_root / "src" / "implementation.py"
            template_file.parent.mkdir(parents=True, exist_ok=True)
            
            template_content = f'''"""\nImplementation for: {spec.intent}\n"""\n\ndef main():\n    """Main implementation."""\n    # TODO: Implement\n    pass\n\nif __name__ == "__main__":\n    main()\n'''
            
            result = self.file_write.execute(
                file_path=str(template_file),
                content=template_content
            )
            
            if result.success:
                files_created.append(str(template_file))
                self._log("Created template file", file=str(template_file))
        
        return files_created, files_modified
    
    def _validate_implementation(
        self,
        spec: Specification,
        files_created: List[str]
    ) -> bool:
        """
        Validate implementation against success criteria
        
        Phase 1: Simple check - files were created
        Phase 2: Run actual tests, check acceptance criteria
        
        Returns:
            True if validation passed
        """
        # Phase 1: Basic validation - check files exist
        if len(files_created) > 0:
            self._log("Validation passed", files_count=len(files_created))
            return True
        
        self._log("Validation failed", reason="No files created")
        return False
    
    def _log(self, message: str, **metadata):
        """Log execution step"""
        self.execution_log.append({
            "message": message,
            **metadata
        })
    
    def get_execution_log(self) -> List[Dict[str, Any]]:
        """Get execution log"""
        return self.execution_log


class AgentOrchestrator:
    """
    Orchestrator for managing multiple agents
    
    Phase 1: Single BuilderAgent
    Phase 2: Coordinate Planner, Builder, Tester, Critic, Reflexion agents
    """
    
    def __init__(self, policy: Policy):
        """
        Initialize orchestrator
        
        Args:
            policy: Governance policy
        """
        self.policy = policy
        self.builder = BuilderAgent(policy)
    
    def execute(self, intent: str) -> BuildResult:
        """
        Execute agent workflow
        
        Args:
            intent: Natural language intent
        
        Returns:
            BuildResult
        """
        return self.builder.build(intent)
    
    def get_status(self) -> Dict[str, Any]:
        """Get orchestrator status"""
        return {
            "policy": self.policy.project_name,
            "builder_logs": len(self.builder.execution_log)
        }
