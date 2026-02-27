# AUREUS Code Separation & Self-Modification Boundaries

**Date**: February 27, 2026  
**Context**: Clarifying separation between Aureus agent code and user workspace code, and defining self-modification boundaries for self-play/self-learning

---

## 1. Code Separation: Aureus vs User Workspace

### Current Architecture

**Aureus Agent Code** (`/aureus/src/`):
```
d:\All_Projects\Aureus_Coding_Agent\
├── src/                    # ← AUREUS AGENT CODE
│   ├── agents/            # Builder, Enhanced Builder
│   ├── governance/        # GVUFD, SPK
│   ├── memory/            # Trajectory, Summarization
│   ├── toolbus/           # Tools (Shell, Git, Web, etc.)
│   ├── model_provider/    # LLM integration
│   ├── cli/               # CLI commands
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

### Separation Mechanism

**Policy.project_root** (from `src/interfaces.py`):
```python
@dataclass
class Policy:
    """
    Policy governs what Aureus can do in a workspace
    """
    project_root: Path  # ← Defines boundary!
    # ... other fields
```

**Tool Sandboxing** (from `src/toolbus/tools.py`):
```python
class FileWriteTool:
    def __init__(self, project_root: Path):
        self.project_root = project_root.resolve()  # ← All operations scoped here
        
    def write_file(self, path: str, content: str):
        # Resolve path relative to project_root
        full_path = self.project_root / path
        
        # Validate path doesn't escape project_root
        full_path.relative_to(self.project_root)  # Raises if outside!
```

### Key Boundaries

| Aspect | Aureus Code | User Workspace |
|--------|-------------|----------------|
| **Location** | `/aureus/src/` | `policy.project_root` |
| **Purpose** | Coding agent implementation | User's application code |
| **Modified By** | Aureus developers (or Aureus self-play) | Aureus agent (governed by policy) |
| **Governance** | Aureus's own policy | User's `.aureus-policy.yaml` |
| **Memory** | Aureus learning data | Per-workspace `.aureus/memory/` |
| **Tests** | `/aureus/tests/` | `{project_root}/tests/` |

---

## 2. Self-Play / Self-Learning / Self-Optimization Boundaries

### What Aureus CAN Modify (During Self-Play)

#### ✅ 1. Aureus Agent Code (`/aureus/src/`)

**Governed by Aureus's own policy** (`aureus-self-policy.yaml`):

```yaml
version: "1.0"
project:
  name: "Aureus Agent"
  root: "/aureus"
  
budgets:
  max_loc: 10000          # Aureus can grow to 10K LOC
  max_modules: 50         # Limit module explosion
  max_files: 100          # Keep architecture clean
  max_dependencies: 20    # Minimize external deps

permissions:
  file_operations:
    - pattern: "src/**/*.py"        # ✅ Can modify agent code
      operations: ["read", "write"]
    - pattern: "tests/**/*.py"      # ✅ Can modify tests
      operations: ["read", "write"]
    - pattern: "docs/**/*.md"       # ✅ Can update docs
      operations: ["read", "write"]
      
  forbidden_patterns:
    - pattern: ".git/**"            # ❌ Can't modify version control
    - pattern: "LICENSE"            # ❌ Can't change license
    - pattern: "pyproject.toml"     # ❌ Can't modify build config (manually reviewed)
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
spec_generator = SpecificationGenerator()
spec = spec_generator.generate(intent, aureus_policy)

# SPK prices the change to Aureus itself
pricing_kernel = PricingKernel()
cost = pricing_kernel.price(spec, aureus_policy)

if cost.within_budget:
    # Aureus builds itself using its own builder!
    builder = EnhancedBuilderAgent(policy=aureus_policy)
    result = builder.build(intent)
    
    # Result: src/agents/builder_enhanced.py modified
    # New tests: tests/test_builder_rl.py created
```

#### ✅ 2. Learned Patterns & Utility Functions

**Location**: `/aureus/src/memory/learned_models/`

```python
# Aureus learns better cost models from experience
class LearnedCostModel:
    """Cost model trained on 10,000+ real sessions"""
    
    def predict_cost(self, spec: Specification) -> Cost:
        # Uses ML model trained from memory.trajectory data
        features = self._extract_features(spec)
        predicted_cost = self.model.predict(features)
        return predicted_cost

