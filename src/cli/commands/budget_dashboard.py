"""
Budget Dashboard - Sprint 1 Item 4

Visual budget tracking for the AUREUS CLI.

Shows real-time budget consumption with:
- Progress bars for each metric (LOC, files, dependencies, modules)
- Used / Remaining / Total display
- Color-coded warnings (green < 70%, yellow 70-90%, red > 90%)
- Per-session and cumulative views
- Persistent tracking across sessions
"""

from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import json


# ============================================================================
# Budget Usage Data Structures
# ============================================================================

@dataclass
class BudgetEntry:
    """Single budget consumption entry from one build."""
    session_id: str
    intent: str
    timestamp: str
    loc_used: int = 0
    files_created: int = 0
    files_modified: int = 0
    dependencies_added: int = 0
    cost_total: float = 0.0
    success: bool = False

    def to_dict(self) -> Dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict) -> "BudgetEntry":
        return BudgetEntry(**data)


@dataclass
class BudgetState:
    """Cumulative project budget state."""
    policy_max_loc: int
    policy_max_files: int
    policy_max_dependencies: int
    policy_max_modules: int

    used_loc: int = 0
    used_files: int = 0
    used_dependencies: int = 0
    used_modules: int = 0
    total_cost: float = 0.0
    total_builds: int = 0
    successful_builds: int = 0
    last_updated: Optional[str] = None
    entries: List[Dict] = field(default_factory=list)

    def to_dict(self) -> Dict:
        d = asdict(self)
        return d

    @staticmethod
    def from_dict(data: Dict) -> "BudgetState":
        entries = data.pop("entries", [])
        state = BudgetState(**data)
        state.entries = entries
        return state


# ============================================================================
# Progress Bar Renderer
# ============================================================================

class ProgressBar:
    """
    Renders ASCII progress bars with color coding.

    Example output:
        LOC       [████████████░░░░░░░░]  1,250 / 10,000  (12.5%)  ✅
        Files     [████░░░░░░░░░░░░░░░░]      6 / 30       (20.0%)  ✅
    """

    BAR_WIDTH = 20
    FILL_CHAR = "█"
    EMPTY_CHAR = "░"

    # ANSI color codes (work on most terminals)
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    RESET = "\033[0m"
    BOLD = "\033[1m"

    @classmethod
    def render(
        cls,
        label: str,
        used: int,
        total: int,
        unit: str = "",
        use_color: bool = True,
        label_width: int = 14,
    ) -> str:
        """
        Render a single progress bar row.

        Args:
            label: Metric name (e.g. "LOC")
            used: Amount consumed
            total: Policy maximum
            unit: Optional unit suffix
            use_color: Whether to emit ANSI color codes
            label_width: Column width for the label

        Returns:
            Formatted progress bar string
        """
        if total <= 0:
            pct = 0.0
        else:
            pct = min(used / total, 1.0)

        filled = int(pct * cls.BAR_WIDTH)
        empty = cls.BAR_WIDTH - filled

        bar_chars = cls.FILL_CHAR * filled + cls.EMPTY_CHAR * empty

        # Determine status icon and color
        if pct >= 0.90:
            color = cls.RED if use_color else ""
            icon = "🚨"
        elif pct >= 0.70:
            color = cls.YELLOW if use_color else ""
            icon = "⚠️ "
        else:
            color = cls.GREEN if use_color else ""
            icon = "✅"

        reset = cls.RESET if use_color else ""

        # Format numbers with commas
        used_str = f"{used:,}{unit}"
        total_str = f"{total:,}{unit}"
        remaining = max(0, total - used)
        remaining_str = f"{remaining:,}{unit}"

        label_padded = label.ljust(label_width)
        numbers = f"{used_str:>10} / {total_str:<10}  ({pct*100:5.1f}%)  remaining: {remaining_str}"

        bar_colored = f"{color}[{bar_chars}]{reset}"

        return f"  {label_padded} {bar_colored}  {numbers}  {icon}"

    @classmethod
    def render_compact(cls, label: str, used: int, total: int, use_color: bool = True) -> str:
        """Compact single-line variant for post-build summary."""
        if total <= 0:
            pct = 0.0
        else:
            pct = min(used / total, 1.0)

        if pct >= 0.90:
            color = cls.RED if use_color else ""
            icon = "🚨"
        elif pct >= 0.70:
            color = cls.YELLOW if use_color else ""
            icon = "⚠️ "
        else:
            color = cls.GREEN if use_color else ""
            icon = "✅"

        reset = cls.RESET if use_color else ""
        remaining = max(0, total - used)

        return (
            f"  {color}{label:<14}{reset}"
            f"  {used:>6,} used  |  {remaining:>6,} remaining  |  {pct*100:5.1f}%  {icon}"
        )


