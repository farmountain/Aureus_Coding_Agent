"""
UVUAS Agent Swarm Architecture

Unified goal-driven agent swarm for code generation.
Multiple specialized agents coordinate to build high-quality code.
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Any, Optional
from pathlib import Path


class AgentRole(Enum):
    """Agent roles in the swarm"""
    COORDINATOR = "coordinator"  # Orchestrates the swarm
    CODE_GENERATOR = "code_generator"  # Generates implementation code
    TEST_WRITER = "test_writer"  # Generates tests
    REFACTOR = "refactor"  # Improves code quality
    VALIDATOR = "validator"  # Validates correctness
    ARCHITECT = "architect"  # Designs structure


@dataclass
class AgentMessage:
    """Message between agents"""
    sender: str
    receiver: str
    message_type: str  # request | response | notification
    content: Dict[str, Any]
    priority: int = 5  # 1-10, higher is more urgent


@dataclass
class AgentTask:
    """Task for an agent"""
    task_id: str
    role: AgentRole
    description: str
    inputs: Dict[str, Any]
    dependencies: List[str] = None  # Task IDs this depends on
    status: str = "pending"  # pending | in_progress | completed | failed
    result: Any = None
    error: Optional[str] = None


class BaseAgent:
    """Base class for all agents in the swarm"""
    
    def __init__(self, agent_id: str, role: AgentRole):
        self.agent_id = agent_id
        self.role = role
        self.inbox: List[AgentMessage] = []
        self.outbox: List[AgentMessage] = []
        self.current_task: Optional[AgentTask] = None
        self.completed_tasks: List[AgentTask] = []
    
    def receive_message(self, message: AgentMessage):
        """Receive a message from another agent"""
        self.inbox.append(message)
    
    def send_message(self, message: AgentMessage):
        """Send a message to another agent"""
        self.outbox.append(message)
    
    def execute_task(self, task: AgentTask) -> AgentTask:
        """Execute a task - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement execute_task")
    
    def get_capabilities(self) -> List[str]:
        """Return list of capabilities - to be overridden"""
        return []


class CoordinatorAgent(BaseAgent):
    """
    Orchestrates the agent swarm
    
    Responsibilities:
    - Breaks down user intent into tasks
    - Assigns tasks to specialist agents
    - Manages dependencies
    - Aggregates results
    - Enforces global value function alignment
    """
    
    def __init__(self, global_value_memory=None):
        super().__init__("coordinator", AgentRole.COORDINATOR)
        self.agents: Dict[AgentRole, BaseAgent] = {}
        self.task_queue: List[AgentTask] = []
        self.global_value_memory = global_value_memory
        
        # Register coordinator with global value function
        if self.global_value_memory:
            self.global_value_memory.register_agent(
                agent_id="coordinator",
                agent_role="orchestration",
                local_goals=["task_coordination", "result_aggregation", "alignment_enforcement"]
            )
    
    def register_agent(self, agent: BaseAgent):
        """Register a specialist agent"""
        self.agents[agent.role] = agent
    
    def decompose_intent(self, intent: str, spec: 'Specification') -> List[AgentTask]:
        """
        Break down intent into agent tasks
        
        Example flow:
        1. Architect designs structure
        2. CodeGenerator generates implementation
        3. TestWriter generates tests
        4. Validator runs tests
        5. Refactor improves code (if needed)
        """
        tasks = []
        
        # Task 1: Architecture design
        tasks.append(AgentTask(
            task_id="task_1_arch",
            role=AgentRole.ARCHITECT,
            description="Design code structure",
            inputs={"intent": intent, "spec": spec}
        ))
        
        # Task 2: Code generation (depends on architecture)
        tasks.append(AgentTask(
            task_id="task_2_codegen",
            role=AgentRole.CODE_GENERATOR,
            description="Generate implementation",
            inputs={"intent": intent, "spec": spec},
            dependencies=["task_1_arch"]
        ))
        
        # Task 3: Test generation (depends on code)
        tasks.append(AgentTask(
            task_id="task_3_tests",
            role=AgentRole.TEST_WRITER,
            description="Generate tests",
            inputs={"intent": intent},
            dependencies=["task_2_codegen"]
        ))
        
        # Task 4: Validation
        tasks.append(AgentTask(
            task_id="task_4_validate",
            role=AgentRole.VALIDATOR,
            description="Run tests and validate",
            inputs={},
            dependencies=["task_2_codegen", "task_3_tests"]
        ))
        
        return tasks
    
    def execute_workflow(self, tasks: List[AgentTask]) -> Dict[str, Any]:
        """
        Execute tasks with dependency management and global value alignment
        
        Returns:
            Results aggregated from all agents
        """
        results = {}
        completed_task_ids = set()
        
        while len(completed_task_ids) < len(tasks):
            # Find tasks ready to execute (dependencies met)
            ready_tasks = [
                task for task in tasks
                if task.task_id not in completed_task_ids
                and (not task.dependencies or all(dep in completed_task_ids for dep in task.dependencies))
            ]
            
            if not ready_tasks:
                break  # No more tasks can be executed
            
            # Execute ready tasks
            for task in ready_tasks:
                agent = self.agents.get(task.role)
                if agent:
                    # Pass previous results as input
                    if task.dependencies:
                        for dep_id in task.dependencies:
                            task.inputs[dep_id] = results.get(dep_id)
                    
                    # Execute
                    result_task = agent.execute_task(task)
                    
                    # ===== GLOBAL VALUE FUNCTION VALIDATION =====
                    if self.global_value_memory and result_task.result:
                        action = {
                            "type": f"{task.role.value}_output",
                            "result": result_task.result,
                            "task_id": task.task_id
                        }
                        state = {
                            "completed_tasks": list(completed_task_ids),
                            "intent": task.inputs.get("intent", "")
                        }
                        
                        aligned, warnings = self.global_value_memory.validate_agent_action(
                            agent_id=agent.agent_id,
                            action=action,
                            state=state
                        )
                        
                        if not aligned:
                            print(f"⚠️ Task {task.task_id} not aligned with global goals:")
                            for warning in warnings:
                                print(f"   - {warning}")
                    
                    results[task.task_id] = result_task.result
                    completed_task_ids.add(task.task_id)
        
        return results