# Aureus learns better threshold derivation
class LearnedUtilityFunction:
    """Utility function optimized via self-play"""
    
    def derive_thresholds(self, context: Context) -> Thresholds:
        # Uses RL policy trained via self-play
        state = self._context_to_state(context)
        thresholds = self.policy.predict(state)
        return thresholds
```

**Storage**: Serialized ML models, not hardcoded logic
- `learned_cost_model.pkl`
- `utility_function_v2.pkl`
- `pattern_weights.json`

#### ✅ 3. Configuration & Hyperparameters

**Location**: `/aureus/config/`

```yaml
# config/spk_config.yaml - Can be updated by self-play
cost_weights:
  loc_weight: 1.5        # ← Learned from data
  dependency_weight: 3.0  # ← Optimized via self-play
  abstraction_weight: 2.0 # ← Tuned based on outcomes

thresholds:
  auto_proceed_base: 300  # ← Updated when better values found
  prompt_base: 800
  rejection_base: 2000
```

### What Aureus CANNOT Modify (Immutable)

#### ❌ 1. Core Governance Principles

**Location**: Hardcoded in `/aureus/src/governance/principles.py`

**7 User-Facing Principles** (enforced by 18 technical constants):

```python
# These are IMMUTABLE - define what Aureus IS
class GovernancePrinciple(Enum):
    """7 user-facing governance guarantees"""
    RESPECT_POLICY = "respect_policy"
    ENFORCE_SANDBOX = "enforce_sandbox"
    PROVIDE_ALTERNATIVES = "provide_alternatives"
    REQUIRE_HUMAN_APPROVAL = "require_human_approval"
    MAINTAIN_BACKUPS = "maintain_backups"
    PROTECT_IMMUTABLE = "protect_immutable"
    GRADUAL_ENFORCEMENT = "gradual_enforcement"

class ImmutablePrinciples:
    """18 technical constants backing the 7 principles"""
    ENFORCE_SANDBOX: Final[bool] = True
    VALIDATE_ALL_PATHS: Final[bool] = True
    MAINTAIN_BACKUPS: Final[bool] = True
    # ... 15 more Final[bool] = True constants
```

**Why Immutable?**
- Define Aureus's identity
- Prevent self-modification into unsafe agent
- Ensure alignment with human values

#### ❌ 2. User Workspace Code (Without User Policy Permission)

**Protected by Policy Enforcement**:

```python
# Aureus CANNOT modify user code unless:
# 1. User policy explicitly allows it
# 2. User approves the change (for high-cost changes)
# 3. Change is within budget

def modify_user_code(intent: str, policy: Policy):
    # Generate specification
    spec = generate_specification(intent, policy)
    
    # Check if allowed by policy
    if not policy.allows(spec):
        raise PolicyViolation("Modification not allowed by policy")
    
    # Check budget
    cost = calculate_cost(spec, policy)
    if not cost.within_budget:
        raise BudgetExceeded("Change exceeds budget")
    
    # If high cost, require human approval
    if cost.total > policy.cost_thresholds["prompt"]:
        if not human_approves(spec, cost):
            raise HumanRejected("Human rejected change")
    
    # Only NOW can modify user code
    execute(spec)
```

#### ❌ 3. Safety-Critical Components

**Location**: `/aureus/src/security/` (if it exists)

```python
# Safety checks that prevent catastrophic failures
class SafetyChecks:
    """
    Immutable safety checks.
    Self-play cannot disable these.
    """
    
    @immutable
    def validate_file_path(self, path: Path, project_root: Path) -> bool:
        """Ensure path doesn't escape sandbox"""
        try:
            path.resolve().relative_to(project_root.resolve())
            return True
        except ValueError:
            return False  # Path escapes sandbox!
    
    @immutable
    def validate_git_history_intact(self, repo: Path) -> bool:
        """Ensure .git is never modified"""
        return not any_changes_to_git_history()
