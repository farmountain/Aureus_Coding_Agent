# AUREUS Coding Agent Architecture

## 1. System Layers

The AUREUS architecture consists of 10 distinct layers, each with clear responsibilities and boundaries:

### 1.1 CLI Frontend
- Command-line interface and user interaction
- Session initialization and teardown
- Configuration loading
- Human-readable output formatting

### 1.2 Session & Context Manager
- Project context assembly
- File system watching
- Git state tracking
- Environment variable management
- Session state persistence
- **Context budget tracking** (token usage/remaining per model)
- **Working set management** (hot files, dependency closure)
- **Context pruning strategies** (evict least-used files)
- **Checkpoint creation/restoration** (named snapshots for rollback)

### 1.3 Agentic Harness
- Main orchestration loop (Gather → Act → Verify)
- Agent lifecycle management
- Context switching between specialized agents
- Coordination protocol enforcement
- **Phase-specific tool restrictions** (read-only in Gather, mutations in Act)
- **Multi-model strategy** (reasoning model vs fast model selection)
- **Streaming output renderer** (real-time diff display)
- **Diff aggregation and approval** (user can approve/reject per change)
- **Mandatory reflexion trigger** (simplification after every verification)

### 1.4 Tier 1: Global Value Utility Function Designer (GVUFD)
**Intelligence Layer**: Auto-detects project context and generates appropriate governance

- **Project Intelligence**:
  - Auto-detect project type (web, API, CLI, library, etc.)
  - Infer tech stack from existing files
  - Analyze current architecture patterns
  - Detect team size from git history
  - Estimate project maturity (greenfield vs legacy)

- **Policy Auto-Generation**:
  - Propose appropriate budgets based on project size
  - Suggest forbidden patterns based on detected issues
  - Generate acceptance criteria from intent + context
  - Set risk boundaries based on security surface
  - Create test templates matching project style

- **Adaptive Learning**:
  - Observe which policies are frequently overridden
  - Adjust budgets based on actual project growth
  - Learn team coding patterns over sessions
  - Refine forbidden patterns based on violations

### 1.5 Tier 2: Self-Pricing Kernel (SPK)
**Learning Layer**: Learns actual complexity costs from outcomes

- **Intelligent Cost Prediction**:
  - Start with simple linear model (LOC, deps, abstractions)
  - Learn actual costs from completed actions
  - Refine pricing model based on variance (estimated vs actual)
  - Adapt to project-specific complexity factors
  - Weight costs based on historical outcomes (did it cause issues?)

- **Smart Budget Allocation**:
  - Auto-allocate budgets based on task complexity
  - Learn team velocity over sessions
  - Adjust thresholds based on override frequency
  - Predict total cost from partial implementation

- **Alternative Intelligence**:
  - Suggest simpler implementations when over budget
  - Learn which alternatives users prefer
  - Detect when users consistently override → adjust model
  - Propose budget increases with justification

### 1.6 Tier 3: Unified Value Utility Agent Swarm (UVUAS)
**Execution Layer**: Learns from outcomes and improves over time

**Phase 1 (MVP)**: Single **Builder** agent handles planning, implementation, and testing
- Learns project coding style and patterns
- Adapts to team conventions automatically
- Improves implementation quality from feedback
- Verifies changes against acceptance criteria
- Plans task decomposition (simple approach)

**Phase 2+**: Expand to specialized agent swarm:

- **Planner**: 
  - Learns effective task decomposition strategies
  - Observes which plans succeed vs fail
  - Adapts planning based on project complexity
  
- **Builder**: 
  - Focused on implementation only
  - Learns project coding style and patterns
  
- **Tester**: 
  - Learns what tests are valuable (run frequently, catch bugs)
  - Adapts test generation to project test style
  - Prioritizes tests based on failure history
  
- **Critic**: 
  - Learns which patterns cause issues in this project
  - Adapts strictness based on false positive rate
  - Discovers new anti-patterns specific to codebase
  
- **Reflexion**: 
  - Learns what simplifications are accepted
  - Adapts aggressiveness based on user feedback
  - Discovers project-specific refactoring opportunities

All agents coordinate through shared memory and learn collectively.

### 1.7 Tool Bus
- Unified tool invocation interface
- **Permission tier enforcement** (Tier 0-3: safe → risky)
- **Phase-aware tool gating** (restrict tools by execution phase)
- Execution sandboxing
- Rollback management
- Tool result validation
- **Repository indexer** (ripgrep + symbol table + dependency graph)
- **Working set optimizer** (track hot files and dependencies)

