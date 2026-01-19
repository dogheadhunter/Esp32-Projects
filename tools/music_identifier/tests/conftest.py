"""Pytest fixtures and configuration for music identifier tests."""

import json
from pathlib import Path
from typing import Dict
from unittest.mock import Mock

import pytest


@pytest.fixture
def temp_music_dirs(tmp_path):
    """Create temporary music directories for testing.
    
    Returns:
        Dict with paths to input, identified, and unidentified directories
    """
    input_dir = tmp_path / "input"
    identified_dir = tmp_path / "identified"
    unidentified_dir = tmp_path / "unidentified"
    
    input_dir.mkdir()
    identified_dir.mkdir()
    unidentified_dir.mkdir()
    
    return {
        "input": input_dir,
        "identified": identified_dir,
        "unidentified": unidentified_dir
    }


@pytest.fixture
def sample_mp3_path(tmp_path):
    """Create a dummy MP3 file for testing.
    
    Returns:
        Path to sample MP3 file
    """
    mp3_path = tmp_path / "test_song.mp3"
    # Create a minimal valid MP3 file (ID3v2 header + minimal data)
    # This won't be playable but is enough for testing tag operations
    mp3_path.write_bytes(b'ID3\x04\x00\x00\x00\x00\x00\x00' + b'\xff\xfb' + b'\x00' * 100)
    return mp3_path


@pytest.fixture
def mock_config(temp_music_dirs):
    """Create a mock configuration for testing.
    
    Returns:
        Mock MusicIdentifierConfig object
    """
    from tools.music_identifier.config import MusicIdentifierConfig
    
    config = MusicIdentifierConfig(
        acoustid_api_key="test_api_key_12345",
        input_dir=temp_music_dirs["input"],
        identified_dir=temp_music_dirs["identified"],
        unidentified_dir=temp_music_dirs["unidentified"],
        rate_limit=10.0,  # Fast for testing
        min_confidence=0.5
    )
    
    return config


@pytest.fixture
def mock_fingerprint_result():
    """Mock fingerprint generation result.
    
    Returns:
        Tuple of (fingerprint, duration)
    """
    return ("AQADtFYaRukARQsQVD4uvn_gPzH8gD6_4Ef4_0f8A_9xPEePH3gQftB_", 180)


@pytest.fixture
def mock_acoustid_response():
    """Mock AcoustID API response.
    
    Returns:
        Dict representing API response
    """
    return {
        "status": "ok",
        "results": [
            {
                "score": 0.95,
                "recordings": [
                    {
                        "id": "abc123-def456-789",
                        "title": "Bohemian Rhapsody",
                        "artists": [
                            {"name": "Queen"}
                        ],
                        "releasegroups": [
                            {
                                "title": "A Night at the Opera",
                                "firstreleasedate": "1975-11-21"
                            }
                        ]
                    }
                ]
            }
        ]
    }


@pytest.fixture
def mock_acoustid_no_match():
    """Mock AcoustID API response with no good matches.
    
    Returns:
        Dict representing API response with low confidence
    """
    return {
        "status": "ok",
        "results": [
            {
                "score": 0.3,  # Below default threshold
                "recordings": []
            }
        ]
    }


@pytest.fixture
def sample_identification_result():
    """Create a sample IdentificationResult for testing.
    
    Returns:
        IdentificationResult object
    """
    from tools.music_identifier.identifier import IdentificationResult
    from pathlib import Path
    
    return IdentificationResult(
        filepath=Path("/test/song.mp3"),
        identified=True,
        title="Bohemian Rhapsody",
        artist="Queen",
        album="A Night at the Opera",
        year=1975,
        confidence=0.95,
        recording_id="abc123-def456-789"
    )


@pytest.fixture
def sample_unidentified_result():
    """Create a sample unidentified IdentificationResult.
    
    Returns:
        IdentificationResult object for unidentified file
    """
    from tools.music_identifier.identifier import IdentificationResult
    from pathlib import Path
    
    return IdentificationResult(
        filepath=Path("/test/unknown.mp3"),
        identified=False,
        error="No match above confidence threshold (50%)"
    )