# ============================================================================
# Budget Dashboard
# ============================================================================

class BudgetDashboard:
    """
    Persistent budget tracker for an AUREUS project.

    Reads policy limits from the loaded Policy object and tracks
    cumulative consumption across all build sessions.  State is
    stored at <project_root>/.aureus/budget.json.

    Usage
    -----
    # After a build completes:
    dashboard = BudgetDashboard(project_root)
    dashboard.record_build(result, intent="Add login")

    # To display:
    dashboard.print_dashboard()
    """

    BUDGET_FILE = ".aureus/budget.json"

    def __init__(self, project_root: Path, policy=None):
        """
        Initialise dashboard.

        Args:
            project_root: Root directory of the project
            policy: Optional Policy object (provides limits); if None the
                    stored limits are used on reload.
        """
        self.project_root = Path(project_root)
        self.budget_path = self.project_root / self.BUDGET_FILE
        self.budget_path.parent.mkdir(parents=True, exist_ok=True)

        # Bootstrap or reload state
        self.state = self._load_or_init(policy)

    # ------------------------------------------------------------------ #
    # Persistence                                                          #
    # ------------------------------------------------------------------ #

    def _load_or_init(self, policy) -> BudgetState:
        """Load existing state or create fresh state from policy."""
        if self.budget_path.exists():
            try:
                with open(self.budget_path) as f:
                    data = json.load(f)
                state = BudgetState.from_dict(data)
                # Update policy limits if a fresh policy was provided
                if policy is not None:
                    state.policy_max_loc = policy.budgets.max_loc
                    state.policy_max_files = policy.budgets.max_files
                    state.policy_max_dependencies = policy.budgets.max_dependencies
                    state.policy_max_modules = policy.budgets.max_modules
                return state
            except (json.JSONDecodeError, KeyError, TypeError):
                pass  # Fall through to create fresh

        # Create fresh state from policy
        if policy is not None:
            return BudgetState(
                policy_max_loc=policy.budgets.max_loc,
                policy_max_files=policy.budgets.max_files,
                policy_max_dependencies=policy.budgets.max_dependencies,
                policy_max_modules=policy.budgets.max_modules,
            )

        # No policy and no stored state — use safe defaults
        return BudgetState(
            policy_max_loc=10_000,
            policy_max_files=30,
            policy_max_dependencies=20,
            policy_max_modules=8,
        )

    def save(self):
        """Persist current state to disk."""
        with open(self.budget_path, "w") as f:
            json.dump(self.state.to_dict(), f, indent=2)

    # ------------------------------------------------------------------ #
    # Recording                                                            #
    # ------------------------------------------------------------------ #

    def record_build(
        self,
        result,
        intent: str = "",
        session_id: Optional[str] = None,
    ):
        """
        Record consumption from a completed BuildResult.

        Args:
            result: BuildResult from BuilderAgent.build()
            intent: Original user intent string
            session_id: Optional session ID
        """
        # Compute LOC delta from files created + modified
        loc_delta = 0
        files_created = 0
        files_modified = 0

        if hasattr(result, "files_created"):
            files_created = len(result.files_created)
            # Estimate LOC per new file using cost if available
            if hasattr(result, "cost") and result.cost is not None:
                loc_delta = int(result.cost.loc)
            else:
                loc_delta = files_created * 50  # conservative estimate

        if hasattr(result, "files_modified"):
            files_modified = len(result.files_modified)

        # Count dependencies from cost
        deps_added = 0
        if hasattr(result, "cost") and result.cost is not None:
            deps_added = max(0, int(result.cost.dependencies))

        cost_total = 0.0
        if hasattr(result, "cost") and result.cost is not None:
            cost_total = float(result.cost.total)

        success = bool(getattr(result, "success", False))

        # Update cumulative state
        self.state.used_loc += loc_delta
        self.state.used_files += files_created
        self.state.used_dependencies += deps_added
        self.state.total_cost += cost_total
        self.state.total_builds += 1
        if success:
            self.state.successful_builds += 1
        self.state.last_updated = datetime.now().isoformat()

        # Append entry to history
        entry = BudgetEntry(
            session_id=session_id or "",
            intent=intent,
            timestamp=datetime.now().isoformat(),
            loc_used=loc_delta,
            files_created=files_created,
            files_modified=files_modified,
            dependencies_added=deps_added,
            cost_total=cost_total,
            success=success,
        )
        self.state.entries.append(entry.to_dict())

        self.save()

    def reset(self):
        """Reset all budget consumption counters (keeps policy limits)."""
        self.state.used_loc = 0
        self.state.used_files = 0
        self.state.used_dependencies = 0
        self.state.used_modules = 0
        self.state.total_cost = 0.0
        self.state.total_builds = 0
        self.state.successful_builds = 0
        self.state.last_updated = datetime.now().isoformat()
        self.state.entries = []
        self.save()

    # ------------------------------------------------------------------ #
    # Query helpers                                                        #
    # ------------------------------------------------------------------ #

    def get_usage_pct(self, metric: str) -> float:
        """Return usage percentage for a metric (0.0 – 1.0)."""
        mapping = {
            "loc": (self.state.used_loc, self.state.policy_max_loc),
            "files": (self.state.used_files, self.state.policy_max_files),
            "dependencies": (self.state.used_dependencies, self.state.policy_max_dependencies),
            "modules": (self.state.used_modules, self.state.policy_max_modules),
        }
        used, total = mapping.get(metric, (0, 1))
        return used / total if total > 0 else 0.0

    def is_near_limit(self, threshold: float = 0.80) -> bool:
        """Return True if any metric exceeds *threshold* of its budget."""
        return any(
            self.get_usage_pct(m) >= threshold
            for m in ("loc", "files", "dependencies")
        )

    def budget_remaining(self) -> Dict[str, int]:
        """Return remaining budget for each metric."""
        return {
            "loc": max(0, self.state.policy_max_loc - self.state.used_loc),
            "files": max(0, self.state.policy_max_files - self.state.used_files),
            "dependencies": max(0, self.state.policy_max_dependencies - self.state.used_dependencies),
            "modules": max(0, self.state.policy_max_modules - self.state.used_modules),
        }

    # ------------------------------------------------------------------ #
    # Rendering                                                            #
    # ------------------------------------------------------------------ #

    def format_dashboard(self, use_color: bool = True, verbose: bool = False) -> str:
        """
        Render the full budget dashboard as a string.

        Args:
            use_color: Include ANSI color codes
            verbose: Include per-session history

        Returns:
            Multi-line string ready to print
        """
        s = self.state
        lines = []

        # ── Header ──────────────────────────────────────────────────────
        bold = ProgressBar.BOLD if use_color else ""
        reset = ProgressBar.RESET if use_color else ""
        lines.append(f"\n{bold}╔══════════════════════════════════════════════════════════╗{reset}")
        lines.append(f"{bold}║              📊  AUREUS BUDGET DASHBOARD                 ║{reset}")
        lines.append(f"{bold}╚══════════════════════════════════════════════════════════╝{reset}")

        # ── Progress bars ────────────────────────────────────────────────
        lines.append("")
        lines.append(f"  {'Metric':<14}  {'Progress Bar':<24}  {'Used / Limit':>22}   {'Status'}")
        lines.append("  " + "─" * 78)

        lines.append(ProgressBar.render(
            "Lines of Code", s.used_loc, s.policy_max_loc, use_color=use_color
        ))
        lines.append(ProgressBar.render(
            "Files", s.used_files, s.policy_max_files, use_color=use_color
        ))
        lines.append(ProgressBar.render(
            "Dependencies", s.used_dependencies, s.policy_max_dependencies, use_color=use_color
        ))
        lines.append(ProgressBar.render(
            "Modules", s.used_modules, s.policy_max_modules, use_color=use_color
        ))

        # ── Summary ──────────────────────────────────────────────────────
        lines.append("")
        lines.append("  " + "─" * 78)
        lines.append(f"  {'Total Builds:':<22} {s.total_builds}")
        lines.append(f"  {'Successful Builds:':<22} {s.successful_builds}")
        lines.append(f"  {'Total Cost Score:':<22} {s.total_cost:,.1f}")
        if s.last_updated:
            ts = s.last_updated[:19].replace("T", " ")
            lines.append(f"  {'Last Updated:':<22} {ts}")

        # ── Warnings ─────────────────────────────────────────────────────
        warnings = self._build_warnings()
        if warnings:
            lines.append("")
            lines.append(f"  {'⚠️  BUDGET WARNINGS':}")
            for w in warnings:
                lines.append(f"    • {w}")

        # ── History (verbose) ────────────────────────────────────────────
        if verbose and s.entries:
            lines.append("")
            lines.append(f"  {'Recent Build History':}")
            lines.append(f"  {'─'*78}")
            for entry_dict in s.entries[-10:]:
                entry = BudgetEntry.from_dict(entry_dict)
                ts = entry.timestamp[:19].replace("T", " ")
                status = "✅" if entry.success else "❌"
                intent_short = (entry.intent[:40] + "…") if len(entry.intent) > 41 else entry.intent
                lines.append(
                    f"  {status}  {ts}  +{entry.loc_used:>5} LOC"
                    f"  +{entry.files_created} files  {intent_short!r}"
                )

        lines.append("")
        return "\n".join(lines)

    def format_post_build_summary(self, use_color: bool = True) -> str:
        """
        Compact budget summary to append after each 'aureus code' run.

        Returns:
            2–5 line string ready to print below build results
        """
        s = self.state
        bold = ProgressBar.BOLD if use_color else ""
        reset = ProgressBar.RESET if use_color else ""
        lines = []

        lines.append(f"\n{bold}📊 Budget Remaining:{reset}")
        lines.append(ProgressBar.render_compact("Lines of Code", s.used_loc, s.policy_max_loc, use_color=use_color))
        lines.append(ProgressBar.render_compact("Files", s.used_files, s.policy_max_files, use_color=use_color))
        lines.append(ProgressBar.render_compact("Dependencies", s.used_dependencies, s.policy_max_dependencies, use_color=use_color))

        warnings = self._build_warnings()
        if warnings:
            yellow = ProgressBar.YELLOW if use_color else ""
            for w in warnings:
                lines.append(f"  {yellow}⚠️  {w}{reset}")

        lines.append("")
        return "\n".join(lines)

    # ------------------------------------------------------------------ #
    # Internal helpers                                                     #
    # ------------------------------------------------------------------ #

    def _build_warnings(self) -> List[str]:
        """Return list of warning strings for metrics approaching limits."""
        warnings = []
        checks = [
            ("loc", "Lines of Code", self.state.used_loc, self.state.policy_max_loc),
            ("files", "Files", self.state.used_files, self.state.policy_max_files),
            ("dependencies", "Dependencies", self.state.used_dependencies, self.state.policy_max_dependencies),
        ]
        for _, label, used, total in checks:
            if total <= 0:
                continue
            pct = used / total
            remaining = total - used
            if pct >= 0.90:
                warnings.append(
                    f"CRITICAL: {label} at {pct*100:.0f}% capacity "
                    f"({remaining:,} remaining of {total:,})"
                )
            elif pct >= 0.70:
                warnings.append(
                    f"{label} at {pct*100:.0f}% capacity "
                    f"({remaining:,} remaining of {total:,}) — consider refactoring"
                )
        return warnings


# ============================================================================
# Convenience functions
# ============================================================================

def print_budget_dashboard(
    project_root: Path,
    policy=None,
    use_color: bool = True,
    verbose: bool = False,
) -> None:
    """Load and print the full budget dashboard."""
    dashboard = BudgetDashboard(project_root, policy)
    print(dashboard.format_dashboard(use_color=use_color, verbose=verbose))


def print_post_build_summary(
    project_root: Path,
    policy=None,
    use_color: bool = True,
) -> None:
    """Print compact budget summary (call after each build)."""
    dashboard = BudgetDashboard(project_root, policy)
    print(dashboard.format_post_build_summary(use_color=use_color))