### 1.8 Memory Subsystem
AUREUS memory is intentionally lightweight and structured, avoiding heavy vector databases in favor of deterministic, queryable storage.

**Phase 1 (Simplified)**:
- **Project Policy Memory** (`.aureus/policy.yaml`)
  - **Auto-generated on first run** from project analysis
  - User can override, but defaults are intelligent
  - Evolves based on actual usage patterns
  - Schema: [policy-schema.json](../docs/schemas/policy-schema.json)
  - Versioned with project (tracks policy evolution)
  
- **Unified History Log** (`.aureus/history.jsonl`)
  - Combined ledger + trajectories in single JSONL file
  - Records: intent, spec, actions, costs (estimated/actual), outcomes
  - Append-only format for learning and debugging
  - Enables cost model refinement over time

**Phase 2+ (Full Memory)**:
- **Architecture Decision Records (ADRs)**
  - Markdown-based ADR format
  - Captures why decisions were made, not just what
  - Location: `.aureus/decisions/`
  - Includes: context, decision, consequences, governance approval
  
- **Separate Trajectory Logs**
  - Detailed JSON logs of each session
  - Location: `.aureus/trajectories/`
  
- **Forbidden Pattern Registry**
  - Detected violations and their resolutions
  - Location: `.aureus/patterns.json`
  - Feeds into critic agent training

**Memory Structure**:
```
.aureus/
├── policy.yaml              # Main governance policy
├── decisions/               # ADRs
│   ├── 001-use-bcrypt.md
│   ├── 002-separate-auth-module.md
│   └── ...
├── trajectories/            # Session logs
│   ├── 2026-02-27-session-1.json
│   └── ...
├── ledger.jsonl            # Cost/evidence log
└── patterns.json           # Pattern violations
```

**Memory Operations**:
- **Load**: Fast (< 100ms), lazy loading of trajectories
- **Save**: Atomic writes, no corruption on failure
- **Query**: Simple file-based queries, no SQL needed
- **Retention**: Configurable (default: keep all ADRs, last 30 sessions)

### 1.9 Security & Permission Layer
- **Permission tier matrix** (4-tier graduated risk model)
  - Tier 0: Always safe (file_read, search)
  - Tier 1: Approve once per session (file_write, git_commit)
  - Tier 2: Prompt every time (shell_exec, file_delete)
  - Tier 3: Disabled by default (web_fetch, git_push)
- **Phase-based permission escalation** (tighter in Gather phase)
- File system boundary enforcement
- Shell command whitelisting/blacklisting
- Network access control (disabled by default)
- **Hook sandboxing** (isolated FS, no network, resource limits, timeouts)
- **Checkpoint-based rollback** (atomic revert to named snapshots)
- Audit logging (all tool executions with timestamps)

### 1.10 Model Provider Interface
- Unified LLM abstraction
- Provider-specific adapters (Anthropic, OpenAI, Google, Local)
- **Multi-model strategy** (reasoning vs fast model selection)
  - Planning: Expensive, smart model (Claude Opus, GPT-4)
  - Building: Fast, capable model (Claude Sonnet, GPT-4o)
  - Testing: Cheap verification model (GPT-4o-mini, local)
- Prompt template management
- Token counting and cost tracking
- Response streaming and parsing
- **Context budget enforcement** (track tokens per phase)

---

## 2. Execution Flow

