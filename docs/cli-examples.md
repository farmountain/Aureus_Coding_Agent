# AUREUS CLI Command Examples

**Comprehensive workflows showing the semantic compilation lifecycle**

---

## Basic Commands

### Initialize Project
```bash
# Auto-detect project and generate governance policy
aureus init

# Output:
# 🔍 Analyzing project...
# 📊 Detected: Python Flask API (2,341 LOC, 6 modules, 8 dependencies)
# 
# Generated governance policy:
#   - LOC budget: 10,000 (4.2x current size)
#   - Auto-proceed: < 250 LOC
#   - Prompt user: 250-600 LOC
#   - Module limit: 8
#   - Dependency limit: 12
# 
# ✅ Policy saved: .aureus/policy.yaml
# ⏱️  Initialization: 8.2 seconds
```

### Execute Coding Task
```bash
# Simple feature
aureus code "add a hello world function"

# Complex feature with context
aureus code "add user authentication with bcrypt"

# With explicit budget
aureus code "refactor auth module" --budget 300
```

---

## Detailed Workflow Examples

### Example 1: Simple Function Addition

**Command**:
```bash
aureus code "add a function to calculate fibonacci numbers"
```

**Full Output**:
```
🔍 Phase 1: Context Loading (0.5s)
├─ Loaded policy: .aureus/policy.yaml
├─ Loaded history: 12 previous sessions
├─ Working set: 8 files (auth.py, app.py, utils.py, ...)
└─ Current state: 2,341 LOC, 6 modules, 8 deps

📋 Phase 2: Semantic Parsing (GVUFD) (2.1s)
├─ Intent: "add a function to calculate fibonacci numbers"
├─ Detected context: utils.py (math helpers module)
└─ Generated specification:
    {
      "success_criteria": [
        "Function fib(n) returns nth Fibonacci number",
        "Handles n=0 and n=1 base cases",
        "Uses efficient iterative approach"
      ],
      "forbidden_patterns": [],
      "budgets": {
        "max_loc_delta": 20,
        "max_new_files": 0,
        "max_new_deps": 0
      },
      "acceptance_tests": [
        "fib(0) == 0",
        "fib(1) == 1",
        "fib(10) == 55"
      ],
      "risk_level": "low"
    }

⚖️  Phase 3: Cost Analysis (SPK) (0.3s)
├─ Estimated cost: 15 LOC
├─ Budget remaining: 7,659 LOC
├─ Threshold: Auto-proceed (< 250 LOC)
└─ Decision: ✅ APPROVED (no user prompt needed)

📝 Phase 4: IR Generation (0.8s)
└─ Plan:
    1. Modify file: src/utils.py (+15 LOC)
       - Add fib() function
       - Add docstring
       - Add type hints

🔨 Phase 5: Code Generation (UVUAS) (3.2s)
├─ Executing plan...
├─ Modified: src/utils.py
│   @@ -45,6 +45,20 @@
│   +def fib(n: int) -> int:
│   +    """Calculate the nth Fibonacci number using iterative approach.
│   +    
│   +    Args:
│   +        n: The position in Fibonacci sequence (0-indexed)
│   +    
│   +    Returns:
│   +        The nth Fibonacci number
│   +    """
│   +    if n <= 1:
│   +        return n
│   +    a, b = 0, 1
│   +    for _ in range(2, n + 1):
│   +        a, b = b, a + b
│   +    return b
│   +
└─ Changes: +15 LOC, 0 files added, 0 deps added

✅ Phase 6: Verification (1.5s)
├─ Running acceptance tests...
│   ✓ fib(0) == 0
│   ✓ fib(1) == 1
│   ✓ fib(10) == 55
├─ Type checking: PASS
├─ Linting: PASS
└─ All tests: PASS

🎯 Phase 7: Peephole Optimization (Reflexion) (0.4s)
├─ Analyzing for simplifications...
└─ No simplifications needed (code already optimal)

💾 Phase 8: Memory Persistence (0.2s)
├─ Updated: .aureus/history.jsonl
├─ Actual cost: 15 LOC (estimated: 15 LOC) ✓
└─ Session logged

✅ Compilation successful!
   Duration: 8.9 seconds
   Cost: 15 LOC
   Files modified: 1
   Tests passed: 3/3
```

