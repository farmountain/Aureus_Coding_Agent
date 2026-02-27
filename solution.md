# AUREUS Coding Agent — Solution Specification

This document provides the **engineering specification** for implementing AUREUS, including module boundaries, interface definitions, schemas, and technical details.

---

## 1. Module Boundaries

### 1.1 Core Modules (≤ 6)

#### Module 1: `cli`
**Responsibility**: Command-line interface and user interaction

**Files**:
- `cli/main.py` — Entry point
- `cli/parser.py` — Argument parsing
- `cli/output.py` — Formatted output
- `cli/config_loader.py` — Configuration loading

**Public Interface**:
```python
def main(args: list[str]) -> int:
    """Main entry point. Returns exit code."""

def parse_command(args: list[str]) -> Command:
    """Parse CLI arguments into Command object."""

def format_output(result: ExecutionResult) -> str:
    """Format execution result for display."""
```

**Dependencies**: None (stdlib only)

**LOC Budget**: ≤ 400

---

#### Module 2: `harness`
**Responsibility**: Agentic orchestration loop

**Files**:
- `harness/orchestrator.py` — Main loop
- `harness/session.py` — Session management
- `harness/context.py` — Context assembly

**Public Interface**:
```python
class Orchestrator:
    def execute(self, intent: str, context: Context) -> ExecutionResult:
        """Execute agentic loop for given intent."""
    
    def initialize_session(self, project_path: str) -> Session:
        """Initialize new session."""
    
    def teardown_session(self, session: Session) -> None:
        """Clean up session resources."""

class Context:
    project_path: str
    policy: Policy
    memory: Memory
    git_state: GitState
    file_tree: FileTree
```

**Dependencies**: `governance`, `agents`, `memory`

**LOC Budget**: ≤ 600

---

#### Module 3: `governance`
**Responsibility**: Tier 1 (GVUFD) + Tier 2 (SPK)

**Files**:
- `governance/gvufd.py` — Spec generator (Tier 1)
- `governance/pricing.py` — Cost calculator (Tier 2)
- `governance/budget.py` — Budget enforcement
- `governance/policy.py` — Policy schema and validation

**Public Interface**:
```python
# Tier 1: GVUFD
class GVUFD:
    def generate_spec(self, intent: str, context: Context) -> Specification:
        """Convert intent to bounded specification."""

@dataclass
class Specification:
    success_criteria: list[str]
    forbidden_patterns: list[Pattern]
    loc_budget: int
    module_budget: int
    dependency_budget: int
    acceptance_tests: list[Test]
    risk_level: RiskLevel

# Tier 2: Self-Pricing Kernel
class PricingKernel:
    def calculate_cost(self, action: Action) -> Cost:
        """Calculate complexity cost of action."""
    
    def check_budget(self, cost: Cost, budget: Budget) -> bool:
        """Check if cost fits within budget."""

@dataclass
class Cost:
    loc_delta: int
    new_dependencies: int
    new_abstractions: int
    security_risk: float
    tool_risk: float
    total: float  # Weighted sum
```

**Pricing Formula**:

**Phase 1 (Simple Linear)**:
```python
# LOC-only model (simple, defensible, understandable)
total_cost = loc_delta

# Thresholds (LOC-based):
# - Auto-proceed: < 300 LOC
# - Prompt user: 300-800 LOC
# - Reject: > 800 LOC
```

**Phase 2+ (Learned Weights)**:
```python
# Learn weights from actual outcomes
total_cost = (
    loc_delta * w_loc +              # Base complexity
    new_dependencies * w_dep +        # Learn from data
    new_abstractions * w_abs +        # Learn from data
    security_risk * w_sec +           # Learn from data
    tool_risk * w_tool                # Learn from data
)

# Initial weights are discovered through:
# - Self-play pre-seeding (1000 iterations before release)
# - User feedback and overrides
# - Actual cost vs estimated cost variance
```

**Dependencies**: `memory`, `security`

**LOC Budget**: ≤ 1000 (GVUFD + SPK require substantial logic)

---

#### Module 4: `agents`
**Responsibility**: Tier 3 agent execution

**Phase 1 (Single Agent)**:
- `agents/base.py` — Agent interface
- `agents/builder.py` — Unified builder (plans + implements + tests)

**Phase 2+ (Full Swarm)**:
- `agents/planner.py` — Task decomposition
- `agents/tester.py` — Verification
- `agents/critic.py` — Architectural review
- `agents/reflexion.py` — Simplification