```

#### ❌ 4. License & Legal

**Files**: `LICENSE`, `COPYRIGHT`, legal notices
- Cannot be modified by self-play
- Changes require manual human review

---

## 3. Self-Play Implementation

### Self-Play Process (from `docs/meta-governance.md`)

```python
# AUREUS self-play for improvement
class AureusSelfPlay:
    """
    Aureus improves itself via self-play iterations
    """
    
    def run_self_play_iteration(self, iteration: int):
        """
        One iteration of self-improvement
        """
        # 1. Generate synthetic task for Aureus development
        task = self._generate_aureus_task()
        # Example: "Improve cost estimation accuracy for React projects"
        
        # 2. Use current Aureus to implement improvement
        aureus_policy = load_policy("aureus-self-policy.yaml")
        builder = EnhancedBuilderAgent(policy=aureus_policy)
        result = builder.build(task)
        
        # 3. Validate improvement
        if self._validate_improvement(result):
            # 4. Run regression tests
            test_result = run_tests("tests/")
            
            if test_result.all_pass:
                # 5. Commit improvement
                git_commit(result, message=f"Self-play iteration {iteration}")
                
                # 6. Update learned models
                self._update_learned_models(result)
            else:
                # Rollback if tests fail
                git_reset("HEAD~1")
        
        # 7. Record outcome in memory
        self._record_self_play_outcome(task, result)
    
    def _generate_aureus_task(self) -> str:
        """
        Generate task for improving Aureus itself
        
        Ideas:
        - Improve cost estimation
        - Better plan decomposition
        - Faster memory retrieval
        - More accurate pattern matching
        """
        # Use meta-learning to find weak areas
        weak_areas = self._analyze_aureus_performance()
        return self._create_improvement_task(weak_areas)
    
    def _validate_improvement(self, result: BuildResult) -> bool:
        """
        Validate that improvement doesn't break immutable principles
        """
        # Check 1: Core principles still intact
        assert GovernancePrinciples.RESPECT_POLICY == True
        assert GovernancePrinciples.ENFORCE_SANDBOX == True
        
        # Check 2: All existing tests still pass
        assert run_tests("tests/").all_pass
        
        # Check 3: Performance improved (or stayed same)
        assert self._measure_performance() >= self._baseline_performance()
        
        return True
