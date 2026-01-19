"""Tests for metadata_tagger module."""

from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

from tools.music_identifier.metadata_tagger import MetadataTagger
from tools.music_identifier.identifier import IdentificationResult


class TestMetadataTagger:
    """Tests for MetadataTagger class."""
    
    def test_init(self):
        """Test tagger initialization."""
        tagger = MetadataTagger()
        assert tagger is not None
    
    @patch('tools.music_identifier.metadata_tagger.EasyID3')
    def test_read_tags_success(self, mock_easyid3):
        """Test reading tags from MP3 file."""
        # Mock EasyID3 to return tags as a dict
        mock_audio = {
            "title": ["Test Song"],
            "artist": ["Test Artist"],
            "album": ["Test Album"]
        }
        mock_easyid3.return_value = mock_audio
        
        tagger = MetadataTagger()
        tags = tagger.read_tags(Path("test.mp3"))
        
        assert "title" in tags
        assert "artist" in tags
    
    @patch('tools.music_identifier.metadata_tagger.EasyID3')
    def test_read_tags_no_id3(self, mock_easyid3):
        """Test reading tags from file without ID3."""
        from mutagen.id3 import ID3NoHeaderError
        mock_easyid3.side_effect = ID3NoHeaderError()
        
        tagger = MetadataTagger()
        tags = tagger.read_tags(Path("test.mp3"))
        
        assert tags == {}
    
    @patch('tools.music_identifier.metadata_tagger.EasyID3')
    def test_has_complete_tags_true(self, mock_easyid3):
        """Test checking for complete tags (has title and artist)."""
        mock_audio = {
            "title": ["Song"],
            "artist": ["Artist"]
        }
        mock_easyid3.return_value = mock_audio
        
        tagger = MetadataTagger()
        result = tagger.has_complete_tags(Path("test.mp3"))
        
        assert result is True
    
    @patch('tools.music_identifier.metadata_tagger.EasyID3')
    def test_has_complete_tags_false(self, mock_easyid3):
        """Test checking for complete tags (missing artist)."""
        mock_audio = {
            "title": ["Song"]
        }
        mock_easyid3.return_value = mock_audio
        
        tagger = MetadataTagger()
        result = tagger.has_complete_tags(Path("test.mp3"))
        
        assert result is False
    
    @patch('tools.music_identifier.metadata_tagger.MP3')
    @patch('tools.music_identifier.metadata_tagger.EasyID3')
    def test_update_tags_success(
        self,
        mock_easyid3,
        mock_mp3,
        sample_identification_result
    ):
        """Test updating tags successfully."""
        # Mock EasyID3
        mock_audio = MagicMock()
        mock_easyid3.return_value = mock_audio
        
        tagger = MetadataTagger()
        result = tagger.update_tags(
            Path("test.mp3"),
            sample_identification_result,
            force=True
        )
        
        assert result is True
        # Verify tags were set
        assert mock_audio.__setitem__.called
        assert mock_audio.save.called
    
    def test_update_tags_not_identified(self):
        """Test updating tags for unidentified file."""
        result = IdentificationResult(
            filepath=Path("test.mp3"),
            identified=False,
            error="Not found"
        )
        
        tagger = MetadataTagger()
        success = tagger.update_tags(Path("test.mp3"), result)
        
        assert success is False
    
    @patch('tools.music_identifier.metadata_tagger.MetadataTagger.has_complete_tags')
    def test_update_tags_skip_existing(
        self,
        mock_has_tags,
        sample_identification_result
    ):
        """Test skipping files with existing tags when force=False."""
        mock_has_tags.return_value = True
        
        tagger = MetadataTagger()
        result = tagger.update_tags(
            Path("test.mp3"),
            sample_identification_result,
            force=False
        )
        
        assert result is False
    
    @patch('tools.music_identifier.metadata_tagger.MP3')
    def test_clear_tags(self, mock_mp3):
        """Test clearing all tags."""
        mock_audio = MagicMock()
        mock_mp3.return_value = mock_audio
        
        tagger = MetadataTagger()
        result = tagger.clear_tags(Path("test.mp3"))
        
        assert result is True
        assert mock_audio.delete.called
        assert mock_audio.save.called
    
    @patch('tools.music_identifier.metadata_tagger.MP3')
    def test_get_file_info(self, mock_mp3):
        """Test getting file information."""
        # Mock MP3 info
        mock_info = Mock()
        mock_info.length = 180.5
        mock_info.bitrate = 320000
        mock_info.sample_rate = 44100
        mock_info.channels = 2
        
        mock_audio = MagicMock()
        mock_audio.info = mock_info
        mock_mp3.return_value = mock_audio
        
        tagger = MetadataTagger()
        
        # Need to patch Path.stat too
        with patch('pathlib.Path.stat') as mock_stat:
            mock_stat.return_value.st_size = 1024000
            info = tagger.get_file_info(Path("test.mp3"))
        
        assert info["duration"] == 180.5
        assert info["bitrate"] == 320000
        assert info["sample_rate"] == 44100
        assert info["channels"] == 2
        assert info["size"] == 1024000
