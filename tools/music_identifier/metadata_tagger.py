"""ID3 metadata tagging for MP3 files using mutagen."""

import logging
from pathlib import Path
from typing import Optional

from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3NoHeaderError
from mutagen.mp3 import MP3

from .identifier import IdentificationResult

logger = logging.getLogger(__name__)


class MetadataTagger:
    """Manages ID3 tags for MP3 files.
    
    Uses the mutagen library to read and write ID3 tags in a safe,
    standards-compliant way.
    
    Example:
        >>> tagger = MetadataTagger()
        >>> result = IdentificationResult(...)
        >>> tagger.update_tags("song.mp3", result)
    """
    
    def __init__(self):
        """Initialize the metadata tagger."""
        logger.info("MetadataTagger initialized")
    
    def read_tags(self, filepath: Path) -> dict:
        """Read existing ID3 tags from an MP3 file.
        
        Args:
            filepath: Path to the MP3 file
            
        Returns:
            Dictionary of tag name to value(s)
        """
        filepath = Path(filepath)
        
        try:
            audio = EasyID3(str(filepath))
            tags = dict(audio)
            logger.debug(f"Read tags from {filepath.name}: {tags}")
            return tags
        except ID3NoHeaderError:
            logger.debug(f"No ID3 tags found in {filepath.name}")
            return {}
        except Exception as e:
            logger.error(f"Error reading tags from {filepath.name}: {e}")
            return {}
    
    def has_complete_tags(self, filepath: Path) -> bool:
        """Check if file already has complete metadata tags.
        
        Args:
            filepath: Path to the MP3 file
            
        Returns:
            True if file has title and artist tags, False otherwise
        """
        tags = self.read_tags(filepath)
        has_title = bool(tags.get("title"))
        has_artist = bool(tags.get("artist"))
        
        is_complete = has_title and has_artist
        
        if is_complete:
            logger.info(f"{filepath.name} already has complete tags")
        
        return is_complete
    
    def update_tags(
        self,
        filepath: Path,
        result: IdentificationResult,
        force: bool = False
    ) -> bool:
        """Update MP3 file with identified metadata.
        
        Args:
            filepath: Path to the MP3 file
            result: IdentificationResult with metadata to write
            force: If True, overwrite existing tags. If False, skip files with existing tags.
            
        Returns:
            True if tags were updated, False otherwise
        """
        filepath = Path(filepath)
        
        if not result.identified:
            logger.warning(f"Cannot update tags: file not identified")
            return False
        
        # Check if file already has tags and we're not forcing
        if not force and self.has_complete_tags(filepath):
            logger.info(f"Skipping {filepath.name}: already has tags (use force=True to overwrite)")
            return False
        
        try:
            # Try to load existing tags, or create new
            try:
                audio = EasyID3(str(filepath))
            except ID3NoHeaderError:
                # No ID3 tags exist, create them
                audio = MP3(str(filepath))
                audio.add_tags()
                audio.save()
                audio = EasyID3(str(filepath))
            
            # Update tags with identified metadata
            if result.title:
                audio["title"] = result.title
            
            if result.artist:
                audio["artist"] = result.artist
            
            if result.album:
                audio["album"] = result.album
            
            if result.year:
                audio["date"] = str(result.year)
            
            if result.track_number:
                audio["tracknumber"] = str(result.track_number)
            
            if result.genre:
                audio["genre"] = result.genre
            
            # Save changes
            audio.save()
            
            logger.info(f"Updated tags for {filepath.name}: '{result.title}' by {result.artist}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating tags for {filepath.name}: {e}")
            return False
    
    def clear_tags(self, filepath: Path) -> bool:
        """Remove all ID3 tags from an MP3 file.
        
        Args:
            filepath: Path to the MP3 file
            
        Returns:
            True if tags were cleared, False otherwise
        """
        filepath = Path(filepath)
        
        try:
            audio = MP3(str(filepath))
            audio.delete()
            audio.save()
            logger.info(f"Cleared all tags from {filepath.name}")
            return True
        except Exception as e:
            logger.error(f"Error clearing tags from {filepath.name}: {e}")
            return False
    
    def get_file_info(self, filepath: Path) -> dict:
        """Get technical information about an MP3 file.
        
        Args:
            filepath: Path to the MP3 file
            
        Returns:
            Dictionary with file information (duration, bitrate, sample rate, etc.)
        """
        filepath = Path(filepath)
        
        try:
            audio = MP3(str(filepath))
            
            info = {
                "duration": audio.info.length,
                "bitrate": audio.info.bitrate,
                "sample_rate": audio.info.sample_rate,
                "channels": audio.info.channels,
                "size": filepath.stat().st_size
            }
            
            logger.debug(f"File info for {filepath.name}: {info}")
            return info
            
        except Exception as e:
            logger.error(f"Error getting file info for {filepath.name}: {e}")
            return {}
