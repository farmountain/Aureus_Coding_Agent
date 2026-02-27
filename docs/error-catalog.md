# AUREUS Error Catalog

**Purpose**: Consistent, helpful error messages across all components  
**Format**: Error codes with IDs, messages, suggestions, and documentation links

---

## Error Format Standard

All AUREUS errors follow this structure:

```python
class AUREUSError(Exception):
    """Base exception for all AUREUS errors."""
    
    def __init__(
        self,
        code: str,          # Error code (e.g., "BUDGET_001")
        message: str,       # Human-readable message
        details: dict = None,  # Additional context
        suggestion: str = None,  # What user should do
        docs_url: str = None    # Link to documentation
    ):
        self.code = code
        self.message = message
        self.details = details or {}
        self.suggestion = suggestion
        self.docs_url = docs_url or f"https://aureus.dev/errors/{code}"
        
        super().__init__(self.format_message())
    
    def format_message(self) -> str:
        """Format error for CLI display."""
        
        lines = [
            f"❌ Error [{self.code}]: {self.message}",
            ""
        ]
        
        if self.details:
            lines.append("Details:")
            for key, value in self.details.items():
                lines.append(f"  • {key}: {value}")
            lines.append("")
        
        if self.suggestion:
            lines.append(f"💡 Suggestion: {self.suggestion}")
            lines.append("")
        
        lines.append(f"📖 More info: {self.docs_url}")
        
        return "\n".join(lines)
```

---

## Error Categories

### 1. Budget Errors (BUDGET_xxx)
### 2. Policy Errors (POLICY_xxx)
### 3. Specification Errors (SPEC_xxx)
### 4. Implementation Errors (IMPL_xxx)
### 5. Context Errors (CONTEXT_xxx)
### 6. Tool Errors (TOOL_xxx)
### 7. Session Errors (SESSION_xxx)
### 8. Security Errors (SECURITY_xxx)

---

## 1. Budget Errors (BUDGET_xxx)

### BUDGET_001: LOC Budget Exceeded

```python
class BudgetExceededError(AUREUSError):
    """Lines of code budget exceeded."""
    
    def __init__(self, current: int, limit: int, delta: int):
        super().__init__(
            code="BUDGET_001",
            message=f"LOC budget exceeded: {current + delta} > {limit}",
            details={
                "current_loc": current,
                "requested_change": delta,
                "total_after": current + delta,
                "limit": limit,
                "overage": (current + delta) - limit
            },
            suggestion=(
                "Try one of:\n"
                "  • Break into smaller tasks\n"
                "  • Remove unused code first\n"
                "  • Increase budget: aureus policy edit\n"
                "  • See alternatives suggested by SPK"
            )
        )
```

### BUDGET_002: Module Budget Exceeded

```python
class ModuleBudgetExceededError(AUREUSError):
    """Too many modules."""
    
    def __init__(self, current: int, limit: int):
        super().__init__(
            code="BUDGET_002",
            message=f"Module budget exceeded: {current + 1} > {limit}",
            details={
                "current_modules": current,
                "limit": limit
            },
            suggestion=(
                "Consider:\n"
                "  • Add to existing module instead of creating new one\n"
                "  • Merge similar modules\n"
                "  • Increase limit if justified"
            )
        )
```

### BUDGET_003: Dependency Budget Exceeded

```python
class DependencyBudgetExceededError(AUREUSError):
    """Too many dependencies."""
    
    def __init__(self, dependency: str, current: int, limit: int):
        super().__init__(
            code="BUDGET_003",
            message=f"Cannot add dependency '{dependency}': limit {limit} reached",
            details={
                "requested_dependency": dependency,
                "current_dependencies": current,
                "limit": limit
            },
            suggestion=(
                "Options:\n"
                "  • Use stdlib alternative if available\n"
                "  • Implement yourself (if small)\n"
                "  • Remove unused dependency first\n"
                "  • Justify and increase limit"
            )
        )
```

