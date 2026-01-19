"""Tests for identifier module."""

import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

from tools.music_identifier.identifier import (
    IdentificationResult,
    MusicIdentifier
)


class TestIdentificationResult:
    """Tests for IdentificationResult dataclass."""
    
    def test_identified_result(self):
        """Test creating an identified result."""
        result = IdentificationResult(
            filepath=Path("test.mp3"),
            identified=True,
            title="Test Song",
            artist="Test Artist",
            album="Test Album",
            year=2020,
            confidence=0.95
        )
        
        assert result.identified is True
        assert result.title == "Test Song"
        assert result.artist == "Test Artist"
        assert result.confidence == 0.95
    
    def test_unidentified_result(self):
        """Test creating an unidentified result."""
        result = IdentificationResult(
            filepath=Path("unknown.mp3"),
            identified=False,
            error="No matches found"
        )
        
        assert result.identified is False
        assert result.error == "No matches found"
        assert result.title is None
    
    def test_str_identified(self):
        """Test string representation of identified result."""
        result = IdentificationResult(
            filepath=Path("test.mp3"),
            identified=True,
            title="Test Song",
            artist="Test Artist",
            confidence=0.95
        )
        
        s = str(result)
        assert "Test Song" in s
        assert "Test Artist" in s
        assert "95%" in s
    
    def test_str_unidentified(self):
        """Test string representation of unidentified result."""
        result = IdentificationResult(
            filepath=Path("test.mp3"),
            identified=False,
            error="Failed"
        )
        
        s = str(result)
        assert "Unidentified" in s
        assert "Failed" in s


