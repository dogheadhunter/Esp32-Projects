"""Integration tests for the complete music identification workflow."""

import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from tools.music_identifier.config import get_config
from tools.music_identifier.file_organizer import FileOrganizer
from tools.music_identifier.identifier import MusicIdentifier
from tools.music_identifier.metadata_tagger import MetadataTagger


@pytest.mark.integration
class TestMusicIdentifierIntegration:
    """Integration tests for the complete workflow."""
    
    @patch('subprocess.run')
    @patch('requests.post')
    @patch('tools.music_identifier.metadata_tagger.EasyID3')
    @patch('tools.music_identifier.metadata_tagger.MP3')
    def test_complete_workflow_identified(
        self,
        mock_mp3,
        mock_easyid3,
        mock_requests,
        mock_subprocess,
        temp_music_dirs,
        mock_fingerprint_result,
        mock_acoustid_response
    ):
        """Test complete workflow for successfully identified file."""
        # Setup mocks
        # 1. fpcalc fingerprint generation
        mock_fpcalc_result = Mock()
        mock_fpcalc_result.stdout = json.dumps({
            "fingerprint": mock_fingerprint_result[0],
            "duration": mock_fingerprint_result[1]
        })
        mock_subprocess.return_value = mock_fpcalc_result
        
        # 2. AcoustID API response
        mock_response = Mock()
        mock_response.json.return_value = mock_acoustid_response
        mock_requests.return_value = mock_response
        
        # 3. ID3 tag handling - use a proper mock that supports dict-like operations
        mock_audio_dict = {}
        mock_audio_obj = Mock()
        mock_audio_obj.__setitem__ = Mock(side_effect=lambda k, v: mock_audio_dict.__setitem__(k, v))
        mock_audio_obj.save = Mock()
        mock_easyid3.return_value = mock_audio_obj
        
        # Create test file
        test_file = temp_music_dirs["input"] / "unknown_song.mp3"
        test_file.write_text("fake mp3 content")
        
        # Initialize components
        config = get_config(
            acoustid_api_key="test_key",
            input_dir=temp_music_dirs["input"],
            identified_dir=temp_music_dirs["identified"],
            unidentified_dir=temp_music_dirs["unidentified"],
            min_confidence=0.5
        )
        
        identifier = MusicIdentifier(config=config)
        tagger = MetadataTagger()
        organizer = FileOrganizer(
            config.identified_dir,
            config.unidentified_dir
        )
        
        # Step 1: Identify file
        result = identifier.identify_file(test_file)
        
        assert result.identified is True
        assert result.title == "Bohemian Rhapsody"
        assert result.artist == "Queen"
        assert result.confidence == 0.95
        
        # Step 2: Update tags
        # For this test, we'll mock the complete tags check
        with patch.object(tagger, 'has_complete_tags', return_value=False):
            tags_updated = tagger.update_tags(test_file, result, force=True)
        
        assert tags_updated is True
        
        # Step 3: Organize file
        new_path = organizer.organize_file(result, dry_run=False, rename=True)
        
        assert new_path is not None
        assert new_path.parent == temp_music_dirs["identified"]
        assert "Queen" in new_path.name
        assert "Bohemian Rhapsody" in new_path.name
    
    @patch('subprocess.run')
    @patch('requests.post')
    def test_complete_workflow_unidentified(
        self,
        mock_requests,
        mock_subprocess,
        temp_music_dirs
    ):
        """Test complete workflow for file that cannot be identified."""
        # Setup mocks for low confidence result
        mock_fpcalc_result = Mock()
        mock_fpcalc_result.stdout = json.dumps({
            "fingerprint": "some_fingerprint",
            "duration": 180
        })
        mock_subprocess.return_value = mock_fpcalc_result
        
        # AcoustID returns low confidence
        mock_response = Mock()
        mock_response.json.return_value = {
            "status": "ok",
            "results": [
                {
                    "score": 0.2,  # Below threshold
                    "recordings": []
                }
            ]
        }
        mock_requests.return_value = mock_response
        
        # Create test file
        test_file = temp_music_dirs["input"] / "unidentifiable.mp3"
        test_file.write_text("fake mp3 content")
        
        # Initialize components
        config = get_config(
            acoustid_api_key="test_key",
            input_dir=temp_music_dirs["input"],
            identified_dir=temp_music_dirs["identified"],
            unidentified_dir=temp_music_dirs["unidentified"],
            min_confidence=0.5
        )
        
        identifier = MusicIdentifier(config=config)
        organizer = FileOrganizer(
            config.identified_dir,
            config.unidentified_dir
        )
        
        # Identify file
        result = identifier.identify_file(test_file)
        
        assert result.identified is False
        assert result.error is not None
        
        # Organize to unidentified folder
        new_path = organizer.organize_file(result, dry_run=False, rename=False)
        
        assert new_path is not None
        assert new_path.parent == temp_music_dirs["unidentified"]
        assert new_path.name == "unidentifiable.mp3"
    
    def test_batch_processing(self, temp_music_dirs):
        """Test processing multiple files."""
        # Create multiple test files
        files = []
        for i in range(3):
            file_path = temp_music_dirs["input"] / f"song{i}.mp3"
            file_path.write_text(f"content {i}")
            files.append(file_path)
        
        # Find all MP3 files
        found_files = list(temp_music_dirs["input"].glob("*.mp3"))
        
        assert len(found_files) == 3
        assert all(f.exists() for f in found_files)
    
    def test_organizer_statistics(self, temp_music_dirs):
        """Test statistics after organizing files."""
        organizer = FileOrganizer(
            temp_music_dirs["identified"],
            temp_music_dirs["unidentified"]
        )
        
        # Create some files in each directory
        (temp_music_dirs["identified"] / "identified1.mp3").write_text("1")
        (temp_music_dirs["identified"] / "identified2.mp3").write_text("2")
        (temp_music_dirs["unidentified"] / "unknown1.mp3").write_text("3")
        
        stats = organizer.get_stats()
        
        assert stats["identified_count"] == 2
        assert stats["unidentified_count"] == 1
        assert stats["total_count"] == 3


