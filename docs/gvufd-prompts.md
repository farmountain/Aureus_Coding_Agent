# GVUFD Prompt Engineering Guide

**Component**: Tier 1 - Global Value Utility Function Designer  
**Purpose**: Transform natural language intent → formal specification  
**Critical Success Factor**: Quality of GVUFD directly determines quality of implementation

---

## Overview

GVUFD is the "intelligence layer" that understands user intent and generates bounded specifications. It must:

1. **Understand ambiguous natural language** ("add auth")
2. **Generate specific success criteria** (what "done" means)
3. **Allocate appropriate budgets** (LOC, files, dependencies)
4. **Identify forbidden patterns** (architectural constraints)
5. **Create acceptance tests** (verification strategy)

**This is the most critical prompt in AUREUS** - everything else depends on spec quality.

---

## System Prompt

```markdown
# GVUFD - Global Value Utility Function Designer

You are the specification generator for AUREUS, an intelligent coding agent with governance.

## Your Role

Transform user intent (natural language) into formal, bounded specifications that guide implementation.

## Input Context

You receive:
- **Intent**: User's natural language request (e.g., "add user authentication")
- **Project Profile**: Language, framework, size, patterns, team size
- **Historical Policy**: Budgets, forbidden patterns, previous specs that worked
- **Current State**: Existing code, dependencies, architecture

## Your Output

Generate a **Specification** with:

1. **Success Criteria** (3-7 items)
   - Concrete, testable conditions
   - Specific enough to verify completion
   - Focus on user-visible outcomes, not implementation details
   
2. **Budget Allocation**
   - max_loc: Maximum lines of code to add/modify
   - max_new_files: Maximum new files to create
   - max_new_dependencies: Maximum new dependencies to add
   - max_new_abstractions: Maximum new classes/interfaces
   
3. **Forbidden Patterns**
   - Architectural anti-patterns to avoid
   - Project-specific constraints from policy
   - Security concerns specific to this task
   
4. **Acceptance Tests**
   - 3-5 concrete test cases
   - Cover success criteria
   - Include edge cases and error conditions
   
5. **Risk Assessment**
   - Risk level: LOW / MEDIUM / HIGH / CRITICAL
   - Potential breaking changes
   - Security implications
   - Complexity factors

## Principles

### Conservative Budgeting
- Start with minimal viable implementation
- Better to underestimate than overestimate
- Users can override if needed

### Specific Success Criteria
- Bad: "Authentication works"
- Good: "Users can register with email/password, login returns JWT, protected routes require valid token"

### Realistic Acceptance Tests
- Match project's existing test style
- Cover happy path and errors
- Don't require excessive test infrastructure

### Risk-Aware
- Large LOC changes = higher risk
- Breaking changes = higher risk
- Security-related = higher risk
- New external services = higher risk

## Budget Heuristics

Use these guidelines (adjust based on project):

**Simple Feature** (helper function, utility):
- LOC: 20-50
- Files: 0-1
- Dependencies: 0
- Abstractions: 0-1
- Risk: LOW

**Medium Feature** (REST endpoint, data model):
- LOC: 100-300
- Files: 1-3
- Dependencies: 0-1
- Abstractions: 1-3
- Risk: MEDIUM

**Complex Feature** (authentication, payment integration):
- LOC: 300-800
- Files: 3-8
- Dependencies: 1-3
- Abstractions: 3-6
- Risk: MEDIUM-HIGH

**Major Refactor** (architecture change, DB migration):
- LOC: 500-2000
- Files: 10+
- Dependencies: variable
- Abstractions: 5+
- Risk: HIGH-CRITICAL

## Few-Shot Examples

See examples section below for complete examples of high-quality specifications.

## Important Notes

- Your spec guides the entire implementation - be precise
- SPK will validate cost - be realistic about budgets
- Agents will follow your success criteria exactly
- Users see your output - use clear language
- Learn from overrides - if users consistently exceed budgets, adjust model

## Output Format

Respond with JSON matching the Specification schema:

```json
{
  "intent": "original user request",
  "success_criteria": ["criterion 1", "criterion 2", ...],
  "budgets": {
    "max_loc": 200,
    "max_new_files": 2,
    "max_new_dependencies": 1,
    "max_new_abstractions": 2
  },
  "forbidden_patterns": [
    {"name": "pattern_name", "reason": "why forbidden"}
  ],
  "acceptance_tests": [
    {"name": "test_name", "description": "what it tests"}
  ],
  "risk_level": "MEDIUM",
  "risk_factors": ["factor 1", "factor 2"],
  "estimated_complexity": 250
}
```
```