**Public Interface**:
```python
class Agent(ABC):
    @abstractmethod
    def execute(self, spec: Specification, context: Context) -> AgentResult:
        """Execute agent-specific logic."""

# Phase 1: Single unified builder
class BuilderAgent(Agent):
    def execute(self, spec: Specification, context: Context) -> AgentResult:
        """Plan, build, and test in single agent."""
    
    def plan(self, spec: Specification) -> Plan:
        """Simple task decomposition."""
    
    def build(self, plan: Plan) -> BuildResult:
        """Execute approved actions."""
    
    def test(self, result: BuildResult, spec: Specification) -> TestResult:
        """Verify against acceptance criteria."""

# Phase 2+: Specialized agents (deferred)
# class PlannerAgent(Agent): ...
# class TesterAgent(Agent): ...
# class CriticAgent(Agent): ...
# class ReflexionAgent(Agent): ...
```

**Dependencies**: `governance`, `toolbus`, `model_provider`

**LOC Budget**: ≤ 600 (Phase 1 single agent)
**LOC Budget**: ≤ 1200 (Phase 2+ full swarm)

---

#### Module 5: `toolbus`
**Responsibility**: Tool abstraction and execution

**Files**:
- `toolbus/bus.py` — Tool dispatcher
- `toolbus/tools/file.py` — File operations
- `toolbus/tools/search.py` — Code search
- `toolbus/tools/shell.py` — Shell execution
- `toolbus/tools/git.py` — Git operations
- `toolbus/registry.py` — Tool registration

**Public Interface**:
```python
class ToolBus:
    def execute(self, tool: str, params: dict, context: Context) -> ToolResult:
        """Execute tool with permission and pricing gates."""
    
    def register_tool(self, tool: Tool) -> None:
        """Register new tool."""
    
    def create_rollback_point(self) -> RollbackPoint:
        """Create snapshot for rollback."""
    
    def rollback(self, point: RollbackPoint) -> None:
        """Rollback to snapshot."""

class Tool(ABC):
    name: str
    risk_level: RiskLevel
    
    @abstractmethod
    def execute(self, params: dict) -> ToolResult:
        """Execute tool action."""
    
    @abstractmethod
    def validate_params(self, params: dict) -> bool:
        """Validate parameters."""
```

**Dependencies**: `security`, `governance`

**LOC Budget**: ≤ 700 (simpler tool set in Phase 1)

---

#### Module 6: `memory`
**Responsibility**: Persistent and session state

**Phase 1 (Simplified)**:
- `memory/policy.py` — Policy persistence
- `memory/history.py` — Unified history log (combined ledger + trajectories)

**Phase 2+ (Full Memory)**:
- `memory/adr.py` — Architecture Decision Records
- `memory/trajectory.py` — Detailed session logs
- `memory/ledger.py` — Separate cost/evidence tracking

**Public Interface**:
```python
class Memory:
    def load_policy(self, project_path: str) -> Policy:
        """Load project policy."""
    
    def save_policy(self, policy: Policy) -> None:
        """Persist policy updates."""
    
    def log_history(self, entry: HistoryEntry) -> None:
        """Append to unified history log (Phase 1)."""
    
    # Phase 2+ methods:
    # def record_adr(self, decision: Decision) -> None:
    # def log_trajectory(self, trajectory: Trajectory) -> None:
    # def update_ledger(self, cost: Cost, evidence: Evidence) -> None:
```

**Dependencies**: None

**LOC Budget**: ≤ 300 (Phase 1 simplified)
**LOC Budget**: ≤ 600 (Phase 2+ full memory)

---

### 1.2 Supporting Modules (≤ 4)

#### Module 7: `model_provider`
**Responsibility**: LLM abstraction

**Files**:
- `model_provider/interface.py` — Unified interface
- `model_provider/anthropic.py` — Anthropic adapter
- `model_provider/openai.py` — OpenAI adapter
- `model_provider/google.py` — Google adapter
- `model_provider/local.py` — Local LLM adapter

**Interface**:
```python
class ModelProvider(ABC):
    @abstractmethod
    def complete(self, prompt: str, max_tokens: int) -> str:
        """Generate completion."""
    
    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""

# Each adapter ≤ 200 LOC
```

**LOC Budget**: ≤ 700

---

#### Module 8: `security`
**Responsibility**: Permission and sandboxing

**Files**:
- `security/permissions.py` — Permission matrix
- `security/sandbox.py` — Execution sandbox
- `security/audit.py` — Audit logging

**Interface**:
```python
class PermissionLayer:
    def check_permission(self, tool: str, params: dict, policy: Policy) -> bool:
        """Check if tool execution is allowed."""
    
    def enforce_boundaries(self, path: str, project_root: str) -> bool:
        """Enforce file system boundaries."""

class Sandbox:
    def execute_safely(self, command: str) -> SandboxResult:
        """Execute command in sandbox."""
```

