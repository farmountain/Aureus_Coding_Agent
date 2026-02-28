"""
Build Memory System - Track successful patterns and failures across builds

Enables learning from previous builds to improve future code generation.
Part of the continuous intelligence improvement loop.
"""

import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional


@dataclass
class BuildMemoryEntry:
    """Single build memory entry"""
    
    timestamp: str
    intent: str
    success: bool
    files_created: List[str]
    attempts: int
    cost: float
    patterns_used: List[str]
    error: Optional[str] = None
    resolution: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BuildMemoryEntry':
        return cls(**data)


class BuildMemory:
    """
    Persistent memory of build history
    
    Stores:
    - Successful build patterns
    - Common failures and solutions
    - Intent→Implementation mappings
    - Performance metrics
    """
    
    def __init__(self, memory_file: Optional[Path] = None):
        """
        Initialize build memory
        
        Args:
            memory_file: Path to JSON file for persistence
        """
        self.memory_file = memory_file or Path(".aureus") / "build_memory.json"
        self.entries: List[BuildMemoryEntry] = []
        self._load()
    
    def _load(self):
        """Load memory from disk"""
        if self.memory_file.exists():
            try:
                with open(self.memory_file, 'r') as f:
                    data = json.load(f)
                    self.entries = [BuildMemoryEntry.from_dict(e) for e in data.get("entries", [])]
            except Exception as e:
                print(f"Warning: Could not load memory: {e}")
                self.entries = []
    
    def _save(self):
        """Save memory to disk"""
        try:
            self.memory_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.memory_file, 'w') as f:
                json.dump({
                    "version": "1.0",
                    "last_updated": datetime.now().isoformat(),
                    "entries": [e.to_dict() for e in self.entries]
                }, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save memory: {e}")
    
    def record_build(
        self,
        intent: str,
        success: bool,
        files_created: List[str],
        attempts: int,
        cost: float,
        error: Optional[str] = None,
        resolution: Optional[str] = None
    ):
        """
        Record a build attempt
        
        Args:
            intent: User's intent
            success: Whether build succeeded
            files_created: List of created file paths
            attempts: Number of attempts needed
            cost: SPK cost
            error: Error message if failed
            resolution: How error was resolved (if applicable)
        """
        # Extract patterns from intent
        patterns = self._extract_patterns(intent, files_created)
        
        entry = BuildMemoryEntry(
            timestamp=datetime.now().isoformat(),
            intent=intent,
            success=success,
            files_created=files_created,
            attempts=attempts,
            cost=cost,
            patterns_used=patterns,
            error=error,
            resolution=resolution
        )
        
        self.entries.append(entry)
        self._save()
    
    def find_similar_intents(self, intent: str, limit: int = 5) -> List[BuildMemoryEntry]:
        """
        Find previous builds with similar intents
        
        Args:
            intent: Current intent
            limit: Max number of results
        
        Returns:
            List of similar build entries, sorted by relevance
        """
        # Simple keyword-based similarity
        intent_keywords = set(intent.lower().split())
        
        scored_entries = []
        for entry in self.entries:
            entry_keywords = set(entry.intent.lower().split())
            similarity = len(intent_keywords & entry_keywords) / len(intent_keywords | entry_keywords)
            scored_entries.append((similarity, entry))
        
        # Sort by similarity and filter successful builds
        scored_entries.sort(reverse=True, key=lambda x: x[0])
        return [entry for score, entry in scored_entries[:limit] if entry.success]
    
    def get_common_failures(self) -> List[Dict[str, Any]]:
        """
        Get most common failure patterns
        
        Returns:
            List of failure patterns with frequency
        """
        failures = [e for e in self.entries if not e.success]
        
        # Group by error type
        error_groups: Dict[str, List[BuildMemoryEntry]] = {}
        for failure in failures:
            if failure.error:
                # Extract error type (first line)
                error_type = failure.error.split('\n')[0][:100]
                if error_type not in error_groups:
                    error_groups[error_type] = []
                error_groups[error_type].append(failure)
        
        # Return sorted by frequency
        common_failures = [
            {
                "error": error_type,
                "frequency": len(entries),
                "resolutions": [e.resolution for e in entries if e.resolution]
            }
            for error_type, entries in error_groups.items()
        ]
        
        common_failures.sort(key=lambda x: x["frequency"], reverse=True)
        return common_failures
    
    def get_success_rate(self) -> float:
        """Calculate overall success rate"""
        if not self.entries:
            return 0.0
        successful = sum(1 for e in self.entries if e.success)
        return successful / len(self.entries)
    
    def get_avg_attempts(self) -> float:
        """Calculate average attempts needed for successful builds"""
        successful = [e for e in self.entries if e.success]
        if not successful:
            return 0.0
        return sum(e.attempts for e in successful) / len(successful)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get memory statistics"""
        return {
            "total_builds": len(self.entries),
            "successful_builds": sum(1 for e in self.entries if e.success),
            "failed_builds": sum(1 for e in self.entries if not e.success),
            "success_rate": self.get_success_rate(),
            "avg_attempts": self.get_avg_attempts(),
            "total_files_created": sum(len(e.files_created) for e in self.entries),
            "common_failures": len(self.get_common_failures())
        }
    
    def _extract_patterns(self, intent: str, files_created: List[str]) -> List[str]:
        """Extract reusable patterns from successful builds"""
        patterns = []
        
        # Intent patterns
        intent_lower = intent.lower()
        if "class" in intent_lower:
            patterns.append("class_creation")
        if "function" in intent_lower:
            patterns.append("function_creation")
        if "api" in intent_lower or "endpoint" in intent_lower:
            patterns.append("api_development")
        if "test" in intent_lower:
            patterns.append("test_creation")
        if "data" in intent_lower or "model" in intent_lower:
            patterns.append("data_modeling")
        
        # File patterns
        for file_path in files_created:
            if "test" in file_path.lower():
                patterns.append("test_file")
            if "model" in file_path.lower():
                patterns.append("model_file")
            if "controller" in file_path.lower() or "handler" in file_path.lower():
                patterns.append("controller_file")
        
        return list(set(patterns))  # Deduplicate
