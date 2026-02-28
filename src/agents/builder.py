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

from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, field
from src.interfaces import Policy, Specification, Cost
from src.governance.gvufd import SpecificationGenerator
from src.governance.spk import PricingKernel
from src.toolbus import FileReadTool, FileWriteTool, GrepSearchTool, PermissionChecker
from src.model_provider import ModelProvider, MockProvider
from src.agents.file_placement import FilePlacementEngine
from src.coordination.three_tier_coordinator import ThreeTierCoordinator


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
        
        # Initialize memory system
        from src.memory.build_memory import BuildMemory
        from src.memory.global_value_function import GlobalValueMemory
        self.memory = BuildMemory()
        self.global_value_memory = GlobalValueMemory()
        
        # Register this agent with global value function
        self.global_value_memory.register_agent(
            agent_id="builder_agent",
            agent_role="unified_builder",
            local_goals=["code_generation", "validation", "refinement"]
        )
        
        # Initialize tools
        self.file_read = FileReadTool(self.project_root)
        self.file_write = FileWriteTool(self.project_root)
        self.grep_search = GrepSearchTool(self.project_root)
        
        # Extract tool permissions from policy (handle nested structure)
        tool_permissions = {}
        if isinstance(self.policy.permissions, dict):
            if 'tools' in self.policy.permissions:
                # Convert 'allow'/'deny'/'prompt' to boolean
                for key, value in self.policy.permissions['tools'].items():
                    tool_permissions[key] = (value == 'allow')
            else:
                # Flat structure
                for key, value in self.policy.permissions.items():
                    tool_permissions[key] = (value == 'allow' if isinstance(value, str) else value)
        
        self.permission_checker = PermissionChecker(tool_permissions)
        
        # Initialize file placement intelligence
        self.file_placement = FilePlacementEngine(self.project_root)
        
        # Initialize 3-tier coordinator (GVUFD → SPK → UVUAS)
        self.coordinator = ThreeTierCoordinator(
            policy=self.policy,
            global_value_memory=self.global_value_memory,
            workspace_root=self.project_root
        )
        
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
        # Use coordinated 3-tier flow instead of sequential
        return self._coordinated_build(intent)
    
    def _coordinated_build(self, intent: str) -> BuildResult:
        """
        Execute build using 3-tier coordination (GVUFD → SPK → UVUAS).
        
        This ensures tight integration:
        - GVUFD extracts goals from intent → updates global value function
        - SPK generates spec variants → selects by value alignment
        - UVUAS executes with Claude Code loop (Context → Execute → Reflect)
        """
        try:
            # Execute coordinated flow
            coord_result = self.coordinator.coordinate(intent)
            
            # Log coordination
            self._log("3-Tier Coordination Complete", 
                     goals=coord_result.get("goals_extracted"),
                     alignment=coord_result.get("alignment_score"))
            
            # Check if coordination succeeded
            if "error" in coord_result:
                return BuildResult(
                    success=False,
                    specification=coord_result.get("spec"),
                    cost=coord_result.get("cost"),
                    error=coord_result["error"],
                    metadata={"coordination_log": coord_result["coordination_log"]}
                )
            
            # Get selected spec and cost from coordination
            spec = coord_result["selected_spec"]
            cost = coord_result["cost"]
            alignment_score = coord_result["alignment_score"]
            
            # Execute implementation with coordinated context
            files_created, files_modified = self._execute_coordinated_implementation(
                spec, cost, coord_result
            )
            
            # Validate with reflection
            tests_passed = self._validate_implementation(spec, files_created)
            
            if tests_passed:
                # Record in memory
                self.memory.record_build(
                    intent=intent,
                    specification=spec,
                    files_created=files_created,
                    success=True,
                    attempts=1,
                    cost=cost.total
                )
                
                return BuildResult(
                    success=True,
                    specification=spec,
                    cost=cost,
                    files_created=files_created,
                    files_modified=files_modified,
                    metadata={
                        "coordination_log": coord_result["coordination_log"],
                        "alignment_score": alignment_score,
                        "optimization_target": coord_result["goals_extracted"].optimization_target
                    }
                )
            else:
                return BuildResult(
                    success=False,
                    specification=spec,
                    cost=cost,
                    error="Validation failed",
                    metadata={"coordination_log": coord_result["coordination_log"]}
                )
        
        except Exception as e:
            self._log("Build failed with exception", error=str(e))
            import traceback
            traceback.print_exc()
            
            # Create a minimal spec for error case
            from src.interfaces import SpecificationBudget
            error_spec = Specification(
                intent=intent,
                success_criteria=["Error occurred"],
                budgets=SpecificationBudget(
                    max_loc_delta=0,
                    max_new_files=0,
                    max_new_dependencies=0
                ),
                risk_level="low"
            )
            error_cost = Cost(
                loc=0,
                dependencies=0,
                abstractions=0,
                total=0,
                within_budget=False,
                budget_status="error"
            )
            
            return BuildResult(
                success=False,
                specification=error_spec,
                cost=error_cost,
                error=f"Build failed: {str(e)}"
            )
    
    def _legacy_build(self, intent: str) -> BuildResult:
        """
        Legacy sequential build workflow (kept for comparison)
        
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
            
            # Step 3: Execute implementation with iterative refinement
            self._log("Executing implementation")
            max_attempts = 3
            last_error = None
            
            for attempt in range(max_attempts):
                self._log("Generation attempt", attempt=attempt + 1, max_attempts=max_attempts)
                
                # Generate code
                files_created, files_modified = self._execute_implementation(
                    spec, cost, 
                    previous_error=last_error if attempt > 0 else None,
                    attempt=attempt + 1
                )
                
                # Validate
                self._log("Validating implementation")
                tests_passed = self._validate_implementation(spec, files_created)
                
                if tests_passed:
                    # Success!
                    self._log("Implementation validated successfully", attempt=attempt + 1)
                    
                    # Record successful build in memory
                    self.memory.record_build(
                        intent=intent,
                        success=True,
                        files_created=files_created,
                        attempts=attempt + 1,
                        cost=cost.total
                    )
                    
                    return BuildResult(
                        success=True,
                        specification=spec,
                        cost=cost,
                        files_created=files_created,
                        files_modified=files_modified,
                        tests_passed=tests_passed,
                        metadata={
                            "budget_status": cost.budget_status,
                            "execution_log": self.execution_log,
                            "attempts": attempt + 1
                        }
                    )
                else:
                    # Validation failed - capture error and retry
                    last_error = self._extract_validation_error()
                    self._log("Validation failed, will retry", 
                             attempt=attempt + 1,
                             error=last_error)
                    
                    # Clean up failed files for retry
                    for file_path in files_created:
                        try:
                            Path(file_path).unlink()
                        except:
                            pass
            
            # All attempts exhausted
            error_msg = f"Failed after {max_attempts} attempts. Last error: {last_error}"
            
            # Record failed build in memory
            self.memory.record_build(
                intent=intent,
                success=False,
                files_created=[],
                attempts=max_attempts,
                cost=cost.total,
                error=error_msg
            )
            
            return BuildResult(
                success=False,
                specification=spec,
                cost=cost,
                files_created=[],
                files_modified=[],
                tests_passed=False,
                error=error_msg,
                metadata={
                    "budget_status": cost.budget_status,
                    "execution_log": self.execution_log,
                    "attempts": max_attempts
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
        cost: Cost,
        previous_error: Optional[str] = None,
        attempt: int = 1
    ) -> tuple[List[str], List[str]]:
        """
        Execute implementation using tools
        
        Integrates GVUFD→SPK→UVUAS pipeline:
        - GVUFD provides specification with intent and success criteria
        - SPK has validated budget and provided cost breakdown
        - UVUAS (this method) generates code within constraints
        
        Uses the configured model provider (OpenAI, Anthropic, or Mock) to
        generate actual code based on the specification.
        
        Args:
            spec: Specification from GVUFD
            cost: Cost from SPK
            previous_error: Error from previous attempt (for refinement)
            attempt: Current attempt number
        
        Returns:
            (files_created, files_modified)
        """
        files_created = []
        files_modified = []
        
        # Check permissions
        if not self.permission_checker.has_permission("file_write"):
            self._log("File write permission denied")
            return files_created, files_modified
        
        # CONTEXT GATHERING: Read existing files for patterns
        context = self._gather_context(spec.intent)
        
        # MEMORY LOOKUP: Find similar successful builds
        similar_builds = self.memory.find_similar_intents(spec.intent, limit=3)
        
        # Generate actual implementation using model provider
        try:
            # Create comprehensive prompt with GVUFD spec and SPK cost breakdown
            prompt = f"""Generate Python code for the following specification:

Intent: {spec.intent}

Success Criteria:
{chr(10).join(f"- {criterion}" for criterion in spec.success_criteria)}

Budget Constraints (SPK-validated):
- Max LOC: {spec.budgets.max_loc_delta} (Cost: {cost.loc})
- Max new files: {spec.budgets.max_new_files}
- Max dependencies: {spec.budgets.max_new_dependencies} (Cost: {cost.dependencies})
- Max abstractions: {spec.budgets.max_new_abstractions} (Cost: {cost.abstractions})
- Total complexity cost: {cost.total}

Risk Level: {spec.risk_level}
"""

            # Add context from existing codebase
            if context["relevant_files"]:
                prompt += "\nEXISTING CODEBASE CONTEXT:\n"
                prompt += f"Found {len(context['relevant_files'])} related files:\n"
                for file_info in context["relevant_files"][:3]:  # Top 3 most relevant
                    prompt += f"\nFile: {file_info['path']}\n"
                    prompt += f"Preview: {file_info['preview']}\n"
                prompt += "\nPlease follow similar patterns and style from the existing codebase.\n"
            
            # Add memory context - similar successful builds
            if similar_builds:
                prompt += "\nSIMILAR SUCCESSFUL BUILDS (from memory):\n"
                for build in similar_builds:
                    prompt += f"- Intent: '{build.intent}' → Created: {', '.join([Path(f).name for f in build.files_created])}\n"
                prompt += "\nConsider using similar approaches that have succeeded before.\n"

            # Add refinement context if this is a retry
            if previous_error and attempt > 1:
                prompt += f"""