class TestMusicIdentifier:
    """Tests for MusicIdentifier class."""
    
    def test_init_with_api_key(self, mock_config):
        """Test initialization with API key."""
        identifier = MusicIdentifier(config=mock_config)
        assert identifier.config.acoustid_api_key == "test_api_key_12345"
    
    def test_init_override_api_key(self, mock_config):
        """Test API key override in init."""
        identifier = MusicIdentifier(config=mock_config, api_key="override_key")
        assert identifier.config.acoustid_api_key == "override_key"
    
    def test_rate_limiting(self, mock_config):
        """Test rate limiting mechanism."""
        import time
        
        identifier = MusicIdentifier(config=mock_config)
        identifier.config.rate_limit = 10.0  # 10 requests per second
        
        start = time.time()
        identifier._rate_limit()
        identifier._rate_limit()
        identifier._rate_limit()
        elapsed = time.time() - start
        
        # Should have at least 2 * (1/10) = 0.2 seconds of delay
        assert elapsed >= 0.15  # Allow some tolerance
    
    @patch('subprocess.run')
    def test_generate_fingerprint_success(self, mock_run, mock_config):
        """Test successful fingerprint generation."""
        # Mock fpcalc output
        mock_result = Mock()
        mock_result.stdout = json.dumps({
            "fingerprint": "AQAD_fingerprint_data_here",
            "duration": 180
        })
        mock_run.return_value = mock_result
        
        identifier = MusicIdentifier(config=mock_config)
        result = identifier.generate_fingerprint(Path("test.mp3"))
        
        assert result is not None
        fingerprint, duration = result
        assert fingerprint == "AQAD_fingerprint_data_here"
        assert duration == 180
    
    @patch('subprocess.run')
    def test_generate_fingerprint_fpcalc_not_found(self, mock_run, mock_config):
        """Test fingerprint generation when fpcalc is not found."""
        mock_run.side_effect = FileNotFoundError()
        
        identifier = MusicIdentifier(config=mock_config)
        result = identifier.generate_fingerprint(Path("test.mp3"))
        
        assert result is None
    
    @patch('subprocess.run')
    def test_generate_fingerprint_timeout(self, mock_run, mock_config):
        """Test fingerprint generation timeout."""
        import subprocess
        mock_run.side_effect = subprocess.TimeoutExpired("fpcalc", 30)
        
        identifier = MusicIdentifier(config=mock_config)
        result = identifier.generate_fingerprint(Path("test.mp3"))
        
        assert result is None
    
    @patch('requests.post')
    def test_query_acoustid_success(
        self,
        mock_post,
        mock_config,
        mock_acoustid_response
    ):
        """Test successful AcoustID query."""
        mock_response = Mock()
        mock_response.json.return_value = mock_acoustid_response
        mock_post.return_value = mock_response
        
        identifier = MusicIdentifier(config=mock_config)
        results = identifier.query_acoustid("fingerprint", 180)
        
        assert results is not None
        assert len(results) == 1
        assert results[0]["score"] == 0.95
    
    @patch('requests.post')
    def test_query_acoustid_no_api_key(self, mock_post):
        """Test AcoustID query without API key."""
        from tools.music_identifier.config import get_config
        
        config = get_config(acoustid_api_key="")
        identifier = MusicIdentifier(config=config)
        
        results = identifier.query_acoustid("fingerprint", 180)
        assert results is None
        mock_post.assert_not_called()
    
    @patch('requests.post')
    def test_query_acoustid_api_error(self, mock_post, mock_config):
        """Test AcoustID query with API error."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "status": "error",
            "error": {"message": "Invalid API key"}
        }
        mock_post.return_value = mock_response
        
        identifier = MusicIdentifier(config=mock_config)
        results = identifier.query_acoustid("fingerprint", 180)
        
        assert results is None
    
    @patch('requests.post')
    def test_query_acoustid_timeout(self, mock_post, mock_config):
        """Test AcoustID query timeout with retry."""
        import requests
        mock_post.side_effect = requests.exceptions.Timeout()
        
        mock_config.max_retries = 2
        mock_config.retry_delay = 0.1  # Fast retries for testing
        
        identifier = MusicIdentifier(config=mock_config)
        results = identifier.query_acoustid("fingerprint", 180)
        
        assert results is None
        assert mock_post.call_count == 2
    
    def test_extract_metadata_success(self, mock_config, mock_acoustid_response):
        """Test metadata extraction from good results."""
        identifier = MusicIdentifier(config=mock_config)
        result = identifier.extract_metadata(mock_acoustid_response["results"])
        
        assert result is not None
        assert result.identified is True
        assert result.title == "Bohemian Rhapsody"
        assert result.artist == "Queen"
        assert result.album == "A Night at the Opera"
        assert result.year == 1975
        assert result.confidence == 0.95
    
    def test_extract_metadata_low_confidence(self, mock_config):
        """Test metadata extraction with low confidence."""
        low_conf_results = [
            {
                "score": 0.3,  # Below default 0.5 threshold
                "recordings": [
                    {
                        "title": "Uncertain Song",
                        "artists": [{"name": "Unknown Artist"}]
                    }
                ]
            }
        ]
        
        identifier = MusicIdentifier(config=mock_config)
        result = identifier.extract_metadata(low_conf_results)
        
        assert result is None
    
    def test_extract_metadata_empty_results(self, mock_config):
        """Test metadata extraction with empty results."""
        identifier = MusicIdentifier(config=mock_config)
        result = identifier.extract_metadata([])
        
        assert result is None
    
    @patch('tools.music_identifier.identifier.MusicIdentifier.generate_fingerprint')
    @patch('tools.music_identifier.identifier.MusicIdentifier.query_acoustid')
    @patch('tools.music_identifier.identifier.MusicIdentifier.extract_metadata')
    def test_identify_file_success(
        self,
        mock_extract,
        mock_query,
        mock_fingerprint,
        mock_config,
        sample_mp3_path,
        sample_identification_result
    ):
        """Test complete file identification workflow."""
        # Setup mocks
        mock_fingerprint.return_value = ("fingerprint", 180)
        mock_query.return_value = [{"score": 0.95}]
        mock_extract.return_value = sample_identification_result
        
        identifier = MusicIdentifier(config=mock_config)
        result = identifier.identify_file(sample_mp3_path)
        
        assert result.identified is True
        assert result.title == "Bohemian Rhapsody"
    
    def test_identify_file_not_found(self, mock_config):
        """Test identification of non-existent file."""
        identifier = MusicIdentifier(config=mock_config)
        result = identifier.identify_file(Path("nonexistent.mp3"))
        
        assert result.identified is False
        assert result.error == "File not found"
    
    @patch('tools.music_identifier.identifier.MusicIdentifier.generate_fingerprint')
    def test_identify_file_fingerprint_fails(
        self,
        mock_fingerprint,
        mock_config,
        sample_mp3_path
    ):
        """Test identification when fingerprint generation fails."""
        mock_fingerprint.return_value = None
        
        identifier = MusicIdentifier(config=mock_config)
        result = identifier.identify_file(sample_mp3_path)
        
        assert result.identified is False
        assert "fingerprint" in result.error.lower()