@pytest.mark.mock
class TestErrorHandling:
    """Tests for error handling and edge cases."""
    
    def test_missing_fpcalc(self, temp_music_dirs):
        """Test graceful handling when fpcalc is not installed."""
        config = get_config(
            acoustid_api_key="test_key",
            input_dir=temp_music_dirs["input"],
            fpcalc_path="/nonexistent/fpcalc"
        )
        
        identifier = MusicIdentifier(config=config)
        
        test_file = temp_music_dirs["input"] / "test.mp3"
        test_file.write_text("content")
        
        with patch('subprocess.run', side_effect=FileNotFoundError()):
            result = identifier.identify_file(test_file)
        
        assert result.identified is False
        assert "fingerprint" in result.error.lower()
    
    @patch('requests.post')
    def test_api_network_error(self, mock_post, temp_music_dirs):
        """Test handling of network errors."""
        import requests as req_module
        mock_post.side_effect = req_module.exceptions.ConnectionError()
        
        config = get_config(
            acoustid_api_key="test_key",
            max_retries=1,
            retry_delay=0.1
        )
        
        identifier = MusicIdentifier(config=config)
        results = identifier.query_acoustid("fingerprint", 180)
        
        assert results is None
    
    def test_file_permission_error(self, temp_music_dirs):
        """Test handling of file permission errors."""
        organizer = FileOrganizer(
            temp_music_dirs["identified"],
            temp_music_dirs["unidentified"]
        )
        
        # Create a file
        source_file = temp_music_dirs["input"] / "test.mp3"
        source_file.write_text("content")
        
        from tools.music_identifier.identifier import IdentificationResult
        result = IdentificationResult(
            filepath=source_file,
            identified=True,
            title="Test",
            artist="Artist"
        )
        
        # Mock shutil.move to raise PermissionError
        with patch('shutil.move', side_effect=PermissionError()):
            new_path = organizer.organize_file(result, dry_run=False)
        
        assert new_path is None