PREVIOUS ATTEMPT FAILED:
Attempt #{attempt - 1} failed with error:
{previous_error}

Please fix the issue and generate corrected code.
"""

            prompt += """
Requirements:
1. Generate complete, working Python code
2. Include docstrings and type hints
3. Ensure code meets all success criteria
4. Stay within budget constraints
5. Follow Python best practices
6. Code must be importable without errors
7. All imports must be resolvable

Format your response as:
FILE: <filepath>
```python
<code>
```

If multiple files needed, repeat FILE: and code blocks.
"""
            
            # Get code from model provider
            response = self.model_provider.complete(prompt)
            
            # Parse response and extract file path and code
            code_content = response.content
            self._log("Received LLM response", 
                     attempt=attempt,
                     content_length=len(code_content), 
                     content_preview=code_content[:200])
            
            # Debug: Print full response to see what we got
            print(f"\n=== LLM RESPONSE DEBUG ===\n{code_content}\n=== END DEBUG ===\n")
            
            # Simple parsing: look for FILE: and ```python blocks
            import re
            file_match = re.search(r'FILE:\s*(\S+)', code_content)
            code_match = re.search(r'```python\n(.*?)\n```', code_content, re.DOTALL)
            
            if code_match:
                code = code_match.group(1)
                
                # ===== GLOBAL VALUE FUNCTION VALIDATION =====
                # Check if generated code aligns with global goals
                action = {
                    "type": "code_generation",
                    "code": code,
                    "intent": spec.intent,
                    "patterns": self._extract_code_patterns(code)
                }
                
                state = {
                    "existing_files": list(self.project_root.glob("**/*.py")),
                    "patterns": context.get("patterns", []),
                    "intent": spec.intent
                }
                
                aligned, warnings = self.global_value_memory.validate_agent_action(
                    agent_id="builder_agent",
                    action=action,
                    state=state
                )
                
                if warnings:
                    self._log("Global value function warnings", warnings=warnings)
                    for warning in warnings:
                        print(f"⚠️  {warning}")
                
                if not aligned:
                    self._log("Action not aligned with global value function", warnings=warnings)
                    # Continue anyway for now, but log the misalignment
                
                # Determine file path using intelligent placement
                if file_match:
                    suggested_filepath = file_match.group(1)
                else:
                    # Generate filename from intent
                    words = spec.intent.split()
                    filename = '_'.join([w.lower() for w in words if w.isalnum()])[:30] + '.py'
                    suggested_filepath = filename
                
                # Use intelligent file placement engine
                target_path = self.file_placement.determine_file_path(
                    filename=Path(suggested_filepath).name,  # Extract just the filename
                    intent=spec.intent,
                    suggested_path=suggested_filepath if file_match else None
                )
                
                self._log("Determined file placement", 
                         target_path=str(target_path),
                         role=target_path.parent.name,
                         structure=self.file_placement.get_structure_summary())
                
                # Create directories if needed
                target_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Write the file
                target_path.write_text(code)
                
                files_created.append(str(target_path))
                self._log("Generated code file", filepath=str(target_path), lines=len(code.split('\n')))
            else:
                self._log("Could not parse LLM response - no Python code block found", response_preview=code_content[:300])
        
        except Exception as e:
            self._log("Error generating code", error=str(e))
        
        return files_created, files_modified
    
    def _execute_coordinated_implementation(
        self,
        spec: Specification,
        cost: Cost,
        coord_result: Dict[str, Any]
    ) -> Tuple[List[str], List[str]]:
        """
        Execute implementation using coordinated context from 3-tier flow.
        
        This uses the context gathered by ClaudeCodeLoop (Context → Execute → Reflect).
        """
        files_created = []
        files_modified = []
        
        # Extract context from coordination
        context = coord_result.get("execution_result", {})
        intent_goals = coord_result.get("goals_extracted")
        
        # Build prompt with coordination context
        prompt = f"""Generate Python code for the following specification.

