# Meta-Governance: Using the 3-Tier System to Define Its Own Thresholds

**Core Insight**: Instead of hardcoding thresholds like 300/800 LOC or 6k hard limits, AUREUS's 3-tier governance should **derive these values dynamically** from its utility function.

**Date**: February 27, 2026

---

## The Bootstrapping Problem

**Current Approach** (Phase 1):
```python
# Hardcoded thresholds
AUTO_PROCEED_THRESHOLD = 300  # LOC
PROMPT_THRESHOLD = 800        # LOC
HARD_LIMIT = 6000            # LOC

def should_approve(cost: Cost) -> Decision:
    if cost < 300:
        return Decision.approved()
    elif cost < 800:
        return Decision.prompt()
    else:
        return Decision.rejected()
```

**Problem**: These are **arbitrary** - they don't adapt to:
- Project size (300 LOC is huge for 1k LOC project, tiny for 100k LOC project)
- Team velocity (fast team can handle more)
- Historical success rate (if 95% of 500 LOC changes succeed, raise threshold)
- User preferences (some users want tighter control)

---

## The Meta-Governance Solution

**Insight**: AUREUS's 3-tier system can govern **itself**!

### Phase 2: Self-Governance via Utility Function

```python
class GVUFD:
    def derive_thresholds(self, context: Context) -> Thresholds:
        """
        Instead of hardcoding, derive thresholds from utility function.
        
        The utility function is:
        U(change) = value(change) - cost(change) - risk(change)
        
        Where thresholds are chosen to maximize expected utility.
        """
        
        # Analyze project context
        project_size = context.current_loc
        project_complexity = self._measure_complexity(context)
        team_velocity = self._estimate_velocity(context.history)
        user_risk_tolerance = context.policy.risk_tolerance  # user-configurable
        
        # Derive auto-proceed threshold
        # "At what LOC delta does expected utility turn negative?"
        auto_proceed = self._find_threshold(
            condition=lambda loc: self._expected_utility(loc, context) > 0,
            project_size=project_size,
            complexity=project_complexity
        )
        
        # Derive prompt threshold
        # "At what LOC delta is variance too high to auto-approve?"
        prompt_threshold = self._find_threshold(
            condition=lambda loc: self._utility_variance(loc, context) > user_risk_tolerance,
            project_size=project_size,
            complexity=project_complexity
        )
        
        # Derive hard limit
        # "At what LOC delta does value approach zero regardless of implementation?"
        hard_limit = self._find_threshold(
            condition=lambda loc: self._marginal_value(loc, context) < 0.1,
            project_size=project_size,
            complexity=project_complexity
        )
        
        return Thresholds(
            auto_proceed=auto_proceed,
            prompt=prompt_threshold,
            reject=hard_limit
        )
```

### Concrete Example

**For a 2k LOC Flask API**:
```python
context = Context(
    current_loc=2000,
    modules=6,
    dependencies=8,
    history=past_30_sessions,
    policy=user_policy
)

thresholds = gvufd.derive_thresholds(context)
# Result:
# - auto_proceed: 250 LOC (12.5% of project)
# - prompt: 600 LOC (30% of project)
# - reject: 1200 LOC (60% of project - would double size)
```

**For a 50k LOC monolith**:
```python
context = Context(
    current_loc=50000,
    modules=25,
    dependencies=50,
    history=past_30_sessions,
    policy=user_policy
)

thresholds = gvufd.derive_thresholds(context)
# Result:
# - auto_proceed: 800 LOC (1.6% of project)
# - prompt: 2000 LOC (4% of project)
# - reject: 5000 LOC (10% of project)
```

**Notice**: Thresholds scale with project size and adapt to context!

---

## The Complete Utility Function

**Mathematical Formulation**:

```
U(change | context) = V(change | context) - C(change | context) - R(change | context)

Where:
- V = Value function (how much does this help?)
- C = Cost function (how expensive to implement/maintain?)
- R = Risk function (what can go wrong?)
```

### Value Function V(change | context)

```python
def value_function(change: Change, context: Context) -> float:
    """
    Value = alignment with user intent × quality of solution × velocity improvement
    """
    
    # How well does this solve the user's problem?
    alignment = self._measure_alignment(change, context.intent)
    
    # How clean/maintainable is the solution?
    quality = self._measure_quality(change, context.standards)
    
    # Does this unblock future work?
    enablement = self._measure_enablement(change, context.roadmap)
    
    return alignment * quality * (1 + 0.1 * enablement)
```

