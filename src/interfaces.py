"""
AUREUS Python Interface Definitions

Type stubs showing exact module APIs for all 10 core modules.
These serve as implementation contracts for Phase 1 development.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Protocol, TypeVar, Union
from datetime import datetime


# ============================================================================
# Module 1: CLI
# ============================================================================

@dataclass
class Command:
    """Parsed CLI command."""
    action: str  # "code", "init", "verify", "policy", etc.
    args: List[str]
    options: Dict[str, Any]


class CLIFormatter:
    """Format output for terminal display."""
    
    def format_success(self, message: str) -> str:
        """Format success message with colors/icons."""
        ...
    
    def format_error(self, error: Exception) -> str:
        """Format error message with details."""
        ...
    
    def format_progress(self, phase: str, duration: float) -> str:
        """Format compilation phase progress."""
        ...
    
    def format_table(self, headers: List[str], rows: List[List[str]]) -> str:
        """Format tabular data for display."""
        ...


class CLI:
    """Main CLI entry point - handles command dispatch."""
    
    def __init__(self, workspace: Path):
        self.workspace = workspace
        self.formatter = CLIFormatter()
    
    def parse_command(self, argv: List[str]) -> Command:
        """Parse command-line arguments into Command object."""
        ...
    
    def execute(self, command: Command) -> int:
        """Execute command and return exit code (0=success)."""
        ...
    
    def handle_code(self, intent: str, **options) -> int:
        """Handle `aureus code <intent>` - main compilation entry point."""
        ...
    
    def handle_init(self) -> int:
        """Handle `aureus init` - auto-detect and generate policy."""
        ...
    
    def handle_verify(self) -> int:
        """Handle `aureus verify` - check governance compliance."""
        ...
    
    def handle_policy(self, action: str) -> int:
        """Handle policy commands (show/edit/regenerate/reset)."""
        ...
    
    def handle_history(self, **options) -> int:
        """Handle history commands (sessions/learning)."""
        ...


# ============================================================================
# Module 2: Compilation Harness
# ============================================================================

class CompilationPhase(Enum):
    """Compilation phases matching semantic compiler architecture."""
    CONTEXT_LOADING = "context_loading"
    SEMANTIC_PARSING = "semantic_parsing"      # GVUFD: Parser
    COST_ANALYSIS = "cost_analysis"            # SPK: Cost Analysis
    IR_GENERATION = "ir_generation"            # SPK: Intermediate Representation
    CODE_GENERATION = "code_generation"        # UVUAS: Code Generator
    VERIFICATION = "verification"              # UVUAS: Verifier
    PEEPHOLE_OPT = "peephole_optimization"     # Reflexion: Peephole Optimizer
    MEMORY_PERSISTENCE = "memory_persistence"  # Store learning data
    COMPLETION = "completion"


@dataclass
class CompilationResult:
    """Result of full compilation pipeline."""
    success: bool
    change: 'Change'  # The executed change
    phases: Dict[CompilationPhase, float]  # Phase durations
    total_duration: float
    errors: List[Exception]
    warnings: List[str]


@dataclass
class CompilationContext:
    """Context available during compilation."""
    workspace: Path
    intent: str
    policy: 'Policy'
    codebase_state: Dict[str, Any]
    history: List['HistoryEntry']
    session_budget: 'SessionBudget'


class CompilationHarness:
    """Orchestrates full compilation pipeline - main workflow controller."""
    
    def __init__(
        self,
        workspace: Path,
        governance: 'GovernanceEngine',
        agent: 'Agent',
        toolbus: 'ToolBus',
        memory: 'MemorySystem',
        model_provider: 'ModelProvider'
    ):
        self.workspace = workspace
        self.governance = governance
        self.agent = agent
        self.toolbus = toolbus
        self.memory = memory
        self.model_provider = model_provider
    
    def compile(self, intent: str, context: CompilationContext) -> CompilationResult:
        """
        Full compilation pipeline: Intent → Verified Code
        
        Phases:
        1. Context Loading: Load workspace state
        2. Semantic Parsing (GVUFD): Parse intent + generate specification
        3. Cost Analysis (SPK): Predict change cost
        4. IR Generation (SPK): Propose implementation plan
        5. Code Generation (UVUAS): Execute change via agent
        6. Verification (UVUAS): Verify correctness + governance compliance
        7. Peephole Optimization (Reflexion): Self-critique and improve
        8. Memory Persistence: Store learning data
        9. Completion: Return result
        """
        ...
    
    def run_phase(
        self,
        phase: CompilationPhase,
        context: CompilationContext,
        **kwargs
    ) -> Any:
        """Execute single compilation phase."""
        ...
    
    def handle_error(
        self,
        phase: CompilationPhase,
        error: Exception,
        context: CompilationContext
    ) -> None:
        """Handle compilation errors - may trigger rollback."""
        ...


# ============================================================================
# Module 3: Governance (3-Tier System)
# ============================================================================

@dataclass
class Budget:
    """Budget constraints for a single change."""
    max_loc: int  # Maximum lines of code
    max_files: int  # Maximum files touched
    max_dependencies: int  # Maximum new dependencies
    max_abstractions: int  # Maximum new abstractions
    max_cost_dollars: float  # Maximum monetary cost
    max_llm_calls: int  # Maximum LLM API calls


@dataclass
class SessionBudget:
    """Session-level budget constraints."""
    timeout_minutes: int  # Hard timeout
    max_llm_calls: int  # Total LLM calls allowed
    max_cost_dollars: float  # Total cost allowed
    max_tokens: int  # Total tokens allowed
    remaining_calls: int  # Calls left in session
    remaining_tokens: int  # Tokens left in session
    elapsed_seconds: float  # Time elapsed


@dataclass
class Policy:
    """
    Tier 1: GVUFD (Goals, Values, Uncertainties, Failure modes, Dependencies)
    User-facing business intent specification.
    """
    # Business Goals
    goals: List[str]  # What the project aims to achieve
    
    # Values & Constraints
    values: Dict[str, Any]  # Code quality values (maintainability, performance, etc.)
    constraints: Dict[str, Any]  # Technical constraints (dependencies, LOC limits, etc.)
    
    # Uncertainties & Risks
    uncertainties: List[str]  # Known unknowns
    failure_modes: List[str]  # Anticipated failure scenarios
    
    # Dependencies & Context
    dependencies: Dict[str, str]  # External dependencies (name -> version)
    tech_stack: List[str]  # Technologies used
    
    # Budget Configuration
    budget: Budget  # Per-change budget
    session_budget: SessionBudget  # Per-session budget


@dataclass
class Specification:
    """
    Tier 2: SPK (Specification, Proof obligations, Known constraints)
    Machine-checkable translation of GVUFD.
    """
    # Formal Specification
    preconditions: List[str]  # What must be true before change
    postconditions: List[str]  # What must be true after change
    invariants: List[str]  # What must always remain true
    
    # Proof Obligations
    proofs: List[str]  # Properties that must be verified
    
    # Known Constraints
    constraints: Dict[str, Any]  # Translated from GVUFD constraints
    
    # Cost Model
    cost_function: str  # Formula for calculating change cost
    thresholds: Dict[str, float]  # Decision thresholds (auto_proceed, prompt, reject)


@dataclass
class Change:
    """
    Tier 3: UVUAS (Units, Verifications, Uncertainties, Alternatives, Success criteria)
    Executable change with verification.
    """
    # Units of Work
    units: List['WorkUnit']  # Atomic code changes
    
    # Verifications
    verifications: List[str]  # Tests/checks to run
    
    # Uncertainties
    uncertainties: List[str]  # Risks in this specific change
    
    # Alternatives
    alternatives: List['Alternative']  # Other ways to achieve goal
    
    # Success Criteria
    success_criteria: List[str]  # How to know if change succeeded
    
    # Metadata
    estimated_cost: float  # Predicted cost
    actual_cost: Optional[float]  # Actual cost after execution
    files_touched: List[Path]  # Files modified
    loc_delta: int  # Net lines added/removed


@dataclass
class WorkUnit:
    """Atomic unit of code change."""
    file: Path
    operation: str  # "create", "edit", "delete"
    content: Optional[str]  # New content for create/edit
    line_range: Optional[tuple[int, int]]  # For edits: (start, end)


@dataclass
class Alternative:
    """Alternative way to implement change."""
    description: str
    estimated_cost: float
    tradeoffs: List[str]


class GovernanceDecision(Enum):
    """5-gate governance decisions."""
    AUTO_PROCEED = "auto_proceed"  # Tier 2: Change within comfort zone
    PROMPT_USER = "prompt_user"    # Tier 2: Change needs approval
    HARD_LIMIT = "hard_limit"      # Tier 2: Change exceeds maximum
    VIOLATION = "violation"        # Tier 1: Change violates policy
    APPROVED = "approved"          # User explicitly approved


@dataclass
class GovernanceResult:
    """Result of governance check."""
    decision: GovernanceDecision
    gate: str  # Which gate produced this decision
    reason: str  # Explanation
    alternatives: List[Alternative]  # Suggested alternatives (if rejected)


class GovernanceEngine:
    """
    Implements 3-tier governance system.
    Translates GVUFD → SPK → UVUAS and enforces constraints at all levels.
    """
    
    def __init__(self, policy: Policy):
        self.policy = policy
        self.specification = self._translate_policy_to_spec(policy)
    
    def _translate_policy_to_spec(self, policy: Policy) -> Specification:
        """
        Translate Tier 1 (GVUFD) → Tier 2 (SPK).
        Convert business intent to machine-checkable specification.
        """
        ...
    
    def generate_change(
        self,
        intent: str,
        context: CompilationContext
    ) -> Change:
        """
        Translate Tier 2 (SPK) → Tier 3 (UVUAS).
        Generate executable change from specification.
        """
        ...
    
    def check_gates(self, change: Change) -> GovernanceResult:
        """
        5-gate governance check:
        1. Safety Gate: Check for dangerous operations
        2. Budget Gate: Check if within budget
        3. Quality Gate: Check code quality metrics
        4. Dependency Gate: Check new dependencies
        5. Complexity Gate: Check cognitive complexity
        
        Returns decision + alternatives if rejected.
        """
        ...
    
    def check_safety_gate(self, change: Change) -> GovernanceResult:
        """Gate 1: Check for dangerous operations (file deletion, network calls, etc.)."""
        ...
    
    def check_budget_gate(self, change: Change) -> GovernanceResult:
        """Gate 2: Check if change within budget constraints."""
        ...
    
    def check_quality_gate(self, change: Change) -> GovernanceResult:
        """Gate 3: Check code quality (patterns, style, maintainability)."""
        ...
    
    def check_dependency_gate(self, change: Change) -> GovernanceResult:
        """Gate 4: Check new dependencies against policy."""
        ...
    
    def check_complexity_gate(self, change: Change) -> GovernanceResult:
        """Gate 5: Check cognitive complexity (nesting, abstractions, etc.)."""
        ...
    
    def verify_change(self, change: Change) -> bool:
        """
        Post-execution verification:
        - All tests pass
        - Postconditions satisfied
        - Invariants preserved
        - Success criteria met
        """
        ...
    
    def suggest_alternatives(self, change: Change) -> List[Alternative]:
        """Generate alternative approaches when change rejected."""
        ...
    
    def update_thresholds(
        self,
        utility_function: Callable[[Change, CompilationContext], float]
    ) -> None:
        """
        Meta-governance: Derive thresholds from utility function.
        auto_proceed: E[U] > 0 AND Var[U] < tolerance
        prompt: E[U] ~ 0 OR Var[U] > tolerance
        hard_limit: E[U] < -threshold
        """
        ...


# ============================================================================
# Module 4: Agents (Phase 1: Single Builder Agent)
# ============================================================================

@dataclass
class AgentContext:
    """Context available to agent during execution."""
    workspace: Path
    change: Change  # The change to implement
    tools: 'ToolBus'  # Available tools
    budget: SessionBudget  # Remaining budget
    codebase_state: Dict[str, Any]  # Current state


@dataclass
class AgentAction:
    """Single action taken by agent."""
    tool: str  # Tool name
    args: Dict[str, Any]  # Tool arguments
    reasoning: str  # Why this action
    timestamp: datetime


@dataclass
class AgentResult:
    """Result of agent execution."""
    success: bool
    actions: List[AgentAction]  # Actions taken
    files_changed: List[Path]  # Files modified
    loc_delta: int  # Net LOC change
    errors: List[Exception]
    llm_calls: int  # LLM calls made
    tokens_used: int  # Tokens consumed


class Agent(ABC):
    """Abstract base class for all agents."""
    
    @abstractmethod
    def execute(self, context: AgentContext) -> AgentResult:
        """Execute change in given context."""
        ...
    
    @abstractmethod
    def reflect(self, result: AgentResult) -> str:
        """Self-critique: What could be improved?"""
        ...
    
    @abstractmethod
    def learn(self, feedback: 'Feedback') -> None:
        """Update internal models based on feedback."""
        ...


class BuilderAgent(Agent):
    """
    Phase 1: Single agent that handles all implementation.
    Uses ReAct pattern: Reasoning + Acting in loop until change complete.
    """
    
    def __init__(
        self,
        model_provider: 'ModelProvider',
        tools: 'ToolBus',
        max_iterations: int = 10
    ):
        self.model_provider = model_provider
        self.tools = tools
        self.max_iterations = max_iterations
    
    def execute(self, context: AgentContext) -> AgentResult:
        """
        ReAct loop:
        1. Reason: Analyze change requirements and plan next action
        2. Act: Execute tool with arguments
        3. Observe: Check result and update state
        4. Repeat until change complete or max iterations
        """
        ...
    
    def reason(
        self,
        context: AgentContext,
        history: List[AgentAction]
    ) -> AgentAction:
        """Plan next action using LLM reasoning."""
        ...
    
    def act(self, action: AgentAction) -> Any:
        """Execute planned action via ToolBus."""
        ...
    
    def observe(self, action: AgentAction, result: Any) -> bool:
        """Check if change complete after action."""
        ...
    
    def reflect(self, result: AgentResult) -> str:
        """Reflexion: Critique own work and suggest improvements."""
        ...
    
    def learn(self, feedback: 'Feedback') -> None:
        """
        Update from feedback:
        - Adjust cost model weights
        - Improve reasoning patterns
        - Cache successful strategies
        """
        ...


# ============================================================================
# Module 5: ToolBus (Abstraction Layer for External Tools)
# ============================================================================

@dataclass
class Tool:
    """Tool metadata."""
    name: str
    description: str
    parameters: Dict[str, Any]  # JSON schema
    category: str  # "file", "search", "build", "test", etc.


@dataclass
class ToolResult:
    """Result of tool execution."""
    success: bool
    output: Any  # Tool-specific output
    error: Optional[Exception]
    duration: float


class ToolAdapter(ABC):
    """Abstract adapter for tool implementations."""
    
    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        """Execute tool with given arguments."""
        ...
    
    @abstractmethod
    def validate_args(self, **kwargs) -> bool:
        """Validate arguments before execution."""
        ...


class BashToolAdapter(ToolAdapter):
    """Adapter for bash commands."""
    
    def execute(self, command: str, **kwargs) -> ToolResult:
        """Execute bash command."""
        ...


class NativeToolAdapter(ToolAdapter):
    """Adapter for native Python implementations."""
    
    def execute(self, **kwargs) -> ToolResult:
        """Execute native Python function."""
        ...


class ToolBus:
    """
    Central tool registry and dispatcher.
    Abstracts tool implementations (bash vs native) from agents.
    """
    
    def __init__(self):
        self.tools: Dict[str, ToolAdapter] = {}
        self._register_builtin_tools()
    
    def _register_builtin_tools(self) -> None:
        """Register core tools (file ops, search, build, test)."""
        ...
    
    def register_tool(self, name: str, adapter: ToolAdapter) -> None:
        """Register new tool adapter."""
        ...
    
    def execute_tool(self, name: str, **kwargs) -> ToolResult:
        """Execute tool by name with arguments."""
        ...
    
    def list_tools(self, category: Optional[str] = None) -> List[Tool]:
        """List available tools (optionally filtered by category)."""
        ...
    
    def get_tool_schema(self, name: str) -> Dict[str, Any]:
        """Get JSON schema for tool parameters."""
        ...


# ============================================================================
# Module 6: Memory System (Phase 1: Simplified)
# ============================================================================

@dataclass
class HistoryEntry:
    """Single compilation session record."""
    session_id: str
    timestamp: datetime
    intent: str
    change: Change
    result: CompilationResult
    governance_decision: GovernanceDecision
    user_feedback: Optional['Feedback']
    
    # Learning data
    estimated_cost: float
    actual_cost: float
    cost_error: float  # |estimated - actual| / actual


@dataclass
class Feedback:
    """User feedback on agent performance."""
    session_id: str
    rating: int  # 1-5 stars
    comments: str
    was_helpful: bool
    problems: List[str]  # What went wrong


class MemorySystem:
    """
    Phase 1: Simple file-based memory.
    - policy.yaml: Current policy (Tier 1 GVUFD)
    - history.jsonl: All compilation sessions (JSONL format)
    """
    
    def __init__(self, workspace: Path):
        self.workspace = workspace
        self.policy_path = workspace / ".aureus" / "policy.yaml"
        self.history_path = workspace / ".aureus" / "history.jsonl"
    
    def load_policy(self) -> Policy:
        """Load policy from policy.yaml."""
        ...
    
    def save_policy(self, policy: Policy) -> None:
        """Save policy to policy.yaml."""
        ...
    
    def append_history(self, entry: HistoryEntry) -> None:
        """Append new session to history.jsonl."""
        ...
    
    def load_history(
        self,
        limit: Optional[int] = None,
        session_id: Optional[str] = None
    ) -> List[HistoryEntry]:
        """Load history entries (all or filtered)."""
        ...
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Compute learning statistics:
        - Total sessions
        - Success rate
        - Average cost error
        - Most common intents
        - Budget utilization
        """
        ...
    
    def learn_from_history(self) -> Dict[str, float]:
        """
        Analyze history to improve cost model:
        - Compute actual vs estimated cost errors
        - Identify patterns (which changes underestimated)
        - Return updated cost model weights
        
        Phase 1: Simple linear regression
        Phase 2+: Neural network or more sophisticated model
        """
        ...