INTENT: {spec.intent}
DESCRIPTION: {spec.description}

GLOBAL GOALS (from intent analysis):
- Optimization Target: {intent_goals.optimization_target if intent_goals else 'balance'}
- Explicit Goals: {', '.join(intent_goals.explicit_goals) if intent_goals else 'none'}
- Alignment Score Required: {coord_result.get('alignment_score', 0.0):.2f}

SUCCESS CRITERIA:
{chr(10).join(f'- {c}' for c in spec.success_criteria)}

BUDGET:
- Max LOC: {spec.budgets.max_loc_delta}
- Max dependencies: {spec.budgets.max_new_dependencies}
- Max abstractions: {spec.budgets.max_new_abstractions}

RISK LEVEL: {spec.risk_level}

COORDINATION CONTEXT:
{chr(10).join(coord_result.get('coordination_log', [])[-5:])}

Generate complete, working code that aligns with the global goals.
Return ONLY the code, no explanations.
"""
        
        # Generate code
        response = self.model_provider.generate(prompt)
        code = response.strip()
        
        # Extract code if wrapped in markdown
        if "```python" in code:
            code = code.split("```python")[1].split("```")[0].strip()
        elif "```" in code:
            code = code.split("```")[1].split("```")[0].strip()
        
        # Validate alignment before writing
        patterns = self._extract_code_patterns(code)
        action = {
            "type": "code_generation",
            "code": code,
            "patterns": patterns,
            "spec": spec.dict() if hasattr(spec, 'dict') else str(spec)
        }
        
        aligned, warnings = self.global_value_memory.validate_agent_action(
            agent_id="builder_agent",
            action=action,
            expected_goals=intent_goals.explicit_goals if intent_goals else []
        )
        
        if not aligned:
            self._log("⚠️ Generated code not fully aligned with global goals", warnings=warnings)
        
        # Write code
        file_path = self.file_placement.determine_placement(
            intent=spec.intent,
            code_content=code
        )
        
        self.file_write.write(file_path, code)
        files_created.append(str(file_path))
        
        self._log("Implementation complete", 
                 files=files_created, 
                 aligned=aligned)
        
        return files_created, files_modified

    def _validate_implementation(
        self,
        spec: Specification,
        files_created: List[str]
    ) -> bool:
        """
        Validate implementation against success criteria
        
        Phase 2: Run actual tests and execute code in sandbox
        
        Returns:
            True if validation passed
        """
        if len(files_created) == 0:
            self._log("Validation failed", reason="No files created")
            return False
        
        # Execute generated code in sandbox to check for syntax/runtime errors
        validation_results = {
            "syntax_valid": False,
            "imports_valid": False,
            "tests_passed": False,
            "acceptance_criteria_met": False
        }
        
        try:
            # 1. Check syntax validity
            for file_path in files_created:
                if not self._validate_syntax(file_path):
                    self._log("Validation failed", reason=f"Syntax error in {file_path}")
                    return False
            validation_results["syntax_valid"] = True
            
            # 2. Check imports
            for file_path in files_created:
                if not self._validate_imports(file_path):
                    self._log("Validation failed", reason=f"Import error in {file_path}")
                    return False
            validation_results["imports_valid"] = True
            
            # 3. Run acceptance tests if specified
            if spec.acceptance_tests:
                tests_passed = self._run_acceptance_tests(spec, files_created)
                validation_results["tests_passed"] = tests_passed
                if not tests_passed:
                    self._log("Validation failed", reason="Acceptance tests failed")
                    return False
            else:
                validation_results["tests_passed"] = True  # No tests to run
            
            # 4. Verify basic functionality
            if not self._verify_basic_functionality(files_created):
                self._log("Validation failed", reason="Basic functionality verification failed")
                return False
            validation_results["acceptance_criteria_met"] = True
            
            self._log("Validation passed", results=validation_results, files_count=len(files_created))
            return True
            
        except Exception as e:
            self._log("Validation error", error=str(e), results=validation_results)
            return False
    
    def _validate_syntax(self, file_path: str) -> bool:
        """Check if Python file has valid syntax"""
        import ast
        try:
            with open(file_path, 'r') as f:
                code = f.read()
            ast.parse(code)
            self._log("Syntax check passed", file=file_path)
            return True
        except SyntaxError as e:
            self._log("Syntax error", file=file_path, error=str(e), line=e.lineno)
            return False
        except Exception as e:
            self._log("Syntax validation error", file=file_path, error=str(e))
            return False
    
    def _validate_imports(self, file_path: str) -> bool:
        """Check if all imports in file are resolvable"""
        import ast
        import importlib.util
        import sys
        
        try:
            with open(file_path, 'r') as f:
                code = f.read()
            
            tree = ast.parse(code)
            
            # Extract imports
            imports = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name.split('.')[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module.split('.')[0])
            
            # Check each import (skip standard library and relative imports)
            stdlib_modules = sys.stdlib_module_names
            for imp in imports:
                if imp in stdlib_modules:
                    continue
                
                # Try to find the module
                spec = importlib.util.find_spec(imp)
                if spec is None:
                    # Check if it's a local file in workspace
                    workspace_file = Path(self.project_root) / "workspace" / f"{imp}.py"
                    if not workspace_file.exists():
                        self._log("Import not found", file=file_path, import_name=imp)
                        return False
            
            self._log("Import check passed", file=file_path)
            return True
            
        except Exception as e:
            self._log("Import validation error", file=file_path, error=str(e))
            return False
    
    def _run_acceptance_tests(self, spec: Specification, files_created: List[str]) -> bool:
        """Run acceptance tests defined in specification"""
        import subprocess
        import sys
        
        try:
            # For each acceptance test, try to execute basic validation
            for test in spec.acceptance_tests:
                self._log("Running acceptance test", test_name=test.name)
                
                # Generate simple test based on test description
                test_code = self._generate_test_code(test, files_created)
                if test_code:
                    # Execute test
                    result = subprocess.run(
                        [sys.executable, "-c", test_code],
                        capture_output=True,
                        text=True,
                        timeout=5,
                        cwd=self.project_root
                    )
                    
                    if result.returncode != 0:
                        self._log("Acceptance test failed", 
                                 test_name=test.name,
                                 stderr=result.stderr,
                                 stdout=result.stdout)
                        return False
                    
                    self._log("Acceptance test passed", test_name=test.name)
            
            return True
            
        except subprocess.TimeoutExpired:
            self._log("Acceptance test timeout")
            return False
        except Exception as e:
            self._log("Acceptance test error", error=str(e))
            return False
    
    def _generate_test_code(self, test: 'AcceptanceTest', files_created: List[str]) -> str:
        """Generate executable test code from acceptance test description"""
        # Simple heuristic: try to import and instantiate classes
        if not files_created:
            return ""
        
        # Get the main file
        main_file = files_created[0]
        file_name = Path(main_file).stem
        
        # Generate basic import and sanity check
        return f"""
