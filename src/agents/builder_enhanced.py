"""
Enhanced Builder Agent with Memory Integration

Extends the base builder with:
- Plan decomposition into subtasks
- Memory and trajectory integration
- Error recovery mechanisms
- Learning from past sessions
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import uuid

from src.agents.builder import BuilderAgent, BuildResult
from src.interfaces import Policy
from src.memory.trajectory import TrajectoryStore, ActionRecord
from src.memory.cost_ledger import CostLedger, CostEntry
from src.memory.summarization import PatternExtractor


class TaskStatus(Enum):
    """Status of a subtask"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class SubTask:
    """A decomposed subtask"""
    id: str
    description: str
    estimated_cost: float
    dependencies: List[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class PlanDecomposer:
    """
    Decomposes high-level intents into executable subtasks
    
    Phase 1: Rule-based decomposition
    Phase 2: LLM-driven decomposition with learned patterns
    """
    
    def __init__(self, policy: Policy):
        """
        Initialize plan decomposer
        
        Args:
            policy: Governance policy
        """
        self.policy = policy
    
    def decompose(self, intent: str) -> List[SubTask]:
        """
        Decompose intent into subtasks
        
        Args:
            intent: High-level intent
            
        Returns:
            List of subtasks
        """
        # Phase 1: Simple rule-based decomposition
        # Look for keywords to identify task types
        
        subtasks = []
        
        # Common patterns
        has_api = any(word in intent.lower() for word in ["api", "endpoint", "route"])
        has_auth = any(word in intent.lower() for word in ["auth", "login", "register"])
        has_db = any(word in intent.lower() for word in ["database", "db", "storage"])
        has_tests = "test" in intent.lower()
        
        # Task 1: Always start with requirements analysis
        task1_id = str(uuid.uuid4())[:8]
        subtasks.append(SubTask(
            id=task1_id,
            description="Analyze requirements and existing code",
            estimated_cost=10.0,
            dependencies=[]
        ))
        
        # Task 2: Implementation (depends on analysis)
        task2_id = str(uuid.uuid4())[:8]
        
        if has_auth:
            desc = "Implement authentication logic"
            cost = 50.0
        elif has_api:
            desc = "Implement API endpoints"
            cost = 40.0
        elif has_db:
            desc = "Set up database schema and models"
            cost = 45.0
        else:
            desc = "Implement core functionality"
            cost = 30.0
        
        subtasks.append(SubTask(
            id=task2_id,
            description=desc,
            estimated_cost=cost,
            dependencies=[task1_id]
        ))
        
        # Task 3: Tests (if needed, depends on implementation)
        if has_tests or len(intent.split()) > 5:  # Complex tasks need tests
            task3_id = str(uuid.uuid4())[:8]
            subtasks.append(SubTask(
                id=task3_id,
                description="Add tests and validation",
                estimated_cost=20.0,
                dependencies=[task2_id]
            ))
        
        return subtasks


class ErrorRecoveryManager:
    """
    Manages error recovery and retry logic
    """
    
    def __init__(self, max_retries: int = 3):
        """
        Initialize error recovery manager
        
        Args:
            max_retries: Maximum retry attempts
        """
        self.max_retries = max_retries
        self.error_counts: Dict[str, int] = {}
        self.error_history: List[Dict[str, Any]] = []
    
    def record_error(
        self,
        operation: str,
        error: str,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Record an error occurrence
        
        Args:
            operation: Operation that failed
            error: Error message
            context: Additional context
        """
        self.error_counts[operation] = self.error_counts.get(operation, 0) + 1
        
        self.error_history.append({
            "operation": operation,
            "error": error,
            "context": context or {},
            "timestamp": datetime.now(),
            "retry_count": self.error_counts[operation]
        })
    
    def should_retry(self, operation: str) -> bool:
        """
        Check if operation should be retried
        
        Args:
            operation: Operation name
            
        Returns:
            True if should retry
        """
        return self.error_counts.get(operation, 0) < self.max_retries
    
    def get_error_count(self, operation: str) -> int:
        """Get error count for operation"""
        return self.error_counts.get(operation, 0)
    
    def suggest_recovery(self, operation: str) -> Optional[Dict[str, Any]]:
        """
        Suggest recovery action based on error history
        
        Args:
            operation: Operation that failed
            
        Returns:
            Recovery suggestion or None
        """
        if operation not in self.error_counts:
            return None
        
        # Simple rule-based recovery suggestions
        # Phase 2: Use learned patterns from memory
        
        if "file_write" in operation:
            return {
                "suggestion": "Check file permissions",
                "action": "verify_permissions",
                "details": "Ensure write permission is granted in policy"
            }
        elif "file_read" in operation:
            return {
                "suggestion": "Check file exists",
                "action": "verify_file_exists",
                "details": "File may not exist or path may be incorrect"
            }
        else:
            return {
                "suggestion": "Review error and retry",
                "action": "retry_with_modification",
                "details": f"Operation {operation} failed {self.error_counts[operation]} times"
            }
    
    def reset_errors(self, operation: Optional[str] = None):
        """
        Reset error counters
        
        Args:
            operation: Specific operation to reset, or None for all
        """
        if operation:
            self.error_counts.pop(operation, None)
        else:
            self.error_counts.clear()


class EnhancedBuilderAgent(BuilderAgent):
    """
    Enhanced Builder Agent with memory integration
    
    Extends base BuilderAgent with:
    - Subtask decomposition and execution
    - Trajectory and cost tracking
    - Learning from past sessions
    - Error recovery
    """
    
    def __init__(
        self,
        policy: Policy,
        storage_dir: Optional[Path] = None,
        model_provider=None,
        **kwargs
    ):
        """
        Initialize enhanced builder agent
        
        Args:
            policy: Governance policy
            storage_dir: Memory storage directory
            model_provider: LLM provider (OpenAI, Anthropic, or MockProvider)
            **kwargs: Additional args for base BuilderAgent
        """
        # Pass model_provider to parent BuilderAgent
        super().__init__(policy=policy, model_provider=model_provider, **kwargs)
        
        # Memory components
        storage_dir = storage_dir or (self.project_root / ".aureus" / "memory")
        self.trajectory_store = TrajectoryStore(storage_dir=storage_dir)
        self.cost_ledger = CostLedger(storage_path=storage_dir / "costs.json")
        self.pattern_extractor = PatternExtractor(storage_dir=storage_dir)
        
        # Enhanced components
        self.plan_decomposer = PlanDecomposer(policy=policy)
        self.error_recovery = ErrorRecoveryManager(max_retries=3)
        
        # Track current session
        self.current_session_id: Optional[str] = None
    
    def build(self, intent: str) -> BuildResult:
        """
        Execute build with enhanced features
        
        Args:
            intent: Natural language intent
            
        Returns:
            BuildResult with enhanced metadata
        """
        # Start trajectory session
        session = self.trajectory_store.start_session(intent=intent)
        self.current_session_id = session.session_id
        
        try:
            # Step 0: Learn from past similar sessions
            similar_sessions = self._find_similar_sessions(intent)
            self._log("Found similar sessions", count=len(similar_sessions))
            
            # Step 1: Decompose into subtasks
            subtasks = self.plan_decomposer.decompose(intent)
            self._log("Decomposed plan", subtasks=len(subtasks))
            self._record_action(
                phase="gather",
                tool="plan_decomposition",
                input={"intent": intent},
                output={"subtask_count": len(subtasks)},
                cost=1.0
            )
            
            # Step 2: Execute base build workflow
            base_result = super().build(intent)
            
            # Step 3: Execute subtasks
            self._execute_subtasks(subtasks)
            
            # Update result with enhanced metadata
            base_result.metadata.update({
                "subtasks": [self._subtask_to_dict(t) for t in subtasks],
                "similar_sessions": similar_sessions,
                "session_id": self.current_session_id
            })
            
            # End trajectory session
            self.trajectory_store.end_session(
                session_id=self.current_session_id,
                success=base_result.success,
                total_cost=base_result.cost.total if base_result.cost else 0.0,
                outcome=base_result.error if not base_result.success else "Build completed successfully"
            )
            
            return base_result
            
        except Exception as e:
            self._log("Enhanced build error", error=str(e))
            self._record_action(
                phase="error",
                tool="build",
                input={"intent": intent},
                output=str(e),
                cost=0.0,
                success=False
            )
            
            # End session with error
            self.trajectory_store.end_session(
                session_id=self.current_session_id,
                success=False,
                total_cost=0.0,
                outcome=f"Build failed: {e}"
            )
            
            raise
    
    def _find_similar_sessions(self, intent: str) -> List[Dict[str, Any]]:
        """Find similar past sessions"""
        try:
            similar = self.pattern_extractor.find_similar_sessions(
                intent=intent,
                limit=3
            )
            return similar
        except Exception:
            return []
    
    def _execute_subtasks(self, subtasks: List[SubTask]):
        """Execute subtasks in dependency order"""
        completed_ids = set()
        
        for subtask in subtasks:
            # Check dependencies
            deps_met = all(dep_id in completed_ids for dep_id in subtask.dependencies)
            
            if not deps_met:
                subtask.status = TaskStatus.SKIPPED
                self._log("Subtask skipped", task_id=subtask.id, reason="Dependencies not met")
                continue
            
            # Execute subtask
            subtask.status = TaskStatus.IN_PROGRESS
            self._log("Executing subtask", task_id=subtask.id, description=subtask.description)
            
            try:
                # Phase 1: Simple execution simulation
                # Phase 2: Actual LLM-driven implementation
                
                self._record_action(
                    phase="act",
                    tool="subtask_execution",
                    input={"task_id": subtask.id, "description": subtask.description},
                    output="completed",
                    cost=subtask.estimated_cost
                )
                
                subtask.status = TaskStatus.COMPLETED
                subtask.result = {"success": True}
                completed_ids.add(subtask.id)
                
            except Exception as e:
                subtask.status = TaskStatus.FAILED
                subtask.error = str(e)
                self._log("Subtask failed", task_id=subtask.id, error=str(e))
                
                # Try recovery
                if self.error_recovery.should_retry("subtask_" + subtask.id):
                    recovery = self.error_recovery.suggest_recovery("subtask_execution")
                    self._log("Recovery suggested", suggestion=recovery)
    
    def _record_action(
        self,
        phase: str,
        tool: str,
        input: Dict[str, Any],
        output: Any,
        cost: float,
        success: bool = True
    ):
        """Record action to trajectory and cost ledger"""
        # Record to trajectory
        action = ActionRecord(
            phase=phase,
            tool=tool,
            input=input,
            output=output,
            cost=cost,
            success=success
        )
        self.trajectory_store.record_action(self.current_session_id, action)
        
        # Record to cost ledger
        cost_entry = CostEntry(
            session_id=self.current_session_id,
            phase=phase,
            operation=tool,
            cost=cost,
            timestamp=datetime.now()
        )
        self.cost_ledger.record(cost_entry)
    
    def _subtask_to_dict(self, subtask: SubTask) -> Dict[str, Any]:
        """Convert subtask to dictionary"""
        return {
            "id": subtask.id,
            "description": subtask.description,
            "estimated_cost": subtask.estimated_cost,
            "dependencies": subtask.dependencies,
            "status": subtask.status.value,
            "result": subtask.result,
            "error": subtask.error
        }
