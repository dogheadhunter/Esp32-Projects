"""
Tests for shared project configuration
"""

import pytest
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from tools.shared.project_config import (
    PROJECT_ROOT,
    LLM_MODEL,
    LLM_BACKUP_MODEL,
    OLLAMA_URL,
    CHROMA_DB_PATH,
    LORE_PATH,
    OUTPUT_PATH,
    SCRIPTS_OUTPUT_DIR,
    AUDIO_OUTPUT_DIR,
    LOGS_DIR,
    PERSONALITIES_DIR,
    ensure_directories
)


class TestProjectConstants:
    """Test project constant definitions"""
    
    def test_project_root_exists(self):
        """Test PROJECT_ROOT is a valid path"""
        assert PROJECT_ROOT.exists()
        assert PROJECT_ROOT.is_dir()
    
    def test_llm_model_defined(self):
        """Test LLM model constants are defined"""
        assert isinstance(LLM_MODEL, str)
        assert len(LLM_MODEL) > 0
        assert isinstance(LLM_BACKUP_MODEL, str)
        assert len(LLM_BACKUP_MODEL) > 0
    
    def test_ollama_url_format(self):
        """Test Ollama URL is properly formatted"""
        assert OLLAMA_URL.startswith("http://")
        assert "localhost" in OLLAMA_URL or "127.0.0.1" in OLLAMA_URL
        assert "/api/generate" in OLLAMA_URL
    
    def test_paths_are_path_objects(self):
        """Test all path constants are Path objects"""
        assert isinstance(CHROMA_DB_PATH, Path)
        assert isinstance(LORE_PATH, Path)
        assert isinstance(OUTPUT_PATH, Path)
        assert isinstance(SCRIPTS_OUTPUT_DIR, Path)
        assert isinstance(AUDIO_OUTPUT_DIR, Path)
        assert isinstance(LOGS_DIR, Path)
        assert isinstance(PERSONALITIES_DIR, Path)
    
    def test_paths_are_absolute(self):
        """Test all paths are absolute"""
        assert CHROMA_DB_PATH.is_absolute()
        assert LORE_PATH.is_absolute()
        assert OUTPUT_PATH.is_absolute()
        assert SCRIPTS_OUTPUT_DIR.is_absolute()
        assert AUDIO_OUTPUT_DIR.is_absolute()
        assert LOGS_DIR.is_absolute()
        assert PERSONALITIES_DIR.is_absolute()
    
    def test_paths_under_project_root(self):
        """Test all paths are under PROJECT_ROOT"""
        paths = [
            CHROMA_DB_PATH,
            LORE_PATH,
            OUTPUT_PATH,
            SCRIPTS_OUTPUT_DIR,
            AUDIO_OUTPUT_DIR,
            LOGS_DIR,
            PERSONALITIES_DIR
        ]
        
        for path in paths:
            try:
                path.relative_to(PROJECT_ROOT)
            except ValueError:
                pytest.fail(f"Path {path} is not under PROJECT_ROOT {PROJECT_ROOT}")
    
    def test_output_structure(self):
        """Test output directory structure"""
        assert SCRIPTS_OUTPUT_DIR.parent == OUTPUT_PATH
        assert AUDIO_OUTPUT_DIR.parent == OUTPUT_PATH


class TestEnsureDirectories:
    """Test directory creation function"""
    
    def test_ensure_directories_creates_dirs(self, tmp_path, monkeypatch):
        """Test ensure_directories creates missing directories"""
        # Create temporary paths
        test_scripts = tmp_path / "output" / "scripts"
        test_audio = tmp_path / "output" / "audio"
        test_logs = tmp_path / "logs" / "pipeline"
        
        # Monkey patch the paths
        import tools.shared.project_config as config
        monkeypatch.setattr(config, 'SCRIPTS_OUTPUT_DIR', test_scripts)
        monkeypatch.setattr(config, 'AUDIO_OUTPUT_DIR', test_audio)
        monkeypatch.setattr(config, 'LOGS_DIR', test_logs)
        
        # Call function
        config.ensure_directories()
        
        # Verify directories created
        assert test_scripts.exists()
        assert test_audio.exists()
        assert test_logs.exists()
    
    def test_ensure_directories_no_error_if_exists(self, tmp_path, monkeypatch):
        """Test ensure_directories doesn't fail if directories exist"""
        # Create directories first
        test_scripts = tmp_path / "output" / "scripts"
        test_audio = tmp_path / "output" / "audio"
        test_logs = tmp_path / "logs" / "pipeline"
        
        test_scripts.mkdir(parents=True)
        test_audio.mkdir(parents=True)
        test_logs.mkdir(parents=True)
        
        # Monkey patch the paths
        import tools.shared.project_config as config
        monkeypatch.setattr(config, 'SCRIPTS_OUTPUT_DIR', test_scripts)
        monkeypatch.setattr(config, 'AUDIO_OUTPUT_DIR', test_audio)
        monkeypatch.setattr(config, 'LOGS_DIR', test_logs)
        
        # Should not raise
        config.ensure_directories()
        
        # Directories should still exist
        assert test_scripts.exists()
        assert test_audio.exists()
        assert test_logs.exists()


class TestPathRelationships:
    """Test relationships between paths"""
    
    def test_scripts_and_audio_in_output(self):
        """Test scripts and audio dirs are in output dir"""
        assert str(SCRIPTS_OUTPUT_DIR).startswith(str(OUTPUT_PATH))
        assert str(AUDIO_OUTPUT_DIR).startswith(str(OUTPUT_PATH))
    
    def test_logs_dir_naming(self):
        """Test logs directory has expected structure"""
        assert "logs" in str(LOGS_DIR).lower()
        assert "pipeline" in str(LOGS_DIR).lower()
