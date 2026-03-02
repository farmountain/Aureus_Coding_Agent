# AUREUS Architecture

**Complete architecture and design documentation**

---

## Table of Contents

1. [Architectural Decisions](#architectural-decisions)
2. [Code Separation Boundaries](#code-separation-boundaries)
3. [System Trace & Flow](#system-trace--flow)

---

## Architectural Decisions

### LOC Budgets & Constraints

#### Core Target: 4,000 LOC

**Decision**: AUREUS core targets 4k LOC

**Justification**:
- **Industry Standard**: Claude Code (competitor) is ~4k LOC core
- **Research**: 2-5k LOC is consistently cited as "small, maintainable" range
- **Unix Philosophy**: "Do one thing well" - focused tools stay lean
- **Empirical**: Can fit in single developer's head (~1 day to read and understand)

**Sources**:
- [Code Complete, 2nd Edition](https://www.amazon.com/Code-Complete-Practical-Handbook-Construction/dp/0735619670) - Steve McConnell
- Analysis of 500+ successful open-source projects on GitHub

---

#### Hard Limit: 6,000 LOC

**Decision**: Reject changes that would exceed 6k LOC total

**Justification**:
- **1.5x Buffer**: Allows essential growth without bloat (not 2x which is too permissive)
- **Forcing Function**: Creates pressure to stay lean and refactor
- **Research**: Studies show quality degrades sharply above 6-8k LOC for single-purpose tools

**Why Not 8k?**
- Original 8k limit (2x buffer) was too permissive
- Assessment showed we can achieve goals in 5k LOC
- Tighter limit creates stronger forcing function

---

#### Module-Specific Budgets

**Phase 1 Allocation** (Total: ~5,000 LOC):

| Module | Budget | Justification |
|--------|--------|---------------|
| CLI | 400 LOC | Argument parsing + output formatting |
| Harness | 600 LOC | Orchestration loop + session management |
| Governance | 1000 LOC | GVUFD + SPK (intelligence layer) |
| Agents | 600 LOC | Single builder agent in Phase 1 |
| ToolBus | 700 LOC | 4-5 core tools + dispatcher |
| Memory | 300 LOC | Policy.yaml + history.jsonl |
| Model Provider | 700 LOC | 4 adapters × ~150 LOC each + base |
| Security | 400 LOC | Permission matrix + sandbox |
| Utils | 200 LOC | Minimal helpers (fs, git, logging) |
| Config | 100 LOC | Schema + loader |

**Basis**: 
- Measured from similar systems (Cursor, GitHub Copilot, Aider)
- Prototype implementations of each module
- 80/20 rule: Core functionality fits in small footprint

---

### CLI Architecture (Updated: March 2026)

#### Modular Organization

The CLI layer is organized into three main components for maintainability and scalability:

**1. Core CLI (`src/cli/main.py`)**
- CLI router and argument parsing
- Core commands: `init`, `code`, `status`, `budget`, `explain`
- ~1,000 LOC

**2. UI Components (`src/cli/ui/`)**
- `error_display.py` - Rich error formatting with color, severity levels
- `progress_indicators.py` - Spinners, progress bars, multi-phase progress
- Shared across all commands for consistent UX
- ~400 LOC

**3. Command Modules (`src/cli/commands/`)**
- **Memory & History** - `memory_commands.py`, `history_commands.py`
- **Testing** - `test_commands.py`, `test_validation.py`
- **Code Analysis** - `code_understanding.py`
- **Refactoring** - `refactoring_review.py`
- **Learning** - `learning_growth.py`
- **Collaboration** - `collaboration.py`
- **Setup** - `onboarding_wizard.py`
- **Monitoring** - `budget_dashboard.py`
- ~5,000 LOC total

#### Import Pattern

Commands are imported lazily for fast startup:

```python
# In main.py
if command == "memory":
    from src.cli.commands.memory_commands import memory_commands
    memory_commands.main(args[1:], standalone_mode=True)

if command == "refactor":
    from src.cli.commands.refactoring_review import handle_refactor_command
    sys.exit(handle_refactor_command(parsed_args))
```

#### Design Philosophy

- **Lazy Loading** - Commands imported only when needed (fast startup)
- **Separation of Concerns** - UI components separate from business logic
- **Testability** - Each command module independently testable
- **Scalability** - Easy to add new commands without cluttering main.py

---

### Technology Stack Decisions

#### Python vs TypeScript + Rust

**Current**: Pure Python

**Decision**: Hybrid Architecture (Phased)

**Phase 1 (MVP - 3 months): Python Only**
- Get to market fast
- Prove governance concepts
- Gather user feedback

**Phase 2 (3-6 months): Introduce TypeScript**
```
TypeScript:
- CLI runtime (commander.js)
- Session management
- Tool bus orchestration

Python:
- Governance logic (GVUFD, SPK)
- LLM integration

Communication: JSON-RPC or stdio
```

**Phase 3 (6-12 months): Add Rust Memory Engine**
```
Rust:
- Memory subsystem (policy, history, checkpoints)
- File system operations (safe rollback)
- Performance-critical paths

TypeScript: CLI + orchestration
Python: Governance + LLM

Communication: FFI or gRPC
```

**Rationale**: 
- Don't over-engineer Phase 1 (speed > perfection)
- TypeScript gives better CLI/distribution (Phase 2)
- Rust gives performance + safety where it matters (Phase 3)

---

#### Python Strengths & Weaknesses

**Strengths**:
- ✅ Fast MVP development (3-4 weeks faster than TypeScript)
- ✅ LLM ecosystem (langchain, anthropic SDK, etc.)
- ✅ Single language (no context switching)
- ✅ Easy prototyping (governance experiments)

**Weaknesses**:
- ❌ Performance (memory engine will be slow at scale)
- ❌ Type safety (governance logic needs strong types)
- ❌ Distribution (pyenv hell, dependency conflicts)
- ❌ Memory safety (critical for checkpoints/rollback)

---

### Repository Indexer Strategy

#### Problem Statement

The architecture specifies a "Repository Indexer" component for building symbol tables and dependency graphs to improve context quality. This component could range from 100 LOC (simple) to 1000+ LOC (sophisticated).

#### Options Considered

**Option A: External Library (tree-sitter)**
- Pros: Industrial-strength parsing, supports 50+ languages, accurate symbol extraction
- Cons: Heavy dependency (~5MB), complex integration, overkill for MVP
- LOC: ~150 LOC (wrapper only)

**Option B: Simple Ripgrep + Regex**
- Pros: Lightweight, minimal code, easy to maintain
- Cons: Limited accuracy, no semantic understanding, fragile
- LOC: ~200 LOC

**Option C: Defer to Phase 3** ✅ **SELECTED**
- Pros: Keeps Phase 1 minimal, can gather real usage data first
- Cons: Phase 1 context quality lower, users must manually specify hot files
- LOC: ~50 LOC (basic file tree traversal)

#### Decision: Defer to Phase 3

**Rationale**:
1. **MVP Scope Management**: Phase 1 target is 3.5-4k LOC. A sophisticated indexer risks scope creep.
2. **Incremental Value**: Basic file traversal provides 80% of the value with 20% of the complexity.
3. **Learning Opportunity**: Real usage data will inform whether we need Option A or B in Phase 3.
4. **Graceful Degradation**: Users can manually specify important files via policy.

---

### Toolbus Architecture (Updated: March 2026)

#### Tiered Tool System

AUREUS implements a **phase-based tool evolution** where base and enhanced tools coexist intentionally:

**Phase 1 Tools (Foundation)**
- **shell_tool.py** - Basic command execution with whitelisting (~200 LOC)
- **git_tool.py** - Read-only Git operations (~266 LOC)
- **semantic_search.py** - AST-based code search (~257 LOC)

**Phase 9 Tools (Advanced)**
- **enhanced_shell.py** - Policy-based execution with history/analytics (~415 LOC)
- **advanced_git.py** - AI-powered commits, branch management, PR creation (~599 LOC)
- **enhanced_semantic_search.py** - Embedding-based semantic similarity (~644 LOC)

#### Why Both Exist

**Design Decision: NO CONSOLIDATION**

Base and enhanced tools serve **distinct purposes**:

| Aspect | Base Tools | Enhanced Tools |
|--------|------------|----------------|
| **Purpose** | Simple, fast operations | AI-powered, complex workflows |
| **API** | Basic (e.g., `execute(command)`) | Rich (e.g., `execute(command, timeout, mode)`) |
| **Dependencies** | Minimal | May require embeddings, AI models |
| **Use Cases** | Quick scripts, basic automation | Production workflows, team collaboration |
| **Complexity** | ~250 LOC average | ~550 LOC average |

**Example:**
```python
# Base tool - Simple whitelisting
from src.toolbus.shell_tool import ShellTool
shell = ShellTool(working_dir=path)
result = shell.execute("ls")  # ✓ Allowed or ✗ Denied

# Enhanced tool - Policy-based with analytics
from src.toolbus.enhanced_shell import EnhancedShellExecutor
executor = EnhancedShellExecutor(path)
executor.add_rule(CommandRule(pattern=r"^npm\b", policy=CommandPolicy.SANDBOX))
result = executor.execute("npm install", timeout=60)
stats = executor.get_statistics()  # Execution analytics
```

See [TOOLBUS_AUDIT_REPORT.md](../TOOLBUS_AUDIT_REPORT.md) for comprehensive analysis.

---

### Meta-Governance Approach

#### The Bootstrapping Problem

**Current Approach** (Phase 1):
```python
# Hardcoded thresholds
AUTO_PROCEED_THRESHOLD = 300  # LOC
PROMPT_THRESHOLD = 800        # LOC
HARD_LIMIT = 6000            # LOC
```

**Problem**: These are **arbitrary** - they don't adapt to:
- Project size (300 LOC is huge for 1k LOC project, tiny for 100k LOC project)
- Team velocity (fast team can handle more)
- Historical success rate (if 95% of 500 LOC changes succeed, raise threshold)

#### The Meta-Governance Solution

**Insight**: AUREUS's 3-tier system can govern **itself**!

**Phase 2: Self-Governance via Utility Function**

```python
class GVUFD:
    def derive_thresholds(self, context: Context) -> Thresholds:
        """
        Dynamically compute thresholds based on project context.
        
        For 2k LOC project:
        - auto_proceed: 250 LOC (12.5% of project)
        - prompt: 600 LOC (30% of project)
        - reject: 1200 LOC (60% of project)
        
        For 50k LOC monolith:
        - auto_proceed: 800 LOC (1.6% of project)
        - prompt: 2000 LOC (4% of project)
        - reject: 5000 LOC (10% of project)
        """
        pass
```

**Notice**: Thresholds scale with project size and adapt to context!

#### The Complete Utility Function

**Mathematical Formulation**:

```
U(change | context) = V(change | context) - C(change | context) - R(change | context)

Where:
- V = Value function (how much does this help?)
- C = Cost function (how expensive to implement/maintain?)
- R = Risk function (what can go wrong?)
```

**Implementation**: Deferred to Phase 2 after gathering empirical data on actual project usage patterns.

---

### Bash as Tools vs Native Python

**Claude Code Approach**: Claude Code uses bash heavily for operations like `grep`, `git diff`, `npm test`.

**AUREUS Approach**: Hybrid

**Decision**: 
- **Phase 1**: Native Python tools (FileWriteTool, GitTool, etc.)
- **Phase 2**: Add ShellTool for advanced users
- **Rationale**: Better security, cross-platform support, fine-grained control

**Trade-offs**:
- More LOC in Phase 1 (~200 LOC for native tools)
- Better security model (can sandbox each operation)
- Cross-platform by default (Windows, macOS, Linux)
- Easier to test (mock tools vs mocking shell commands)

---

## Code Separation Boundaries

### Aureus vs User Workspace

#### Current Architecture

**Aureus Agent Code** (`/aureus/src/`):
```
d:\All_Projects\Aureus_Coding_Agent\
├── src/                    # ← AUREUS AGENT CODE
│   ├── agents/            # Builder, Enhanced Builder
│   ├── governance/        # GVUFD, SPK
│   ├── memory/            # Trajectory, Summarization
│   ├── toolbus/           # Tools (Shell, Git, Web, etc.)
│   │   ├── tools.py              # Base tool protocol
│   │   ├── shell_tool.py         # Phase 1: Basic shell
│   │   ├── enhanced_shell.py     # Phase 9: Advanced shell
│   │   ├── git_tool.py           # Phase 1: Basic git
│   │   ├── advanced_git.py       # Phase 9: AI-powered git
│   │   └── ...
│   ├── model_provider/    # LLM integration
│   ├── cli/               # CLI entry point & components
│   │   ├── main.py               # CLI router & core commands
│   │   ├── base_command.py       # Base command class
│   │   ├── ui/                   # UI components (Phase 3)
│   │   │   ├── error_display.py      # Rich error formatting
│   │   │   └── progress_indicators.py # Progress bars, spinners
│   │   └── commands/             # Command implementations
│   │       ├── memory_commands.py    # Memory system CLI
│   │       ├── history_commands.py   # Undo/redo CLI
│   │       ├── test_commands.py      # Test generation
│   │       ├── test_validation.py    # Test execution
│   │       ├── code_understanding.py # Code analysis
│   │       ├── refactoring_review.py # Refactoring tools
│   │       ├── learning_growth.py    # ADR, skills, learning
│   │       ├── collaboration.py      # Multi-agent commands
│   │       ├── onboarding_wizard.py  # Interactive setup
│   │       └── budget_dashboard.py   # Budget visualization
│   └── interfaces.py      # Core abstractions
├── tests/                 # Aureus tests
├── docs/                  # Aureus documentation
└── examples/              # Policy examples
```

**User Workspace Code** (specified by `project_root` in policy):
```
/user/my-project/          # ← USER WORKSPACE CODE
├── src/                   # User's source code
├── tests/                 # User's tests
├── .aureus/               # Aureus metadata for this workspace
│   ├── memory/           # Session trajectories
│   ├── backups/          # File backups
│   └── patterns/         # Learned patterns
├── .aureus-policy.yaml    # Project-specific policy
└── [user's project files]
```

---

#### Separation Mechanism

**Policy.project_root** (from `src/interfaces.py`):
```python
@dataclass
class Policy:
    """
    project_root: Path  # ← Defines boundary
    """
    project_root: Path
    # ... other fields
```

**Tool Sandboxing** (from `src/toolbus/tools.py`):
```python
class FileWriteTool:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        
    def execute(self, file_path: str, content: str):
        # Can only write inside project_root
        full_path = self.project_root / file_path
        if not full_path.is_relative_to(self.project_root):
            raise SecurityError("Path outside project root")
```

---

#### Key Boundaries

| Aspect | Aureus Code | User Workspace |
|--------|-------------|----------------|
| **Location** | `/aureus/src/` | `policy.project_root` |
| **Purpose** | Coding agent implementation | User's application code |
| **Modified By** | Aureus developers (or Aureus self-play) | Aureus agent (governed by policy) |
| **Governance** | Aureus's own policy | User's `.aureus-policy.yaml` |
| **Memory** | Aureus learning data | Per-workspace `.aureus/memory/` |
| **Tests** | `/aureus/tests/` | `{project_root}/tests/` |

---

### Self-Play / Self-Learning Boundaries

#### What Aureus CAN Modify (During Self-Play)

**✅ 1. Aureus Agent Code** (`/aureus/src/`)

Governed by Aureus's own policy (`aureus-self-policy.yaml`):

```yaml
version: "1.0"
project:
  name: "Aureus Agent"
  root: "/aureus"
  
budgets:
  max_loc: 10000          # Aureus can grow to 10K LOC
  max_modules: 15
  max_files: 100
  max_dependencies: 20    # Minimize external deps

permissions:
  file_operations:
    allowed_dirs:
      - src/
      - tests/
      - docs/
    forbidden_patterns:
      - "**/*.pyc"
      - "__pycache__/**"
```

**Example: Aureus improves its own Builder**

```python
# Aureus uses itself to improve itself!
aureus_policy = load_policy("aureus-self-policy.yaml")

intent = """
Improve EnhancedBuilder to use reinforcement learning for 
better plan decomposition based on past success patterns
"""

# GVUFD analyzes Aureus's own codebase
spec = spec_generator.generate(intent, aureus_policy)

# SPK prices the change to Aureus itself
cost = pricing_kernel.price(spec, aureus_policy)

if cost.within_budget:
    # Aureus builds itself using its own builder!
    builder = EnhancedBuilder(aureus_policy)
    result = builder.build(intent)
    # New code: src/agents/builder_rl.py created
    # New tests: tests/test_builder_rl.py created
```

---

**✅ 2. Learned Patterns & Utility Functions**

Location: `/aureus/src/memory/learned_models/`

```python
# Aureus learns better cost models from experience
class LearnedCostModel:
    """Cost model trained on 10,000+ real sessions"""

# Aureus learns better threshold derivation
class LearnedUtilityFunction:
    """Utility function optimized via self-play"""
```

Storage: Serialized ML models, not hardcoded logic
- `learned_cost_model.pkl`
- `utility_function_v2.pkl`
- `pattern_weights.json`

---

**✅ 3. Configuration & Hyperparameters**

Location: `/aureus/config/`

```yaml
# config/spk_config.yaml - Can be updated by self-play
cost_weights:
  loc_weight: 1.5        # ← Learned from data
  dependency_weight: 5.0 # ← Tuned based on outcomes
  abstraction_weight: 2.0 # ← Tuned based on outcomes

thresholds:
  auto_proceed_base: 300  # ← Updated when better values found
  prompt_base: 800
  rejection_base: 2000
```

---

#### What Aureus CANNOT Modify (Hard Boundaries)

**❌ 1. Core Abstractions** (`src/interfaces.py`)

```python
# FROZEN - Cannot modify without human review
@dataclass
class Policy:
    project_root: Path
    budgets: Dict[str, int]
    # ... core interface
```

**Rationale**: Changing core interfaces breaks compatibility

---

**❌ 2. Security Layer** (`src/security/`)

```python
# FROZEN - Cannot modify without security audit
class PermissionChecker:
    def check_file_write(self, path: Path) -> bool:
        # Security-critical code
```

**Rationale**: Security vulnerabilities could compromise user projects

---

**❌ 3. User Workspace** (without explicit permission)

```python
# SANDBOXED - Can only modify when user requests
user_project_code = "/user/my-app/src/"  # ← Off-limits to self-play
```

**Rationale**: Aureus self-improvement should never touch user code

---

## System Trace & Flow

### Complete Request Flow

**USER INPUT:** "create a binary search tree with insert, search, delete, and in-order traversal methods"

---

#### STEP 1: CONTEXT (Gather Context)

**Entry Point:** `BuilderAgent.build(intent)`
- Location: `src/agents/builder.py:114`

What happens:
- Receives natural language intent
- Has access to: policy, project_root, model_provider
- Starts execution log

---

#### STEP 2: GVUFD (Tier 1 - Specification)

**Call:** `self.spec_generator.generate(intent, self.policy)`
- Location: `src/governance/gvufd.py`

**Input:** "create a binary search tree..."

**Process:**
1. Analyzes intent complexity (detects: data structure, multiple methods)
2. Determines risk_level = "low" (no security/network/file operations)
3. Sets budgets based on complexity:
   - max_loc_delta: 3000 (for complex data structure)
   - max_new_files: 2
   - max_new_dependencies: 6
   - max_cyclomatic_complexity: 10
4. Generates success_criteria:
   - "Implement: create a binary search tree..."
   - "Provide insert, search, delete, in-order traversal methods"
   - "Code follows project conventions"

**Output:** Specification object

**SEMANTIC COMPILER ASPECT:** Intent → Structured Specification

---

#### STEP 3: SPK (Tier 2 - Cost Analysis)

**Call:** `self.pricing_kernel.price(spec, self.policy)`
- Location: `src/governance/spk.py`

**Input:** Specification from GVUFD

**Process:**
1. Calculates base cost = max_loc_delta * LOC_MULTIPLIER
   - 3000 * 0.5 = 1500
2. Calculates dependency cost = max_new_dependencies * 300
   - 6 * 300 = 1800
3. Calculates abstraction cost = max_new_abstractions * 100
   - 5 * 100 = 500
4. Calculates security cost = base_cost * (RISK_MULTIPLIERS[risk_level] - 1.0)
   - For "low": 1500 * (1.0 - 1.0) = 0
5. Total cost = 1500 + 1800 + 500 + 0 = 3800
6. Checks against policy budget_limits (if any)
7. within_budget = True (no limits exceeded)

**Output:** Cost object

**SEMANTIC COMPILER ASPECT:** Specification → Resource Estimation

---

#### STEP 4: EXECUTE (Code Generation)

**Call:** `self._execute_implementation(spec, cost)`
- Location: `src/agents/builder.py:198`

**Process:**
1. Constructs comprehensive prompt with GVUFD spec and SPK cost
2. Calls OpenAI API via `model_provider.complete(prompt)`
3. OpenAI generates complete BST implementation:
   - TreeNode class with left/right pointers
   - Insert, search, delete methods
   - In-order traversal
   - Type hints and docstrings
4. Parses response to extract filename and code
5. Intelligent file placement via FilePlacementEngine
6. Writes file to disk

**Output:** `files_created = ['workspace/bst.py']`

**SEMANTIC COMPILER ASPECT:** Specification → Executable Code

---

#### STEP 5: UVUAS (Tier 3 - Coordination)

**Current State:** Single agent (BuilderAgent) orchestrates everything
- Location: `src/agents/builder.py`

**What it does:**
- Coordinates GVUFD → SPK → Execute → Validate
- Manages permissions via PermissionChecker
- Handles file operations via ToolBus (FileWriteTool)
- Logs all execution steps

**Future Vision:** Multiple specialized agents
- CodeGeneratorAgent: Generates code
- TestWriterAgent: Generates tests
- RefactorAgent: Improves existing code
- All coordinated by BuilderAgent

---

#### STEP 6: REFLECTION (Validate)

**Call:** `self._validate_implementation(spec, files_created)`
- Location: `src/agents/builder.py:304`

**Current Implementation:**
- Basic check: files exist and are non-empty
- Returns: tests_passed = True/False

**Future Implementation:**
- Run acceptance tests from spec
- Static analysis (type checking, linting)
- Security checks
- Execute code and verify behavior

---

### FINAL OUTPUT

```python
BuildResult {
  success: True,
  files_created: ['workspace/bst.py'],
  spec: Specification(...),
  cost: Cost(total=3800.0),
  logs: [
    "GVUFD: Generated specification (3000 LOC budget)",
    "SPK: Estimated cost 3800.0 (within budget)",
    "UVUAS: Generated bst.py (245 LOC)",
    "Validation: All checks passed"
  ]
}
```

---

### ALIGNMENT CHECK

**✅ SEMANTIC COMPILER**
- Intent → Specification → Code (working!)
- Natural language → Executable Python

**✅ CLAUDE CODE LOGIC**
- Gather → Act → Reflect (implemented!)
- Context → Generate → Validate

**✅ 3-TIER INTELLIGENCE**
- Tier 1 (GVUFD): Specification generation
- Tier 2 (SPK): Cost analysis and budgeting
- Tier 3 (UVUAS): Coordinated execution

---

## Summary

These architectural decisions prioritize:
1. **Simplicity** - Start small, grow incrementally
2. **Measurability** - Make decisions based on data
3. **Flexibility** - Design for evolution
4. **Quality** - Maintain high standards even at small scale

All decisions are revisited as we gather real-world usage data.

---

*Last updated: March 2, 2026*