# ============================================================================
# Module 7: Model Provider (LLM Abstraction)
# ============================================================================

@dataclass
class Message:
    """Single chat message."""
    role: str  # "system", "user", "assistant"
    content: str


@dataclass
class ModelResponse:
    """LLM response with metadata."""
    content: str  # Generated text
    tokens_used: int  # Tokens consumed (prompt + completion)
    cost: float  # Cost in dollars
    model: str  # Model used
    finish_reason: str  # "stop", "length", "error"


class ModelProvider(ABC):
    """Abstract LLM provider interface."""
    
    @abstractmethod
    def chat(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: int = 4000
    ) -> ModelResponse:
        """Send chat completion request."""
        ...
    
    @abstractmethod
    def estimate_cost(self, prompt: str, max_tokens: int) -> float:
        """Estimate cost before making request."""
        ...


class OpenAIProvider(ModelProvider):
    """OpenAI API provider (GPT-4, GPT-3.5, etc.)."""
    
    def __init__(self, api_key: str, model: str = "gpt-4"):
        self.api_key = api_key
        self.model = model
    
    def chat(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: int = 4000
    ) -> ModelResponse:
        """Call OpenAI Chat Completion API."""
        ...
    
    def estimate_cost(self, prompt: str, max_tokens: int) -> float:
        """Estimate cost using OpenAI pricing."""
        ...


