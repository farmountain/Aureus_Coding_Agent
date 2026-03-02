"""
Progress Indicators - Sprint 1 Item 5

Real-time feedback for long-running operations in the AUREUS CLI.

Provides:
- Animated spinners for indeterminate progress
- Progress bars for determinate operations
- Phase status tracking (Specification → Cost → Code)
- Elapsed time and ETA display
- Clean terminal updates without flickering
"""

import sys
import time
import threading
from typing import Optional, Callable, Any
from dataclasses import dataclass
from datetime import datetime, timedelta


# ============================================================================
# Progress Data Structures
# ============================================================================

@dataclass
class PhaseProgress:
    """Progress state for a single phase of work."""
    name: str
    status: str  # "pending", "running", "complete", "failed"
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    progress_pct: float = 0.0  # 0.0 - 1.0
    message: str = ""

    @property
    def duration(self) -> Optional[float]:
        """Return elapsed time in seconds if phase has started."""
        if self.start_time is None:
            return None
        end = self.end_time or time.time()
        return end - self.start_time

    @property
    def is_active(self) -> bool:
        return self.status == "running"


# ============================================================================
# Spinner Animation
# ============================================================================

class Spinner:
    """
    Animated spinner for indeterminate progress.
    
    Example output:
        ⠋ Generating specification...
        ⠙ Generating specification...
        ⠹ Generating specification...
    """
    
    # Unicode Braille patterns for smooth animation
    FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    
    # Alternative frame sets
    DOTS = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    ARROWS = ["←", "↖", "↑", "↗", "→", "↘", "↓", "↙"]
    SIMPLE = ["|", "/", "-", "\\"]
    
    def __init__(self, message: str = "", frame_set: str = "dots"):
        self.message = message
        self.frame_idx = 0
        
        if frame_set == "arrows":
            self.frames = self.ARROWS
        elif frame_set == "simple":
            self.frames = self.SIMPLE
        else:
            self.frames = self.DOTS
        
        self.running = False
        self.thread: Optional[threading.Thread] = None
    
    def start(self):
        """Start the spinner animation in a background thread."""
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._animate, daemon=True)
        self.thread.start()
    
    def stop(self, final_message: str = ""):
        """Stop the spinner and optionally print a final message."""
        if not self.running:
            return
        self.running = False
        if self.thread:
            self.thread.join(timeout=0.5)
        # Clear the line
        sys.stdout.write("\r" + " " * 80 + "\r")
        sys.stdout.flush()
        if final_message:
            print(final_message)
    
    def update_message(self, message: str):
        """Update the spinner message while it's running."""
        self.message = message
    
    def _animate(self):
        """Background animation loop."""
        while self.running:
            frame = self.frames[self.frame_idx]
            sys.stdout.write(f"\r{frame} {self.message}")
            sys.stdout.flush()
            self.frame_idx = (self.frame_idx + 1) % len(self.frames)
            time.sleep(0.1)


# ============================================================================
# Progress Bar
# ============================================================================

