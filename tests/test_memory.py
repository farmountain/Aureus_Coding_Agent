"""
Test Suite for Memory System

Tests trajectory storage, cost ledger, and ADR generation.
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime
import json

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.memory.trajectory import TrajectoryStore, SessionTrajectory, ActionRecord
from src.memory.cost_ledger import CostLedger, CostEntry
from src.memory.adr import ADRGenerator, ArchitecturalDecision


@pytest.fixture
def temp_storage(tmp_path):
    """Create temporary storage directory"""
    storage_dir = tmp_path / ".aureus" / "memory"
    storage_dir.mkdir(parents=True, exist_ok=True)
    return storage_dir


class TestTrajectoryStore:
    """Test trajectory storage and retrieval"""
    
    def test_create_trajectory_store(self, temp_storage):
        """Test creating trajectory store"""
        store = TrajectoryStore(storage_dir=temp_storage)
        
        assert store.storage_dir == temp_storage
        assert store.storage_dir.exists()
    
    def test_start_new_session(self, temp_storage):
        """Test starting a new session"""
        store = TrajectoryStore(storage_dir=temp_storage)
        
        session = store.start_session(intent="Add hello function")
        
        assert session.session_id is not None
        assert session.intent == "Add hello function"
        assert session.start_time is not None
        assert len(session.actions) == 0
    
    def test_record_action(self, temp_storage):
        """Test recording an action in trajectory"""
        store = TrajectoryStore(storage_dir=temp_storage)
        session = store.start_session(intent="Test action")
        
        action = ActionRecord(
            phase="gather",
            tool="file_read",
            input={"path": "test.py"},
            output="content",
            cost=1.0,
            success=True
        )
        
        store.record_action(session.session_id, action)
        
        # Retrieve session
        retrieved = store.get_session(session.session_id)
        assert len(retrieved.actions) == 1
        assert retrieved.actions[0].tool == "file_read"
    
    def test_end_session(self, temp_storage):
        """Test ending a session"""
        store = TrajectoryStore(storage_dir=temp_storage)
        session = store.start_session(intent="Test completion")
        
        store.end_session(
            session_id=session.session_id,
            success=True,
            total_cost=50.0
        )
        
        retrieved = store.get_session(session.session_id)
        assert retrieved.end_time is not None
        assert retrieved.success is True
        assert retrieved.total_cost == 50.0
    
    def test_persist_session(self, temp_storage):
        """Test session persistence to disk"""
        store = TrajectoryStore(storage_dir=temp_storage)
        session = store.start_session(intent="Persistence test")
        store.end_session(session.session_id, success=True, total_cost=10.0)
        
        # Create new store instance
        new_store = TrajectoryStore(storage_dir=temp_storage)
        
        # Should be able to load previous session
        loaded = new_store.get_session(session.session_id)
        assert loaded.intent == "Persistence test"
        assert loaded.total_cost == 10.0
    
    def test_list_sessions(self, temp_storage):
        """Test listing all sessions"""
        store = TrajectoryStore(storage_dir=temp_storage)
        
        s1 = store.start_session(intent="Session 1")
        s2 = store.start_session(intent="Session 2")
        s3 = store.start_session(intent="Session 3")
        
        # End sessions to save them to disk
        store.end_session(s1.session_id, success=True, total_cost=10.0)
        store.end_session(s2.session_id, success=True, total_cost=20.0)
        store.end_session(s3.session_id, success=True, total_cost=30.0)
        
        sessions = store.list_sessions()
        
        assert len(sessions) >= 3


class TestCostLedger:
    """Test cost tracking and ledger"""
    
    def test_create_cost_ledger(self, temp_storage):
        """Test creating cost ledger"""
        ledger = CostLedger(storage_path=temp_storage / "costs.json")
        
        assert ledger.storage_path.parent.exists()
    
    def test_record_cost(self, temp_storage):
        """Test recording a cost entry"""
        ledger = CostLedger(storage_path=temp_storage / "costs.json")
        
        entry = CostEntry(
            session_id="test-123",
            phase="gather",
            operation="file_read",
            cost=5.0,
            timestamp=datetime.now()
        )
        
        ledger.record(entry)
        
        assert ledger.get_total_cost() == 5.0
    
    def test_get_costs_by_session(self, temp_storage):
        """Test retrieving costs for a session"""
        ledger = CostLedger(storage_path=temp_storage / "costs.json")
        
        ledger.record(CostEntry("session-1", "gather", "read", 10.0, datetime.now()))
        ledger.record(CostEntry("session-1", "act", "write", 20.0, datetime.now()))
        ledger.record(CostEntry("session-2", "gather", "read", 5.0, datetime.now()))
        
        session_costs = ledger.get_session_costs("session-1")
        
        assert session_costs == 30.0
    
    def test_get_costs_by_phase(self, temp_storage):
        """Test retrieving costs by phase"""
        ledger = CostLedger(storage_path=temp_storage / "costs.json")
        
        ledger.record(CostEntry("s1", "gather", "read", 10.0, datetime.now()))
        ledger.record(CostEntry("s2", "gather", "read", 15.0, datetime.now()))
        ledger.record(CostEntry("s3", "act", "write", 20.0, datetime.now()))
        
        gather_costs = ledger.get_phase_costs("gather")
        
        assert gather_costs == 25.0
    
    def test_ledger_persistence(self, temp_storage):
        """Test ledger persists to disk"""
        ledger_path = temp_storage / "costs.json"
        
        ledger1 = CostLedger(storage_path=ledger_path)
        ledger1.record(CostEntry("test", "gather", "read", 100.0, datetime.now()))
        ledger1.save()
        
        # Load in new instance
        ledger2 = CostLedger(storage_path=ledger_path)
        ledger2.load()
        
        assert ledger2.get_total_cost() == 100.0


class TestADRGenerator:
    """Test Architectural Decision Record generation"""
    
    def test_create_adr_generator(self, temp_storage):
        """Test creating ADR generator"""
        generator = ADRGenerator(adr_dir=temp_storage / "adrs")
        
        assert generator.adr_dir.exists()
    
    def test_generate_adr(self, temp_storage):
        """Test generating an ADR"""
        generator = ADRGenerator(adr_dir=temp_storage / "adrs")
        
        decision = ArchitecturalDecision(
            title="Use SQLite for local storage",
            context="Need lightweight persistent storage",
            decision="Use SQLite with JSON1 extension",
            consequences=["Simple deployment", "No server needed"],
            alternatives=["PostgreSQL", "File-based JSON"]
        )
        
        adr_path = generator.generate(decision)
        
        assert adr_path.exists()
        assert adr_path.suffix == ".md"
        
        # Check content
        content = adr_path.read_text()
        assert "Use SQLite for local storage" in content
        assert decision.decision in content
    
    def test_list_adrs(self, temp_storage):
        """Test listing all ADRs"""
        generator = ADRGenerator(adr_dir=temp_storage / "adrs")
        
        # Generate multiple ADRs
        generator.generate(ArchitecturalDecision(
            title="Decision 1",
            context="Context 1",
            decision="Option A",
            consequences=["Pro1"],
            alternatives=["Option B"]
        ))
        
        generator.generate(ArchitecturalDecision(
            title="Decision 2",
            context="Context 2",
            decision="Option C",
            consequences=["Pro2"],
            alternatives=["Option D"]
        ))
        
        adrs = generator.list_adrs()
        
        assert len(adrs) >= 2