class AnthropicProvider(ModelProvider):
    """Anthropic API provider (Claude)."""
    
    def __init__(self, api_key: str, model: str = "claude-3-opus-20240229"):
        self.api_key = api_key
        self.model = model
    
    def chat(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: int = 4000
    ) -> ModelResponse:
        """Call Anthropic Messages API."""
        ...
    
    def estimate_cost(self, prompt: str, max_tokens: int) -> float:
        """Estimate cost using Anthropic pricing."""
        ...


# ============================================================================
# Module 8: Security
# ============================================================================

class SecurityViolation(Exception):
    """Raised when change violates security policy."""
    pass


class SecurityChecker:
    """Validates changes for security risks."""
    
    def check_change(self, change: Change) -> List[str]:
        """
        Check change for security violations:
        - Dangerous file operations (delete, chmod)
        - Network calls without approval
        - Arbitrary code execution
        - Credential exposure
        - Path traversal
        
        Returns list of violations (empty if safe).
        """
        ...
    
    def check_file_operation(self, unit: WorkUnit) -> Optional[str]:
        """Check single file operation for safety."""
        ...
    
    def check_dependencies(self, dependencies: List[str]) -> List[str]:
        """Check new dependencies for known vulnerabilities."""
        ...
    
    def sandbox_command(self, command: str) -> str:
        """Wrap command in sandbox for safe execution."""
        ...


