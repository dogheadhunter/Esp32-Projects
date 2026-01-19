"""Tests for fingerprint_cache module."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from tools.music_identifier.fingerprint_cache import FingerprintCache


class TestFingerprintCache:
    """Tests for FingerprintCache class."""
    
    def test_init(self, tmp_path):
        """Test cache initialization."""
        cache_dir = tmp_path / "cache"
        cache = FingerprintCache(cache_dir=cache_dir)
        
        assert cache.cache_dir == cache_dir
        assert cache.cache_dir.exists()
        assert cache.cache_file == cache_dir / "fingerprints.json"
    
    def test_default_cache_dir(self):
        """Test default cache directory."""
        cache = FingerprintCache()
        assert cache.cache_dir.exists()
        assert "music" in str(cache.cache_dir)
        assert ".cache" in str(cache.cache_dir)
    
    def test_put_and_get(self, tmp_path):
        """Test storing and retrieving fingerprints."""
        cache_dir = tmp_path / "cache"
        cache = FingerprintCache(cache_dir=cache_dir)
        
        # Create a test file
        test_file = tmp_path / "test.mp3"
        test_file.write_bytes(b"test audio data")
        
        # Store fingerprint
        cache.put(test_file, "fingerprint123", 180)
        
        # Retrieve fingerprint
        result = cache.get(test_file)
        
        assert result is not None
        assert result[0] == "fingerprint123"
        assert result[1] == 180
    
    def test_get_nonexistent(self, tmp_path):
        """Test retrieving non-existent fingerprint."""
        cache_dir = tmp_path / "cache"
        cache = FingerprintCache(cache_dir=cache_dir)
        
        test_file = tmp_path / "test.mp3"
        test_file.write_bytes(b"test audio data")
        
        result = cache.get(test_file)
        assert result is None
    
    def test_cache_persistence(self, tmp_path):
        """Test that cache persists across instances."""
        cache_dir = tmp_path / "cache"
        
        # Create first cache instance
        cache1 = FingerprintCache(cache_dir=cache_dir)
        
        test_file = tmp_path / "test.mp3"
        test_file.write_bytes(b"test audio data")
        
        cache1.put(test_file, "fingerprint456", 200)
        
        # Create second cache instance
        cache2 = FingerprintCache(cache_dir=cache_dir)
        
        # Should load existing cache
        result = cache2.get(test_file)
        assert result is not None
        assert result[0] == "fingerprint456"
        assert result[1] == 200
    
    def test_file_change_detection(self, tmp_path):
        """Test that cache detects file changes."""
        cache_dir = tmp_path / "cache"
        cache = FingerprintCache(cache_dir=cache_dir)
        
        test_file = tmp_path / "test.mp3"
        test_file.write_bytes(b"original data")
        
        # Cache original file
        cache.put(test_file, "fingerprint1", 180)
        
        # Modify file
        test_file.write_bytes(b"modified data")
        
        # Should return None for modified file
        result = cache.get(test_file)
        assert result is None
    
    def test_clear(self, tmp_path):
        """Test clearing cache."""
        cache_dir = tmp_path / "cache"
        cache = FingerprintCache(cache_dir=cache_dir)
        
        test_file = tmp_path / "test.mp3"
        test_file.write_bytes(b"test audio data")
        
        cache.put(test_file, "fingerprint789", 150)
        
        # Clear cache
        cache.clear()
        
        # Cache should be empty
        result = cache.get(test_file)
        assert result is None
    
    def test_get_stats(self, tmp_path):
        """Test cache statistics."""
        cache_dir = tmp_path / "cache"
        cache = FingerprintCache(cache_dir=cache_dir)
        
        stats = cache.get_stats()
        
        assert 'total_entries' in stats
        assert 'cache_file' in stats
        assert 'cache_size_bytes' in stats
        assert stats['total_entries'] == 0
    
    def test_corrupted_cache_file(self, tmp_path):
        """Test handling of corrupted cache file."""
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        cache_file = cache_dir / "fingerprints.json"
        
        # Write corrupted JSON
        cache_file.write_text("{ invalid json }")
        
        # Should handle gracefully
        cache = FingerprintCache(cache_dir=cache_dir)
        assert len(cache._cache) == 0