### BUDGET_004: Cost Threshold Exceeded

```python
class CostThresholdExceededError(AUREUSError):
    """Complexity cost too high."""
    
    def __init__(self, cost: float, threshold: float, alternatives: list):
        super().__init__(
            code="BUDGET_004",
            message=f"Complexity cost {cost} exceeds threshold {threshold}",
            details={
                "estimated_cost": cost,
                "rejection_threshold": threshold,
                "breakdown": {
                    "loc_cost": cost * 0.4,
                    "dependency_cost": cost * 0.3,
                    "abstraction_cost": cost * 0.3
                }
            },
            suggestion=(
                f"SPK suggests {len(alternatives)} simpler alternatives:\n" +
                "\n".join(f"  {i+1}. {alt.description}" for i, alt in enumerate(alternatives[:3]))
            )
        )
```

---

## 2. Policy Errors (POLICY_xxx)

### POLICY_001: Policy File Not Found

```python
class PolicyNotFoundError(AUREUSError):
    """No policy file exists."""
    
    def __init__(self, path: Path):
        super().__init__(
            code="POLICY_001",
            message=f"Policy file not found: {path}",
            details={"expected_path": str(path)},
            suggestion=(
                "Initialize policy first:\n"
                "  aureus init\n"
                "\n"
                "This will analyze your project and create intelligent defaults."
            )
        )
```

### POLICY_002: Policy Validation Failed

```python
class PolicyValidationError(AUREUSError):
    """Policy file is invalid."""
    
    def __init__(self, errors: list[str]):
        super().__init__(
            code="POLICY_002",
            message="Policy file has validation errors",
            details={"errors": errors},
            suggestion=(
                "Fix validation errors or regenerate policy:\n"
                "  aureus policy validate  # See all errors\n"
                "  aureus init --force    # Regenerate from scratch"
            )
        )
```

### POLICY_003: Forbidden Pattern Violated

```python
class ForbiddenPatternError(AUREUSError):
    """Code violates forbidden pattern."""
    
    def __init__(self, pattern: str, location: str, reason: str):
        super().__init__(
            code="POLICY_003",
            message=f"Forbidden pattern detected: {pattern}",
            details={
                "pattern": pattern,
                "location": location,
                "reason": reason
            },
            suggestion=(
                "This pattern is forbidden by project policy.\n"
                "Either:\n"
                "  • Refactor to avoid pattern\n"
                "  • Override with: aureus code --allow-pattern {pattern}\n"
                "  • Remove from policy if no longer needed"
            )
        )
```

---

## 3. Specification Errors (SPEC_xxx)

### SPEC_001: Cannot Generate Specification

```python
class SpecificationGenerationError(AUREUSError):
    """GVUFD failed to generate valid spec."""
    
    def __init__(self, intent: str, attempts: int):
        super().__init__(
            code="SPEC_001",
            message=f"Cannot generate specification after {attempts} attempts",
            details={
                "intent": intent,
                "attempts": attempts
            },
            suggestion=(
                "Your request may be too ambiguous. Try:\n"
                "  • Be more specific (e.g., 'add REST endpoint for users' not 'add API')\n"
                "  • Break into smaller tasks\n"
                "  • Provide more context about what you want\n"
                "\n"
                "Examples of good requests:\n"
                "  ✓ 'add user authentication with JWT'\n"
                "  ✓ 'add GET /users endpoint with pagination'\n"
                "  ✗ 'make it better'\n"
                "  ✗ 'add stuff'"
            )
        )
```

### SPEC_002: Specification Validation Failed

```python
class SpecificationValidationError(AUREUSError):
    """Generated spec is invalid."""
    
    def __init__(self, issues: list[str]):
        super().__init__(
            code="SPEC_002",
            message="Generated specification is invalid",
            details={"validation_errors": issues},
            suggestion="This is an internal error. Please report with your request."
        )
```

---

## 4. Implementation Errors (IMPL_xxx)

### IMPL_001: Tests Failed

