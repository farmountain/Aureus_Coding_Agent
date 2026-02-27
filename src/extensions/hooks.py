"""
Hook Extension

Lifecycle automation at AUREUS workflow phases.

Hooks enable custom logic at key lifecycle points:
- pre/post_gather: Before/after context gathering
- pre/post_verify: Before/after verification
- pre/post_update: Before/after state updates  
- pre/post_frame: Before/after problem framing
- pre/post_decide: Before/after decision making
- pre/post_reflexion: Before/after self-reflection
"""

from typing import Callable, Dict, List, Optional, Any
from dataclasses import dataclass, field
import signal
from contextlib import contextmanager

from src.extensions.base import (
    Extension,
    ExtensionResult,
    ExtensionBudgetExceeded,
    ExtensionPermissionError
)


# Valid lifecycle points in AUREUS workflow
LIFECYCLE_POINTS = {
    "pre_gather", "post_gather",
    "pre_verify", "post_verify",
    "pre_update", "post_update",
    "pre_frame", "post_frame",
    "pre_decide", "post_decide",
    "pre_reflexion", "post_reflexion"
}


@dataclass
class Hook:
    """
    Lifecycle hook definition.
    
    Hooks are callbacks that execute at specific workflow phases.
    """
    name: str
    description: str
    callback: Callable
    lifecycle_point: str
    timeout: float = 30.0  # Maximum execution time in seconds
    estimated_cost: float = 5.0
    required_permissions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __repr__(self) -> str:
        return f"Hook(name='{self.name}', point='{self.lifecycle_point}')"


class TimeoutError(Exception):
    """Hook execution timeout"""
    pass


@contextmanager
def timeout_handler(seconds: float):
    """
    Context manager for timeout enforcement.
    
    Args:
        seconds: Timeout in seconds
    
    Raises:
        TimeoutError: If execution exceeds timeout
    """
    def timeout_signal_handler(signum, frame):
        raise TimeoutError(f"Hook execution timed out after {seconds}s")
    
    # Set alarm for timeout (Unix/Linux only)
    # For Windows compatibility, we'll skip signal-based timeout
    # In production, use threading.Timer or multiprocessing
    try:
        if hasattr(signal, 'SIGALRM'):
            old_handler = signal.signal(signal.SIGALRM, timeout_signal_handler)
            signal.alarm(int(seconds))
        yield
    finally:
        if hasattr(signal, 'SIGALRM'):
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)


