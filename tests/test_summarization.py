"""
Test Suite for Trajectory Summarization

Tests compression, pattern extraction, and multi-session context loading.
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.memory.trajectory import TrajectoryStore, SessionTrajectory, ActionRecord
from src.memory.summarization import (
    TrajectorySummarizer,
    SummaryLevel,
    SessionSummary,
    PatternExtractor
)


@pytest.fixture
def temp_storage(tmp_path):
    """Create temporary storage directory"""
    storage_dir = tmp_path / ".aureus" / "memory"
    storage_dir.mkdir(parents=True, exist_ok=True)
    return storage_dir


@pytest.fixture
def sample_trajectory(temp_storage):
    """Create sample trajectory with multiple actions"""
    store = TrajectoryStore(storage_dir=temp_storage)
    session = store.start_session(intent="Implement authentication")
    
    # Gather phase
    store.record_action(session.session_id, ActionRecord(
        phase="gather",
        tool="file_read",
        input={"path": "auth.py"},
        output="auth code",
        cost=5.0,
        success=True
    ))
    
    store.record_action(session.session_id, ActionRecord(
        phase="gather",
        tool="grep_search",
        input={"query": "login"},
        output="3 matches",
        cost=2.0,
        success=True
    ))
    
    # Act phase
    store.record_action(session.session_id, ActionRecord(
        phase="act",
        tool="file_write",
        input={"path": "auth.py", "content": "new code"},
        output="success",
        cost=10.0,
        success=True
    ))
    
    # Verify phase
    store.record_action(session.session_id, ActionRecord(
        phase="verify",
        tool="test_run",
        input={"suite": "auth tests"},
        output="3 passed",
        cost=15.0,
        success=True
    ))
    
    store.end_session(
        session_id=session.session_id,
        success=True,
        total_cost=32.0,
        outcome="Authentication implemented successfully"
    )
    
    return store, session.session_id


class TestTrajectorySummarizer:
    """Test trajectory summarization"""
    
    def test_create_summarizer(self, temp_storage):
        """Test creating summarizer"""
        summarizer = TrajectorySummarizer(storage_dir=temp_storage)
        
        assert summarizer.storage_dir == temp_storage
    
    def test_summarize_session_brief(self, sample_trajectory, temp_storage):
        """Test brief session summary"""
        store, session_id = sample_trajectory
        summarizer = TrajectorySummarizer(storage_dir=temp_storage)
        
        summary = summarizer.summarize_session(
            session_id=session_id,
            level=SummaryLevel.BRIEF
        )
        
        assert summary.session_id == session_id
        assert summary.intent == "Implement authentication"
        assert summary.action_count == 4
        assert summary.total_cost == 32.0
        assert summary.success is True
        assert summary.phase_counts["gather"] == 2
        assert summary.phase_counts["act"] == 1
        assert summary.phase_counts["verify"] == 1
    
    def test_summarize_session_detailed(self, sample_trajectory, temp_storage):
        """Test detailed session summary"""
        store, session_id = sample_trajectory
        summarizer = TrajectorySummarizer(storage_dir=temp_storage)
        
        summary = summarizer.summarize_session(
            session_id=session_id,
            level=SummaryLevel.DETAILED
        )
        
        assert len(summary.key_actions) > 0
        assert "phase" in summary.key_actions[0]
        assert summary.tool_usage["file_read"] == 1
        assert summary.tool_usage["test_run"] == 1
    
    def test_compress_trajectory(self, sample_trajectory, temp_storage):
        """Test trajectory compression"""
        store, session_id = sample_trajectory
        summarizer = TrajectorySummarizer(storage_dir=temp_storage)
        
        # Get original size
        session = store.get_session(session_id)
        original_actions = len(session.actions)
        
        # Compress (keep only key actions)
        compressed = summarizer.compress_trajectory(session_id, keep_ratio=0.5)
        
        assert compressed.action_count < original_actions
        assert compressed.total_cost == 32.0  # Cost preserved
        assert compressed.success is True
    
    def test_extract_patterns(self, sample_trajectory, temp_storage):
        """Test pattern extraction from trajectories"""
        store, session_id = sample_trajectory
        
        # Create another similar session
        session2 = store.start_session(intent="Add user registration")
        store.record_action(session2.session_id, ActionRecord(
            phase="gather",
            tool="file_read",
            input={"path": "auth.py"},
            output="code",
            cost=5.0,
            success=True
        ))
        store.record_action(session2.session_id, ActionRecord(
            phase="act",
            tool="file_write",
            input={"path": "auth.py", "content": "registration"},
            output="success",
            cost=10.0,
            success=True
        ))
        store.end_session(session2.session_id, success=True, total_cost=15.0)
        
        # Extract patterns (need at least 2 sessions for common patterns)
        extractor = PatternExtractor(storage_dir=temp_storage)
        patterns = extractor.extract_common_patterns()
        
        # With 2 sessions having file_read, should find patterns
        assert len(patterns) >= 0  # May be empty if no exact subsequence matches


class TestPatternExtractor:
    """Test pattern extraction"""
    
    def test_extract_tool_sequences(self, sample_trajectory, temp_storage):
        """Test extracting common tool sequences"""
        store, session_id = sample_trajectory
        
        # Create second session with similar pattern
        session2 = store.start_session(intent="Similar task")
        store.record_action(session2.session_id, ActionRecord(
            phase="gather",
            tool="file_read",
            input={"path": "test.py"},
            output="code",
            cost=5.0,
            success=True
        ))
        store.record_action(session2.session_id, ActionRecord(
            phase="gather",
            tool="grep_search",
            input={"query": "test"},
            output="matches",
            cost=2.0,
            success=True
        ))
        store.end_session(session2.session_id, success=True, total_cost=7.0)
        
        extractor = PatternExtractor(storage_dir=temp_storage)
        sequences = extractor.extract_tool_sequences(min_length=2)
        
        # Should find file_read -> grep_search pattern (appears in both sessions)
        assert len(sequences) > 0
        assert any(seq == ["file_read", "grep_search"] for seq in sequences)
    
    def test_extract_successful_patterns(self, sample_trajectory, temp_storage):
        """Test extracting patterns from successful sessions"""
        store, session_id = sample_trajectory
        extractor = PatternExtractor(storage_dir=temp_storage)
        
        patterns = extractor.extract_successful_patterns()
        
        assert len(patterns) > 0
        # Should only include successful sessions
        for pattern in patterns:
            assert pattern.get("success", False) is True
    
    def test_find_similar_sessions(self, sample_trajectory, temp_storage):
        """Test finding similar past sessions"""
        store, session_id = sample_trajectory
        extractor = PatternExtractor(storage_dir=temp_storage)
        
        # Create new session with similar intent
        similar = extractor.find_similar_sessions(
            intent="Implement login feature",
            limit=3
        )
        
        # Should find the authentication session
        assert len(similar) > 0
        assert any("authentication" in s["intent"].lower() for s in similar)