**LOC Budget**: ≤ 400

---

#### Module 9: `utils`
**Responsibility**: Shared utilities

**Files**:
- `utils/fs.py` — File system helpers
- `utils/git.py` — Git helpers
- `utils/log.py` — Logging utilities

**LOC Budget**: ≤ 200

---

#### Module 10: `config`
**Responsibility**: Configuration management

**Files**:
- `config/schema.py` — Config schema
- `config/loader.py` — Config loading

**LOC Budget**: ≤ 100 (minimal in Phase 1)

---

## 2. Data Schemas

### 2.1 Policy Schema (YAML)

```yaml
# .aureus/policy.yaml
version: "1.0"

project:
  name: "my-project"
  root: "/path/to/project"

budgets:
  max_loc: 10000
  max_modules: 8
  max_files: 30
  max_dependencies: 20

forbidden_patterns:
  - name: "god_object"
    description: "Classes over 500 LOC"
    rule: "class_loc > 500"
  
  - name: "deep_inheritance"
    description: "Inheritance depth > 2"
    rule: "inheritance_depth > 2"
  
  - name: "circular_deps"
    description: "Circular module dependencies"
    rule: "has_circular_dependency"

permissions:
  tools:
    file_read: allow
    file_write: allow
    shell_exec: deny  # Require explicit approval
    git_commit: allow
    web_fetch: deny

  file_boundaries:
    - "/src/**"
    - "/tests/**"
    - "!/node_modules/**"
    - "!/.git/**"

cost_thresholds:
  warning: 100.0
  rejection: 500.0

simplification:
  trigger_at_budget_percent: 90
  mandatory: true
```

---

### 2.2 Specification Schema (JSON)

```json
{
  "intent": "Add user authentication",
  "success_criteria": [
    "User can register with email/password",
    "User can login with valid credentials",
    "Invalid credentials return 401",
    "Passwords are hashed with bcrypt"
  ],
  "forbidden_patterns": [
    "god_object",
    "plaintext_passwords",
    "global_auth_state"
  ],
  "budgets": {
    "max_loc_delta": 500,
    "max_new_files": 5,
    "max_new_dependencies": 2,
    "max_new_abstractions": 3
  },
  "acceptance_tests": [
    "test_user_registration",
    "test_user_login_valid",
    "test_user_login_invalid",
    "test_password_hashing"
  ],
  "risk_level": "medium"
}
```

---

### 2.3 Cost Ledger Schema (JSON)

```json
{
  "session_id": "abc123",
  "timestamp": "2026-02-27T10:30:00Z",
  "actions": [
    {
      "action_id": "1",
      "type": "file_write",
      "file": "src/auth.py",
      "cost": {
        "loc_delta": 120,
        "new_dependencies": 1,
        "new_abstractions": 2,
        "security_risk": 0.3,
        "tool_risk": 0.1,
        "total": 195.3
      },
      "status": "approved",
      "evidence": {
        "tests_passed": true,
        "patterns_clean": true,
        "budget_remaining": 304.7
      }
    }
  ],
  "total_cost": 195.3,
  "budget_remaining": 304.7
}
```

---

### 2.4 ADR Schema (Markdown)

```markdown
# ADR-001: Use bcrypt for password hashing

## Status
Accepted

## Context
Need secure password storage for user authentication.

## Decision
Use bcrypt library with cost factor 12.

## Consequences
- Positive: Industry-standard security
- Positive: Configurable cost factor
- Negative: Slower than SHA256 (but acceptable)
- Cost: +1 dependency, +50 LOC

## Governance
- Approved by: Critic agent
- Cost: 50.0 (within budget)
- Date: 2026-02-27
```

---

## 3. Tool API

### 3.1 File Operations

```python
# Read file
tool_bus.execute("file_read", {
    "path": "src/main.py",
    "start_line": 1,
    "end_line": 50
})

# Write file
tool_bus.execute("file_write", {
    "path": "src/auth.py",
    "content": "...",
    "mode": "create"  # or "append", "replace"
})

# Search
tool_bus.execute("file_search", {
    "query": "class User",
    "file_pattern": "**/*.py"
})
```

---

### 3.2 Shell Execution

```python
tool_bus.execute("shell", {
    "command": "pytest tests/",
    "timeout": 30,
    "capture_output": true
})
```

---

### 3.3 Git Operations

```python
tool_bus.execute("git_commit", {
    "message": "Add user authentication",
    "files": ["src/auth.py", "tests/test_auth.py"]
})

tool_bus.execute("git_diff", {
    "staged": false
})
```

