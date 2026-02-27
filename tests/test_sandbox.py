"""
Tests for Security Sandbox

Tests:
- Code separation (Aureus vs workspace)
- Path validation
- Immutability enforcement
- Self-play mode boundaries
"""

import pytest
from pathlib import Path
import tempfile
from src.security import (
    Sandbox,
    SandboxViolation,
    validate_file_read,
    validate_file_write,
    is_safe_path
)


class TestSandbox:
    """Test Sandbox functionality"""
    
    def test_aureus_root_detection(self):
        """Test that Aureus root is correctly detected"""
        assert Sandbox.AUREUS_ROOT.exists()
        assert (Sandbox.AUREUS_ROOT / "src").exists()
        assert (Sandbox.AUREUS_ROOT / "tests").exists()
    
    def test_is_aureus_code(self):
        """Test detection of Aureus agent code"""
        # Aureus code
        assert Sandbox.is_aureus_code(Sandbox.AUREUS_ROOT / "src" / "agents" / "builder.py")
        assert Sandbox.is_aureus_code(Sandbox.AUREUS_ROOT / "tests" / "test_sandbox.py")
        
        # Not Aureus code
        assert not Sandbox.is_aureus_code(Path("/tmp/user-project/main.py"))
        assert not Sandbox.is_aureus_code(Path("/other/path"))
    
    def test_is_immutable(self):
        """Test immutability detection"""
        # Immutable files
        assert Sandbox.is_immutable(Sandbox.AUREUS_ROOT / "LICENSE")
        assert Sandbox.is_immutable(Sandbox.AUREUS_ROOT / "src" / "governance" / "principles.py")
        assert Sandbox.is_immutable(Sandbox.AUREUS_ROOT / "src" / "security" / "sandbox.py")
        assert Sandbox.is_immutable(Sandbox.AUREUS_ROOT / "pyproject.toml")
        
        # Immutable directories
        assert Sandbox.is_immutable(Sandbox.AUREUS_ROOT / ".git" / "config")
        assert Sandbox.is_immutable(Sandbox.AUREUS_ROOT / "__pycache__" / "test.pyc")
        
        # Not immutable
        assert not Sandbox.is_immutable(Sandbox.AUREUS_ROOT / "src" / "agents" / "builder.py")
        assert not Sandbox.is_immutable(Sandbox.AUREUS_ROOT / "tests" / "test_new.py")
    
    def test_is_user_workspace(self, tmp_path):
        """Test user workspace detection"""
        project_root = tmp_path / "user-project"
        project_root.mkdir()
        
        user_file = project_root / "src" / "main.py"
        user_file.parent.mkdir(parents=True)
        user_file.write_text("# user code")
        
        # User workspace
        assert Sandbox.is_user_workspace(user_file, project_root)
        
        # Not user workspace (Aureus code)
        aureus_file = Sandbox.AUREUS_ROOT / "src" / "agents" / "builder.py"
        assert not Sandbox.is_user_workspace(aureus_file, project_root)
    
    def test_validate_path_in_workspace(self, tmp_path):
        """Test path validation within workspace"""
        project_root = tmp_path / "project"
        project_root.mkdir()
        
        # Valid path
        valid_path = project_root / "src" / "main.py"
        resolved = Sandbox.validate_path_in_workspace(valid_path, project_root)
        assert resolved.is_absolute()
        
        # Relative path
        relative = Path("src/main.py")
        resolved = Sandbox.validate_path_in_workspace(relative, project_root)
        assert resolved.is_absolute()
        assert str(resolved).startswith(str(project_root))
    
    def test_validate_path_escape_attempt(self, tmp_path):
        """Test that path traversal is blocked"""
        project_root = tmp_path / "project"
        project_root.mkdir()
        
        # Attempt to escape via ..
        evil_path = project_root / ".." / ".." / "etc" / "passwd"
        
        with pytest.raises(SandboxViolation) as exc:
            Sandbox.validate_path_in_workspace(evil_path, project_root)
        
        assert "escapes workspace" in str(exc.value).lower()
    
    def test_validate_modification_normal_mode(self, tmp_path):
        """Test modification validation in normal mode"""
        project_root = tmp_path / "project"
        project_root.mkdir()
        
        user_file = project_root / "main.py"
        user_file.write_text("# code")
        
        # Can modify user file
        assert Sandbox.validate_modification(user_file, project_root, is_self_play=False)
        
        # Cannot modify Aureus code
        aureus_file = Sandbox.AUREUS_ROOT / "src" / "agents" / "builder.py"
        with pytest.raises(SandboxViolation) as exc:
            Sandbox.validate_modification(aureus_file, project_root, is_self_play=False)
        
        assert "within project root" in str(exc.value).lower()
    
    def test_validate_modification_self_play_mode(self):
        """Test modification validation in self-play mode"""
        # Can modify Aureus code (non-immutable)
        aureus_file = Sandbox.AUREUS_ROOT / "src" / "agents" / "test_new.py"
        assert Sandbox.validate_modification(aureus_file, is_self_play=True)
        
        # Cannot modify immutable files
        immutable = Sandbox.AUREUS_ROOT / "LICENSE"
        with pytest.raises(SandboxViolation) as exc:
            Sandbox.validate_modification(immutable, is_self_play=True)
        
        assert "immutable" in str(exc.value).lower()
    
    def test_self_play_cannot_modify_workspace(self, tmp_path):
        """Test that self-play cannot modify user workspace"""
        project_root = tmp_path / "project"
        project_root.mkdir()
        
        user_file = project_root / "main.py"
        user_file.write_text("# code")
        
        with pytest.raises(SandboxViolation) as exc:
            Sandbox.validate_modification(user_file, project_root, is_self_play=True)
        
        assert "Aureus agent code" in str(exc.value)
    
    def test_self_play_restricted_to_allowed_dirs(self):
        """Test that self-play is restricted to specific directories"""
        # Allowed directories
        allowed = [
            Sandbox.AUREUS_ROOT / "src" / "test.py",
            Sandbox.AUREUS_ROOT / "tests" / "test.py",
            Sandbox.AUREUS_ROOT / "docs" / "test.md",
        ]
        
        for path in allowed:
            try:
                Sandbox.validate_modification(path, is_self_play=True)
            except SandboxViolation:
                pytest.fail(f"Should allow modification of {path}")
        
        # Not allowed (root level file)
        root_file = Sandbox.AUREUS_ROOT / "random_file.txt"
        with pytest.raises(SandboxViolation):
            Sandbox.validate_modification(root_file, is_self_play=True)
    
    def test_metadata_directory(self, tmp_path):
        """Test .aureus metadata directory creation"""
        project_root = tmp_path / "project"
        project_root.mkdir()
        
        metadata_dir = Sandbox.ensure_metadata_dir(project_root)
        
        assert metadata_dir.exists()
        assert metadata_dir == project_root / ".aureus"
        assert (metadata_dir / "memory").exists()
        assert (metadata_dir / "backups").exists()
        assert (metadata_dir / "patterns").exists()
    
    def test_convenience_functions(self, tmp_path):
        """Test convenience validation functions"""
        project_root = tmp_path / "project"
        project_root.mkdir()
        
        valid_file = project_root / "test.py"
        valid_file.write_text("# code")
        
        # validate_file_read
        resolved = validate_file_read(valid_file, project_root)
        assert resolved.is_absolute()
        
        # validate_file_write
        new_file = project_root / "new.py"
        resolved = validate_file_write(new_file, project_root)
        assert resolved.is_absolute()
        
        # is_safe_path
        assert is_safe_path(valid_file, project_root)
        assert not is_safe_path(Path("/etc/passwd"), project_root)