# ============================================================================
# Module 9: Utils
# ============================================================================

class CodeAnalyzer:
    """Analyze code structure and metrics."""
    
    def count_loc(self, file: Path) -> int:
        """Count lines of code (excluding comments/blank lines)."""
        ...
    
    def extract_dependencies(self, file: Path) -> List[str]:
        """Extract import statements."""
        ...
    
    def measure_complexity(self, file: Path) -> float:
        """Compute cyclomatic complexity."""
        ...
    
    def measure_nesting(self, file: Path) -> int:
        """Compute maximum nesting depth."""
        ...
    
    def count_abstractions(self, file: Path) -> int:
        """Count classes, functions, interfaces."""
        ...


class DiffUtils:
    """Git diff utilities."""
    
    def get_changed_files(self) -> List[Path]:
        """Get list of modified files in git workspace."""
        ...
    
    def get_diff(self, file: Path) -> str:
        """Get git diff for single file."""
        ...
    
    def rollback(self, files: List[Path]) -> None:
        """Rollback changes to specified files."""
        ...
    
    def create_checkpoint(self, name: str) -> str:
        """Create git commit as checkpoint."""
        ...


class TimeUtils:
    """Time tracking utilities."""
    
    def start_timer(self) -> str:
        """Start new timer, return timer ID."""
        ...
    
    def stop_timer(self, timer_id: str) -> float:
        """Stop timer and return duration in seconds."""
        ...