class ProgressBar:
    """
    ASCII progress bar for determinate operations.
    
    Example output:
        [████████████░░░░░░░░]  60%  (12.5s elapsed, ~8.3s remaining)
    """
    
    BAR_WIDTH = 20
    FILL_CHAR = "█"
    EMPTY_CHAR = "░"
    
    def __init__(
        self,
        total: int = 100,
        prefix: str = "",
        show_time: bool = True,
        use_color: bool = True,
    ):
        self.total = total
        self.current = 0
        self.prefix = prefix
        self.show_time = show_time
        self.use_color = use_color
        self.start_time = time.time()
        self.last_update = 0.0
    
    def update(self, current: int, message: str = ""):
        """Update progress bar to current value."""
        self.current = min(current, self.total)
        
        # Throttle updates to avoid flickering (max 10 fps)
        now = time.time()
        if now - self.last_update < 0.1 and current < self.total:
            return
        self.last_update = now
        
        self._render(message)
    
    def _render(self, message: str = ""):
        """Render the progress bar to stdout."""
        pct = self.current / self.total if self.total > 0 else 0
        filled = int(pct * self.BAR_WIDTH)
        bar = self.FILL_CHAR * filled + self.EMPTY_CHAR * (self.BAR_WIDTH - filled)
        
        # Time information
        elapsed = time.time() - self.start_time
        time_str = ""
        if self.show_time and elapsed > 1.0:
            if pct > 0.05:  # Only show ETA if we have some progress
                total_time = elapsed / pct
                remaining = total_time - elapsed
                time_str = f"  ({elapsed:.1f}s elapsed, ~{remaining:.1f}s remaining)"
            else:
                time_str = f"  ({elapsed:.1f}s elapsed)"
        
        # Color coding
        color = ""
        reset = ""
        if self.use_color:
            if pct >= 0.9:
                color = "\033[92m"  # Green
            elif pct >= 0.5:
                color = "\033[93m"  # Yellow
            else:
                color = "\033[94m"  # Blue
            reset = "\033[0m"
        
        # Build output line
        prefix_str = f"{self.prefix} " if self.prefix else ""
        msg_str = f"  {message}" if message else ""
        line = f"\r{prefix_str}{color}[{bar}]{reset}  {pct*100:5.1f}%{time_str}{msg_str}"
        
        # Pad to clear any previous longer messages
        line = line.ljust(100)
        
        sys.stdout.write(line)
        sys.stdout.flush()
    
    def finish(self, message: str = "✓ Complete"):
        """Mark progress as 100% complete and print final message."""
        self.update(self.total, message)
        print()  # New line after completion


# ============================================================================
# Multi-Phase Progress Tracker
# ============================================================================

class MultiPhaseProgress:
    """
    Tracks progress across multiple sequential phases.
    
    Example output:
        Phase 1/3: Specification Generation    [████████████████████]  100%  ✓ Complete
        Phase 2/3: Cost Analysis              [████████░░░░░░░░░░░░]   40%  Analyzing...
        Phase 3/3: Code Generation            [░░░░░░░░░░░░░░░░░░░░]    0%  Waiting...
        
        Overall: [█████████░░░░░░░░░░░]  46%  (15.3s elapsed)
    """
    
    def __init__(self, phases: list[str], use_color: bool = True):
        self.phases = [PhaseProgress(name, "pending") for name in phases]
        self.use_color = use_color
        self.start_time = time.time()
        self.current_phase_idx = 0
    
    def start_phase(self, phase_idx: int, message: str = ""):
        """Start a specific phase."""
        if 0 <= phase_idx < len(self.phases):
            phase = self.phases[phase_idx]
            phase.status = "running"
            phase.start_time = time.time()
            phase.message = message or f"Running {phase.name}..."
            self.current_phase_idx = phase_idx
            self._render()
    
    def update_phase(self, phase_idx: int, progress_pct: float, message: str = ""):
        """Update progress for a specific phase (0.0 - 1.0)."""
        if 0 <= phase_idx < len(self.phases):
            phase = self.phases[phase_idx]
            phase.progress_pct = min(progress_pct, 1.0)
            if message:
                phase.message = message
            self._render()
    
    def complete_phase(self, phase_idx: int, message: str = "✓ Complete"):
        """Mark a phase as complete."""
        if 0 <= phase_idx < len(self.phases):
            phase = self.phases[phase_idx]
            phase.status = "complete"
            phase.end_time = time.time()
            phase.progress_pct = 1.0
            phase.message = message
            self._render()
    
    def fail_phase(self, phase_idx: int, message: str = "✗ Failed"):
        """Mark a phase as failed."""
        if 0 <= phase_idx < len(self.phases):
            phase = self.phases[phase_idx]
            phase.status = "failed"
            phase.end_time = time.time()
            phase.message = message
            self._render()
    
    def _render(self):
        """Render all phases to stdout."""
        # Clear previous output (move cursor up if needed)
        # For simplicity, we'll just print new state each time
        
        lines = []
        
        for idx, phase in enumerate(self.phases):
            # Phase number and name
            phase_label = f"Phase {idx+1}/{len(self.phases)}: {phase.name:<30}"
            
            # Progress bar
            filled = int(phase.progress_pct * 20)
            bar = "█" * filled + "░" * (20 - filled)
            
            # Status icon
            if phase.status == "complete":
                icon = "✓"
                color = "\033[92m" if self.use_color else ""
            elif phase.status == "failed":
                icon = "✗"
                color = "\033[91m" if self.use_color else ""
            elif phase.status == "running":
                icon = "⟳"
                color = "\033[93m" if self.use_color else ""
            else:  # pending
                icon = "·"
                color = "\033[90m" if self.use_color else ""
            
            reset = "\033[0m" if self.use_color else ""
            
            # Time for active phase
            time_str = ""
            if phase.duration is not None and phase.duration > 1.0:
                time_str = f"  ({phase.duration:.1f}s)"
            
            line = f"  {phase_label}  {color}[{bar}]{reset}  {phase.progress_pct*100:5.1f}%  {icon}  {phase.message}{time_str}"
            lines.append(line)
        
        # Overall progress
        overall_pct = sum(p.progress_pct for p in self.phases) / len(self.phases)
        overall_filled = int(overall_pct * 20)
        overall_bar = "█" * overall_filled + "░" * (20 - overall_filled)
        elapsed = time.time() - self.start_time
        
        lines.append("")
        lines.append(f"  Overall: [{overall_bar}]  {overall_pct*100:5.1f}%  ({elapsed:.1f}s elapsed)")
        
        # Print (overwriting previous output would require ANSI escape codes)
        sys.stdout.write("\r" + "\n".join(lines) + "\n")
        sys.stdout.flush()
    
    def finish(self, message: str = "✓ All phases complete"):
        """Mark all phases as complete and print final summary."""
        elapsed = time.time() - self.start_time
        print(f"\n{message}  (Total time: {elapsed:.1f}s)")