class TestSandboxIntegration:
    """Integration tests with actual file operations"""
    
    def test_cannot_escape_via_symlink(self, tmp_path):
        """Test that symlink escapes are blocked"""
        project_root = tmp_path / "project"
        project_root.mkdir()
        
        # Create symlink to outside directory
        outside = tmp_path / "outside"
        outside.mkdir()
        
        symlink = project_root / "escape"
        try:
            symlink.symlink_to(outside)
        except (OSError, NotImplementedError):
            pytest.skip("Symlinks not supported")
        
        # Should block access through symlink
        evil_path = symlink / "evil.py"
        
        with pytest.raises(SandboxViolation):
            Sandbox.validate_path_in_workspace(evil_path, project_root)
    
    def test_metadata_does_not_escape(self, tmp_path):
        """Test that .aureus metadata stays in workspace"""
        project_root = tmp_path / "project"
        project_root.mkdir()
        
        metadata = Sandbox.ensure_metadata_dir(project_root)
        
        # Metadata should be within project
        assert is_safe_path(metadata, project_root)
        assert is_safe_path(metadata / "memory", project_root)


class TestPrinciplesEnforcement:
    """Test that immutable principles are enforced"""
    
    def test_cannot_modify_principles_file(self):
        """Test that principles.py cannot be modified"""
        principles_file = Sandbox.AUREUS_ROOT / "src" / "governance" / "principles.py"
        
        # Not even in self-play mode
        with pytest.raises(SandboxViolation) as exc:
            Sandbox.validate_modification(principles_file, is_self_play=True)
        
        assert "immutable" in str(exc.value).lower()
    
    def test_cannot_modify_sandbox_file(self):
        """Test that sandbox.py cannot be modified"""
        sandbox_file = Sandbox.AUREUS_ROOT / "src" / "security" / "sandbox.py"
        
        with pytest.raises(SandboxViolation):
            Sandbox.validate_modification(sandbox_file, is_self_play=True)
    
    def test_cannot_modify_license(self):
        """Test that LICENSE cannot be modified"""
        license_file = Sandbox.AUREUS_ROOT / "LICENSE"
        
        with pytest.raises(SandboxViolation):
            Sandbox.validate_modification(license_file, is_self_play=True)