```python
class TestsFailedError(AUREUSError):
    """Implementation tests failed."""
    
    def __init__(self, failed_tests: list[str], iteration: int):
        super().__init__(
            code="IMPL_001",
            message=f"{len(failed_tests)} tests failed (iteration {iteration})",
            details={
                "failed_tests": failed_tests,
                "iteration": iteration,
                "max_iterations": 3
            },
            suggestion=(
                "Tests are failing. Options:\n"
                "  • Let me try to fix (continuing...)\n"
                "  • Stop and review manually\n"
                "  • Adjust requirements if tests are too strict"
            )
        )
```

### IMPL_002: Critical Issues Found

```python
class CriticalIssuesError(AUREUSError):
    """Critic found critical issues."""
    
    def __init__(self, issues: list[str], iteration: int):
        super().__init__(
            code="IMPL_002",
            message=f"{len(issues)} critical issues found",
            details={
                "issues": issues,
                "iteration": iteration
            },
            suggestion=(
                "Critical issues detected:\n" +
                "\n".join(f"  • {issue}" for issue in issues[:5]) +
                "\n\nI'll attempt to fix these..."
            )
        )
```

### IMPL_003: Max Iterations Reached

```python
class MaxIterationsError(AUREUSError):
    """Reached max refinement iterations."""
    
    def __init__(self, remaining_issues: list[str]):
        super().__init__(
            code="IMPL_003",
            message="Stopped after max refinement iterations (3)",
            details={
                "remaining_issues": remaining_issues,
                "status": "best_effort"
            },
            suggestion=(
                "Implementation completed with best effort.\n"
                "Remaining minor issues:\n" +
                "\n".join(f"  • {issue}" for issue in remaining_issues[:3]) +
                "\n\nYou can:\n"
                "  • Accept as-is and fix manually\n"
                "  • Retry with more specific requirements\n"
                "  • Adjust policy strictness"
            )
        )
```

---

## 5. Context Errors (CONTEXT_xxx)

### CONTEXT_001: Token Budget Exceeded

```python
class TokenBudgetExceededError(AUREUSError):
    """Context size exceeds model limits."""
    
    def __init__(self, current: int, limit: int):
        super().__init__(
            code="CONTEXT_001",
            message=f"Context size {current} tokens exceeds limit {limit}",
            details={
                "current_tokens": current,
                "limit_tokens": limit,
                "overage": current - limit
            },
            suggestion=(
                "Context is too large. I'll:\n"
                "  • Prune least recently used files\n"
                "  • Keep only hot files and dependencies\n"
                "  • You can manually specify important files with:\n"
                "    aureus context add <file>"
            )
        )
```

### CONTEXT_002: File Not In Working Set

```python
class FileNotInContextError(AUREUSError):
    """File needed but not in context."""
    
    def __init__(self, file: Path):
        super().__init__(
            code="CONTEXT_002",
            message=f"File not in working set: {file}",
            details={"file": str(file)},
            suggestion=(
                f"Add file to context:\n"
                f"  aureus context add {file}\n"
                "\n"
                "Or let me analyze and add automatically:\n"
                "  aureus context auto"
            )
        )
```

---

## 6. Tool Errors (TOOL_xxx)

### TOOL_001: Permission Denied

```python
class ToolPermissionError(AUREUSError):
    """Tool requires permission."""
    
    def __init__(self, tool: str, tier: int):
        super().__init__(
            code="TOOL_001",
            message=f"Permission denied for tool: {tool}",
            details={
                "tool": tool,
                "permission_tier": tier,
                "tier_meaning": {
                    0: "Safe (always allowed)",
                    1: "Approve once per session",
                    2: "Prompt each time",
                    3: "Disabled"
                }[tier]
            },
            suggestion=(
                f"Tool '{tool}' requires approval.\n"
                "Grant permission:\n"
                f"  aureus policy allow {tool}\n"
                "\n"
                "Or run with --allow-all (not recommended)"
            )
        )
```