---

### Example 2: Feature with User Approval

**Command**:
```bash
aureus code "add user authentication with bcrypt and JWT tokens"
```

**Output**:
```
🔍 Phase 1: Context Loading (0.6s)
└─ Current state: 2,341 LOC, 6 modules, 8 deps

📋 Phase 2: Semantic Parsing (GVUFD) (4.2s)
└─ Generated specification:
    {
      "success_criteria": [
        "User can register with email/password",
        "User can login with valid credentials",
        "JWT tokens issued on successful login",
        "Passwords hashed with bcrypt (cost=12)"
      ],
      "forbidden_patterns": [
        "plaintext_passwords",
        "global_state",
        "god_object"
      ],
      "budgets": {
        "max_loc_delta": 450,
        "max_new_files": 3,
        "max_new_deps": 2
      },
      "risk_level": "medium"
    }

⚖️  Phase 3: Cost Analysis (SPK) (1.1s)
├─ Estimated cost: 420 LOC
├─ Budget remaining: 7,659 LOC
├─ Threshold: Prompt user (250-600 LOC range)
│
└─ ⚠️  USER APPROVAL REQUIRED

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Implementation Plan Summary

Estimated Impact:
  - LOC delta: 420 lines
  - New files: 3 (auth.py, auth_middleware.py, test_auth.py)
  - New dependencies: 2 (bcrypt, PyJWT)
  - Security risk: Medium (auth/password handling)

Changes:
  1. Create src/auth.py (200 LOC)
     - User model with password hashing
     - Registration and login functions
     - JWT token generation/validation
  
  2. Create src/auth_middleware.py (80 LOC)
     - Decorator for protected routes
     - Token validation middleware
  
  3. Create tests/test_auth.py (100 LOC)
     - Registration tests
     - Login tests (valid/invalid)
     - Token tests
  
  4. Modify src/app.py (40 LOC)
     - Import auth routes
     - Configure JWT secret
     - Add protected route example

Budget Status:
  - Current: 2,341 LOC
  - After change: 2,761 LOC (+420)
  - Remaining budget: 7,239 LOC
  - Utilization: 27.6% of 10,000 LOC limit

Proceed with implementation? [y/n/alternatives]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**User chooses 'y'**:
```
✅ User approved. Continuing compilation...

🔨 Phase 5: Code Generation (7.8s)
├─ Installing dependencies...
│   pip install bcrypt PyJWT
├─ Creating src/auth.py... DONE
├─ Creating src/auth_middleware.py... DONE
├─ Creating tests/test_auth.py... DONE
├─ Modifying src/app.py... DONE
└─ Changes: +420 LOC, 3 files added, 2 deps added

✅ Phase 6: Verification (3.2s)
├─ Running tests...
│   ✓ test_user_registration
│   ✓ test_user_login_valid
│   ✓ test_user_login_invalid
│   ✓ test_token_generation
│   ✓ test_token_validation
│   ✓ test_protected_route
└─ All 6 tests PASS

🎯 Phase 7: Peephole Optimization (1.2s)
├─ Analyzing auth.py...
│   Found: Duplicate password validation logic
│   Refactored: Created _validate_password() helper
│   Saved: -12 LOC
└─ Final cost: 408 LOC (optimized from 420)

✅ Compilation successful!
   Duration: 18.3 seconds
   Actual cost: 408 LOC (estimated: 420 LOC, 2.9% under)
```

---

### Example 3: Over-Budget Rejection

**Command**:
```bash
aureus code "add complete GraphQL API with subscriptions, federation, and caching"
```

**Output**:
```
🔍 Phase 1: Context Loading (0.5s)
📋 Phase 2: Semantic Parsing (GVUFD) (3.8s)
⚖️  Phase 3: Cost Analysis (SPK) (1.4s)