---

## Few-Shot Examples

### Example 1: Simple Feature - Add Helper Function

**Input Context**:
```json
{
  "intent": "add a helper function to format timestamps",
  "project_profile": {
    "language": "python",
    "framework": "flask",
    "size": 2341,
    "type": "web_api"
  },
  "policy": {
    "max_loc": 10000,
    "forbidden_patterns": ["global_state", "god_object"]
  }
}
```

**Output Specification**:
```json
{
  "intent": "add a helper function to format timestamps",
  "success_criteria": [
    "Function converts datetime to ISO 8601 string format",
    "Function handles timezone-aware and naive datetimes",
    "Function has docstring with examples",
    "Function has unit tests with edge cases"
  ],
  "budgets": {
    "max_loc": 30,
    "max_new_files": 0,
    "max_new_dependencies": 0,
    "max_new_abstractions": 0
  },
  "forbidden_patterns": [],
  "acceptance_tests": [
    {
      "name": "test_format_timestamp_utc",
      "description": "Formats UTC datetime correctly"
    },
    {
      "name": "test_format_timestamp_with_timezone",
      "description": "Handles timezone-aware datetime"
    },
    {
      "name": "test_format_timestamp_naive",
      "description": "Handles naive datetime (assumes UTC)"
    }
  ],
  "risk_level": "LOW",
  "risk_factors": [],
  "estimated_complexity": 25
}
```

---

### Example 2: Medium Feature - Add User Authentication

**Input Context**:
```json
{
  "intent": "add user authentication",
  "project_profile": {
    "language": "python",
    "framework": "flask",
    "size": 2341,
    "type": "web_api",
    "has_database": true,
    "auth_current": "none"
  },
  "policy": {
    "max_loc": 10000,
    "forbidden_patterns": ["plaintext_passwords", "global_state"]
  }
}
```

**Output Specification**:
```json
{
  "intent": "add user authentication with JWT",
  "success_criteria": [
    "Users can register with email and password",
    "Passwords are hashed using bcrypt",
    "Users can login and receive JWT token",
    "Protected endpoints verify JWT token",
    "Invalid tokens return 401 Unauthorized",
    "Token expiration is configurable"
  ],
  "budgets": {
    "max_loc": 300,
    "max_new_files": 3,
    "max_new_dependencies": 2,
    "max_new_abstractions": 3
  },
  "forbidden_patterns": [
    {
      "name": "plaintext_passwords",
      "reason": "Security requirement - must hash passwords"
    },
    {
      "name": "global_auth_state",
      "reason": "Makes testing difficult, creates coupling"
    }
  ],
  "acceptance_tests": [
    {
      "name": "test_user_registration",
      "description": "User can register with valid email/password"
    },
    {
      "name": "test_user_login",
      "description": "User receives JWT token on successful login"
    },
    {
      "name": "test_protected_endpoint",
      "description": "Endpoint requires valid JWT token"
    },
    {
      "name": "test_invalid_token",
      "description": "Invalid token returns 401"
    },
    {
      "name": "test_expired_token",
      "description": "Expired token returns 401"
    }
  ],
  "risk_level": "MEDIUM",
  "risk_factors": [
    "Security-sensitive (authentication)",
    "Adds new dependency (PyJWT, bcrypt)",
    "Modifies existing endpoints (adds auth decorator)"
  ],
  "estimated_complexity": 280
}
```

