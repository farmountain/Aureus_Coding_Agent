# AUREUS Termination Conditions & Circuit Breakers

## Critical Question: How Does AUREUS Know When to Stop?

**Problem**: Without clear termination conditions, the system could loop indefinitely:
- GVUFD generates spec → SPK rejects → GVUFD tries alternatives → SPK rejects → ∞
- Builder implements → Critic finds issues → Reflexion simplifies → Critic still unhappy → ∞
- User rejects → System tries alternatives → User rejects again → ∞

**Solution**: Multiple layers of circuit breakers and clear "done" conditions.

---

## 🛑 Termination Conditions by Component

### 1. GVUFD (Specification Generation)

#### Success Condition
```python
def is_spec_complete(spec: Specification) -> bool:
    """When is a specification "done"?"""
    return (
        len(spec.success_criteria) > 0 and
        spec.budgets.max_loc > 0 and
        len(spec.acceptance_tests) > 0 and
        spec.risk_level is not None
    )
```

#### Failure Conditions (Abandon)
```python
class GVUFD:
    MAX_SPEC_ATTEMPTS = 3  # Try at most 3 times to generate valid spec
    
    def generate_specification(self, intent: str, context: Context) -> Specification:
        """Generate spec with circuit breaker."""
        
        for attempt in range(self.MAX_SPEC_ATTEMPTS):
            spec = self._llm_generate_spec(intent, context)
            
            if self.is_spec_complete(spec):
                return spec  # ✅ SUCCESS
            
            # Retry with more explicit instructions
            context.add_constraint(f"Previous attempt {attempt+1} was incomplete")
        
        # After 3 attempts, give up
        raise GVUFDError(
            "Cannot generate valid specification",
            reason="Intent too ambiguous or context insufficient",
            suggestion="Rephrase your request more specifically"
        )  # ❌ ABANDON
```

---

### 2. SPK (Cost Approval)

#### Success Condition
```python
def should_approve(self, cost: Cost, policy: Policy) -> Decision:
    """Clear approval decision."""
    
    if cost.total < policy.auto_proceed_threshold:
        return Decision.approved()  # ✅ AUTO-APPROVE
    
    if cost.total > policy.rejection_threshold:
        return Decision.rejected()  # ❌ AUTO-REJECT
    
    return Decision.prompt_user()  # ⚠️ ASK USER
```

#### Circuit Breaker: Alternative Generation
```python
class SPK:
    MAX_ALTERNATIVES = 3  # Only suggest up to 3 alternatives
    
    def generate_alternatives(self, spec: Specification) -> list[Alternative]:
        """Don't loop forever trying to find cheaper alternatives."""
        
        alternatives = []
        
        # Strategy 1: Reduce scope
        alt1 = self.reduce_scope(spec)
        if self.calculate_cost(alt1) < self.rejection_threshold:
            alternatives.append(alt1)
        
        # Strategy 2: Split into phases
        alt2 = self.split_into_phases(spec)
        alternatives.append(alt2)  # Always valid (smaller phases)
        
        # Strategy 3: Simpler implementation
        alt3 = self.simplify_approach(spec)
        if self.calculate_cost(alt3) < self.rejection_threshold:
            alternatives.append(alt3)
        
        # Stop at 3 - don't generate endless alternatives
        return alternatives[:self.MAX_ALTERNATIVES]  # ✅ BOUNDED
```

#### Abandonment After User Rejection
```python
def handle_user_rejection(self, spec: Specification, alternatives: list[Alternative]) -> Result:
    """What if user rejects everything?"""
    
    if user.rejects_all(alternatives):
        return Result.abandoned(
            reason="No acceptable alternative found",
            suggestion="Try breaking into smaller tasks",
            next_steps=[
                "Rephrase request more specifically",
                "Increase budget with: aureus policy edit",
                "Split into multiple sessions"
            ]
        )  # ✅ GRACEFUL ABANDONMENT
```

---

### 3. UVUAS (Agent Swarm Execution)

#### The Critical Loop: Build → Test → Review → Simplify

**Risk**: Critic could keep finding issues forever.

