"""Fingerprint cache for storing and retrieving audio fingerprints."""

import hashlib
import json
import logging
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class FingerprintCache:
    """Cache for storing audio fingerprints to avoid re-processing.
    
    Stores fingerprints keyed by file hash (MD5) to detect file changes.
    Cache is stored as JSON in the project's cache directory.
    """
    
    def __init__(self, cache_dir: Optional[Path] = None):
        """Initialize the fingerprint cache.
        
        Args:
            cache_dir: Directory to store cache file. Defaults to music/.cache/
        """
        if cache_dir is None:
            # Default to music/.cache/ directory
            cache_dir = Path(__file__).parent.parent.parent / "music" / ".cache"
        
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / "fingerprints.json"
        
        # Load existing cache
        self._cache = self._load_cache()
        
        logger.debug(f"Fingerprint cache initialized at {self.cache_file}")
        logger.debug(f"Cache contains {len(self._cache)} entries")
    
    def _load_cache(self) -> dict:
        """Load cache from disk.
        
        Returns:
            Dictionary of cached fingerprints
        """
        if not self.cache_file.exists():
            return {}
        
        try:
            with open(self.cache_file, 'r') as f:
                cache = json.load(f)
            logger.debug(f"Loaded {len(cache)} fingerprints from cache")
            return cache
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load cache: {e}, starting fresh")
            return {}
    
    def _save_cache(self) -> None:
        """Save cache to disk."""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self._cache, f, indent=2)
            logger.debug(f"Saved {len(self._cache)} fingerprints to cache")
        except IOError as e:
            logger.error(f"Failed to save cache: {e}")
    
    def _get_file_hash(self, filepath: Path) -> str:
        """Calculate MD5 hash of file.
        
        Args:
            filepath: Path to the file
            
        Returns:
            Hex string of MD5 hash
        """
        md5 = hashlib.md5()
        
        # Read file in chunks to handle large files
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                md5.update(chunk)
        
        return md5.hexdigest()
    
    def get(self, filepath: Path) -> Optional[Tuple[str, int]]:
        """Get cached fingerprint for a file.
        
        Args:
            filepath: Path to the audio file
            
        Returns:
            Tuple of (fingerprint, duration) if cached, None otherwise
        """
        if not filepath.exists():
            return None
        
        try:
            file_hash = self._get_file_hash(filepath)
            
            if file_hash in self._cache:
                entry = self._cache[file_hash]
                logger.debug(f"Cache hit for {filepath.name}")
                return (entry['fingerprint'], entry['duration'])
            
            logger.debug(f"Cache miss for {filepath.name}")
            return None
            
        except Exception as e:
            logger.warning(f"Error reading cache for {filepath.name}: {e}")
            return None
    
    def put(self, filepath: Path, fingerprint: str, duration: int) -> None:
        """Store fingerprint in cache.
        
        Args:
            filepath: Path to the audio file
            fingerprint: The acoustic fingerprint
            duration: Duration in seconds
        """
        try:
            file_hash = self._get_file_hash(filepath)
            
            self._cache[file_hash] = {
                'fingerprint': fingerprint,
                'duration': duration,
                'filename': filepath.name  # For debugging
            }
            
            self._save_cache()
            logger.debug(f"Cached fingerprint for {filepath.name}")
            
        except Exception as e:
            logger.warning(f"Error caching fingerprint for {filepath.name}: {e}")
    
    def clear(self) -> None:
        """Clear all cached fingerprints."""
        self._cache = {}
        self._save_cache()
        logger.info("Cleared fingerprint cache")
    
    def get_stats(self) -> dict:
        """Get cache statistics.
        
        Returns:
            Dictionary with cache stats
        """
        return {
            'total_entries': len(self._cache),
            'cache_file': str(self.cache_file),
            'cache_size_bytes': self.cache_file.stat().st_size if self.cache_file.exists() else 0
        }
