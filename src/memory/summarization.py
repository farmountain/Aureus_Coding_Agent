"""
Trajectory Summarization System

Compresses and extracts patterns from trajectories to reduce memory usage
and enable learning from past sessions.
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from enum import Enum
from collections import Counter, defaultdict
import json

from src.memory.trajectory import TrajectoryStore, SessionTrajectory, ActionRecord


class SummaryLevel(Enum):
    """Summary detail level"""
    BRIEF = "brief"  # Just stats
    DETAILED = "detailed"  # Include key actions
    FULL = "full"  # Complete trajectory


@dataclass
class SessionSummary:
    """Compressed session summary"""
    session_id: str
    intent: str
    start_time: datetime
    end_time: Optional[datetime]
    action_count: int
    total_cost: float
    success: bool
    outcome: Optional[str]
    phase_counts: Dict[str, int]
    tool_usage: Dict[str, int]
    key_actions: List[Dict[str, Any]]  # Most important actions
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'session_id': self.session_id,
            'intent': self.intent,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'action_count': self.action_count,
            'total_cost': self.total_cost,
            'success': self.success,
            'outcome': self.outcome,
            'phase_counts': self.phase_counts,
            'tool_usage': self.tool_usage,
            'key_actions': self.key_actions
        }


class TrajectorySummarizer:
    """
    Compresses trajectories to reduce storage
    
    Applies compression algorithms to summarize long trajectories,
    keeping only essential information while preserving learnings.
    """
    
    def __init__(self, storage_dir: Path):
        """
        Initialize summarizer
        
        Args:
            storage_dir: Directory containing trajectory store
        """
        self.storage_dir = Path(storage_dir)
        self.store = TrajectoryStore(storage_dir=storage_dir)
    
    def summarize_session(
        self,
        session_id: str,
        level: SummaryLevel = SummaryLevel.DETAILED
    ) -> SessionSummary:
        """
        Create a summary of a session
        
        Args:
            session_id: Session to summarize
            level: Level of detail to include
            
        Returns:
            Session summary
        """
        session = self.store.get_session(session_id)
        if session is None:
            raise ValueError(f"Session {session_id} not found")
        
        # Count phases
        phase_counts = Counter(action.phase for action in session.actions)
        
        # Count tool usage
        tool_usage = Counter(action.tool for action in session.actions)
        
        # Extract key actions based on level
        if level == SummaryLevel.BRIEF:
            key_actions = []
        elif level == SummaryLevel.DETAILED:
            key_actions = self._extract_key_actions(session)
        else:  # FULL
            key_actions = [action.to_dict() for action in session.actions]
        
        return SessionSummary(
            session_id=session.session_id,
            intent=session.intent,
            start_time=session.start_time,
            end_time=session.end_time,
            action_count=len(session.actions),
            total_cost=session.total_cost,
            success=session.success,
            outcome=session.outcome,
            phase_counts=dict(phase_counts),
            tool_usage=dict(tool_usage),
            key_actions=key_actions
        )
    
    def compress_trajectory(
        self,
        session_id: str,
        keep_ratio: float = 0.3
    ) -> SessionSummary:
        """
        Compress a trajectory by keeping only most important actions
        
        Args:
            session_id: Session to compress
            keep_ratio: Ratio of actions to keep (0.0-1.0)
            
        Returns:
            Compressed session summary
        """
        session = self.store.get_session(session_id)
        if session is None:
            raise ValueError(f"Session {session_id} not found")
        
        # Rank actions by importance
        ranked_actions = self._rank_actions(session.actions)
        
        # Keep top N actions
        keep_count = max(1, int(len(ranked_actions) * keep_ratio))
        key_actions = ranked_actions[:keep_count]
        
        # Create summary with compressed actions
        return SessionSummary(
            session_id=session.session_id,
            intent=session.intent,
            start_time=session.start_time,
            end_time=session.end_time,
            action_count=len(key_actions),
            total_cost=session.total_cost,
            success=session.success,
            outcome=session.outcome,
            phase_counts=Counter(a['phase'] for a in key_actions),
            tool_usage=Counter(a['tool'] for a in key_actions),
            key_actions=key_actions
        )
    
    def _extract_key_actions(
        self,
        session: SessionTrajectory
    ) -> List[Dict[str, Any]]:
        """Extract most important actions from session"""
        # Keep first and last action of each phase
        key_actions = []
        actions_by_phase = defaultdict(list)
        
        for action in session.actions:
            actions_by_phase[action.phase].append(action)
        
        for phase, phase_actions in actions_by_phase.items():
            if phase_actions:
                # First action
                key_actions.append(phase_actions[0].to_dict())
                # Last action if different
                if len(phase_actions) > 1:
                    key_actions.append(phase_actions[-1].to_dict())
        
        # Keep any failed actions
        for action in session.actions:
            if not action.success:
                key_actions.append(action.to_dict())
        
        return key_actions
    
    def _rank_actions(
        self,
        actions: List[ActionRecord]
    ) -> List[Dict[str, Any]]:
        """
        Rank actions by importance
        
        Importance criteria:
        - High cost actions (more impactful)
        - Failed actions (learning opportunities)
        - Phase transitions (structural importance)
        - Unique tools (diversity)
        """
        scored_actions = []
        
        for i, action in enumerate(actions):
            score = 0.0
            
            # Cost score (normalized)
            score += action.cost / 100.0
            
            # Failure score (high value)
            if not action.success:
                score += 10.0
            
            # Phase transition score
            if i > 0 and actions[i-1].phase != action.phase:
                score += 5.0
            
            # First/last action bonus
            if i == 0 or i == len(actions) - 1:
                score += 3.0
            
            scored_actions.append((score, action.to_dict()))
        
        # Sort by score descending
        scored_actions.sort(key=lambda x: x[0], reverse=True)
        
        return [action_dict for score, action_dict in scored_actions]


class PatternExtractor:
    """
    Extracts common patterns from trajectories
    
    Identifies recurring patterns in successful sessions to guide
    future actions and improve efficiency.
    """
    
    def __init__(self, storage_dir: Path):
        """
        Initialize pattern extractor
        
        Args:
            storage_dir: Directory containing trajectory store
        """
        self.storage_dir = Path(storage_dir)
        self.store = TrajectoryStore(storage_dir=storage_dir)
    
    def extract_common_patterns(
        self,
        min_frequency: int = 2
    ) -> List[Dict[str, Any]]:
        """
        Extract common patterns across sessions
        
        Args:
            min_frequency: Minimum times a pattern must occur
            
        Returns:
            List of common patterns
        """
        sessions = self.store.list_sessions()
        
        # Extract tool sequences
        sequences = []
        for session in sessions:
            tools = [action.tool for action in session.actions]
            sequences.append(tools)
        
        # Find common subsequences
        patterns = self._find_common_subsequences(sequences, min_frequency)
        
        return patterns
    
    def extract_tool_sequences(
        self,
        min_length: int = 2
    ) -> List[List[str]]:
        """
        Extract common tool usage sequences
        
        Args:
            min_length: Minimum sequence length
            
        Returns:
            List of tool sequences
        """
        sessions = self.store.list_sessions()
        
        sequences = []
        for session in sessions:
            if session.success:
                tools = [action.tool for action in session.actions]
                # Extract subsequences
                for i in range(len(tools) - min_length + 1):
                    sequence = tools[i:i + min_length]
                    sequences.append(sequence)
        
        # Count frequency
        sequence_counts = Counter(tuple(seq) for seq in sequences)
        
        # Return frequent sequences
        return [
            list(seq)
            for seq, count in sequence_counts.items()
            if count >= 2
        ]
    
    def extract_successful_patterns(self) -> List[Dict[str, Any]]:
        """
        Extract patterns from successful sessions only
        
        Returns:
            List of successful patterns
        """
        sessions = self.store.list_sessions()
        
        patterns = []
        for session in sessions:
            if session.success:
                patterns.append({
                    'intent': session.intent,
                    'phase_sequence': [a.phase for a in session.actions],
                    'tool_sequence': [a.tool for a in session.actions],
                    'cost': session.total_cost,
                    'success': True
                })
        
        return patterns
    
    def find_similar_sessions(
        self,
        intent: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find sessions with similar intent
        
        Args:
            intent: Intent to match
            limit: Maximum number of results
            
        Returns:
            List of similar session summaries
        """
        sessions = self.store.list_sessions()
        
        # Simple keyword matching (can be enhanced with embeddings)
        intent_words = set(intent.lower().split())
        
        scored_sessions = []
        for session in sessions:
            session_words = set(session.intent.lower().split())
            overlap = len(intent_words & session_words)
            
            if overlap > 0:
                scored_sessions.append((overlap, {
                    'session_id': session.session_id,
                    'intent': session.intent,
                    'success': session.success,
                    'cost': session.total_cost,
                    'action_count': len(session.actions)
                }))
        
        # Sort by score
        scored_sessions.sort(key=lambda x: x[0], reverse=True)
        
        return [session_dict for score, session_dict in scored_sessions[:limit]]
    
    def _find_common_subsequences(
        self,
        sequences: List[List[str]],
        min_frequency: int
    ) -> List[Dict[str, Any]]:
        """Find common subsequences across multiple sequences"""
        # Count all 2-grams and 3-grams
        ngrams = defaultdict(int)
        
        for sequence in sequences:
            # 2-grams
            for i in range(len(sequence) - 1):
                bigram = tuple(sequence[i:i+2])
                ngrams[bigram] += 1
            
            # 3-grams
            for i in range(len(sequence) - 2):
                trigram = tuple(sequence[i:i+3])
                ngrams[trigram] += 1
        
        # Filter by frequency
        common = [
            {'pattern': list(ngram), 'frequency': count}
            for ngram, count in ngrams.items()
            if count >= min_frequency
        ]
        
        return common