### Cost Function C(change | context)

```python
def cost_function(change: Change, context: Context) -> float:
    """
    Cost = implementation effort + maintenance burden + integration complexity
    """
    
    # How much LOC/time to implement?
    implementation_cost = change.loc_delta * self._loc_to_effort_ratio(context)
    
    # How much ongoing maintenance?
    maintenance_cost = (
        change.new_abstractions * 10 +  # Each class = 10 LOC-equivalent
        change.new_dependencies * 50 +   # Each dep = 50 LOC-equivalent
        change.cyclomatic_complexity * 2  # Each branch = 2 LOC-equivalent
    )
    
    # How hard to integrate with existing code?
    integration_cost = self._measure_integration_difficulty(change, context)
    
    return implementation_cost + maintenance_cost + integration_cost
```

### Risk Function R(change | context)

```python
def risk_function(change: Change, context: Context) -> float:
    """
    Risk = probability of failure × magnitude of failure
    """
    
    # What's the chance this breaks something?
    failure_probability = self._estimate_failure_rate(change, context.history)
    
    # How bad if it breaks?
    blast_radius = self._measure_blast_radius(change, context.dependencies)
    
    # Can we recover quickly?
    recovery_difficulty = self._measure_recovery_difficulty(change, context)
    
    return failure_probability * blast_radius * recovery_difficulty
```

---

## Deriving Thresholds from Utility

### Auto-Proceed Threshold

**Definition**: Approve automatically if **expected utility is clearly positive**.

```python
def derive_auto_proceed_threshold(self, context: Context) -> float:
    """
    Find the LOC delta where:
    - E[U] > 0 (expected utility positive)
    - Var[U] < user_tolerance (variance low enough)
    - P(failure) < 5% (failure rare)
    """
    
    for loc_delta in range(0, 2000, 50):
        # Simulate utility over historical patterns
        utilities = [
            self.utility_function(self._simulate_change(loc_delta, context))
            for _ in range(100)  # Monte Carlo sampling
        ]
        
        expected_utility = mean(utilities)
        utility_variance = variance(utilities)
        failure_rate = sum(1 for u in utilities if u < 0) / len(utilities)
        
        if expected_utility > 0 and utility_variance < context.policy.risk_tolerance and failure_rate < 0.05:
            continue  # Still safe
        else:
            return loc_delta - 50  # Last safe value
    
    return 2000  # Maximum auto-proceed
```

### Prompt Threshold

**Definition**: Prompt user when **variance is too high to auto-decide**.

```python
def derive_prompt_threshold(self, context: Context) -> float:
    """
    Find the LOC delta where:
    - Utility has high variance (could go either way)
    - User input significantly affects outcome
    - Cost of wrong decision > cost of asking
    """
    
    auto_proceed = self.derive_auto_proceed_threshold(context)
    
    for loc_delta in range(auto_proceed, 5000, 100):
        # Measure utility variance
        utilities = [
            self.utility_function(self._simulate_change(loc_delta, context))
            for _ in range(100)
        ]
        
        # When does asking user add more value than auto-deciding?
        value_of_asking = self._value_of_user_input(utilities, context)
        cost_of_asking = 30  # 30 seconds of user time
        
        if value_of_asking > cost_of_asking:
            return loc_delta
    
    return 3000  # Default prompt threshold
```

### Hard Limit (Rejection Threshold)

**Definition**: Reject when **marginal value approaches zero**.

```python
def derive_hard_limit(self, context: Context) -> float:
    """
    Find the LOC delta where:
    - Marginal value per LOC < threshold (diminishing returns)
    - Risk outweighs value regardless of implementation
    - Better to split into multiple changes
    """
    
    for loc_delta in range(0, 10000, 200):
        # Compute marginal value
        marginal_value = (
            self.value_function(loc_delta + 100, context) - 
            self.value_function(loc_delta, context)
        ) / 100
        
        # When does adding more LOC stop helping?
        if marginal_value < 0.01:  # < 1% value per 100 LOC
            return loc_delta
    
    return 5000  # Conservative default
```

---

## Local Correctness vs Global Utility

**Your Question**: "Is local correctness optimization unified with global value utility functions + goals?"