```python
class UVUAS:
    MAX_REFINEMENT_ITERATIONS = 3  # At most 3 rounds of fixes
    
    def implement(self, spec: Specification, budget: Budget, context: Context) -> Result:
        """Execute with iteration limit."""
        
        # Stage 1: Plan (no loop)
        plan = self.planner.create_plan(spec, context)
        
        # Stage 2: Build (no loop)
        changes = self.builder.implement_plan(plan, context)
        
        # Stage 3-5: Test → Review → Simplify (LOOP RISK HERE)
        for iteration in range(self.MAX_REFINEMENT_ITERATIONS):
            
            # Test
            test_results = self.tester.verify(changes, spec)
            if not test_results.passed:
                # Fix failing tests
                changes = self.builder.fix_test_failures(changes, test_results)
                continue  # Try again
            
            # Review
            issues = self.critic.review(changes, spec, context)
            
            if not issues.critical:
                # Only minor issues - good enough!
                break  # ✅ SUCCESS
            
            # Simplify
            changes = self.reflexion.fix_issues(changes, issues, context)
        
        # After 3 iterations, accept current state
        if iteration >= self.MAX_REFINEMENT_ITERATIONS - 1:
            # Log warning but don't fail
            logger.warning(f"Stopped after {iteration+1} refinement iterations")
            # Still return result - best effort
        
        return Result(changes=changes, iterations=iteration+1)
```

#### Individual Agent Circuit Breakers

**Planner Agent**:
```python
class PlannerAgent:
    MAX_PLANNING_TIME = 30  # seconds
    MAX_TASKS_IN_PLAN = 20  # Don't create 100-step plans
    
    def create_plan(self, spec: Specification, context: Context) -> Plan:
        """Plan with time and complexity limits."""
        
        with timeout(self.MAX_PLANNING_TIME):
            plan = self._llm_generate_plan(spec, context)
        
        if len(plan.tasks) > self.MAX_TASKS_IN_PLAN:
            raise PlanningError(
                "Plan too complex",
                suggestion="Break into multiple sessions"
            )  # ❌ REJECT OVERLY COMPLEX PLANS
        
        return plan
```

**Critic Agent**:
```python
class CriticAgent:
    MAX_ISSUES_TO_REPORT = 10  # Don't report 100 issues
    CRITICAL_ONLY_AFTER_ITERATION_2 = True
    
    def review(self, changes: Changes, spec: Specification, context: Context, iteration: int) -> Issues:
        """Become less strict in later iterations."""
        
        all_issues = self._find_all_issues(changes, spec)
        
        # First iteration: Report everything
        if iteration == 0:
            return all_issues[:self.MAX_ISSUES_TO_REPORT]
        
        # Later iterations: Only critical issues
        if iteration >= 2:
            critical_only = [i for i in all_issues if i.severity == "critical"]
            return critical_only[:self.MAX_ISSUES_TO_REPORT]
        
        # Otherwise: Prioritize by severity
        sorted_issues = sorted(all_issues, key=lambda i: i.severity)
        return sorted_issues[:self.MAX_ISSUES_TO_REPORT]
```

**Reflexion Agent**:
```python
class ReflexionAgent:
    MAX_SIMPLIFICATION_PASSES = 2  # Don't simplify forever
    MIN_LOC_THRESHOLD = 10  # Don't bother simplifying tiny changes
    
    def simplify(self, changes: Changes, issues: Issues, context: Context) -> Changes:
        """Simplify with bounded effort."""
        
        if changes.total_loc < self.MIN_LOC_THRESHOLD:
            return changes  # Too small to bother
        
        simplified = changes
        for pass_num in range(self.MAX_SIMPLIFICATION_PASSES):
            
            new_simplified = self._apply_simplifications(simplified, issues)
            
            # Convergence check: Did we actually improve?
            if new_simplified.total_loc >= simplified.total_loc * 0.95:
                # Less than 5% improvement - diminishing returns
                break  # ✅ CONVERGED
            
            simplified = new_simplified
        
        return simplified
```

---

### 4. Overall Session Limits

#### Global Circuit Breakers

```python
class Session:
    MAX_SESSION_DURATION = 60 * 60  # 1 hour hard limit
    MAX_LLM_CALLS = 100  # Reasonable for complex tasks
    MAX_COST = None  # User-configurable (no hard default)
    MAX_TOKENS = 1_000_000  # 1M tokens (Claude Sonnet context window)
    
    def execute(self, intent: str) -> Result:
        """Execute with global limits."""
        
        start_time = time.time()
        
        with self.track_limits():
            
            # Check limits before every major step
            self._check_limits(start_time)
            
            # ... normal execution ...
            
            result = self.orchestrator.execute(intent, self.context)
            
            return result
    
    def _check_limits(self, start_time: float):
        """Enforce global circuit breakers."""
        
        # Time limit
        if time.time() - start_time > self.MAX_SESSION_DURATION:
            raise SessionTimeout(
                "Session exceeded 1 hour limit",
                suggestion="Break into smaller tasks or continue in new session"
            )
        
        # LLM call limit
        if self.llm_call_count > self.MAX_LLM_CALLS:
            raise SessionExhausted(
                f"Too many LLM calls (>{self.MAX_LLM_CALLS})",
                suggestion="Task may be too complex - consider splitting"
            )
        
        # Cost limit (if user configured)
        if self.MAX_COST and self.total_cost > self.MAX_COST:
            raise BudgetExhausted(
                f"Session cost exceeded ${self.MAX_COST}",
                suggestion="Increase budget in policy.yaml or simplify task"
            )
        
        # Token limit
        if self.total_tokens > self.MAX_TOKENS:
            raise TokenLimitExceeded(
                f"Context size too large (>{self.MAX_TOKENS:,} tokens)",
                suggestion="Reduce scope or enable aggressive pruning"
            )
```