The complete execution flow follows this deterministic sequence:

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. User Intent (CLI)                                            │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. Session Context Assembly                                      │
│    - Load project policy                                         │
│    - Scan file system                                            │
│    - Check git state                                             │
│    - Load memory/ADRs                                            │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. Tier 1 GVUFD — Intelligent Specification                     │
│    - Analyze project context (type, size, patterns)             │
│    - Generate appropriate budgets (not manual config)           │
│    - Infer forbidden patterns from existing code issues         │
│    - Propose policy if first run                                │
│    - Adapt based on previous session learnings                  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. Tier 2 Pricing — Adaptive Cost Prediction                    │
│    - Predict cost using learned model (not just formula)        │
│    - Allocate budget based on task complexity                   │
│    - Learn from past cost predictions (estimated vs actual)     │
│    - Adjust thresholds based on override patterns               │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. Planner Agent — Action Decomposition                         │
│    - Break down task into atomic actions                         │
│    - Assign preliminary costs                                    │
│    - Order actions for dependencies                              │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 6. Pricing Gate — Cost Validation                               │
│    - Calculate total cost                                        │
│    - Check against budget                                        │
│    - Reject or request simplification if over budget            │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼ (if approved)
┌─────────────────────────────────────────────────────────────────┐
│ 7. Tool Execution (via Tool Bus)                                │
│    - Permission check                                            │
│    - Sandbox preparation                                         │
│    - Execute action                                              │
│    - Capture result                                              │
│    - Create rollback point                                       │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 8. Tester Agent — Verification                                  │
│    - Run acceptance tests                                        │
│    - Verify success criteria                                     │
│    - Check for regressions                                       │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 9. Critic Agent — Architectural Review                          │
│    - Scan for forbidden patterns                                 │
│    - Check budget compliance                                     │
│    - Identify over-engineering                                   │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 10. Reflexion Agent — Mandatory Simplification                  │
│     - Remove unnecessary abstractions                            │
│     - Consolidate duplicate logic                                │
│     - Inline trivial functions                                   │
│     - Reduce complexity metrics                                  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 11. Memory Update                                                │
│     - Log trajectory                                             │
│     - Update cost ledger                                         │
│     - Record ADRs if architectural                               │
│     - Persist policy updates                                     │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 12. Report to User                                               │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Phase-Specific Gating Logic

This is the **critical anti-bloat mechanism** that prevents 40k LOC sprawl. Every action passes through multi-layered gates **before execution**.

### 3.1 The Gate Sequence (Before Every Action)

**5 Gates** (simplified from 7 for Phase 1):

```python
def gate_action(action: Action, phase: Phase, context: Context) -> Decision:
    """
    Multi-layered gate that prevents architectural drift.
    Executes in order; first rejection stops the sequence.
    """
    
    # Gate 1: Specification Gate (GVUFD validates intent + phase)
    if not is_allowed_in_phase(action.tool, phase):
        return REJECT(f"Tool {action.tool} not allowed in {phase} phase")
    
    # Gate 2: Cost Estimation Gate (SPK predicts complexity)
    cost = spk.calculate_cost(action, context)
    
    # Gate 3: Budget Gate (SPK enforces limits)
    if cost.total > context.budget.remaining:
        # Trigger alternative engine
        alternatives = spk.suggest_alternatives(action, context)
        return REJECT_WITH_ALTERNATIVES(cost, alternatives)
    
    # Gate 4: Permission Gate (Security checks tool permissions)
    permission_tier = get_permission_tier(action.tool)
    if not check_permission(permission_tier, context.policy):
        return REJECT(f"Permission denied for tier {permission_tier} tool")
    
    # Gate 5: Safety Gate (Pattern check + Checkpoint creation)
    # - Check forbidden patterns
    violations = gvufd.check_patterns(action, context)
    if violations:
        return REJECT(f"Forbidden patterns: {violations}")
    
    # - Create checkpoint before mutation
    if action.is_mutation:
        checkpoint = create_checkpoint(context)
        context.active_checkpoint = checkpoint
    
    # - Verify context budget
    if context.token_usage + action.estimated_tokens > context.token_limit:
        return REJECT("Context budget exceeded - pruning required")
    
    # All gates passed
    return APPROVED(action, cost, checkpoint)
```

### 3.2 Phase-Specific Tool Restrictions

Each phase has different tool access levels:

#### Phase 1: Gather Context (Read-Only)
**Allowed Tools**:
- `file_read` (Tier 0)
- `search` (Tier 0)
- `grep_search` (Tier 0)
- `list_dir` (Tier 0)
- `git_status` (Tier 0)

**Forbidden Tools**:
- All write operations
- All execution operations
- All network operations

**Rationale**: Context gathering must be side-effect free to prevent accidental mutations.

---

#### Phase 2: Take Action (Gated Mutations)
**Allowed Tools** (with gates):
- `file_write` (Tier 1) - after cost + pattern check
- `file_delete` (Tier 2) - with user prompt
- `shell_exec` (Tier 2) - whitelisted commands only
- `git_commit` (Tier 1) - after checkpoint
- `create_file` (Tier 1) - after budget check

**Forbidden Tools**:
- `git_push` (Tier 3) - requires explicit enable
- `web_fetch` (Tier 3) - disabled by default

**Rationale**: Mutations require full governance approval.

---

#### Phase 3: Verify Results (Test Execution)
**Allowed Tools**:
- `file_read` (Tier 0)
- `shell_exec` (Tier 1) - test commands only
- `git_diff` (Tier 0)

