"""
Trajectory Storage System

Stores session trajectories including actions, decisions, and outcomes.
Enables learning from past sessions and context building.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
import json
import uuid


@dataclass
class ActionRecord:
    """Single action in a trajectory"""
    phase: str  # gather, act, verify, reflexion
    tool: str  # tool name used
    input: Dict[str, Any]  # tool input
    output: Any  # tool output
    cost: float  # action cost
    success: bool  # whether action succeeded
    timestamp: datetime = field(default_factory=datetime.now)
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        d = asdict(self)
        d['timestamp'] = self.timestamp.isoformat()
        return d
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'ActionRecord':
        """Create from dictionary"""
        data = data.copy()
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return ActionRecord(**data)


@dataclass
class SessionTrajectory:
    """Complete trajectory for a coding session"""
    session_id: str
    intent: str  # User's high-level goal
    start_time: datetime
    end_time: Optional[datetime] = None
    actions: List[ActionRecord] = field(default_factory=list)
    success: bool = False
    total_cost: float = 0.0
    outcome: Optional[str] = None  # Final outcome description
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'session_id': self.session_id,
            'intent': self.intent,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'actions': [a.to_dict() for a in self.actions],
            'success': self.success,
            'total_cost': self.total_cost,
            'outcome': self.outcome
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'SessionTrajectory':
        """Create from dictionary"""
        return SessionTrajectory(
            session_id=data['session_id'],
            intent=data['intent'],
            start_time=datetime.fromisoformat(data['start_time']),
            end_time=datetime.fromisoformat(data['end_time']) if data.get('end_time') else None,
            actions=[ActionRecord.from_dict(a) for a in data.get('actions', [])],
            success=data.get('success', False),
            total_cost=data.get('total_cost', 0.0),
            outcome=data.get('outcome')
        )


class TrajectoryStore:
    """
    Stores and retrieves session trajectories
    
    Provides persistent storage of all actions taken during sessions,
    enabling learning from past behavior and context building.
    """
    
    def __init__(self, storage_dir: Path):
        """
        Initialize trajectory store
        
        Args:
            storage_dir: Directory to store trajectory files
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._active_sessions: Dict[str, SessionTrajectory] = {}
    
    def start_session(self, intent: str) -> SessionTrajectory:
        """
        Start a new trajectory session
        
        Args:
            intent: High-level goal for this session
            
        Returns:
            New session trajectory
        """
        session_id = str(uuid.uuid4())
        session = SessionTrajectory(
            session_id=session_id,
            intent=intent,
            start_time=datetime.now()
        )
        
        self._active_sessions[session_id] = session
        return session
    
    def record_action(self, session_id: str, action: ActionRecord):
        """
        Record an action in the trajectory
        
        Args:
            session_id: Session identifier
            action: Action to record
        """
        if session_id not in self._active_sessions:
            # Try to load from disk
            session = self.get_session(session_id)
            if session is None:
                raise ValueError(f"Session {session_id} not found")
            self._active_sessions[session_id] = session
        
        self._active_sessions[session_id].actions.append(action)
        
        # Auto-save after each action
        self._save_session(session_id)
    
    def end_session(
        self,
        session_id: str,
        success: bool,
        total_cost: float,
        outcome: Optional[str] = None
    ):
        """
        End a trajectory session
        
        Args:
            session_id: Session identifier
            success: Whether session succeeded
            total_cost: Total cost incurred
            outcome: Final outcome description
        """
        if session_id not in self._active_sessions:
            session = self.get_session(session_id)
            if session is None:
                raise ValueError(f"Session {session_id} not found")
            self._active_sessions[session_id] = session
        
        session = self._active_sessions[session_id]
        session.end_time = datetime.now()
        session.success = success
        session.total_cost = total_cost
        session.outcome = outcome
        
        # Final save
        self._save_session(session_id)
        
        # Remove from active sessions
        del self._active_sessions[session_id]
    
    def get_session(self, session_id: str) -> Optional[SessionTrajectory]:
        """
        Retrieve a session trajectory
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session trajectory or None if not found
        """
        # Check active sessions first
        if session_id in self._active_sessions:
            return self._active_sessions[session_id]
        
        # Load from disk
        session_file = self.storage_dir / f"{session_id}.json"
        if not session_file.exists():
            return None
        
        with open(session_file, 'r') as f:
            data = json.load(f)
        
        return SessionTrajectory.from_dict(data)
    
    def list_sessions(self, limit: Optional[int] = None) -> List[SessionTrajectory]:
        """
        List all stored sessions
        
        Args:
            limit: Maximum number of sessions to return (most recent first)
            
        Returns:
            List of session trajectories
        """
        session_files = sorted(
            self.storage_dir.glob("*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        
        if limit:
            session_files = session_files[:limit]
        
        sessions = []
        for session_file in session_files:
            try:
                with open(session_file, 'r') as f:
                    data = json.load(f)
                # Ensure data is a dict, not a list
                if isinstance(data, dict):
                    sessions.append(SessionTrajectory.from_dict(data))
            except (json.JSONDecodeError, TypeError, KeyError) as e:
                # Skip malformed session files
                continue
        
        return sessions
    
    def _save_session(self, session_id: str):
        """Save session to disk"""
        session = self._active_sessions.get(session_id)
        if session is None:
            return
        
        session_file = self.storage_dir / f"{session_id}.json"
        with open(session_file, 'w') as f:
            json.dump(session.to_dict(), f, indent=2)