---

### Example 3: Complex Feature - Add Caching Layer

**Input Context**:
```json
{
  "intent": "add Redis caching to expensive database queries",
  "project_profile": {
    "language": "python",
    "framework": "flask",
    "size": 5200,
    "type": "web_api",
    "has_database": true,
    "performance_critical": true
  },
  "policy": {
    "max_loc": 15000,
    "forbidden_patterns": ["god_object", "global_state"]
  }
}
```

**Output Specification**:
```json
{
  "intent": "add Redis caching layer for database queries",
  "success_criteria": [
    "Cache decorator wraps expensive query functions",
    "Cache key generation is deterministic from function args",
    "Cache TTL is configurable per query type",
    "Cache invalidation works on data mutation",
    "Cache hit/miss metrics are logged",
    "Graceful degradation when Redis unavailable"
  ],
  "budgets": {
    "max_loc": 400,
    "max_new_files": 4,
    "max_new_dependencies": 2,
    "max_new_abstractions": 4
  },
  "forbidden_patterns": [
    {
      "name": "god_cache_class",
      "reason": "Cache logic should be focused, not handle all concerns"
    },
    {
      "name": "global_redis_connection",
      "reason": "Makes testing difficult, creates hidden dependencies"
    },
    {
      "name": "cache_stampede",
      "reason": "Must handle thundering herd problem"
    }
  ],
  "acceptance_tests": [
    {
      "name": "test_cache_hit",
      "description": "Second call returns cached value, no DB query"
    },
    {
      "name": "test_cache_miss",
      "description": "First call queries DB, stores in cache"
    },
    {
      "name": "test_cache_invalidation",
      "description": "Mutation invalidates related cached queries"
    },
    {
      "name": "test_cache_ttl",
      "description": "Cached value expires after TTL"
    },
    {
      "name": "test_redis_unavailable",
      "description": "System works (slower) when Redis down"
    }
  ],
  "risk_level": "HIGH",
  "risk_factors": [
    "New external service dependency (Redis)",
    "Performance-critical path modification",
    "Cache invalidation complexity (hard problem)",
    "Potential for stale data if invalidation incorrect"
  ],
  "estimated_complexity": 650
}
```

---

### Example 4: High-Risk - Database Migration

**Input Context**:
```json
{
  "intent": "migrate user table to add email verification fields",
  "project_profile": {
    "language": "python",
    "framework": "flask",
    "size": 8500,
    "type": "web_api",
    "has_database": true,
    "in_production": true
  },
  "policy": {
    "max_loc": 20000,
    "forbidden_patterns": ["irreversible_migrations"]
  }
}
```

**Output Specification**:
```json
{
  "intent": "add email verification to user model",
  "success_criteria": [
    "User model has email_verified boolean field",
    "User model has verification_token string field",
    "Database migration is reversible (has down migration)",
    "Existing users default to email_verified=False",
    "Verification email sending endpoint exists",
    "Verification token validation endpoint exists",
    "Migration tested on staging database first"
  ],
  "budgets": {
    "max_loc": 250,
    "max_new_files": 3,
    "max_new_dependencies": 0,
    "max_new_abstractions": 0
  },
  "forbidden_patterns": [
    {
      "name": "irreversible_migration",
      "reason": "Must be able to rollback if issues in production"
    },
    {
      "name": "data_loss_migration",
      "reason": "Existing user data must be preserved"
    }
  ],
  "acceptance_tests": [
    {
      "name": "test_migration_up",
      "description": "Migration adds fields correctly"
    },
    {
      "name": "test_migration_down",
      "description": "Migration reverses cleanly"
    },
    {
      "name": "test_existing_users",
      "description": "Existing users have email_verified=False after migration"
    },
    {
      "name": "test_send_verification_email",
      "description": "Verification email sent with valid token"
    },
    {
      "name": "test_verify_email_token",
      "description": "Valid token sets email_verified=True"
    }
  ],
  "risk_level": "CRITICAL",
  "risk_factors": [
    "Database schema change in production",
    "Affects existing user data",
    "Irreversible if migration has bugs",
    "Requires careful staging testing first"
  ],
  "estimated_complexity": 200,
  "breaking_changes": [
    "User model schema changes (backward compatible for reads)"
  ],
  "deployment_notes": [
    "Run migration on staging first",
    "Backup production database before migration",
    "Plan rollback strategy",
    "Monitor for migration errors"
  ]
}
```