class CodeGeneratorAgent(BaseAgent):
    """
    Specialist agent for code generation
    
    Uses LLM with enhanced prompts to generate high-quality code
    """
    
    def __init__(self, model_provider, context_gatherer=None):
        super().__init__("code_generator", AgentRole.CODE_GENERATOR)
        self.model_provider = model_provider
        self.context_gatherer = context_gatherer
    
    def execute_task(self, task: AgentTask) -> AgentTask:
        """Generate code based on task inputs"""
        intent = task.inputs.get("intent")
        spec = task.inputs.get("spec")
        architecture = task.inputs.get("task_1_arch")  # From architect
        
        # Build enhanced prompt
        prompt = self._build_prompt(intent, spec, architecture)
        
        # Generate code
        response = self.model_provider.complete(prompt)
        
        task.status = "completed"
        task.result = {
            "code": response.content,
            "files": self._extract_files(response.content)
        }
        
        return task
    
    def _build_prompt(self, intent, spec, architecture) -> str:
        """Build comprehensive prompt for code generation"""
        prompt = f"Generate Python code for: {intent}\n\n"
        
        if architecture:
            prompt += f"Architecture: {architecture}\n\n"
        
        prompt += "Requirements:\n"
        prompt += "- Complete, working code\n"
        prompt += "- Type hints and docstrings\n"
        prompt += "- Follow best practices\n"
        
        return prompt
    
    def _extract_files(self, content: str) -> List[Dict[str, str]]:
        """Extract file paths and code from LLM response"""
        import re
        files = []
        
        # Match FILE: path and ```python code ``` blocks
        file_matches = re.finditer(r'FILE:\s*(\S+)', content)
        code_matches = re.finditer(r'```python\n(.*?)\n```', content, re.DOTALL)
        
        for file_match, code_match in zip(file_matches, code_matches):
            files.append({
                "path": file_match.group(1),
                "code": code_match.group(1)
            })
        
        return files


class TestWriterAgent(BaseAgent):
    """
    Specialist agent for test generation
    
    Analyzes generated code and creates comprehensive tests
    """
    
    def __init__(self, model_provider):
        super().__init__("test_writer", AgentRole.TEST_WRITER)
        self.model_provider = model_provider
    
    def execute_task(self, task: AgentTask) -> AgentTask:
        """Generate tests for generated code"""
        code_result = task.inputs.get("task_2_codegen")
        
        if not code_result:
            task.status = "failed"
            task.error = "No code to test"
            return task
        
        # Analyze code and generate tests
        tests = self._generate_tests(code_result["files"])
        
        task.status = "completed"
        task.result = {
            "test_files": tests
        }
        
        return task
    
    def _generate_tests(self, files: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Generate test files for implementation files"""
        test_files = []
        
        for file_info in files:
            # Generate test using LLM
            prompt = f"""Generate pytest tests for this code:

```python
{file_info['code']}
```

Include:
- Unit tests for all functions/methods
- Edge cases
- Error conditions
"""
            
            response = self.model_provider.complete(prompt)
            
            test_files.append({
                "path": f"test_{Path(file_info['path']).name}",
                "code": response.content
            })
        
        return test_files


class ValidatorAgent(BaseAgent):
    """
    Specialist agent for validation
    
    Runs tests and validates code quality
    """
    
    def __init__(self):
        super().__init__("validator", AgentRole.VALIDATOR)
    
    def execute_task(self, task: AgentTask) -> AgentTask:
        """Validate code and tests"""
        code_result = task.inputs.get("task_2_codegen")
        test_result = task.inputs.get("task_3_tests")
        
        validation_results = {
            "syntax_valid": True,
            "tests_passed": False,
            "issues": []
        }
        
        # TODO: Run actual validation
        # For now, mark as completed
        
        task.status = "completed"
        task.result = validation_results
        
        return task


# Factory to create agent swarm
def create_agent_swarm(model_provider, global_value_memory=None) -> CoordinatorAgent:
    """Create and initialize the agent swarm with global value alignment"""
    coordinator = CoordinatorAgent(global_value_memory=global_value_memory)
    
    # Register specialist agents
    code_gen = CodeGeneratorAgent(model_provider)
    test_writer = TestWriterAgent(model_provider)
    validator = ValidatorAgent()
    
    # Register agents with global value function
    if global_value_memory:
        global_value_memory.register_agent(
            agent_id=code_gen.agent_id,
            agent_role="code_generation",
            local_goals=["code_completeness", "code_correctness", "best_practices"]
        )
        global_value_memory.register_agent(
            agent_id=test_writer.agent_id,
            agent_role="test_generation",
            local_goals=["test_coverage", "edge_cases", "test_quality"]
        )
        global_value_memory.register_agent(
            agent_id=validator.agent_id,
            agent_role="validation",
            local_goals=["correctness", "quality_gates", "compliance"]
        )
    
    coordinator.register_agent(code_gen)
    coordinator.register_agent(test_writer)
    coordinator.register_agent(validator)
    
    return coordinator
