"""Tests for config module."""

import os
from pathlib import Path

import pytest

from tools.music_identifier.config import MusicIdentifierConfig, get_config


class TestMusicIdentifierConfig:
    """Tests for MusicIdentifierConfig class."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = MusicIdentifierConfig()
        
        assert config.rate_limit == 2.5
        assert config.max_retries == 3
        assert config.retry_delay == 1.0
        assert config.min_confidence == 0.5
        assert config.update_existing_tags is True
        assert config.fingerprint_duration == 120
    
    def test_config_with_overrides(self):
        """Test configuration with overrides."""
        config = MusicIdentifierConfig(
            acoustid_api_key="test_key",
            rate_limit=5.0,
            min_confidence=0.8
        )
        
        assert config.acoustid_api_key == "test_key"
        assert config.rate_limit == 5.0
        assert config.min_confidence == 0.8
    
    def test_validate_api_key_empty(self):
        """Test API key validation with empty key."""
        config = MusicIdentifierConfig(acoustid_api_key="")
        assert not config.validate_api_key()
    
    def test_validate_api_key_whitespace(self):
        """Test API key validation with whitespace."""
        config = MusicIdentifierConfig(acoustid_api_key="   ")
        assert not config.validate_api_key()
    
    def test_validate_api_key_valid(self):
        """Test API key validation with valid key."""
        config = MusicIdentifierConfig(acoustid_api_key="valid_key_123")
        assert config.validate_api_key()
    
    def test_default_paths(self):
        """Test default path configuration."""
        config = MusicIdentifierConfig()
        
        assert config.input_dir is not None
        assert config.identified_dir is not None
        assert config.unidentified_dir is not None
        
        assert config.input_dir.name == "input"
        assert config.identified_dir.name == "identified"
        assert config.unidentified_dir.name == "unidentified"
    
    def test_custom_paths(self, tmp_path):
        """Test custom path configuration."""
        custom_input = tmp_path / "custom_input"
        custom_identified = tmp_path / "custom_identified"
        custom_unidentified = tmp_path / "custom_unidentified"
        
        config = MusicIdentifierConfig(
            input_dir=custom_input,
            identified_dir=custom_identified,
            unidentified_dir=custom_unidentified
        )
        
        assert config.input_dir == custom_input
        assert config.identified_dir == custom_identified
        assert config.unidentified_dir == custom_unidentified
    
    def test_ensure_directories(self, tmp_path):
        """Test directory creation."""
        input_dir = tmp_path / "test_input"
        identified_dir = tmp_path / "test_identified"
        unidentified_dir = tmp_path / "test_unidentified"
        
        config = MusicIdentifierConfig(
            input_dir=input_dir,
            identified_dir=identified_dir,
            unidentified_dir=unidentified_dir
        )
        
        # Directories shouldn't exist yet
        assert not input_dir.exists()
        assert not identified_dir.exists()
        assert not unidentified_dir.exists()
        
        # Create directories
        config.ensure_directories()
        
        # Now they should exist
        assert input_dir.exists()
        assert identified_dir.exists()
        assert unidentified_dir.exists()
    
    def test_min_confidence_validation(self):
        """Test min_confidence field validation."""
        # Valid values
        config = MusicIdentifierConfig(min_confidence=0.0)
        assert config.min_confidence == 0.0
        
        config = MusicIdentifierConfig(min_confidence=1.0)
        assert config.min_confidence == 1.0
        
        config = MusicIdentifierConfig(min_confidence=0.75)
        assert config.min_confidence == 0.75
        
        # Invalid values should raise validation error
        with pytest.raises(Exception):  # Pydantic validation error
            MusicIdentifierConfig(min_confidence=-0.1)
        
        with pytest.raises(Exception):  # Pydantic validation error
            MusicIdentifierConfig(min_confidence=1.5)


class TestGetConfig:
    """Tests for get_config helper function."""
    
    def test_get_config_default(self):
        """Test get_config with default values."""
        config = get_config()
        assert isinstance(config, MusicIdentifierConfig)
    
    def test_get_config_with_overrides(self):
        """Test get_config with overrides."""
        config = get_config(
            rate_limit=10.0,
            min_confidence=0.9
        )
        
        assert config.rate_limit == 10.0
        assert config.min_confidence == 0.9