**Answer**: **Yes, through the 3-tier translation!**

### The Translation Mechanism

```
User Intent (global goal)
    ↓
[GVUFD: Global → Local Translation]
    ↓
Specification (local constraints)
    ↓
[SPK: Local → Cost Translation]
    ↓
Priced Actions (local operations with global cost)
    ↓
[UVUAS: Execute with Local Correctness]
    ↓
Implementation (locally correct code)
    ↓
[Reflexion: Local → Global Verification]
    ↓
Global Utility Realized
```

### Concrete Example

**User Intent** (global):
```
"Add user authentication"
```

**GVUFD Translation** (global → local):
```python
Specification(
    success_criteria=[
        "User can register with email/password",
        "User can login with valid credentials",
        "Invalid credentials return 401",
        "Passwords are hashed"
    ],
    forbidden_patterns=[
        "god_object",           # Global architectural concern
        "plaintext_passwords",  # Global security concern
        "global_state"          # Global design concern
    ],
    budgets={
        "max_loc_delta": 500,   # Derived from U(change | context)
        "max_new_files": 3,
        "max_new_deps": 1
    }
)
```

**SPK Translation** (local → cost):
```python
# Each local action gets global cost
actions = [
    Action("create_file", "auth.py", estimated_loc=200),
    Action("modify_file", "app.py", estimated_loc=50),
    Action("add_dependency", "bcrypt", cost_equivalent=50)
]

total_cost = 200 + 50 + 50 = 300 LOC-equivalent

# Check against derived threshold
if total_cost < thresholds.auto_proceed:
    return Decision.approved()
```

**UVUAS Execution** (local correctness):
```python
# Builder ensures local correctness
def create_auth_module():
    # Write syntactically correct code
    # Pass type checking
    # Pass unit tests
    # ... local properties satisfied
```

**Reflexion Verification** (local → global):
```python
# Did local changes achieve global utility?
def verify_global_utility(change: Change, spec: Specification) -> bool:
    # Check global constraints
    assert not has_forbidden_patterns(change)
    assert within_budget(change)
    assert satisfies_success_criteria(change, spec)
    
    # Compute actual utility
    actual_utility = utility_function(change, context)
    
    # Did we achieve positive utility?
    return actual_utility > 0
```

### The Unification

**Key Insight**: Local correctness is **necessary but not sufficient** for global utility.

```python
def unified_optimization(intent: str, context: Context) -> Change:
    """
    Optimize for global utility while ensuring local correctness.
    """
    
    # 1. GVUFD: Translate global intent → local constraints
    spec = gvufd.generate_specification(intent, context)
    
    # 2. SPK: Ensure local changes have acceptable global cost
    if not spk.within_budget(spec, context):
        alternatives = spk.generate_alternatives(spec, context)
        spec = user.choose(alternatives)
    
    # 3. UVUAS: Execute with local correctness guarantees
    change = uvuas.implement(spec, context)
    
    # Verify: Local correctness
    assert change.passes_tests()
    assert change.is_syntactically_valid()
    assert change.satisfies_spec(spec)
    
    # Verify: Global utility
    actual_utility = utility_function(change, context)
    assert actual_utility > 0
    
    return change  # Both locally correct AND globally beneficial
```

---

## Phase Evolution

### Phase 1 (Current): Hardcoded Baselines

```python
# Simple, fixed thresholds to bootstrap
AUTO_PROCEED = 300
PROMPT = 800
REJECT = 2000
```

**Rationale**: Need initial values to start learning.

---

### Phase 2: Context-Sensitive Thresholds

```python
# Thresholds adapt to project context
thresholds = gvufd.derive_thresholds(context)
# Different for each project!
```

**Improvement**: Scales with project size, adapts to complexity.

---

### Phase 3: Learned Utility Functions

```python
# Learn from actual outcomes
utility_model = learn_from_history(
    past_changes=context.history,
    outcomes=context.outcomes
)

# Derive optimal thresholds from learned utility
thresholds = optimize_thresholds(utility_model, context)
```

**Improvement**: Personalized to team/project patterns.

---

### Phase 4: Meta-Learning & Self-Play