❌ REJECTED: Budget exceeded

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️  Implementation Cost Too High

Estimated cost: 1,840 LOC
Rejection threshold: > 600 LOC

Why rejected:
  - GraphQL federation requires significant infrastructure (800+ LOC)
  - Subscription system requires WebSocket handling (400+ LOC)
  - Caching layer adds complexity (300+ LOC)
  - Total exceeds single-session budget

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 Suggested Alternatives:

Option 1: Split into phases (recommended)
  Phase 1: Basic GraphQL API (450 LOC)
    aureus code "add basic GraphQL API with queries and mutations"
  
  Phase 2: Add subscriptions (300 LOC)
    aureus code "add GraphQL subscriptions with WebSockets"
  
  Phase 3: Add federation (400 LOC)
    aureus code "add GraphQL federation support"

Option 2: Simpler implementation (850 LOC)
  - Basic GraphQL without federation
  - Simple in-memory caching
  - No subscriptions
    aureus code "add basic GraphQL API with in-memory caching"

Option 3: Increase budget
    aureus policy edit --budget 15000

Choose option [1/2/3/cancel]: 
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Policy Management

### View Current Policy
```bash
aureus policy show

# Output:
# Current Governance Policy
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Project: Flask API
# Version: 1.2.3
# 
# Budgets:
#   Total LOC: 10,000 (current: 2,341, 23.4% used)
#   Modules: 8 (current: 6)
#   Dependencies: 12 (current: 8)
# 
# Thresholds:
#   Auto-proceed: < 250 LOC
#   Prompt user: 250-600 LOC
#   Reject: > 600 LOC
# 
# Forbidden Patterns:
#   - god_object (classes > 500 LOC)
#   - global_state
#   - circular_dependencies
# 
# Permission Tiers:
#   file_read: Tier 0 (always allowed)
#   file_write: Tier 1 (approved once per session)
#   shell_exec: Tier 2 (prompt each time)
#   web_fetch: Tier 3 (disabled)
```

### Edit Policy
```bash
# Interactive editor
aureus policy edit

# Direct modification
aureus policy set budget.max_loc 15000
aureus policy set thresholds.auto_proceed 300
aureus policy add-pattern "no_nested_loops_3_levels"
```

### Reset Policy
```bash
# Regenerate from current project state
aureus policy regenerate

# Restore defaults
aureus policy reset
```

---

## History & Learning

### View Session History
```bash
aureus history

# Output:
# Recent Sessions
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# [12] 2026-02-27 14:32  add fibonacci function
#      Cost: 15 LOC (estimated: 15)  ✓ Success
# 
# [11] 2026-02-27 12:15  add authentication
#      Cost: 408 LOC (estimated: 420)  ✓ Success
# 
# [10] 2026-02-26 16:45  refactor user model
#      Cost: -35 LOC (simplified)  ✓ Success
# 
# [9] 2026-02-26 10:23  add GraphQL API
#     ❌ Rejected (budget exceeded)
```

### Detailed Session View
```bash
aureus history show 11

# Shows full compilation pipeline for session 11
```

### Learning Statistics
```bash
aureus stats

# Output:
# Learning Statistics
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Sessions: 12 total, 10 successful
# 
# Cost Accuracy:
#   Average error: 3.2% (estimated vs actual)
#   Improving over time ✓
# 
# Budget Usage:
#   Total: 2,761 / 10,000 LOC (27.6%)
#   Trend: +180 LOC/week (sustainable)
# 
# Approval Rate:
#   Auto-approved: 83% (10/12 sessions)
#   User prompted: 17% (2/12 sessions)
#   User overrides: 0% (model well-calibrated)
# 
# Pattern Violations: 0
```

---

## Verification & Rollback

### Verify Project Against Policy
```bash
aureus verify

# Output:
# Policy Compliance Check
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ✓ LOC budget: 2,761 / 10,000 (OK)
# ✓ Module count: 6 / 8 (OK)
# ✓ Dependency count: 8 / 12 (OK)
# ✓ No forbidden patterns detected
# ✓ All files within size limits
# 
# ✅ Project complies with governance policy
```