---

## Prompt Engineering Best Practices

### 1. Context Injection Strategy

**Always include in context**:
- Project profile (language, size, type)
- Current policy (budgets, forbidden patterns)
- Recent successful specs (for consistency)
- Current project state (files, dependencies)

**Example Context Assembly**:
```python
context = f"""
Project: {profile.name} ({profile.language} {profile.type})
Size: {profile.current_loc} LOC, {profile.current_files} files
Budgets: {policy.budgets.max_loc} LOC remaining
Forbidden: {', '.join(policy.forbidden_patterns)}

Recent Successful Specs:
{format_recent_specs(memory.successful_specs[-3:])}

Current Intent: {user_intent}
"""
```

### 2. Budget Calibration

**Learn from overrides**:
```python
def adjust_budget_model(self, history: list[Spec]):
    """Learn from user overrides."""
    
    overrides = [s for s in history if s.was_overridden]
    
    if len(overrides) > 5:
        # Calculate adjustment factor
        avg_actual = mean([s.actual_loc for s in overrides])
        avg_estimated = mean([s.estimated_loc for s in overrides])
        
        adjustment = avg_actual / avg_estimated
        
        # Update budget multiplier
        self.budget_multiplier *= adjustment
```

### 3. Risk Assessment Triggers

**Automatic risk elevation**:
```python
def assess_risk(self, spec: Specification, profile: Profile) -> RiskLevel:
    """Compute risk level from spec characteristics."""
    
    risk_score = 0
    
    # Size-based risk
    if spec.budgets.max_loc > profile.current_loc * 0.2:
        risk_score += 1  # Changes >20% of codebase
    
    # Breaking changes
    if spec.has_breaking_changes():
        risk_score += 2
    
    # Security-related
    if any(word in spec.intent.lower() for word in ['auth', 'password', 'security', 'payment']):
        risk_score += 1
    
    # Database changes
    if 'migration' in spec.intent.lower() or 'schema' in spec.intent.lower():
        risk_score += 2
    
    # New dependencies
    if spec.budgets.max_new_dependencies > 2:
        risk_score += 1
    
    # Map to risk level
    if risk_score >= 4:
        return RiskLevel.CRITICAL
    elif risk_score >= 3:
        return RiskLevel.HIGH
    elif risk_score >= 1:
        return RiskLevel.MEDIUM
    else:
        return RiskLevel.LOW
```

### 4. Success Criteria Quality Check

**Validate generated criteria**:
```python
def validate_success_criteria(self, criteria: list[str]) -> bool:
    """Check if success criteria are specific enough."""
    
    # Must have 3-7 criteria
    if not (3 <= len(criteria) <= 7):
        return False
    
    # No vague criteria
    vague_words = ['works', 'correct', 'good', 'better', 'improved']
    if any(any(word in c.lower() for word in vague_words) for c in criteria):
        return False
    
    # Must be testable
    if not all(self.is_testable(c) for c in criteria):
        return False
    
    return True

def is_testable(self, criterion: str) -> bool:
    """Can this criterion be verified?"""
    
    # Good: "Users can login and receive JWT token"
    # Bad: "Authentication is secure"
    
    testable_patterns = [
        r'can \w+',  # "can login"
        r'returns? \w+',  # "returns 200"
        r'has \w+',  # "has validation"
        r'\w+ is \w+ed',  # "password is hashed"
    ]
    
    return any(re.search(pattern, criterion.lower()) for pattern in testable_patterns)
```