---

## ✅ Success Conditions (When to Stop and Succeed)

### Specification Phase
```python
def is_spec_phase_complete(self, spec: Specification) -> bool:
    """GVUFD is done when spec is valid."""
    return (
        spec is not None and
        spec.is_valid() and
        spec.has_success_criteria()
    )
```

### Pricing Phase
```python
def is_pricing_phase_complete(self, decision: Decision) -> bool:
    """SPK is done when decision is made."""
    return decision in [Decision.APPROVED, Decision.REJECTED, Decision.USER_DECIDED]
```

### Implementation Phase
```python
def is_implementation_complete(self, result: Result, spec: Specification) -> bool:
    """Implementation is done when all success criteria met."""
    return (
        all(result.meets_criterion(c) for c in spec.success_criteria) and
        result.tests_passed and
        not result.has_critical_issues() and
        result.within_budget()
    )
```

### Overall Session
```python
def is_session_complete(self, session: Session) -> bool:
    """Session is done when intent is fulfilled or abandoned."""
    return (
        session.result.success or           # ✅ Success
        session.result.abandoned or         # ❌ Abandoned gracefully
        session.result.user_cancelled or    # 🛑 User stopped it
        session.exceeded_limits()           # ⏱️ Hit circuit breaker
    )
```

---

## 🔄 Circular Dependency Prevention

### Problem: GVUFD → SPK → GVUFD Loop

```python
# BAD: Infinite loop possible
while True:
    spec = gvufd.generate(intent)
    decision = spk.evaluate(spec)
    if decision.rejected:
        intent = decision.alternative  # Might loop forever
```

**Solution**: Bounded retries with degradation

```python
# GOOD: Bounded with escape hatch
MAX_SPEC_REFINEMENTS = 2

for attempt in range(MAX_SPEC_REFINEMENTS):
    spec = gvufd.generate(intent, attempt=attempt)
    decision = spk.evaluate(spec)
    
    if decision.approved:
        break  # ✅ Success
    
    if decision.rejected and attempt < MAX_SPEC_REFINEMENTS - 1:
        # Try simpler alternative
        intent = decision.suggest_simpler()
    else:
        # After 2 attempts, give up
        return Result.abandoned(
            reason="Cannot find acceptable approach",
            tried=[spec.summary() for spec in attempted_specs]
        )  # ❌ Graceful abandonment
```

---

## 📊 Convergence Metrics

### How to Detect "Stuck" State

```python
class ConvergenceDetector:
    """Detect when system is making no progress."""
    
    def is_stuck(self, history: list[Iteration]) -> bool:
        """Are we stuck in a loop?"""
        
        if len(history) < 3:
            return False
        
        last_3 = history[-3:]
        
        # Same issue appearing repeatedly?
        issues = [it.issues for it in last_3]
        if issues[0] == issues[1] == issues[2]:
            return True  # 🔄 STUCK - same problem 3x
        
        # No improvement in LOC?
        locs = [it.changes.total_loc for it in last_3]
        if max(locs) - min(locs) < 10:
            return True  # 🔄 STUCK - no progress
        
        # Same cost estimation?
        costs = [it.estimated_cost for it in last_3]
        if len(set(costs)) == 1:
            return True  # 🔄 STUCK - not exploring alternatives
        
        return False
    
    def handle_stuck_state(self, session: Session) -> Result:
        """What to do when stuck?"""
        
        return Result.abandoned(
            reason="System is not making progress",
            suggestion="Try one of:\n"
                      "  • Rephrase request more specifically\n"
                      "  • Break into smaller subtasks\n"
                      "  • Adjust policy constraints\n"
                      "  • Manual intervention required",
            last_state=session.get_checkpoint()
        )
```

---

## 🎯 Summary: The Complete Halting Strategy

### 1. **Bounded Loops Everywhere**
- GVUFD: Max 3 spec attempts
- SPK: Max 3 alternatives
- UVUAS: Max 3 refinement iterations
- Reflexion: Max 2 simplification passes

### 2. **Global Circuit Breakers**
- 30-minute session timeout
- 50 LLM call limit
- $10 cost limit
- 500k token limit

### 3. **Convergence Detection**
- Same issue 3 times in a row → STUCK
- No improvement in LOC → STUCK
- Same cost repeatedly → STUCK