### TOOL_002: Rollback Failed

```python
class RollbackError(AUREUSError):
    """Cannot rollback changes."""
    
    def __init__(self, reason: str):
        super().__init__(
            code="TOOL_002",
            message=f"Rollback failed: {reason}",
            details={"reason": reason},
            suggestion=(
                "Cannot automatically rollback. Manual recovery:\n"
                "  • Check .aureus/checkpoints/ for saved state\n"
                "  • Use git to restore: git stash list\n"
                "  • Review changes: git diff"
            )
        )
```

---

## 7. Session Errors (SESSION_xxx)

### SESSION_001: Timeout

```python
class SessionTimeoutError(AUREUSError):
    """Session exceeded time limit."""
    
    def __init__(self, elapsed: float, limit: float):
        super().__init__(
            code="SESSION_001",
            message=f"Session timeout: {elapsed:.1f}s > {limit:.1f}s",
            details={
                "elapsed_seconds": elapsed,
                "limit_seconds": limit
            },
            suggestion=(
                "Session took too long (30 min limit).\n"
                "This task may be too complex. Try:\n"
                "  • Break into smaller subtasks\n"
                "  • Simplify requirements\n"
                "  • Increase timeout (not recommended)"
            )
        )
```

### SESSION_002: Exhausted

```python
class SessionExhaustedError(AUREUSError):
    """Session exhausted resources."""
    
    def __init__(self, resource: str, limit: int):
        super().__init__(
            code="SESSION_002",
            message=f"Session exhausted: {resource} limit {limit} reached",
            details={
                "resource": resource,
                "limit": limit
            },
            suggestion=(
                f"{resource} limit reached.\n"
                "This suggests task is too complex.\n"
                "Consider breaking into smaller pieces."
            )
        )
```

### SESSION_003: Stuck State

```python
class SessionStuckError(AUREUSError):
    """Session is stuck (no progress)."""
    
    def __init__(self, iterations: int):
        super().__init__(
            code="SESSION_003",
            message=f"Session stuck after {iterations} iterations (no progress)",
            details={"iterations": iterations},
            suggestion=(
                "System is not making progress.\n"
                "Same issues appearing repeatedly.\n"
                "\n"
                "Try:\n"
                "  • Rephrase request more specifically\n"
                "  • Break into smaller subtasks\n"
                "  • Adjust policy constraints\n"
                "  • Manual intervention may be needed"
            )
        )
```

---

## 8. Security Errors (SECURITY_xxx)

### SECURITY_001: Unsafe Operation

```python
class UnsafeOperationError(AUREUSError):
    """Operation is unsafe."""
    
    def __init__(self, operation: str, risk: str):
        super().__init__(
            code="SECURITY_001",
            message=f"Unsafe operation blocked: {operation}",
            details={
                "operation": operation,
                "risk": risk
            },
            suggestion=(
                "This operation is considered unsafe.\n"
                f"Risk: {risk}\n"
                "\n"
                "If you trust this operation:\n"
                "  aureus code --allow-unsafe\n"
                "\n"
                "Or adjust security policy:\n"
                "  aureus policy edit"
            )
        )
```

### SECURITY_002: Plaintext Secrets Detected

```python
class PlaintextSecretsError(AUREUSError):
    """Plaintext secrets in code."""
    
    def __init__(self, locations: list[str]):
        super().__init__(
            code="SECURITY_002",
            message="Plaintext secrets detected in code",
            details={"locations": locations},
            suggestion=(
                "Never commit plaintext secrets!\n"
                "\n"
                "Use environment variables:\n"
                "  api_key = os.getenv('API_KEY')\n"
                "\n"
                "Or a secrets manager:\n"
                "  from secretmanager import get_secret\n"
                "  api_key = get_secret('api_key')"
            )
        )
```

---

## 9. Model Errors (MODEL_xxx)

### MODEL_001: API Error