**Forbidden Tools**:
- `file_write` - no mutations during verification
- `file_delete` - no cleanup during test

**Rationale**: Verification must be deterministic and reproducible.

---

### 3.3 SPK Alternative Suggestion Engine

When an action is rejected due to high cost, SPK suggests cheaper alternatives:

```python
def suggest_alternatives(action: Action, context: Context) -> list[Alternative]:
    """
    Generate progressively simpler alternatives to high-cost actions.
    Ordered from most feature-preserving to most aggressive simplification.
    """
    alternatives = []
    
    # Strategy 1: Single-File Solution
    if action.creates_new_files > 1:
        alternatives.append(Alternative(
            strategy="single_file",
            description="Consolidate into one file",
            cost_reduction=action.cost * 0.6,
            code_snippet="# Combine all logic into single module"
        ))
    
    # Strategy 2: Reuse Existing Library
    if action.adds_dependencies > 0:
        existing_libs = find_existing_capabilities(action, context)
        if existing_libs:
            alternatives.append(Alternative(
                strategy="reuse_library",
                description=f"Use existing {existing_libs[0]}",
                cost_reduction=action.cost * 0.8,
                code_snippet=f"# Use {existing_libs[0]} instead"
            ))
    
    # Strategy 3: Inline Functions (No New Abstraction)
    if action.adds_abstractions > 0:
        alternatives.append(Alternative(
            strategy="inline",
            description="Inline logic without new classes/interfaces",
            cost_reduction=action.cost * 0.5,
            code_snippet="# Direct implementation without abstraction"
        ))
    
    # Strategy 4: Delete Scaffolding
    if action.adds_boilerplate:
        alternatives.append(Alternative(
            strategy="delete_scaffolding",
            description="Remove unnecessary boilerplate",
            cost_reduction=action.cost * 0.4,
            code_snippet="# Minimal implementation only"
        ))
    
    # Strategy 5: Function-First Approach
    if action.creates_classes > 0:
        alternatives.append(Alternative(
            strategy="function_first",
            description="Use functions instead of classes",
            cost_reduction=action.cost * 0.7,
            code_snippet="# Pure functions, no OOP"
        ))
    
    # Strategy 6: Budget Negotiation
    alternatives.append(Alternative(
        strategy="increase_budget",
        description=f"Request budget increase ({action.cost:.0f} points needed)",
        cost_reduction=0.0,
        code_snippet="# User must approve budget increase"
    ))
    
    return alternatives
```

### 3.4 Checkpoint and Rollback Mechanism

Every mutation creates an atomic rollback point:

```python
class CheckpointManager:
    """
    Manages atomic checkpoints for rollback.
    Uses Git under the hood for file changes.
    """
    
    def create_checkpoint(self, context: Context) -> Checkpoint:
        """Create named checkpoint before mutation."""
        checkpoint = Checkpoint(
            id=generate_id(),
            timestamp=now(),
            session_id=context.session_id,
            working_tree_state=git.stash_create(),
            file_checksums=calculate_checksums(context.working_set),
            budget_snapshot=context.budget.copy()
        )
        self.checkpoints.append(checkpoint)
        return checkpoint
    
    def rollback(self, checkpoint: Checkpoint) -> None:
        """Atomic rollback to checkpoint."""
        # Restore file state
        git.stash_apply(checkpoint.working_tree_state)
        
        # Restore budget
        context.budget = checkpoint.budget_snapshot
        
        # Log rollback
        log_rollback(checkpoint)
    
    def list_checkpoints(self) -> list[Checkpoint]:
        """List available rollback points."""
        return self.checkpoints
```

### 3.5 Context Budget Management

Prevent context window overflow:

```python
class ContextManager:
    """
    Manages working set and context budget.
    Prunes least-used files when approaching token limit.
    """
    
    def __init__(self, token_limit: int):
        self.token_limit = token_limit
        self.token_usage = 0
        self.working_set = {}  # file -> (content, last_access, tokens)
    
    def add_file(self, path: str, content: str) -> bool:
        """Add file to working set if budget allows."""
        tokens = count_tokens(content)
        
        if self.token_usage + tokens > self.token_limit:
            # Try pruning
            self.prune_lru(needed=tokens)
            
            if self.token_usage + tokens > self.token_limit:
                return False  # Still can't fit
        
        self.working_set[path] = {
            "content": content,
            "last_access": now(),
            "tokens": tokens
        }
        self.token_usage += tokens
        return True
    
    def prune_lru(self, needed: int) -> None:
        """Remove least recently used files until budget available."""
        # Sort by last access
        sorted_files = sorted(
            self.working_set.items(),
            key=lambda x: x[1]["last_access"]
        )
        
        freed = 0
        for path, data in sorted_files:
            if freed >= needed:
                break
            
            # Don't prune pinned files
            if not data.get("pinned"):
                self.remove_file(path)
                freed += data["tokens"]
    
    def pin_file(self, path: str) -> None:
        """Mark file as must-keep in working set."""
        if path in self.working_set:
            self.working_set[path]["pinned"] = True
```

