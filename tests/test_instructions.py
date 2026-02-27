"""
Test Suite for InstructionExtension

Tests persistent instructions loaded from .aureus/instructions.md
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.interfaces import Policy, Budget


@pytest.fixture
def test_policy(tmp_path):
    """Create test policy"""
    return Policy(
        version="1.0",
        project_name="test-instructions",
        project_root=tmp_path,
        budgets=Budget(
            max_loc=5000,
            max_modules=20,
            max_files=50,
            max_dependencies=10
        ),
        permissions={
            "file_read": True,
            "extensions": True
        }
    )


@pytest.fixture
def instructions_file(tmp_path):
    """Create test instructions file"""
    aureus_dir = tmp_path / ".aureus"
    aureus_dir.mkdir()
    
    instructions = aureus_dir / "instructions.md"
    instructions.write_text("""# Project Instructions

## Coding Style
- Use type hints
- Write docstrings
- Keep functions under 50 LOC

## Architecture
- Follow clean architecture principles
- Separate concerns
- Use dependency injection

## Testing
- Write tests for all new code
- Aim for 80%+ coverage
""")
    
    return instructions


class TestInstructionExtension:
    """Test InstructionExtension functionality"""
    
    def test_load_instructions_from_file(self, test_policy, instructions_file):
        """Test loading instructions from .aureus/instructions.md"""
        from src.extensions.instructions import InstructionExtension
        
        ext = InstructionExtension(
            policy=test_policy,
            instructions_path=instructions_file
        )
        
        instructions = ext.load_instructions()
        
        assert "Coding Style" in instructions
        assert "type hints" in instructions
        assert "clean architecture" in instructions
    
    def test_instructions_have_cost(self, test_policy, instructions_file):
        """Test instruction loading counts toward budget"""
        from src.extensions.instructions import InstructionExtension
        
        ext = InstructionExtension(
            policy=test_policy,
            instructions_path=instructions_file,
            max_cost=50.0
        )
        
        # Initial cost
        assert ext.cost_used == 0.0
        
        # Load instructions
        ext.load_instructions()
        
        # Should have cost (based on text length)
        assert ext.cost_used > 0.0
        assert ext.cost_used < ext.max_cost
    
    def test_large_instructions_exceed_budget(self, test_policy, tmp_path):
        """Test large instructions can exceed budget"""
        from src.extensions.instructions import InstructionExtension
        from src.extensions.base import ExtensionBudgetExceeded
        
        # Create very large instructions
        aureus_dir = tmp_path / ".aureus"
        aureus_dir.mkdir()
        instructions = aureus_dir / "instructions.md"
        
        # Write 10,000 lines of instructions
        large_content = "\n".join([f"Line {i}: Some instruction" for i in range(10000)])
        instructions.write_text(large_content)
        
        # Create extension with low budget
        ext = InstructionExtension(
            policy=test_policy,
            instructions_path=instructions,
            max_cost=10.0  # Very low budget
        )
        
        # Should exceed budget
        with pytest.raises(ExtensionBudgetExceeded):
            ext.load_instructions()
    
    def test_missing_instructions_file(self, test_policy, tmp_path):
        """Test handling of missing instructions file"""
        from src.extensions.instructions import InstructionExtension
        
        missing_file = tmp_path / ".aureus" / "instructions.md"
        
        ext = InstructionExtension(
            policy=test_policy,
            instructions_path=missing_file
        )
        
        # Should return empty string or handle gracefully
        result = ext.execute()
        
        assert result.success is False
        assert "not found" in result.error.lower() or "missing" in result.error.lower()
    
    def test_instructions_cached_after_first_load(self, test_policy, instructions_file):
        """Test instructions are cached to avoid repeated cost"""
        from src.extensions.instructions import InstructionExtension
        
        ext = InstructionExtension(
            policy=test_policy,
            instructions_path=instructions_file
        )
        
        # First load
        instructions1 = ext.load_instructions()
        cost_after_first = ext.cost_used
        
        # Second load (should use cache)
        instructions2 = ext.load_instructions()
        cost_after_second = ext.cost_used
        
        # Should be same content
        assert instructions1 == instructions2
        
        # Should not increase cost (cached)
        assert cost_after_second == cost_after_first
    
    def test_execute_returns_instructions(self, test_policy, instructions_file):
        """Test execute() method returns loaded instructions"""
        from src.extensions.instructions import InstructionExtension
        
        ext = InstructionExtension(
            policy=test_policy,
            instructions_path=instructions_file
        )
        
        result = ext.execute()
        
        assert result.success is True
        assert "Coding Style" in result.output
        assert result.cost_used > 0.0
    
    def test_instructions_metadata_includes_file_info(self, test_policy, instructions_file):
        """Test result metadata includes file information"""
        from src.extensions.instructions import InstructionExtension
        
        ext = InstructionExtension(
            policy=test_policy,
            instructions_path=instructions_file
        )
        
        result = ext.execute()
        
        assert "file_path" in result.metadata
        assert "file_size" in result.metadata
        assert result.metadata["file_path"] == str(instructions_file)