```python
class ModelAPIError(AUREUSError):
    """LLM API call failed."""
    
    def __init__(self, provider: str, error: str):
        super().__init__(
            code="MODEL_001",
            message=f"Model API error ({provider}): {error}",
            details={
                "provider": provider,
                "error": error
            },
            suggestion=(
                "LLM API call failed. Check:\n"
                "  • API key is valid: aureus config check\n"
                "  • Network connection\n"
                "  • Provider status page\n"
                "\n"
                "Or switch provider:\n"
                "  aureus config set model.provider openai"
            )
        )
```

### MODEL_002: Rate Limited

```python
class ModelRateLimitError(AUREUSError):
    """Hit API rate limit."""
    
    def __init__(self, provider: str, retry_after: int):
        super().__init__(
            code="MODEL_002",
            message=f"Rate limited by {provider}",
            details={
                "provider": provider,
                "retry_after_seconds": retry_after
            },
            suggestion=(
                f"Rate limit hit. Retry after {retry_after}s.\n"
                "\n"
                "Options:\n"
                "  • Wait and retry automatically (in progress...)\n"
                "  • Switch to different provider\n"
                "  • Upgrade API tier"
            )
        )
```

---

## Error Handling Best Practices

### 1. Always Be Helpful

```python
# BAD - not helpful
raise Exception("Invalid input")

# GOOD - specific and actionable
raise PolicyValidationError(
    errors=["max_loc must be positive integer"],
    suggestion="Fix policy.yaml line 5: max_loc: 10000"
)
```

### 2. Include Context

```python
# BAD - no context
raise BudgetExceededError()

# GOOD - full context
raise BudgetExceededError(
    current=4200,
    limit=5000,
    delta=1500  # Shows exactly why it failed
)
```

### 3. Suggest Alternatives

```python
# BAD - just says no
raise Error("Cannot do that")

# GOOD - suggests alternatives
raise CostThresholdExceededError(
    cost=850,
    threshold=500,
    alternatives=[
        Alternative("Reduce scope", cost=300),
        Alternative("Split into phases", cost=200),
    ]
)
```

### 4. Link to Documentation

```python
# All errors auto-link to docs
error.docs_url  # https://aureus.dev/errors/BUDGET_001
```

---

## Testing Error Messages

```python
def test_budget_error_message():
    """Budget error has helpful message."""
    
    error = BudgetExceededError(current=4000, limit=5000, delta=1500)
    
    message = str(error)
    
    assert "BUDGET_001" in message
    assert "4000" in message  # Current
    assert "5000" in message  # Limit
    assert "1500" in message  # Delta
    assert "suggestion" in message.lower()
    assert "aureus.dev/errors" in message

def test_error_code_uniqueness():
    """All error codes are unique."""
    
    codes = [
        "BUDGET_001", "BUDGET_002", "BUDGET_003",
        "POLICY_001", "POLICY_002", "POLICY_003",
        # ... all codes
    ]
    
    assert len(codes) == len(set(codes))  # No duplicates
```

---

## CLI Error Display

```bash
$ aureus code "add very complex feature"

❌ Error [BUDGET_004]: Complexity cost 850 exceeds threshold 500

Details:
  • estimated_cost: 850
  • rejection_threshold: 500
  • breakdown:
    - loc_cost: 340
    - dependency_cost: 255
    - abstraction_cost: 255

💡 Suggestion: SPK suggests 3 simpler alternatives:
  1. Reduce scope to core functionality (cost: 300)
  2. Split into 2 phases (cost: 250 per phase)
  3. Use existing library instead of custom implementation (cost: 150)

📖 More info: https://aureus.dev/errors/BUDGET_004
```

**Clear, actionable, helpful.**

---

## Summary

All AUREUS errors:
- ✅ Have unique code (e.g., BUDGET_001)
- ✅ Provide clear message
- ✅ Include relevant details
- ✅ Suggest concrete actions
- ✅ Link to documentation
- ✅ Display beautifully in CLI

**Good errors turn frustration into understanding.**