```

### What Gets Modified in Practice

**Typical Self-Play Modifications**:

1. **Cost Model Weights** (`src/governance/spk.py`)
   ```python
   # Before self-play
   self.loc_weight = 1.0
   self.dependency_weight = 2.0
   
   # After 1000 iterations of self-play
   self.loc_weight = 1.3      # ← Learned better value
   self.dependency_weight = 2.7  # ← Learned better value
   ```

2. **Pattern Recognition** (`src/memory/patterns.py`)
   ```python
   # New pattern learned from 500 sessions
   LEARNED_PATTERN_27 = {
       "trigger": "Adding API endpoint with database",
       "best_approach": "Create model first, then endpoint",
       "avg_cost": 45.3,
       "success_rate": 0.92
   }
   ```

3. **Plan Decomposition Logic** (`src/agents/builder_enhanced.py`)
   ```python
   # Improved decomposition algorithm
   def _decompose_plan_v2(self, spec: Specification):
       # Uses RL policy learned from 10K successful builds
       return self.learned_policy.decompose(spec)
   ```

4. **Threshold Derivation** (`src/governance/gvufd.py`)
   ```python
   # Learned utility function replaces hardcoded thresholds
   def derive_thresholds(self, context: Context) -> Thresholds:
       # Uses trained model instead of hardcoded 300/800/2000
       return self.learned_utility_function.predict(context)
   ```

---

## 4. Summary Table

| Component | Location | Modified By Self-Play? | Protection Mechanism |
|-----------|----------|----------------------|---------------------|
| **Agent Code** | `/aureus/src/` | ✅ Yes | Aureus's own policy + tests |
| **Agent Tests** | `/aureus/tests/` | ✅ Yes | Must pass before commit |
| **Cost Models** | `/aureus/src/governance/spk.py` | ✅ Yes | Validation against holdout data |
| **Learned Patterns** | `/aureus/src/memory/patterns.py` | ✅ Yes | Validation against success metrics |
| **Config/Hyperparams** | `/aureus/config/*.yaml` | ✅ Yes | Bounded optimization (can't set to 0/infinity) |
| **Core Principles** | `/aureus/src/governance/principles.py` | ❌ No | Hardcoded immutable constants |
| **Safety Checks** | `/aureus/src/security/` | ❌ No | Marked `@immutable` |
| **License** | `/aureus/LICENSE` | ❌ No | Requires manual human review |
| **User Workspace** | `{project_root}/` | ❌ Not without policy | Sandbox enforcement |

---

## 5. Implementation Recommendations

### Add Explicit Code Separation

**Create**: `/aureus/src/security/sandbox.py`

```python
"""
Sandbox enforcement for code separation
"""

from pathlib import Path
from typing import Optional

class Sandbox:
    """
    Enforces separation between Aureus code and user workspace
    """
    
    AUREUS_ROOT = Path(__file__).parent.parent.parent  # /aureus/
    
    @staticmethod
    def is_aureus_code(path: Path) -> bool:
        """Check if path is Aureus agent code"""
        try:
            path.resolve().relative_to(Sandbox.AUREUS_ROOT)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def is_user_workspace(path: Path, project_root: Path) -> bool:
        """Check if path is in user workspace"""
        try:
            path.resolve().relative_to(project_root.resolve())
            return not Sandbox.is_aureus_code(path)
        except ValueError:
            return False
    
    @staticmethod
    def validate_modification(
        path: Path,
        policy: "Policy",
        is_self_play: bool = False
    ) -> bool:
        """
        Validate if modification is allowed
        
        Args:
            path: Path to modify
            policy: Applicable policy
            is_self_play: Is this Aureus self-improvement?
        
        Returns:
            True if allowed, False otherwise
        """
        # If self-play, use Aureus's own policy
        if is_self_play:
            if Sandbox.is_aureus_code(path):
                # Check against aureus-self-policy.yaml
                return Sandbox._check_aureus_policy(path)
            else:
                # Self-play shouldn't modify user workspace!
                return False
        
        # Normal operation: check user workspace policy
        if Sandbox.is_user_workspace(path, policy.project_root):
            return policy.allows_modification(path)
        else:
            # Can't modify Aureus code during normal operation
            return False
    
    @staticmethod
    def _check_aureus_policy(path: Path) -> bool:
        """Check if path modification allowed by Aureus's own policy"""
        aureus_policy = load_policy("aureus-self-policy.yaml")
        
        # Check immutable components
        if path.name in ["LICENSE", "principles.py", "sandbox.py"]:
            return False  # Immutable!
        
        # Check against Aureus's own budgets
        return aureus_policy.allows_modification(path)
```

### Add Self-Play Mode Flag

**Modify**: `/aureus/src/cli/main.py`

```python
@click.command()
@click.option('--self-play', is_flag=True, help='Run in self-improvement mode')
def build(intent: str, self_play: bool = False):
    """Build feature from intent"""
    
    if self_play:
        # Load Aureus's own policy
        policy = load_policy("aureus-self-policy.yaml")
        
        # Validate self-play is authorized
        if not authorized_self_play():
            raise SecurityError("Self-play mode requires authorization")
    else:
        # Load user workspace policy
        policy = load_policy(".aureus-policy.yaml")
    
    # Execute with appropriate policy
    builder = EnhancedBuilderAgent(policy=policy, self_play_mode=self_play)
    result = builder.build(intent)
```

---

## 6. Answers to Your Questions

### Q1: Is there code separation?

**Current State**: 
- **Implicit separation** via `project_root` in Policy
- Tools are scoped to `project_root`
- But no explicit "Aureus code vs workspace code" enforcement

**Recommendation**: 
- ✅ Add explicit `Sandbox` class (see above)
- ✅ Add `is_self_play` flag to distinguish modes
- ✅ Create `aureus-self-policy.yaml` for Aureus's own governance

### Q2: What can be modified during self-play/self-learn/self-optimize?

**Can Modify**:
- ✅ Agent implementation code (`/aureus/src/`)
- ✅ Learned models and patterns
- ✅ Configuration and hyperparameters
- ✅ Tests (must pass before commit)

**Cannot Modify**:
- ❌ Core governance principles (immutable)
- ❌ Safety-critical components
- ❌ License and legal files
- ❌ User workspace code (unless explicitly commanded by user)

**Validation**:
- All modifications must pass regression tests
- Performance must improve (or stay same)
- Core principles must remain intact
- Human review for high-impact changes

---

## Next Steps

To fully implement this separation:

1. **Add Sandbox Enforcement** (`src/security/sandbox.py`) - ~150 LOC
2. **Create Aureus Self-Policy** (`aureus-self-policy.yaml`) - ~50 lines
3. **Add Self-Play Mode** (`src/cli/main.py`) - ~100 LOC
4. **Immutable Principles** (`src/governance/principles.py`) - ~80 LOC
5. **Self-Play Tests** (`tests/test_self_play.py`) - ~200 LOC

**Total**: ~580 LOC to formalize separation and self-play boundaries.

Should we implement this now before continuing with CLI Memory Commands?
