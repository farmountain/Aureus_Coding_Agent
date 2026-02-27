"""
Architectural Decision Record (ADR) Generator

Generates and manages ADRs documenting key architectural decisions.
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional
import re


@dataclass
class ArchitecturalDecision:
    """Architectural decision record"""
    title: str
    context: str
    decision: str
    consequences: List[str]
    alternatives: List[str]
    status: str = "accepted"  # accepted, superseded, deprecated
    date: Optional[datetime] = None
    
    def __post_init__(self):
        if self.date is None:
            self.date = datetime.now()


class ADRGenerator:
    """
    Generates Architectural Decision Records
    
    Creates structured markdown documents capturing key architectural
    decisions, their context, and trade-offs.
    """
    
    def __init__(self, adr_dir: Path):
        """
        Initialize ADR generator
        
        Args:
            adr_dir: Directory to store ADR files
        """
        self.adr_dir = Path(adr_dir)
        self.adr_dir.mkdir(parents=True, exist_ok=True)
    
    def generate(self, decision: ArchitecturalDecision) -> Path:
        """
        Generate an ADR document
        
        Args:
            decision: Architectural decision to document
            
        Returns:
            Path to generated ADR file
        """
        # Generate ADR number
        number = self._get_next_number()
        
        # Create filename from title
        filename = self._create_filename(number, decision.title)
        adr_path = self.adr_dir / filename
        
        # Generate content
        content = self._generate_content(number, decision)
        
        # Write file
        adr_path.write_text(content)
        
        return adr_path
    
    def list_adrs(self) -> List[Path]:
        """
        List all ADRs
        
        Returns:
            List of ADR file paths
        """
        return sorted(self.adr_dir.glob("*.md"))
    
    def get_adr(self, number: int) -> Optional[Path]:
        """
        Get ADR by number
        
        Args:
            number: ADR number
            
        Returns:
            Path to ADR file or None
        """
        pattern = f"{number:04d}-*.md"
        matches = list(self.adr_dir.glob(pattern))
        return matches[0] if matches else None
    
    def _get_next_number(self) -> int:
        """Get next ADR number"""
        existing_adrs = self.list_adrs()
        
        if not existing_adrs:
            return 1
        
        # Extract numbers from filenames
        numbers = []
        for adr_path in existing_adrs:
            match = re.match(r'(\d+)-', adr_path.name)
            if match:
                numbers.append(int(match.group(1)))
        
        return max(numbers, default=0) + 1
    
    def _create_filename(self, number: int, title: str) -> str:
        """Create ADR filename from number and title"""
        # Slugify title
        slug = title.lower()
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[-\s]+', '-', slug)
        
        return f"{number:04d}-{slug}.md"
    
    def _generate_content(
        self,
        number: int,
        decision: ArchitecturalDecision
    ) -> str:
        """Generate ADR markdown content"""
        lines = [
            f"# {number}. {decision.title}",
            "",
            f"Date: {decision.date.strftime('%Y-%m-%d')}",
            "",
            f"Status: {decision.status}",
            "",
            "## Context",
            "",
            decision.context,
            "",
            "## Decision",
            "",
            decision.decision,
            "",
            "## Consequences",
            "",
        ]
        
        for consequence in decision.consequences:
            lines.append(f"- {consequence}")
        
        lines.extend([
            "",
            "## Alternatives Considered",
            "",
        ])
        
        for alternative in decision.alternatives:
            lines.append(f"- {alternative}")
        
        lines.append("")
        
        return "\n".join(lines)