# ============================================================================
# Module 10: Config
# ============================================================================

@dataclass
class AureusConfig:
    """Global AUREUS configuration."""
    
    # Model Configuration
    model_provider: str  # "openai", "anthropic", "local"
    model_name: str  # "gpt-4", "claude-3-opus-20240229", etc.
    api_key: str  # API key for provider
    
    # Budget Defaults
    default_max_loc: int = 500
    default_max_files: int = 10
    default_max_cost: float = 1.0
    default_session_timeout: int = 60  # minutes
    default_max_llm_calls: int = 100
    
    # Compilation Options
    auto_approve: bool = False  # Skip user prompts
    dry_run: bool = False  # Don't actually make changes
    verbose: bool = False  # Show detailed logs
    
    # Learning Options
    enable_learning: bool = True  # Learn from history
    pre_seed_iterations: int = 1000  # Self-play iterations before release


class ConfigManager:
    """Manage AUREUS configuration."""
    
    def __init__(self, config_path: Path):
        self.config_path = config_path
    
    def load_config(self) -> AureusConfig:
        """Load config from ~/.aureus/config.yaml."""
        ...
    
    def save_config(self, config: AureusConfig) -> None:
        """Save config to ~/.aureus/config.yaml."""
        ...
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get single config value."""
        ...
    
    def set(self, key: str, value: Any) -> None:
        """Set single config value."""
        ...


# ============================================================================
# Main Entry Point
# ============================================================================

def main(argv: List[str]) -> int:
    """
    Main entry point for AUREUS CLI.
    
    Workflow:
    1. Parse command-line arguments
    2. Load workspace configuration
    3. Initialize compilation harness with all modules
    4. Execute command
    5. Return exit code
    """
    # Parse command
    cli = CLI(Path.cwd())
    command = cli.parse_command(argv)
    
    # Load configuration
    config_manager = ConfigManager(Path.home() / ".aureus" / "config.yaml")
    config = config_manager.load_config()
    
    # Initialize modules
    model_provider = _create_model_provider(config)
    memory = MemorySystem(cli.workspace)
    policy = memory.load_policy()
    governance = GovernanceEngine(policy)
    toolbus = ToolBus()
    agent = BuilderAgent(model_provider, toolbus)
    harness = CompilationHarness(
        cli.workspace,
        governance,
        agent,
        toolbus,
        memory,
        model_provider
    )
    
    # Execute command
    return cli.execute(command)


def _create_model_provider(config: AureusConfig) -> ModelProvider:
    """Factory for model provider based on config."""
    if config.model_provider == "openai":
        return OpenAIProvider(config.api_key, config.model_name)
    elif config.model_provider == "anthropic":
        return AnthropicProvider(config.api_key, config.model_name)
    else:
        raise ValueError(f"Unknown model provider: {config.model_provider}")


if __name__ == "__main__":
    import sys
    sys.exit(main(sys.argv[1:]))