import sys
sys.path.insert(0, '{Path(main_file).parent}')
try:
    import {file_name}
    print("Import successful")
except Exception as e:
    print(f"Import failed: {{e}}")
    sys.exit(1)
"""
    
    def _verify_basic_functionality(self, files_created: List[str]) -> bool:
        """Verify generated code can at least be imported without errors"""
        import subprocess
        import sys
        
        try:
            for file_path in files_created:
                # Try to import the file
                file_name = Path(file_path).stem
                parent_dir = Path(file_path).parent
                
                test_code = f"""
import sys
sys.path.insert(0, '{parent_dir}')
try:
    import {file_name}
    print("OK")
except Exception as e:
    print(f"ERROR: {{e}}")
    sys.exit(1)
"""
                
                result = subprocess.run(
                    [sys.executable, "-c", test_code],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if result.returncode != 0 or "ERROR" in result.stdout:
                    self._log("Basic functionality check failed",
                             file=file_path,
                             error=result.stderr or result.stdout)
                    return False
            
            self._log("Basic functionality verified")
            return True
            
        except Exception as e:
            self._log("Functionality verification error", error=str(e))
            return False
    
    def _extract_validation_error(self) -> str:
        """Extract the last validation error from execution log"""
        # Look backwards through log for error details
        for entry in reversed(self.execution_log):
            if "error" in entry:
                error_msg = entry.get("error", "Unknown error")
                if "stderr" in entry:
                    error_msg += f"\nStderr: {entry['stderr']}"
                if "stdout" in entry:
                    error_msg += f"\nStdout: {entry['stdout']}"
                return error_msg
        return "Validation failed - no specific error captured"
    
    def _gather_context(self, intent: str) -> Dict[str, Any]:
        """
        Gather context from existing codebase for code generation
        
        Uses semantic search and file reading to find related code
        that can inform the LLM about project patterns and style
        
        Args:
            intent: User's intent string
        
        Returns:
            Context dict with relevant_files, project_style, etc.
        """
        context = {
            "relevant_files": [],
            "project_style": None
        }
        
        try:
            # Extract keywords from intent for search
            keywords = self._extract_keywords(intent)
            
            # Search for related files in workspace
            workspace = self.project_root / "workspace"
            if workspace.exists():
                python_files = list(workspace.glob("*.py"))
                
                # Read and score relevance of existing files
                for py_file in python_files[:5]:  # Limit to 5 files
                    try:
                        with open(py_file, 'r') as f:
                            content = f.read()
                        
                        # Simple relevance: check if keywords appear
                        relevance_score = sum(1 for kw in keywords if kw.lower() in content.lower())
                        
                        if relevance_score > 0:
                            context["relevant_files"].append({
                                "path": str(py_file.relative_to(self.project_root)),
                                "preview": content[:300],  # First 300 chars
                                "score": relevance_score
                            })
                    except:
                        continue
                
                # Sort by relevance
                context["relevant_files"].sort(key=lambda x: x["score"], reverse=True)
            
            self._log("Context gathered", 
                     relevant_files_count=len(context["relevant_files"]))
            
        except Exception as e:
            self._log("Context gathering failed", error=str(e))
        
        return context
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract meaningful keywords from intent text"""
        # Remove common stop words
        stop_words = {'a', 'an', 'the', 'with', 'and', 'or', 'for', 'to', 'of', 'in', 'on'}
        words = text.lower().split()
        keywords = [w for w in words if w not in stop_words and len(w) > 3]
        return keywords
    
    def _extract_code_patterns(self, code: str) -> List[str]:
        """Extract patterns from generated code for alignment checking"""
        patterns = []
        
        if "class " in code:
            patterns.append("class_definition")
        if "def " in code:
            patterns.append("function_definition")
        if '"""' in code or "'''" in code:
            patterns.append("docstrings")
        if " -> " in code:
            patterns.append("type_hints")
        if "try:" in code or "except" in code:
            patterns.append("error_handling")
        if "import " in code:
            patterns.append("imports")
        if "@" in code and "def " in code:
            patterns.append("decorators")
        if "raise " in code:
            patterns.append("exception_raising")
        
        return patterns
    
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