### 3.6 Repository Indexer

Fast semantic and structural code search:

```python
class RepositoryIndexer:
    """
    Builds symbol table and dependency graph for fast queries.
    Uses ripgrep for raw search, tree-sitter for parsing.
    """
    
    def __init__(self, project_root: str):
        self.project_root = project_root
        self.symbol_table = {}  # name -> [locations]
        self.dependency_graph = {}  # file -> [dependencies]
    
    def build_index(self) -> None:
        """Build complete index of project."""
        # Use ripgrep for fast file discovery
        files = self.discover_source_files()
        
        for file in files:
            # Parse with tree-sitter
            tree = parse_file(file)
            
            # Extract symbols (classes, functions, variables)
            symbols = extract_symbols(tree)
            for symbol in symbols:
                self.symbol_table[symbol.name] = self.symbol_table.get(symbol.name, [])
                self.symbol_table[symbol.name].append(symbol.location)
            
            # Extract dependencies (imports, requires)
            deps = extract_dependencies(tree)
            self.dependency_graph[file] = deps
    
    def find_symbol(self, name: str) -> list[Location]:
        """Find all locations where symbol is defined."""
        return self.symbol_table.get(name, [])
    
    def get_dependency_closure(self, file: str) -> list[str]:
        """Get all files that file depends on (transitive)."""
        closure = set()
        to_visit = [file]
        
        while to_visit:
            current = to_visit.pop()
            if current in closure:
                continue
            closure.add(current)
            to_visit.extend(self.dependency_graph.get(current, []))
        
        return list(closure)
```

---

## 4. Governance Invariants

These rules are **non-negotiable** and enforced by the governance layers:

### 4.1 No Premature Abstraction
- **Rule**: No abstraction without ≥ 2 concrete implementations
- **Enforcement**: Critic agent rejects single-use abstractions
- **Exception**: Core architecture interfaces (documented in policy)

### 4.2 No Dependency Injection Container
- **Rule**: No DI framework in core
- **Rationale**: Adds complexity without value in small-scale systems
- **Alternative**: Constructor injection with manual wiring

### 4.3 No Plugin Registry in Core
- **Rule**: No dynamic plugin loading in core modules
- **Rationale**: Increases security surface and complexity
- **Alternative**: Compile-time tool registration

### 4.4 No Event Bus
- **Rule**: No pub/sub event system unless ≥ 3 independent subscribers
- **Rationale**: Indirection without benefit
- **Alternative**: Direct function calls

### 4.5 No Repository Pattern (Unless Multiple Backends)
- **Rule**: No repository abstraction for single storage backend
- **Rationale**: Unnecessary layer
- **Alternative**: Direct data access with clear boundaries

### 4.6 Adapter Size Limit
- **Rule**: All adapters ≤ 200 LOC
- **Enforcement**: Pricing kernel rejects oversized adapters
- **Rationale**: Adapters should be thin translation layers

### 4.7 Dependency Budget
- **Rule**: New dependencies require pricing approval
- **Cost Formula**: `cost = lines_of_code / 1000 + transitive_deps * 5 + security_score`
- **Enforcement**: Automated rejection if over budget

### 4.8 Module Limit
- **Rule**: Core architecture ≤ 6 modules
- **Enforcement**: GVUFD specification
- **Rationale**: Forces cohesion and prevents drift

### 4.9 File Count Budget
- **Rule**: ≤ 25 files in core (excluding tests, examples, docs)
- **Enforcement**: Build-time check
- **Rationale**: Discourages file explosion

### 4.10 LOC Budget
- **Rule**: Target 4k LOC, hard limit 8k LOC (core)
- **Enforcement**: Reflexion triggers at 90% budget
- **Action**: Mandatory simplification pass

### 4.11 Forbidden Patterns
Automatically rejected:
- God objects (class > 500 LOC)
- Deep inheritance (> 2 levels)
- Circular dependencies
- Global mutable state (except controlled config)
- Reflection-based metaprogramming (without justification)

