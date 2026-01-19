"""Tests for file_organizer module."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from tools.music_identifier.file_organizer import FileOrganizer
from tools.music_identifier.identifier import IdentificationResult


class TestFileOrganizer:
    """Tests for FileOrganizer class."""
    
    def test_init(self, temp_music_dirs):
        """Test organizer initialization."""
        organizer = FileOrganizer(
            temp_music_dirs["identified"],
            temp_music_dirs["unidentified"]
        )
        
        assert organizer.identified_dir == temp_music_dirs["identified"]
        assert organizer.unidentified_dir == temp_music_dirs["unidentified"]
        assert organizer.identified_dir.exists()
        assert organizer.unidentified_dir.exists()
    
    def test_clean_string(self, temp_music_dirs):
        """Test filename cleaning."""
        organizer = FileOrganizer(
            temp_music_dirs["identified"],
            temp_music_dirs["unidentified"]
        )
        
        # Test various problematic characters
        assert organizer._clean_string("AC/DC") == "AC-DC"
        assert organizer._clean_string("Song: Title") == "Song - Title"
        assert organizer._clean_string("Question?") == "Question"
        assert organizer._clean_string('Song "Title"') == "Song 'Title'"
        assert organizer._clean_string("Song*Name") == "SongName"
        assert organizer._clean_string("Multiple   Spaces") == "Multiple Spaces"
    
    def test_sanitize_filename(
        self,
        temp_music_dirs,
        sample_identification_result
    ):
        """Test filename sanitization."""
        organizer = FileOrganizer(
            temp_music_dirs["identified"],
            temp_music_dirs["unidentified"]
        )
        
        filename = organizer._sanitize_filename(sample_identification_result)
        
        assert filename == "Queen - Bohemian Rhapsody.mp3"
        assert "/" not in filename
        assert "\\" not in filename
    
    def test_sanitize_filename_unidentified(
        self,
        temp_music_dirs,
        sample_unidentified_result
    ):
        """Test filename sanitization for unidentified files."""
        organizer = FileOrganizer(
            temp_music_dirs["identified"],
            temp_music_dirs["unidentified"]
        )
        
        filename = organizer._sanitize_filename(sample_unidentified_result)
        
        # Should return original filename
        assert filename == "unknown.mp3"
    
    def test_get_unique_filename_no_collision(self, temp_music_dirs):
        """Test unique filename when there's no collision."""
        organizer = FileOrganizer(
            temp_music_dirs["identified"],
            temp_music_dirs["unidentified"]
        )
        
        result = organizer._get_unique_filename(
            temp_music_dirs["identified"],
            "song.mp3"
        )
        
        assert result == temp_music_dirs["identified"] / "song.mp3"
    
    def test_get_unique_filename_with_collision(self, temp_music_dirs):
        """Test unique filename when file already exists."""
        organizer = FileOrganizer(
            temp_music_dirs["identified"],
            temp_music_dirs["unidentified"]
        )
        
        # Create existing file
        existing = temp_music_dirs["identified"] / "song.mp3"
        existing.write_text("existing")
        
        result = organizer._get_unique_filename(
            temp_music_dirs["identified"],
            "song.mp3"
        )
        
        assert result == temp_music_dirs["identified"] / "song (1).mp3"
    
    def test_get_unique_filename_multiple_collisions(self, temp_music_dirs):
        """Test unique filename with multiple collisions."""
        organizer = FileOrganizer(
            temp_music_dirs["identified"],
            temp_music_dirs["unidentified"]
        )
        
        # Create multiple existing files
        (temp_music_dirs["identified"] / "song.mp3").write_text("1")
        (temp_music_dirs["identified"] / "song (1).mp3").write_text("2")
        (temp_music_dirs["identified"] / "song (2).mp3").write_text("3")
        
        result = organizer._get_unique_filename(
            temp_music_dirs["identified"],
            "song.mp3"
        )
        
        assert result == temp_music_dirs["identified"] / "song (3).mp3"
    
    def test_organize_identified_file(
        self,
        temp_music_dirs,
        sample_identification_result
    ):
        """Test organizing an identified file."""
        organizer = FileOrganizer(
            temp_music_dirs["identified"],
            temp_music_dirs["unidentified"]
        )
        
        # Create source file
        source_file = temp_music_dirs["input"] / "test.mp3"
        source_file.write_text("test content")
        
        result = sample_identification_result
        result.filepath = source_file
        
        # Organize file
        new_path = organizer.organize_file(result, dry_run=False, rename=True)
        
        assert new_path is not None
        assert new_path.parent == temp_music_dirs["identified"]
        assert new_path.name == "Queen - Bohemian Rhapsody.mp3"
        assert new_path.exists()
        assert not source_file.exists()  # Source should be moved
    
    def test_organize_unidentified_file(
        self,
        temp_music_dirs,
        sample_unidentified_result
    ):
        """Test organizing an unidentified file."""
        organizer = FileOrganizer(
            temp_music_dirs["identified"],
            temp_music_dirs["unidentified"]
        )
        
        # Create source file
        source_file = temp_music_dirs["input"] / "unknown.mp3"
        source_file.write_text("unknown content")
        
        result = sample_unidentified_result
        result.filepath = source_file
        
        # Organize file
        new_path = organizer.organize_file(result, dry_run=False, rename=False)
        
        assert new_path is not None
        assert new_path.parent == temp_music_dirs["unidentified"]
        assert new_path.name == "unknown.mp3"
        assert new_path.exists()
        assert not source_file.exists()
    
    def test_organize_file_dry_run(
        self,
        temp_music_dirs,
        sample_identification_result
    ):
        """Test dry run mode doesn't move files."""
        organizer = FileOrganizer(
            temp_music_dirs["identified"],
            temp_music_dirs["unidentified"]
        )
        
        # Create source file
        source_file = temp_music_dirs["input"] / "test.mp3"
        source_file.write_text("test content")
        
        result = sample_identification_result
        result.filepath = source_file
        
        # Dry run
        new_path = organizer.organize_file(result, dry_run=True, rename=True)
        
        assert new_path is not None
        assert source_file.exists()  # Source should still exist in dry run
    
    def test_organize_file_no_rename(
        self,
        temp_music_dirs,
        sample_identification_result
    ):
        """Test organizing without renaming."""
        organizer = FileOrganizer(
            temp_music_dirs["identified"],
            temp_music_dirs["unidentified"]
        )
        
        # Create source file
        source_file = temp_music_dirs["input"] / "original_name.mp3"
        source_file.write_text("test content")
        
        result = sample_identification_result
        result.filepath = source_file
        
        # Organize without rename
        new_path = organizer.organize_file(result, dry_run=False, rename=False)
        
        assert new_path is not None
        assert new_path.name == "original_name.mp3"
    
    def test_organize_file_not_found(
        self,
        temp_music_dirs,
        sample_identification_result
    ):
        """Test organizing non-existent file."""
        organizer = FileOrganizer(
            temp_music_dirs["identified"],
            temp_music_dirs["unidentified"]
        )
        
        result = sample_identification_result
        result.filepath = Path("nonexistent.mp3")
        
        new_path = organizer.organize_file(result, dry_run=False)
        
        assert new_path is None
    
    def test_get_stats(self, temp_music_dirs):
        """Test statistics gathering."""
        organizer = FileOrganizer(
            temp_music_dirs["identified"],
            temp_music_dirs["unidentified"]
        )
        
        # Create some test files
        (temp_music_dirs["identified"] / "song1.mp3").write_text("1")
        (temp_music_dirs["identified"] / "song2.mp3").write_text("2")
        (temp_music_dirs["unidentified"] / "unknown1.mp3").write_text("3")
        
        stats = organizer.get_stats()
        
        assert stats["identified_count"] == 2
        assert stats["unidentified_count"] == 1
        assert stats["total_count"] == 3
        assert "identified_dir" in stats
        assert "unidentified_dir" in stats