---

## 4. Pricing Formula (Detailed)

### 4.1 Base Formula (Linear Model V1)

```python
def calculate_cost(action: Action) -> float:
    """
    Calculate complexity cost of an action.
    
    Weights are calibrated to:
    - 1 LOC = 1 cost unit
    - 1 new dependency = 50 cost units
    - 1 new abstraction = 25 cost units
    - Security risk: 0-1 scale, * 100
    - Tool risk: 0-1 scale, * 10
    """
    cost = 0.0
    
    # Lines of code impact
    cost += action.loc_delta * 1.0
    
    # Dependency impact
    cost += action.new_dependencies * 50.0
    
    # Abstraction impact (classes, interfaces, etc.)
    cost += action.new_abstractions * 25.0
    
    # Security risk (0.0 = safe, 1.0 = high risk)
    cost += action.security_risk * 100.0
    
    # Tool risk (0.0 = read-only, 1.0 = destructive)
    cost += action.tool_risk * 10.0
    
    return cost
```

### 4.2 Risk Calculation

```python
def calculate_security_risk(action: Action) -> float:
    """Calculate security risk score (0-1)."""
    risk = 0.0
    
    if action.touches_auth:
        risk += 0.3
    if action.touches_network:
        risk += 0.3
    if action.uses_eval:
        risk += 0.8
    if action.modifies_permissions:
        risk += 0.5
    
    return min(risk, 1.0)

def calculate_tool_risk(tool: str) -> float:
    """Calculate tool risk level (0-1)."""
    risk_map = {
        "file_read": 0.0,
        "file_write": 0.3,
        "shell_exec": 0.8,
        "git_commit": 0.4,
        "web_fetch": 0.5,
    }
    return risk_map.get(tool, 0.5)
```

---

## 5. CLI Command Lifecycle

### 5.1 Command Flow

```
$ aureus code "Add user authentication"

1. CLI parses command
2. Initialize session
3. Load project context (policy, memory, git state)
4. Call GVUFD to generate specification
5. Display specification to user
6. User confirms or adjusts
7. Pricing kernel allocates budget
8. Planner decomposes task
9. Price each action
10. Display plan + cost breakdown to user
11. User approves
12. Execute actions via tool bus
13. Tester verifies
14. Critic reviews
15. Reflexion simplifies
16. Display results
17. Persist memory
18. Teardown session
```

### 5.2 CLI Commands

```bash
# Main coding command
aureus code "Add feature X"

# Initialize project
aureus init [project-path]

# Show current policy
aureus policy show

# Edit policy
aureus policy edit

# Show cost ledger
aureus cost show

# Show ADRs
aureus adr list

# Simplify existing code
aureus simplify [path]

# Check compliance
aureus check
```

---

## 6. Error Recovery

### 6.1 Rollback Mechanism

```python
class ToolBus:
    def execute_with_rollback(self, tool: str, params: dict) -> ToolResult:
        """Execute tool with automatic rollback on failure."""
        
        # Create rollback point
        rollback_point = self.create_rollback_point()
        
        try:
            # Execute tool
            result = self.execute(tool, params)
            
            # Validate result
            if not self.validate_result(result):
                raise ValidationError("Result validation failed")
            
            return result
            
        except Exception as e:
            # Rollback on any error
            self.rollback(rollback_point)
            raise ToolExecutionError(f"Tool execution failed: {e}")
```

### 6.2 Rollback Strategies

- **File changes**: Git-based (stash/unstash) or filesystem snapshots
- **Shell executions**: Idempotent commands only, or manual undo scripts
- **Dependency changes**: Lockfile versioning (package.json, requirements.txt)

---

## 7. Reflexion Algorithm

### 7.1 Simplification Pass

```python
class ReflexionAgent:
    def simplify(self, result: BuildResult) -> SimplifiedResult:
        """
        Mandatory simplification pass.
        
        Goals:
        1. Remove unnecessary abstractions
        2. Consolidate duplicate logic
        3. Inline trivial functions
        4. Reduce cyclomatic complexity
        """
        
        # 1. Detect single-use abstractions
        abstractions = self.find_abstractions(result)
        for abstraction in abstractions:
            if abstraction.usage_count == 1:
                self.inline_abstraction(abstraction)
        
        # 2. Detect duplicate code
        duplicates = self.find_duplicates(result)
        for duplicate in duplicates:
            self.consolidate(duplicate)
        
        # 3. Inline trivial functions (< 3 LOC)
        functions = self.find_functions(result)
        for func in functions:
            if func.loc <= 3 and func.usage_count <= 2:
                self.inline_function(func)
        
        # 4. Reduce complexity
        complex_functions = self.find_complex_functions(result)
        for func in complex_functions:
            if func.cyclomatic_complexity > 10:
                self.suggest_refactor(func)
        
        return SimplifiedResult(...)
```