### 4.12 Simplification Priority
- **Rule**: Reflexion runs on every significant change
- **Trigger**: Any action that adds > 100 LOC or introduces abstraction
- **Goal**: Reduce complexity delta by 20% before finalizing

---

## 5. Data Flow

### 4.1 Context Flow
```
User Intent
  → CLI Parser
    → Session Manager (loads context)
      → Memory Loader (policy, ADRs, trajectories)
        → GVUFD (enriches with governance + history)
          → Agent Swarm (operates within bounds)
            → Memory Writer (persists learnings, ADRs, costs)
```

### 4.2 Cost Flow
```
Action Proposal
  → Pricing Kernel (calculates cost)
    → Budget Checker (validates against policy)
      → Cost Ledger (logs estimate)
        → Approval/Rejection
          → Execution or Simplification Request
            → Cost Ledger (logs actual cost)
```

### 4.3 Tool Flow
```
Tool Request
  → Permission Layer (checks policy)
    → Sandbox Preparation
      → Tool Execution
        → Result Capture
          → Rollback Point Creation
            → Validation
              → Memory (log execution + cost)
```

### 4.4 Memory Flow
```
Session Start
  → Load Policy (.aureus/policy.yaml)
    → Load Recent Trajectories (last 5 sessions)
      → Load Active ADRs (.aureus/decisions/)
        → Build Context
          → Execute Session
            → Generate New ADR (if architectural)
              → Append to Cost Ledger
                → Save Trajectory
                  → Update Policy (if changed)
```

---

## 6. Module Boundaries

### 6.1 Core Modules (6)
1. **cli**: User interface and command handling
2. **harness**: Agentic orchestration loop
3. **governance**: Tier 1 + Tier 2 (GVUFD + SPK)
4. **agents**: Tier 3 (Planner, Builder, Tester, Critic, Reflexion)
5. **toolbus**: Tool abstraction and execution
6. **memory**: Persistent and session state

### 6.2 Supporting Modules (4)
7. **model_provider**: LLM abstraction
8. **security**: Permission and sandboxing
9. **utils**: Shared utilities (< 300 LOC)
10. **config**: Configuration management

---

## 7. Memory Architecture (Detailed)

### 7.1 Policy Memory Design

**Format**: YAML (human-readable, version-controllable)

**Schema**: See [docs/schemas/policy-schema.json](../docs/schemas/policy-schema.json)

**Key Sections**:
- `project`: Metadata and configuration
- `budgets`: Complexity limits (LOC, modules, files, dependencies)
- `forbidden_patterns`: Rules with detection logic
- `permissions`: Tool and file access control
- `cost_thresholds`: Warning/rejection limits
- `simplification`: Reflexion configuration
- `model_provider`: LLM settings
- `integrations`: Optional features (MCP, skills, hooks)

**Example**: See [examples/policy-simple-api.yaml](../examples/policy-simple-api.yaml)

**Operations**:
- Load on session start (cached)
- Validate on load (JSON schema)
- Update via CLI commands or agent proposals
- Version-controlled with project

---

### 7.2 Architecture Decision Record (ADR) Design

**Format**: Markdown (human-readable, searchable)

**Template**:
```markdown
# ADR-NNN: [Title]

## Status
[Proposed | Accepted | Rejected | Deprecated | Superseded by ADR-XXX]

## Context
What problem are we solving? What constraints exist?

## Decision
What did we decide to do?

## Consequences
- Positive: [Benefits]
- Negative: [Drawbacks]
- Cost: [Complexity cost breakdown]

## Governance
- Approved by: [Agent or human]
- Cost: [Total cost]
- Budget impact: [Percentage]
- Date: [ISO 8601]
- Patterns checked: [List]

## Alternatives Considered
What else did we consider and why was it rejected?
```

**Lifecycle**:
1. Agent identifies architectural decision
2. Generate ADR from template
3. Critic validates against policy
4. Pricing kernel calculates cost
5. User approves (if needed)
6. ADR committed to `.aureus/decisions/`
7. Referenced in future context loading

---

### 7.3 Session Trajectory Design

**Format**: JSON Lines (JSONL) - one JSON object per session

