"""Core music identification logic using AcoustID and MusicBrainz."""

import json
import logging
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests

from .config import MusicIdentifierConfig

logger = logging.getLogger(__name__)


@dataclass
class IdentificationResult:
    """Result of a music identification attempt."""
    
    filepath: Path
    identified: bool
    
    # Metadata (if identified)
    title: Optional[str] = None
    artist: Optional[str] = None
    album: Optional[str] = None
    year: Optional[int] = None
    track_number: Optional[int] = None
    genre: Optional[str] = None
    
    # Technical details
    confidence: float = 0.0
    duration: Optional[int] = None
    recording_id: Optional[str] = None  # MusicBrainz recording ID
    
    # Error information (if not identified)
    error: Optional[str] = None
    
    def __str__(self) -> str:
        """String representation."""
        if self.identified:
            return f"'{self.title}' by {self.artist} (confidence: {self.confidence:.2%})"
        else:
            return f"Unidentified: {self.error or 'Unknown error'}"


class MusicIdentifier:
    """Music identification using AcoustID fingerprinting and MusicBrainz metadata.
    
    This class handles:
    - Generating acoustic fingerprints using chromaprint/fpcalc
    - Querying AcoustID API for matches
    - Retrieving detailed metadata from MusicBrainz
    - Rate limiting and retry logic
    
    Example:
        >>> identifier = MusicIdentifier(api_key="your-key")
        >>> result = identifier.identify_file("song.mp3")
        >>> if result.identified:
        ...     print(f"Found: {result.title} by {result.artist}")
    """
    
    ACOUSTID_API_URL = "https://api.acoustid.org/v2/lookup"
    
    def __init__(self, config: Optional[MusicIdentifierConfig] = None, api_key: Optional[str] = None):
        """Initialize the music identifier.
        
        Args:
            config: Configuration object (optional)
            api_key: AcoustID API key (overrides config if provided)
        """
        from .config import get_config
        
        self.config = config or get_config()
        
        # Override API key if provided directly
        if api_key:
            self.config.acoustid_api_key = api_key
        
        # Validate configuration
        if not self.config.validate_api_key():
            logger.warning(
                "AcoustID API key not configured. "
                "Set ACOUSTID_API_KEY environment variable or pass api_key parameter."
            )
        
        # Rate limiting
        self._last_request_time = 0.0
        self._min_request_interval = 1.0 / self.config.rate_limit
        
        logger.info(f"MusicIdentifier initialized with rate limit: {self.config.rate_limit} req/sec")
    
    def _rate_limit(self) -> None:
        """Enforce rate limiting between API requests."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self._min_request_interval:
            sleep_time = self._min_request_interval - elapsed
            logger.debug(f"Rate limiting: sleeping {sleep_time:.3f}s")
            time.sleep(sleep_time)
        self._last_request_time = time.time()
    
    def generate_fingerprint(self, filepath: Path) -> Optional[Tuple[str, int]]:
        """Generate acoustic fingerprint for an audio file.
        
        Args:
            filepath: Path to the audio file
            
        Returns:
            Tuple of (fingerprint, duration) if successful, None otherwise
        """
        try:
            # Run fpcalc to generate fingerprint
            cmd = [
                self.config.fpcalc_path,
                "-length", str(self.config.fingerprint_duration),
                "-json",
                str(filepath)
            ]
            
            logger.debug(f"Running: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                check=True
            )
            
            # Parse JSON output
            data = json.loads(result.stdout)
            fingerprint = data.get("fingerprint")
            duration = data.get("duration")
            
            if not fingerprint:
                logger.error(f"No fingerprint generated for {filepath}")
                return None
            
            logger.debug(f"Generated fingerprint (duration: {duration}s)")
            return fingerprint, duration
            
        except subprocess.CalledProcessError as e:
            logger.error(f"fpcalc failed: {e.stderr}")
            return None
        except subprocess.TimeoutExpired:
            logger.error(f"fpcalc timed out for {filepath}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse fpcalc output: {e}")
            return None
        except FileNotFoundError:
            logger.error(
                f"fpcalc not found at '{self.config.fpcalc_path}'. "
                "Install chromaprint: https://acoustid.org/chromaprint"
            )
            return None
        except Exception as e:
            logger.error(f"Unexpected error generating fingerprint: {e}")
            return None
    
    def query_acoustid(
        self,
        fingerprint: str,
        duration: int
    ) -> Optional[List[Dict]]:
        """Query AcoustID API for fingerprint matches.
        
        Args:
            fingerprint: Acoustic fingerprint
            duration: Duration in seconds
            
        Returns:
            List of results from API, or None on failure
        """
        if not self.config.validate_api_key():
            logger.error("Cannot query AcoustID: API key not configured")
            return None
        
        params = {
            "client": self.config.acoustid_api_key,
            "fingerprint": fingerprint,
            "duration": duration,
            "meta": "recordings releasegroups compress"
        }
        
        for attempt in range(self.config.max_retries):
            try:
                self._rate_limit()
                
                logger.debug(f"Querying AcoustID API (attempt {attempt + 1})")
                response = requests.post(
                    self.ACOUSTID_API_URL,
                    data=params,
                    timeout=10
                )
                response.raise_for_status()
                
                data = response.json()
                
                if data.get("status") != "ok":
                    error = data.get("error", {}).get("message", "Unknown error")
                    logger.error(f"AcoustID API error: {error}")
                    return None
                
                results = data.get("results", [])
                logger.info(f"AcoustID returned {len(results)} results")
                return results
                
            except requests.exceptions.Timeout:
                logger.warning(f"AcoustID request timed out (attempt {attempt + 1})")
            except requests.exceptions.RequestException as e:
                logger.warning(f"AcoustID request failed: {e} (attempt {attempt + 1})")
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse AcoustID response: {e}")
                return None
            
            # Exponential backoff
            if attempt < self.config.max_retries - 1:
                delay = self.config.retry_delay * (2 ** attempt)
                logger.debug(f"Retrying in {delay}s...")
                time.sleep(delay)
        
        logger.error("All AcoustID query attempts failed")
        return None
    
    def extract_metadata(self, results: List[Dict]) -> Optional[IdentificationResult]:
        """Extract best metadata from AcoustID results.
        
        Args:
            results: List of results from AcoustID API
            
        Returns:
            IdentificationResult with extracted metadata, or None if no good match
        """
        if not results:
            return None
        
        # Find the result with highest confidence
        best_result = max(results, key=lambda r: r.get("score", 0.0))
        confidence = best_result.get("score", 0.0)
        
        if confidence < self.config.min_confidence:
            logger.info(f"Best match confidence {confidence:.2%} below threshold {self.config.min_confidence:.2%}")
            return None
        
        # Extract recording metadata
        recordings = best_result.get("recordings", [])
        if not recordings:
            logger.warning("No recordings found in best result")
            return None
        
        # Use first recording (usually most common/canonical)
        recording = recordings[0]
        
        # Extract basic metadata
        title = recording.get("title")
        recording_id = recording.get("id")
        
        # Extract artist(s)
        artists = recording.get("artists", [])
        artist = artists[0].get("name") if artists else None
        
        # Extract album and year from release groups
        album = None
        year = None
        release_groups = recording.get("releasegroups", [])
        if release_groups:
            release_group = release_groups[0]
            album = release_group.get("title")
            # Try to extract year from release date
            if "firstreleasedate" in release_group:
                try:
                    release_date = release_group["firstreleasedate"]
                    if release_date and len(release_date) >= 4:
                        year = int(release_date[:4])
                except (ValueError, TypeError):
                    pass
        
        result = IdentificationResult(
            filepath=Path(""),  # Will be set by caller
            identified=True,
            title=title,
            artist=artist,
            album=album,
            year=year,
            confidence=confidence,
            recording_id=recording_id
        )
        
        logger.info(f"Extracted metadata: {result}")
        return result
    
    def identify_file(self, filepath: Path) -> IdentificationResult:
        """Identify a music file and return metadata.
        
        Args:
            filepath: Path to the MP3 file
            
        Returns:
            IdentificationResult with metadata or error information
        """
        filepath = Path(filepath)
        
        if not filepath.exists():
            return IdentificationResult(
                filepath=filepath,
                identified=False,
                error="File not found"
            )
        
        logger.info(f"Identifying: {filepath.name}")
        
        # Generate fingerprint
        fingerprint_data = self.generate_fingerprint(filepath)
        if not fingerprint_data:
            return IdentificationResult(
                filepath=filepath,
                identified=False,
                error="Failed to generate fingerprint"
            )
        
        fingerprint, duration = fingerprint_data
        
        # Query AcoustID
        results = self.query_acoustid(fingerprint, duration)
        if not results:
            return IdentificationResult(
                filepath=filepath,
                identified=False,
                error="AcoustID query failed"
            )
        
        # Extract metadata
        result = self.extract_metadata(results)
        if not result:
            return IdentificationResult(
                filepath=filepath,
                identified=False,
                error=f"No match above confidence threshold ({self.config.min_confidence:.0%})"
            )
        
        # Set filepath
        result.filepath = filepath
        result.duration = duration
        
        return result
