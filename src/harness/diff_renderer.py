"""
Diff Renderer

Streaming diff display for file changes.
"""

from typing import List, Dict, Any
from dataclasses import dataclass
from enum import Enum


class DiffType(Enum):
    """Type of diff operation"""
    ADD = "add"
    REMOVE = "remove"
    MODIFY = "modify"


@dataclass
class FileDiff:
    """Represents a file change"""
    path: str
    diff_type: DiffType
    before_content: str = ""
    after_content: str = ""
    lines_added: int = 0
    lines_removed: int = 0


class DiffRenderer:
    """
    Renders file diffs for user review.
    
    Supports:
    - Side-by-side comparison
    - Syntax highlighting (future)
    - Streaming output
    """
    
    def __init__(self, colored: bool = True):
        """
        Initialize diff renderer.
        
        Args:
            colored: Enable colored output
        """
        self.colored = colored
    
    def render_diff(self, diff: FileDiff) -> str:
        """
        Render a single file diff.
        
        Args:
            diff: File diff to render
        
        Returns:
            Formatted diff string
        """
        lines = []
        
        # Header
        lines.append(f"\n{'=' * 60}")
        lines.append(f"File: {diff.path}")
        lines.append(f"Type: {diff.diff_type.value}")
        
        if diff.diff_type == DiffType.ADD:
            lines.append(f"Lines: +{diff.lines_added}")
            lines.append(f"{'=' * 60}")
            lines.append(self._color_text(diff.after_content, "green"))
        
        elif diff.diff_type == DiffType.REMOVE:
            lines.append(f"Lines: -{diff.lines_removed}")
            lines.append(f"{'=' * 60}")
            lines.append(self._color_text(diff.before_content, "red"))
        
        elif diff.diff_type == DiffType.MODIFY:
            lines.append(f"Lines: +{diff.lines_added} -{diff.lines_removed}")
            lines.append(f"{'=' * 60}")
            lines.append("BEFORE:")
            lines.append(self._color_text(diff.before_content, "red"))
            lines.append("\nAFTER:")
            lines.append(self._color_text(diff.after_content, "green"))
        
        lines.append(f"{'=' * 60}\n")
        
        return "\n".join(lines)
    
    def render_diffs(self, diffs: List[FileDiff]) -> str:
        """
        Render multiple file diffs.
        
        Args:
            diffs: List of file diffs
        
        Returns:
            Formatted diffs string
        """
        if not diffs:
            return "No changes"
        
        output = []
        output.append(f"\n{'#' * 60}")
        output.append(f"CHANGES SUMMARY: {len(diffs)} file(s)")
        output.append(f"{'#' * 60}")
        
        for diff in diffs:
            output.append(self.render_diff(diff))
        
        # Summary
        total_added = sum(d.lines_added for d in diffs)
        total_removed = sum(d.lines_removed for d in diffs)
        output.append(f"\nTOTAL: +{total_added} -{total_removed} lines")
        
        return "\n".join(output)
    
    def render_changes_from_plan(self, changes: List[Dict[str, Any]]) -> str:
        """
        Render changes from execution plan.
        
        Args:
            changes: List of planned changes
        
        Returns:
            Formatted changes string
        """
        diffs = []
        
        for change in changes:
            change_type = change.get("type", "unknown")
            
            if change_type == "file_create":
                diffs.append(FileDiff(
                    path=change.get("path", "unknown"),
                    diff_type=DiffType.ADD,
                    after_content=change.get("content", ""),
                    lines_added=change.get("estimated_loc", 0)
                ))
            
            elif change_type == "file_delete":
                diffs.append(FileDiff(
                    path=change.get("path", "unknown"),
                    diff_type=DiffType.REMOVE,
                    before_content=change.get("content", ""),
                    lines_removed=change.get("estimated_loc", 0)
                ))
            
            elif change_type == "file_modify":
                diffs.append(FileDiff(
                    path=change.get("path", "unknown"),
                    diff_type=DiffType.MODIFY,
                    before_content=change.get("before", ""),
                    after_content=change.get("after", ""),
                    lines_added=change.get("lines_added", 0),
                    lines_removed=change.get("lines_removed", 0)
                ))
        
        return self.render_diffs(diffs)
    
    def _color_text(self, text: str, color: str) -> str:
        """
        Apply color to text if coloring is enabled.
        
        Args:
            text: Text to color
            color: Color name (red/green/yellow)
        
        Returns:
            Colored text or original text
        """
        if not self.colored:
            return text
        
        # ANSI color codes
        colors = {
            "red": "\033[91m",
            "green": "\033[92m",
            "yellow": "\033[93m",
            "blue": "\033[94m",
            "reset": "\033[0m"
        }
        
        color_code = colors.get(color, colors["reset"])
        return f"{color_code}{text}{colors['reset']}"
    
    def stream_diff(self, diff: FileDiff) -> None:
        """
        Stream diff output line-by-line.
        
        Args:
            diff: File diff to stream
        """
        print(self.render_diff(diff))