**Schema**:
```json
{
  "session_id": "uuid",
  "timestamp_start": "ISO 8601",
  "timestamp_end": "ISO 8601",
  "intent": "User's original request",
  "specification": {
    // Generated Tier 1 spec
  },
  "actions": [
    {
      "action_id": "1",
      "type": "file_write | file_read | shell_exec | ...",
      "agent": "planner | builder | tester | critic | reflexion",
      "params": { /* tool parameters */ },
      "estimated_cost": { /* breakdown */ },
      "actual_cost": { /* breakdown */ },
      "duration_ms": 1234,
      "status": "success | failed | rejected",
      "rollback": "yes | no"
    }
  ],
  "verification": {
    "tests_passed": 5,
    "tests_failed": 0,
    "patterns_violated": [],
    "budget_remaining": 305.0
  },
  "simplification": {
    "triggered": true,
    "loc_removed": 45,
    "abstractions_removed": 2,
    "complexity_reduction": 0.18
  },
  "outcome": "success | failed | partial",
  "total_cost": 195.3,
  "learnings": [
    "JWT expiration needs configuration",
    "Bcrypt cost factor should be policy-driven"
  ]
}
```

**Usage**:
- Debugging failed sessions
- Cost model refinement
- Pattern recognition
- Agent learning (future)

---

### 7.4 Cost Ledger Design

**Format**: JSON Lines (append-only)

**Entry Schema**:
```json
{
  "timestamp": "ISO 8601",
  "session_id": "uuid",
  "action_id": "1",
  "action_type": "file_write",
  "estimated_cost": {
    "loc": 120.0,
    "dependencies": 50.0,
    "abstractions": 50.0,
    "security": 30.0,
    "tool": 3.0,
    "total": 253.0
  },
  "actual_cost": {
    "loc": 135.0,
    "dependencies": 50.0,
    "abstractions": 75.0,
    "security": 30.0,
    "tool": 3.0,
    "total": 293.0
  },
  "variance": 40.0,
  "variance_percent": 0.158,
  "budget_before": 500.0,
  "budget_after": 207.0,
  "approved_by": "user | auto",
  "evidence": {
    "tests_passed": true,
    "patterns_clean": true,
    "performance_acceptable": true
  }
}
```

**Analytics**:
- Cost prediction accuracy over time
- Most expensive operation types
- Budget utilization trends
- Variance analysis for model refinement

---

### 7.5 Forbidden Pattern Registry Design

**Format**: JSON (structured violations log)

**Schema**:
```json
{
  "patterns": [
    {
      "name": "god_object",
      "description": "Classes over 500 LOC",
      "detection_rule": "class_loc > 500",
      "violations": [
        {
          "file": "src/models/user.py",
          "line": 1,
          "detected_at": "ISO 8601",
          "session_id": "uuid",
          "severity": "error",
          "auto_fixed": true,
          "resolution": "Split into User, UserAuth, UserProfile"
        }
      ],
      "total_violations": 1,
      "last_violation": "ISO 8601"
    }
  ],
  "statistics": {
    "total_violations": 5,
    "auto_fixed": 3,
    "manual_fixed": 2,
    "by_severity": {
      "error": 3,
      "warning": 2
    }
  }
}
```

**Usage**:
- Critic agent learns common violations
- Reflexion prioritizes frequent patterns
- User visibility into architectural health

---

### 7.6 Memory Query Patterns

**Common Queries**:
1. **Load Policy**: Direct file read, validated against schema
2. **Recent Context**: Load last N trajectories for context
3. **Active ADRs**: Load all non-superseded decisions
4. **Cost History**: Parse ledger for budget analysis
5. **Pattern Trends**: Aggregate violations over time

**No Database Required**:
- File-based storage is sufficient for MVP
- Simple glob patterns for trajectory queries
- JSON parsing for structured data
- Future: Optional vector DB for semantic search (Phase 3+)

---

### 7.7 Memory Retention Policy

**Configurable via Policy**:
```yaml
memory:
  retention:
    trajectories: 30  # Keep last 30 sessions
    ledger: all       # Never delete ledger
    adrs: all         # Never delete ADRs
    patterns: all     # Never delete violations
  
  compression:
    enabled: true
    after_days: 90    # Compress old trajectories
  
  backup:
    enabled: true
    frequency: daily
    location: .aureus/backups/
```

---

### 7.8 Memory Migration Strategy

**Version Changes**:
- Schema version in all files
- Migration scripts for breaking changes
- Backward compatibility for minor versions
- Clear upgrade paths documented

**Example Migration**:
```
v1.0 → v1.1: Add new policy fields (backward compatible)
v1.1 → v2.0: Restructure ADR format (migration script provided)
```

---

## 8. Scaling Strategy