### 4. **Graceful Abandonment**
- Always provide reason
- Always suggest next steps
- Always save progress (checkpoint)
- Never infinite loop

### 5. **Progressive Strictness Decay**
- Iteration 0: Report all issues
- Iteration 1: Report significant issues
- Iteration 2+: Only critical issues
- After max iterations: Accept best effort

---

## 🔧 Implementation

### Add to `src/harness/orchestrator.py`

```python
class Orchestrator:
    """Main orchestrator with termination guarantees."""
    
    # Global limits
    MAX_SESSION_DURATION = 30 * 60  # 30 minutes
    MAX_LLM_CALLS = 50
    MAX_COST = 10.0
    MAX_TOKENS = 500_000
    
    # Component limits
    MAX_SPEC_ATTEMPTS = 3
    MAX_ALTERNATIVES = 3
    MAX_REFINEMENT_ITERATIONS = 3
    
    def execute(self, intent: str, context: Context) -> Result:
        """Execute with guaranteed termination."""
        
        session_start = time.time()
        
        try:
            # Phase 1: Specification (bounded)
            spec = self._generate_spec_bounded(intent, context)
            
            # Phase 2: Pricing (bounded)
            decision = self._evaluate_cost_bounded(spec, context)
            
            if decision.rejected:
                return Result.rejected(decision)
            
            # Phase 3: Implementation (bounded)
            result = self._implement_bounded(spec, decision.budget, context)
            
            return result
            
        except SessionTimeout:
            return self._handle_timeout(context)
        except SessionExhausted:
            return self._handle_exhaustion(context)
        except StuckState:
            return self._handle_stuck(context)
    
    def _check_limits(self, session_start: float):
        """Enforce global circuit breakers."""
        
        elapsed = time.time() - session_start
        
        if elapsed > self.MAX_SESSION_DURATION:
            raise SessionTimeout()
        
        if self.metrics.llm_calls > self.MAX_LLM_CALLS:
            raise SessionExhausted("Too many LLM calls")
        
        if self.metrics.total_cost > self.MAX_COST:
            raise SessionExhausted("Cost limit exceeded")
        
        if self.metrics.total_tokens > self.MAX_TOKENS:
            raise SessionExhausted("Token limit exceeded")
```

---

## ✅ Verification

### Test Cases for Termination

```python
def test_gvufd_terminates_after_max_attempts():
    """GVUFD gives up after 3 failed spec generations."""
    
    gvufd = GVUFD(max_attempts=3)
    
    with pytest.raises(GVUFDError):
        # Ambiguous intent that can't be spec'd
        gvufd.generate("do something undefined")
    
    assert gvufd.attempt_count == 3  # ✅ Tried exactly 3 times

def test_uvuas_terminates_after_max_iterations():
    """UVUAS stops refining after 3 iterations."""
    
    uvuas = UVUAS(max_iterations=3)
    
    # Implement something that Critic will never be happy with
    result = uvuas.implement(impossible_spec, budget, context)
    
    assert result.iterations == 3  # ✅ Stopped at limit
    assert not result.perfect  # ⚠️ Not perfect but returned anyway

def test_session_terminates_on_timeout():
    """Session stops after 30 minutes."""
    
    orchestrator = Orchestrator(max_duration=1)  # 1 second for test
    
    with pytest.raises(SessionTimeout):
        orchestrator.execute("very complex task", context)
    
    assert orchestrator.elapsed_time >= 1.0  # ✅ Hit timeout

def test_convergence_detector_identifies_stuck_state():
    """System detects when stuck in loop."""
    
    detector = ConvergenceDetector()
    
    # Simulate same issue 3 times
    history = [
        Iteration(issues=["god_object"], loc=100),
        Iteration(issues=["god_object"], loc=100),
        Iteration(issues=["god_object"], loc=100),
    ]
    
    assert detector.is_stuck(history)  # ✅ Detected stuck state
```

---

## 🎓 Conclusion

**The utility function ALWAYS terminates** because:

1. ✅ **Every loop is bounded** (max iterations specified)
2. ✅ **Global timeouts exist** (30 min session limit)
3. ✅ **Convergence is detected** (stuck state monitoring)
4. ✅ **Graceful abandonment** (accept best effort, explain why)
5. ✅ **Progressive decay** (become less strict over iterations)

**No infinite loops possible.**

The system either:
- ✅ **Succeeds** (meets all criteria)
- ⚠️ **Succeeds with warnings** (meets most criteria, best effort)
- ❌ **Abandons gracefully** (explains why, suggests alternatives, saves checkpoint)
- ⏱️ **Times out** (hits circuit breaker, saves progress)

**This is a production-ready halting strategy.**