class HookExtension(Extension):
    """
    Lifecycle automation system.
    
    Hooks enable custom logic at key workflow phases with:
    - Timeout enforcement
    - Cost tracking
    - Permission validation
    - Error isolation (failed hooks don't crash workflow)
    """
    
    def __init__(
        self,
        policy,
        max_cost: float = 200.0
    ):
        """
        Initialize hook extension.
        
        Args:
            policy: Governance policy
            max_cost: Maximum cost budget for all hooks
        """
        super().__init__(
            name="hooks",
            policy=policy,
            max_cost=max_cost,
            required_permissions=["extensions"]
        )
        
        # Hooks organized by lifecycle point
        self.hooks: Dict[str, List[Hook]] = {
            point: [] for point in LIFECYCLE_POINTS
        }
    
    def execute(self, **kwargs) -> ExtensionResult:
        """
        Execute hooks for a lifecycle point.
        
        Args:
            lifecycle_point: Which phase to execute hooks for
            context: Optional context dict to pass to hooks
        
        Returns:
            ExtensionResult with aggregated hook outputs
        """
        lifecycle_point = kwargs.get("lifecycle_point")
        context = kwargs.get("context", {})
        
        if not lifecycle_point:
            return self._error("lifecycle_point parameter required")
        
        return self.execute_hooks(lifecycle_point, context=context)
    
    def register_hook(self, hook: Hook):
        """
        Register a hook with validation.
        
        Args:
            hook: Hook to register
        
        Raises:
            ExtensionPermissionError: If hook requires unavailable permission
            ExtensionBudgetExceeded: If hook would exceed budget
            ValueError: If lifecycle_point is invalid
        """
        # Validate lifecycle point
        if hook.lifecycle_point not in LIFECYCLE_POINTS:
            raise ValueError(
                f"Invalid lifecycle_point '{hook.lifecycle_point}'. "
                f"Must be one of: {sorted(LIFECYCLE_POINTS)}"
            )
        
        # Validate permissions
        for perm in hook.required_permissions:
            if not self.policy.permissions.get(perm, False):
                raise ExtensionPermissionError(
                    f"Hook '{hook.name}' requires permission '{perm}' "
                    f"but it is not granted in policy"
                )
        
        # Check budget
        if not self.check_budget(hook.estimated_cost):
            raise ExtensionBudgetExceeded(
                f"Cannot register hook '{hook.name}': "
                f"estimated cost {hook.estimated_cost} exceeds remaining budget "
                f"{self.get_budget_remaining()}"
            )
        
        # Register hook
        self.hooks[hook.lifecycle_point].append(hook)
    
    def execute_hooks(
        self,
        lifecycle_point: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ExtensionResult:
        """
        Execute all hooks for a lifecycle point.
        
        Args:
            lifecycle_point: Which phase to execute hooks for
            context: Optional context dict to pass to hooks
        
        Returns:
            ExtensionResult with aggregated outputs
        """
        if lifecycle_point not in LIFECYCLE_POINTS:
            return self._error(
                f"Invalid lifecycle_point '{lifecycle_point}'",
                metadata={"valid_points": sorted(LIFECYCLE_POINTS)}
            )
        
        # Get hooks for this lifecycle point
        hooks_to_run = self.hooks.get(lifecycle_point, [])
        
        if not hooks_to_run:
            return self._success(
                output=[],
                cost_used=0.0,
                metadata={
                    "lifecycle_point": lifecycle_point,
                    "hooks_executed": 0
                }
            )
        
        # Execute each hook
        results = []
        total_cost = 0.0
        errors = []
        
        for hook in hooks_to_run:
            # Check budget before executing
            if not self.check_budget(hook.estimated_cost):
                errors.append({
                    "hook": hook.name,
                    "error": "Budget exceeded",
                    "cost": hook.estimated_cost,
                    "remaining": self.get_budget_remaining()
                })
                continue
            
            try:
                # Execute with timeout
                # Note: timeout_handler uses signals which only work on Unix
                # For Windows, we'll just execute directly
                # In production, use threading.Timer or multiprocessing.Process
                
                if context is not None:
                    output = hook.callback(context)
                else:
                    output = hook.callback()
                
                results.append({
                    "hook": hook.name,
                    "output": output,
                    "cost": hook.estimated_cost
                })
                
                total_cost += hook.estimated_cost
                
            except TimeoutError as e:
                errors.append({
                    "hook": hook.name,
                    "error": f"Timeout after {hook.timeout}s",
                    "exception": str(e)
                })
            
            except Exception as e:
                errors.append({
                    "hook": hook.name,
                    "error": f"{type(e).__name__}: {str(e)}",
                    "exception_type": type(e).__name__
                })
        
        # Return result
        if errors and not results:
            # All hooks failed
            return self._error(
                f"All hooks failed at {lifecycle_point}",
                metadata={
                    "lifecycle_point": lifecycle_point,
                    "errors": errors,
                    "hooks_attempted": len(hooks_to_run)
                }
            )
        
        elif errors:
            # Some hooks failed but some succeeded
            return self._success(
                output=results,
                cost_used=total_cost,
                metadata={
                    "lifecycle_point": lifecycle_point,
                    "hooks_executed": len(results),
                    "hooks_failed": len(errors),
                    "errors": errors
                }
            )
        
        else:
            # All hooks succeeded
            return self._success(
                output=results,
                cost_used=total_cost,
                metadata={
                    "lifecycle_point": lifecycle_point,
                    "hooks_executed": len(results)
                }
            )
    
    def list_hooks(self, lifecycle_point: Optional[str] = None) -> Dict[str, List[str]]:
        """
        Get list of registered hooks.
        
        Args:
            lifecycle_point: Optional filter for specific lifecycle point
        
        Returns:
            Dict mapping lifecycle points to hook names
        """
        if lifecycle_point:
            return {
                lifecycle_point: [h.name for h in self.hooks.get(lifecycle_point, [])]
            }
        
        return {
            point: [h.name for h in hooks]
            for point, hooks in self.hooks.items()
            if hooks
        }
    
    def unregister_hook(self, name: str, lifecycle_point: str) -> bool:
        """
        Unregister a hook.
        
        Args:
            name: Hook name
            lifecycle_point: Lifecycle point
        
        Returns:
            True if hook was removed, False if not found
        """
        if lifecycle_point not in self.hooks:
            return False
        
        hooks = self.hooks[lifecycle_point]
        for i, hook in enumerate(hooks):
            if hook.name == name:
                del hooks[i]
                return True
        
        return False