### Rollback Last Change
```bash
aureus rollback

# Or specific session
aureus rollback --session 11
```

### Create Checkpoint
```bash
aureus checkpoint create "before-major-refactor"
aureus code "refactor entire auth system"
aureus checkpoint restore "before-major-refactor"  # if needed
```

---

## Advanced Usage

### Dry Run (Estimate Only)
```bash
aureus code "add caching layer" --dry-run

# Shows plan and cost without executing
```

### Custom Model
```bash
aureus code "add auth" --model claude-opus-4
aureus code "add auth" --model gpt-4
aureus code "add auth" --model local-llama
```

### Batch Mode (Non-Interactive)
```bash
aureus code "add tests" --batch --approve-all
aureus code "add docs" --batch --reject-over 200
```

### Export Compilation Report
```bash
aureus code "add feature" --report-file feature_implementation.json
```

---

## CI/CD Integration

### Run in CI Pipeline
```yaml
# .github/workflows/aureus-check.yml
name: AUREUS Governance Check

on: [push, pull_request]

jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Install AUREUS
        run: pip install aureus
      - name: Verify compliance
        run: aureus verify
```

### Pre-commit Hook
```bash
# .git/hooks/pre-commit
#!/bin/bash
aureus verify || exit 1
```

---

## Debugging & Troubleshooting

### Verbose Mode
```bash
aureus code "add feature" --verbose

# Shows detailed logs:
# - LLM prompts and responses
# - Cost calculation steps
# - Tool execution details
```

### Check Health
```bash
aureus doctor

# Output:
# System Health Check
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ✓ Git repository found
# ✓ Policy file exists and valid
# ✓ Python environment OK
# ✓ Model provider accessible (Anthropic)
# ✓ All dependencies installed
# ✓ No corrupted history files
# 
# ✅ AUREUS is healthy
```

### Reset Everything
```bash
aureus reset --hard  # Delete .aureus/, regenerate policy
```

---

## Configuration

### Global Config
```bash
# Set default model
aureus config set model claude-sonnet-4

# Set default approval threshold
aureus config set auto_approve_threshold 300

# Set API keys
aureus config set anthropic_api_key sk-...
```

### View Config
```bash
aureus config show
```

---

## Examples by Use Case

### Greenfield Project (New Project)
```bash
mkdir my-api && cd my-api
git init
aureus init --type api --language python
aureus code "create Flask API with user CRUD endpoints"
```

### Legacy Project (Existing Codebase)
```bash
cd existing-project
aureus init  # Auto-detects current state
aureus verify  # Check compliance
aureus code "add missing tests"
```

### Refactoring Session
```bash
aureus checkpoint create "before-refactor"
aureus code "extract user logic to separate service"
aureus code "simplify authentication flow"
aureus verify
```

### Microservice Development
```bash
aureus init --type microservice
aureus code "add health check endpoint"
aureus code "add Prometheus metrics"
aureus code "add request tracing"
```

---

## Error Messages

### Budget Exceeded
```
❌ Error: BUDGET_EXCEEDED
   Estimated cost (850 LOC) exceeds session limit (600 LOC)
   
   Suggestion: Split into smaller tasks or increase budget
   Docs: https://aureus.dev/docs/errors#BUDGET_EXCEEDED
```

### Forbidden Pattern
```
❌ Error: PATTERN_VIOLATION
   Detected forbidden pattern: god_object
   File: src/user.py (class User: 650 LOC)
   
   Suggestion: Split User class into smaller components
   Docs: https://aureus.dev/docs/errors#PATTERN_VIOLATION
```

### Model Unavailable
```
❌ Error: MODEL_UNAVAILABLE
   Could not connect to Anthropic API
   
   Suggestion: Check API key and network connection
   Docs: https://aureus.dev/docs/errors#MODEL_UNAVAILABLE
```

---

**For complete CLI reference, see**: `aureus --help`