```python
# AUREUS improves its own utility function
for iteration in range(1000):
    # Generate synthetic task
    task = generate_synthetic_task()
    
    # Execute with current utility function
    change = execute(task, utility_function_v1)
    
    # Measure outcome quality
    quality = measure_quality(change)
    
    # Update utility function
    utility_function_v2 = update(utility_function_v1, task, quality)
    
    # Repeat with improved utility function
    utility_function_v1 = utility_function_v2
```

**Improvement**: Continuously optimizes its own optimization function!

---

## The Self-Referential Loop

**AUREUS develops itself using the same principles it applies to user code.**

```python
# When developing AUREUS feature:
def add_feature_to_aureus(feature: str):
    # GVUFD analyzes AUREUS's own codebase
    aureus_context = Context(
        project_path="/aureus/src",
        current_loc=5000,
        policy=aureus_policy  # AUREUS's own policy!
    )
    
    # Derive thresholds for AUREUS development
    thresholds = gvufd.derive_thresholds(aureus_context)
    
    # SPK prices the change to AUREUS
    spec = gvufd.generate_specification(feature, aureus_context)
    cost = spk.calculate_cost(spec, aureus_context)
    
    # Should AUREUS approve this change to itself?
    if cost < thresholds.auto_proceed:
        uvuas.implement(spec, aureus_context)
    elif cost < thresholds.prompt:
        if developer.approves(spec, cost):
            uvuas.implement(spec, aureus_context)
    else:
        print(f"Feature '{feature}' would violate AUREUS's own governance!")
        alternatives = spk.generate_alternatives(spec, aureus_context)
        print(f"Alternatives: {alternatives}")
```

**This is the ultimate dogfooding**: AUREUS can't violate its own principles!

---

## Practical Implementation Timeline

### Phase 1 (MVP - Current)
- ✅ Hardcoded thresholds (300/800/2000 LOC)
- ✅ Fixed LOC-only cost model
- ✅ Simple auto-proceed logic

**Reason**: Need baseline to start learning from.

---

### Phase 2 (Learning - Month 3-6)
- 🔄 Context-sensitive thresholds
- 🔄 Learn cost model weights from data
- 🔄 Adaptive budgets based on project size

**Trigger**: After 1000+ sessions across different projects.

---

### Phase 3 (Optimization - Month 6-12)
- 📅 Full utility function implementation
- 📅 Optimal threshold derivation
- 📅 Personalized per-team/project

**Trigger**: Sufficient data to model utility accurately.

---

### Phase 4 (Meta-Learning - Month 12+)
- 📅 Self-play for utility function improvement
- 📅 AUREUS optimizes its own optimization
- 📅 Continuous self-improvement

**Trigger**: Stable Phase 3 system with robust evaluation metrics.

---

## Summary

### Question 1: Justification for Hardcoded Numbers?

**Answer**: See [design-decisions.md](design-decisions.md) - all values have empirical basis from research and industry data.

**But**: You're right that they're **initial guesses**. They bootstrap the learning process.

---

### Question 2: Can 3-Tier Define Numbers Instead?

**Answer**: **Absolutely yes!** 

The 3-tier system **should** derive its own thresholds from the utility function:

```python
# Instead of:
AUTO_PROCEED = 300  # hardcoded

# Use:
AUTO_PROCEED = gvufd.derive_threshold(
    condition="expected_utility > 0 AND variance < risk_tolerance",
    context=current_context
)  # dynamically derived
```

**Phase 1**: Use hardcoded baselines to bootstrap  
**Phase 2+**: Derive from utility function

---

### Question 3: Local Correctness + Global Utility?

**Answer**: **Yes, they're unified through 3-tier translation:**

```
Global Intent → [GVUFD] → Local Constraints
Local Constraints → [SPK] → Global Cost
Local Implementation → [UVUAS] → Verified Against Global Utility
```

**Local correctness is necessary; global utility is sufficient.**

The system optimizes for global utility **subject to** local correctness constraints.

---

## Key Takeaway

**AUREUS is bootstrapped with hardcoded values but evolves to self-governance:**

1. **Phase 1**: Hardcoded thresholds (pragmatic bootstrap)
2. **Phase 2**: Context-derived thresholds (project-aware)
3. **Phase 3**: Utility-optimized thresholds (team-personalized)
4. **Phase 4**: Meta-learned thresholds (self-improving)

**The 3-tier system is designed to eventually govern itself!**

This is the ultimate expression of the "intelligence-first" philosophy - the system learns its own optimal parameters rather than relying on fixed rules.