# ============================================================================
# Simple Progress Reporter (for callbacks)
# ============================================================================

class ProgressReporter:
    """
    Simple progress reporter that prints periodic updates.
    
    Used as a callback for operations that report (current, total) progress.
    """
    
    def __init__(self, prefix: str = "Progress", use_spinner: bool = False):
        self.prefix = prefix
        self.use_spinner = use_spinner
        self.spinner: Optional[Spinner] = None
        self.last_pct = -1
        
        if use_spinner:
            self.spinner = Spinner(prefix)
            self.spinner.start()
    
    def update(self, current: int, total: int):
        """Progress callback: (current, total)."""
        pct = int((current / total * 100)) if total > 0 else 0
        
        # Only print if percentage changed (avoid spam)
        if pct != self.last_pct:
            self.last_pct = pct
            if self.spinner:
                self.spinner.update_message(f"{self.prefix}  {pct}%")
            else:
                sys.stdout.write(f"\r{self.prefix}  {pct}%")
                sys.stdout.flush()
    
    def finish(self, message: str = "✓ Complete"):
        """Mark complete."""
        if self.spinner:
            self.spinner.stop(message)
        else:
            print(f"\r{self.prefix}  100%  {message}")


# ============================================================================
# Convenience Functions
# ============================================================================

def with_spinner(func: Callable, message: str, *args, **kwargs) -> Any:
    """
    Execute a function with a spinner animation.
    
    Example:
        result = with_spinner(expensive_function, "Processing...", arg1, arg2)
    """
    spinner = Spinner(message)
    spinner.start()
    try:
        result = func(*args, **kwargs)
        spinner.stop(f"✓ {message} complete")
        return result
    except Exception as e:
        spinner.stop(f"✗ {message} failed")
        raise


def with_progress_bar(
    items: list,
    func: Callable,
    message: str = "Processing",
    use_color: bool = True,
) -> list:
    """
    Process a list of items with a progress bar.
    
    Example:
        results = with_progress_bar(files, process_file, "Processing files")
    """
    bar = ProgressBar(total=len(items), prefix=message, use_color=use_color)
    results = []
    
    for idx, item in enumerate(items):
        result = func(item)
        results.append(result)
        bar.update(idx + 1)
    
    bar.finish()
    return results