---

## 8. Security Implementation

### 8.1 Permission Matrix

```python
# security/permissions.py

PERMISSION_MATRIX = {
    "file_read": {
        "default": "allow",
        "requires_approval": False,
        "audit": False
    },
    "file_write": {
        "default": "allow",
        "requires_approval": False,
        "audit": True
    },
    "shell_exec": {
        "default": "deny",
        "requires_approval": True,
        "audit": True
    },
    "git_commit": {
        "default": "allow",
        "requires_approval": False,
        "audit": True
    },
    "web_fetch": {
        "default": "deny",
        "requires_approval": True,
        "audit": True
    }
}
```

### 8.2 Sandbox Implementation (Shell)

```python
# security/sandbox.py

def execute_in_sandbox(command: str, project_root: str) -> SandboxResult:
    """
    Execute shell command with restrictions:
    - Chroot to project directory
    - No network access (optional)
    - Limited environment variables
    - Timeout enforcement
    """
    
    # Validate command against whitelist/blacklist
    if not validate_command(command):
        raise SecurityError("Command not allowed")
    
    # Prepare sandbox environment
    env = {
        "PATH": "/usr/bin:/bin",
        "HOME": project_root,
        "USER": "aureus",
    }
    
    # Execute with timeout
    result = subprocess.run(
        command,
        cwd=project_root,
        env=env,
        timeout=30,
        capture_output=True,
        shell=False  # Prevent shell injection
    )
    
    return SandboxResult(
        stdout=result.stdout,
        stderr=result.stderr,
        exit_code=result.returncode
    )
```

---

## 9. Implementation Phases

### Phase 1: Core Foundation (Week 1-2)
- CLI skeleton
- Basic orchestrator loop
- GVUFD spec generator (simple)
- Pricing kernel (linear model)
- File read/write tools
- Policy schema + loader

### Phase 2: Agent Swarm (Week 3-4)
- Planner agent
- Builder agent
- Tester agent (basic)
- Critic agent (pattern detection)
- Reflexion agent (simple)

### Phase 3: Memory & Safety (Week 5-6)
- ADR writer
- Trajectory logger
- Cost ledger
- Permission layer
- Sandbox implementation

### Phase 4: Model Providers (Week 7-8)
- Anthropic adapter
- OpenAI adapter
- Local LLM adapter
- Prompt templates

### Phase 5: Advanced Tools (Week 9-10)
- Shell execution
- Git operations
- Code search (semantic + grep)
- Rollback mechanism

### Phase 6: Polish & Extensions (Week 11-12)
- CLI refinement
- Error messages
- Documentation
- Skills system (basic)
- MCP connectors (optional)

---

## 10. Testing Requirements

### 10.1 Unit Tests
- Each module ≥ 80% coverage
- Pricing calculations verified
- Policy validation tested
- Tool execution mocked

### 10.2 Integration Tests
- End-to-end scenarios
- Real file system operations
- Git integration
- Budget enforcement

### 10.3 Governance Tests
- Forbidden pattern detection accuracy
- Budget threshold enforcement
- Simplification effectiveness
- Rollback reliability

### 10.4 Security Tests
- Permission bypass attempts
- Sandbox escape attempts
- Command injection tests
- Path traversal tests

---

## 11. Performance Targets

| Operation | Target Latency | Notes |
|-----------|---------------|-------|
| Context assembly | < 500ms | Lazy loading |
| GVUFD spec generation | < 2s | LLM-dependent |
| Pricing calculation | < 10ms | Pure computation |
| Single tool execution | < 5s | File ops |
| Full planning cycle | < 10s | Excludes LLM |
| Session initialization | < 1s | Load policy + scan |

---

## 12. Dependency List (Target ≤ 15)

### Core Dependencies
1. **click** — CLI framework
2. **pyyaml** — Policy parsing
3. **anthropic** — Anthropic SDK (optional)
4. **openai** — OpenAI SDK (optional)
5. **gitpython** — Git operations
6. **pytest** — Testing
7. **typing-extensions** — Type hints (Python < 3.10)

### Optional Dependencies
8. **httpx** — Web fetching (if enabled)
9. **tree-sitter** — Code parsing (advanced features)
10. **chromadb** — Vector memory (Phase 3+)

Total: **7 core + 3 optional = 10 dependencies** ✓

---

This specification provides the complete engineering blueprint for implementing AUREUS Coding Agent as a governance-first, complexity-aware coding runtime.