AUREUS is designed for **bounded complexity**, not infinite scale.

### 8.1 When AUREUS Fits
- Projects under 50k LOC
- Teams under 10 developers
- Monolithic or modular monolithic architecture
- Clear architectural boundaries
- Cost-conscious development

### 8.2 When AUREUS Doesn't Fit
- Microservices with 50+ services
- Projects requiring infinite extensibility
- Teams unwilling to enforce budgets
- Chaotic/exploratory prototyping (where drift is acceptable)

### 8.3 Multi-Project Mode
For larger organizations:
- Each project has independent AUREUS instance
- Shared policy templates
- Centralized cost dashboards
- Cross-project pattern libraries

### 8.4 Extension Points (Optional)
- **plugins/**: Compiled extensions (not dynamically loaded)
- **skills/**: Reusable agent capabilities
- **hooks/**: Lifecycle event handlers

---

## 9. Security Model

### 9.1 Threat Model
AUREUS assumes:
- LLM responses may be adversarial
- User may accidentally grant excessive permissions
- External tools may have vulnerabilities

### 9.2 Defense Layers
1. **Tool Permission Matrix**: Explicit allow/deny per tool
2. **File System Boundaries**: Enforce project root boundaries
3. **Shell Command Filtering**: Whitelist/blacklist + pattern matching
4. **Network Isolation**: Disabled by default, requires explicit policy
5. **Audit Logging**: All tool executions logged with timestamps

### 9.3 Rollback Mechanism
Every mutation creates a rollback point:
- File changes: Git-based or filesystem snapshots
- Shell executions: Captured state before/after
- Dependency changes: Lockfile versioning

---

## 10. Extension Architecture

### 10.1 Skills System
Pre-packaged agent capabilities:
```
skills/
  ├── refactor_module.skill
  ├── add_tests.skill
  └── migrate_api.skill
```

Each skill is a governance-aware mini-workflow.

### 10.2 Hooks System
Lifecycle event handlers:
```
hooks/
  ├── pre_action.hook
  ├── post_verification.hook
  └── pre_commit.hook
```

Hooks are synchronous and budget-limited.

### 10.3 MCP Integration
Model Context Protocol connectors:
```
mcp/
  ├── filesystem_mcp.adapter
  ├── github_mcp.adapter
  └── database_mcp.adapter
```

MCP tools pass through same governance as built-in tools.

---

## 11. Performance Considerations

### 11.1 Latency Budget
- Context assembly: < 500ms
- GVUFD spec generation: < 2s
- Single tool execution: < 5s
- Full planning cycle: < 10s

### 11.2 Memory Usage
- Session memory: < 100MB
- Persistent memory: < 10MB per project
- Model context: Configurable (default 200k tokens)

### 11.3 Optimization Strategies
- Lazy context loading
- Incremental file scanning
- Cached policy evaluation
- Streaming LLM responses

---

## 12. Testing Strategy

### 12.1 Unit Tests
- Each module independently testable
- Mock tool execution
- Deterministic pricing

### 12.2 Integration Tests
- End-to-end scenarios with real file system
- Budget enforcement validation
- Rollback verification

### 12.3 Governance Tests
- Forbidden pattern detection
- Budget threshold enforcement
- Simplification effectiveness

### 12.4 Adversarial Tests
- Malicious tool requests
- Budget evasion attempts
- Permission escalation attempts

---

## 13. Comparison with Similar Systems

| Aspect | Traditional AI Agent | AUREUS |
|--------|---------------------|---------|
| Architecture Drift | Common | Prevented by governance |
| Complexity Growth | Unbounded | Hard budgets enforced |
| Cost Awareness | Post-hoc | Built-in pricing |
| Model Coupling | Tight | Fully abstracted |
| Reflexion | Optional | Mandatory |
| Tool Safety | Partial | Multi-layered |
| Extension Model | Plugin chaos | Governed extensions |

---

## 14. Future Architecture Considerations

### 14.1 Multi-Agent Coordination
- Cross-project agent communication
- Shared pattern libraries
- Distributed policy enforcement

### 14.2 Learning & Adaptation
- Policy evolution based on outcomes
- Cost model refinement
- Pattern recognition improvements

### 14.3 Enterprise Features
- Role-based access control (RBAC)
- Centralized audit dashboards
- Policy compliance reporting
- Integration with CI/CD pipelines

---

This architecture prioritizes **predictability, safety, and bounded complexity** over flexibility and extensibility. Every design decision is optimized for governance and long-term maintainability.
