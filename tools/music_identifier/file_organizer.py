"""File organization and management for identified/unidentified music."""

import logging
import shutil
from pathlib import Path
from typing import Optional

from .identifier import IdentificationResult

logger = logging.getLogger(__name__)


class FileOrganizer:
    """Organizes music files into identified/unidentified directories.
    
    Handles moving files between directories with collision detection
    and safe file operations.
    
    Example:
        >>> organizer = FileOrganizer(identified_dir, unidentified_dir)
        >>> organizer.organize_file(result, dry_run=False)
    """
    
    def __init__(
        self,
        identified_dir: Path,
        unidentified_dir: Path
    ):
        """Initialize the file organizer.
        
        Args:
            identified_dir: Directory for successfully identified files
            unidentified_dir: Directory for unidentified files
        """
        self.identified_dir = Path(identified_dir)
        self.unidentified_dir = Path(unidentified_dir)
        
        # Ensure directories exist
        self.identified_dir.mkdir(parents=True, exist_ok=True)
        self.unidentified_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"FileOrganizer initialized:")
        logger.info(f"  Identified: {self.identified_dir}")
        logger.info(f"  Unidentified: {self.unidentified_dir}")
    
    def _get_unique_filename(self, directory: Path, filename: str) -> Path:
        """Get a unique filename in the target directory.
        
        If the file already exists, appends a number (e.g., "song (1).mp3").
        
        Args:
            directory: Target directory
            filename: Desired filename
            
        Returns:
            Path to a unique filename in the directory
        """
        target = directory / filename
        
        if not target.exists():
            return target
        
        # File exists, find a unique name
        stem = target.stem
        suffix = target.suffix
        counter = 1
        
        while True:
            new_name = f"{stem} ({counter}){suffix}"
            new_target = directory / new_name
            
            if not new_target.exists():
                logger.debug(f"Using unique filename: {new_name}")
                return new_target
            
            counter += 1
            
            # Sanity check
            if counter > 1000:
                raise RuntimeError(f"Could not find unique filename for {filename}")
    
    def _sanitize_filename(self, result: IdentificationResult) -> str:
        """Generate a clean filename from identification result.
        
        Format: "Artist - Title.mp3"
        Falls back to original filename if metadata is incomplete.
        
        Args:
            result: IdentificationResult with metadata
            
        Returns:
            Sanitized filename string
        """
        if result.identified and result.artist and result.title:
            # Clean artist and title
            artist = self._clean_string(result.artist)
            title = self._clean_string(result.title)
            
            filename = f"{artist} - {title}.mp3"
            logger.debug(f"Generated filename: {filename}")
            return filename
        else:
            # Keep original filename
            return result.filepath.name
    
    def _clean_string(self, s: str) -> str:
        """Remove characters that are problematic in filenames.
        
        Args:
            s: String to clean
            
        Returns:
            Cleaned string safe for use in filenames
        """
        # Replace problematic characters
        replacements = {
            '/': '-',
            '\\': '-',
            ':': ' -',
            '*': '',
            '?': '',
            '"': "'",
            '<': '',
            '>': '',
            '|': '-'
        }
        
        for char, replacement in replacements.items():
            s = s.replace(char, replacement)
        
        # Remove multiple spaces
        s = ' '.join(s.split())
        
        return s.strip()
    
    def organize_file(
        self,
        result: IdentificationResult,
        dry_run: bool = False,
        rename: bool = True
    ) -> Optional[Path]:
        """Move file to appropriate directory based on identification result.
        
        Args:
            result: IdentificationResult for the file
            dry_run: If True, log actions but don't move files
            rename: If True, rename file based on metadata. If False, keep original name.
            
        Returns:
            Path to new file location, or None on failure
        """
        source = result.filepath
        
        if not source.exists():
            logger.error(f"Source file not found: {source}")
            return None
        
        # Determine target directory
        if result.identified:
            target_dir = self.identified_dir
            status = "identified"
        else:
            target_dir = self.unidentified_dir
            status = "unidentified"
        
        # Determine filename
        if rename and result.identified:
            filename = self._sanitize_filename(result)
        else:
            filename = source.name
        
        # Get unique target path
        target = self._get_unique_filename(target_dir, filename)
        
        # Move file
        if dry_run:
            logger.info(f"[DRY RUN] Would move {status} file:")
            logger.info(f"  From: {source}")
            logger.info(f"  To:   {target}")
            return target
        
        try:
            shutil.move(str(source), str(target))
            logger.info(f"Moved {status} file to: {target.name}")
            return target
        except Exception as e:
            logger.error(f"Error moving file {source} to {target}: {e}")
            return None
    
    def get_stats(self) -> dict:
        """Get statistics about organized files.
        
        Returns:
            Dictionary with counts of files in each directory
        """
        identified_files = list(self.identified_dir.glob("*.mp3"))
        unidentified_files = list(self.unidentified_dir.glob("*.mp3"))
        
        stats = {
            "identified_count": len(identified_files),
            "unidentified_count": len(unidentified_files),
            "total_count": len(identified_files) + len(unidentified_files),
            "identified_dir": str(self.identified_dir),
            "unidentified_dir": str(self.unidentified_dir)
        }
        
        return stats