---

## Adaptive Learning

### Observing Outcomes

```python
class GVUFDLearner:
    """Learns from spec outcomes."""
    
    def observe_outcome(self, spec: Specification, result: Result):
        """Record estimated vs actual."""
        
        self.history.append({
            'spec': spec,
            'estimated_loc': spec.budgets.max_loc,
            'actual_loc': result.actual_loc,
            'estimated_complexity': spec.estimated_complexity,
            'actual_issues': len(result.issues),
            'user_override': result.was_overridden,
            'success': result.success
        })
    
    def refine_model(self):
        """Update budget estimation model."""
        
        if len(self.history) < 10:
            return  # Need more data
        
        # Which types of tasks are consistently underestimated?
        underestimated = [
            h for h in self.history 
            if h['actual_loc'] > h['estimated_loc'] * 1.5
        ]
        
        if len(underestimated) > len(self.history) * 0.3:
            # More than 30% underestimated - adjust up
            self.budget_multiplier *= 1.2
            logger.info("Adjusted budget multiplier up to {self.budget_multiplier}")
        
        # Which success criteria are frequently missed?
        failed_criteria = []
        for h in self.history:
            if not h['success']:
                # Extract what went wrong
                failed_criteria.extend(h['spec'].success_criteria)
        
        # Suggest improving these in future specs
        self.problematic_criteria = Counter(failed_criteria).most_common(5)
```

---

## Error Handling

### When GVUFD Fails

```python
class GVUFDError(AUREUSError):
    """GVUFD could not generate valid spec."""
    pass

# Handle gracefully
try:
    spec = gvufd.generate_specification(intent, context)
except GVUFDError as e:
    return Result.abandoned(
        reason="Could not understand request",
        details=str(e),
        suggestions=[
            "Rephrase more specifically (e.g., 'add REST endpoint for users' instead of 'add API')",
            "Break into smaller tasks",
            "Provide more context about what you want"
        ]
    )
```

---

## Testing GVUFD

### Unit Tests

```python
def test_gvufd_simple_feature():
    """GVUFD generates reasonable spec for simple feature."""
    
    gvufd = GVUFD()
    spec = gvufd.generate_specification(
        intent="add helper function to format timestamps",
        context=test_context
    )
    
    assert len(spec.success_criteria) >= 3
    assert spec.budgets.max_loc < 100
    assert spec.risk_level == RiskLevel.LOW

def test_gvufd_complex_feature():
    """GVUFD allocates larger budget for complex feature."""
    
    gvufd = GVUFD()
    spec = gvufd.generate_specification(
        intent="add user authentication with JWT",
        context=test_context
    )
    
    assert len(spec.success_criteria) >= 5
    assert 200 <= spec.budgets.max_loc <= 500
    assert spec.risk_level in [RiskLevel.MEDIUM, RiskLevel.HIGH]
    assert spec.budgets.max_new_dependencies >= 1

def test_gvufd_learns_from_overrides():
    """GVUFD adjusts budgets based on user overrides."""
    
    gvufd = GVUFD()
    
    # Simulate 10 overrides where user needed 2x estimated LOC
    for _ in range(10):
        spec = gvufd.generate_specification("add feature", test_context)
        gvufd.observe_outcome(spec, Result(actual_loc=spec.budgets.max_loc * 2))
    
    gvufd.refine_model()
    
    # New specs should have higher budgets
    new_spec = gvufd.generate_specification("add feature", test_context)
    assert new_spec.budgets.max_loc > spec.budgets.max_loc
```

---

## Conclusion

GVUFD prompt engineering is **the most critical component** of AUREUS quality. Follow these principles:

1. ✅ **Conservative budgets** - start small, user can override
2. ✅ **Specific criteria** - testable, concrete outcomes
3. ✅ **Risk-aware** - escalate appropriately
4. ✅ **Adaptive learning** - improve from outcomes
5. ✅ **Few-shot examples** - consistent quality

**Quality of specs determines quality of implementations.**
