"""
Cost Ledger System

Tracks all costs incurred during sessions for budget management and analysis.
"""

from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import json


@dataclass
class CostEntry:
    """Single cost entry"""
    session_id: str
    phase: str  # gather, act, verify, reflexion
    operation: str  # Specific operation type
    cost: float
    timestamp: datetime
    details: Optional[Dict] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        d = asdict(self)
        d['timestamp'] = self.timestamp.isoformat()
        return d
    
    @staticmethod
    def from_dict(data: Dict) -> 'CostEntry':
        """Create from dictionary"""
        data = data.copy()
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return CostEntry(**data)


class CostLedger:
    """
    Cost tracking ledger
    
    Maintains a persistent record of all costs incurred,
    enabling budget analysis and cost optimization.
    """
    
    def __init__(self, storage_path: Path):
        """
        Initialize cost ledger
        
        Args:
            storage_path: Path to ledger JSON file
        """
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.entries: List[CostEntry] = []
        
        # Load existing ledger
        if self.storage_path.exists():
            self.load()
    
    def record(self, entry: CostEntry):
        """
        Record a cost entry
        
        Args:
            entry: Cost entry to record
        """
        self.entries.append(entry)
        # Auto-save after each entry
        self.save()
    
    def get_total_cost(self) -> float:
        """Get total cost across all entries"""
        return sum(entry.cost for entry in self.entries)
    
    def get_session_costs(self, session_id: str) -> float:
        """
        Get total costs for a specific session
        
        Args:
            session_id: Session identifier
            
        Returns:
            Total cost for session
        """
        return sum(
            entry.cost
            for entry in self.entries
            if entry.session_id == session_id
        )
    
    def get_phase_costs(self, phase: str) -> float:
        """
        Get total costs for a specific phase
        
        Args:
            phase: Phase name (gather, act, verify, reflexion)
            
        Returns:
            Total cost for phase
        """
        return sum(
            entry.cost
            for entry in self.entries
            if entry.phase == phase
        )
    
    def get_operation_costs(self, operation: str) -> float:
        """
        Get total costs for a specific operation
        
        Args:
            operation: Operation name
            
        Returns:
            Total cost for operation
        """
        return sum(
            entry.cost
            for entry in self.entries
            if entry.operation == operation
        )
    
    def get_entries_by_session(self, session_id: str) -> List[CostEntry]:
        """
        Get all entries for a session
        
        Args:
            session_id: Session identifier
            
        Returns:
            List of cost entries
        """
        return [
            entry
            for entry in self.entries
            if entry.session_id == session_id
        ]
    
    def get_cost_breakdown(self) -> Dict[str, float]:
        """
        Get cost breakdown by phase
        
        Returns:
            Dictionary mapping phase to total cost
        """
        breakdown = {}
        for entry in self.entries:
            breakdown[entry.phase] = breakdown.get(entry.phase, 0.0) + entry.cost
        return breakdown
    
    def save(self):
        """Save ledger to disk"""
        with open(self.storage_path, 'w') as f:
            json.dump(
                [entry.to_dict() for entry in self.entries],
                f,
                indent=2
            )
    
    def load(self):
        """Load ledger from disk"""
        if not self.storage_path.exists():
            self.entries = []
            return
        
        with open(self.storage_path, 'r') as f:
            data = json.load(f)
        
        self.entries = [CostEntry.from_dict(entry) for entry in data]
