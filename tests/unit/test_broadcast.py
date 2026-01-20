"""
Unit tests for broadcast.py CLI

Tests the command-line interface with mocked dependencies.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import json

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import broadcast


@pytest.mark.mock
class TestBroadcastCLI:
    """Test suite for broadcast.py CLI interface"""
    
    def test_dj_name_resolution(self):
        """Test DJ name resolution from shortcuts"""
        # Test shortcuts
        assert broadcast.resolve_dj_name('julie') == "Julie (2102, Appalachia)"
        assert broadcast.resolve_dj_name('vegas') == "Mr. New Vegas (2281, Mojave)"
        assert broadcast.resolve_dj_name('travis') == "Travis Miles (Nervous) (2287, Commonwealth)"
        
    def test_dj_name_case_insensitive(self):
        """Test that DJ shortcuts are case-insensitive"""
        assert broadcast.resolve_dj_name('JULIE') == "Julie (2102, Appalachia)"
        assert broadcast.resolve_dj_name('Vegas') == "Mr. New Vegas (2281, Mojave)"
    
    def test_dj_full_name_resolution(self):
        """Test resolving DJ by full name"""
        result = broadcast.resolve_dj_name('Julie')
        assert 'Julie' in result
        assert 'Appalachia' in result
    
    def test_invalid_dj_name(self):
        """Test that invalid DJ name exits with error"""
        with pytest.raises(SystemExit):
            broadcast.resolve_dj_name('invalid_dj')
    
    def test_output_filename_generation(self):
        """Test generation of output filenames"""
        # Test with days
        filename = broadcast.generate_output_filename(
            dj_name="Julie (2102, Appalachia)",
            duration_hours=56,  # 7 days
            enable_stories=False
        )
        assert 'Julie' in filename
        assert '7day' in filename
        assert filename.endswith('.json')
        
        # Test with hours
        filename = broadcast.generate_output_filename(
            dj_name="Mr. New Vegas (2281, Mojave)",
            duration_hours=4,
            enable_stories=False
        )
        assert 'Mr.-New-Vegas' in filename or 'Mr-New-Vegas' in filename
        assert '4hr' in filename
    
    def test_output_filename_with_stories(self):
        """Test filename generation with story system enabled"""
        filename = broadcast.generate_output_filename(
            dj_name="Julie (2102, Appalachia)",
            duration_hours=56,
            enable_stories=True
        )
        assert '_stories' in filename
    
    @patch('broadcast.BroadcastEngine')
    def test_main_with_mock_engine(self, mock_engine_class, tmp_output_dir, monkeypatch):
        """Test main() function with mocked BroadcastEngine"""
        # Setup mock
        mock_engine = MagicMock()
        mock_engine.generate_broadcast_sequence.return_value = [
            {
                'segment_type': 'weather',
                'content': 'Test weather segment',
                'timestamp': '2102-08-15T08:00:00'
            }
        ]
        mock_engine.end_broadcast.return_value = {
            'total_time': 10.5,
            'avg_time_per_segment': 5.25,
            'validation_failures': 0
        }
        mock_engine_class.return_value = mock_engine
        
        # Patch sys.argv
        test_args = [
            'broadcast.py',
            '--dj', 'julie',
            '--hours', '4',
            '--output', str(tmp_output_dir / 'test_broadcast.json')
        ]
        monkeypatch.setattr(sys, 'argv', test_args)
        
        # Run main
        result = broadcast.main()
        
        # Assert
        assert result == 0
        mock_engine_class.assert_called_once()
        mock_engine.start_broadcast.assert_called_once()
        mock_engine.generate_broadcast_sequence.assert_called_once()
        mock_engine.end_broadcast.assert_called_once()
        
        # Check output file was created
        output_file = tmp_output_dir / 'test_broadcast.json'
        assert output_file.exists()
        
        # Check output file contents
        with open(output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert 'metadata' in data
        assert 'segments' in data
        assert data['metadata']['dj'] == "Julie (2102, Appalachia)"
        assert data['metadata']['duration_hours'] == 4
    
    @patch('broadcast.BroadcastEngine')
    def test_keyboard_interrupt_handling(self, mock_engine_class, monkeypatch, capsys):
        """Test that Ctrl+C (KeyboardInterrupt) is handled gracefully"""
        # Setup mock to raise KeyboardInterrupt
        mock_engine = MagicMock()
        mock_engine.generate_broadcast_sequence.side_effect = KeyboardInterrupt()
        mock_engine_class.return_value = mock_engine
        
        # Patch sys.argv
        test_args = [
            'broadcast.py',
            '--dj', 'julie',
            '--hours', '4'
        ]
        monkeypatch.setattr(sys, 'argv', test_args)
        
        # Run main
        result = broadcast.main()
        
        # Assert proper exit code for user cancellation
        assert result == 130
        
        # Check that cancellation message was printed
        captured = capsys.readouterr()
        assert 'cancelled' in captured.out.lower() or 'cancelled' in captured.err.lower()
    
    @patch('broadcast.BroadcastEngine')
    def test_exception_handling(self, mock_engine_class, monkeypatch, capsys):
        """Test that exceptions are handled and logged"""
        # Setup mock to raise exception
        mock_engine = MagicMock()
        mock_engine.generate_broadcast_sequence.side_effect = RuntimeError("Test error")
        mock_engine_class.return_value = mock_engine
        
        # Patch sys.argv
        test_args = [
            'broadcast.py',
            '--dj', 'julie',
            '--hours', '4'
        ]
        monkeypatch.setattr(sys, 'argv', test_args)
        
        # Run main
        result = broadcast.main()
        
        # Assert error exit code
        assert result == 1
        
        # Check that error message was printed
        captured = capsys.readouterr()
        assert 'error' in captured.out.lower() or 'error' in captured.err.lower()
    
    def test_parse_args_days(self, monkeypatch):
        """Test argument parsing with --days option"""
        test_args = [
            'broadcast.py',
            '--dj', 'julie',
            '--days', '7'
        ]
        monkeypatch.setattr(sys, 'argv', test_args)
        
        args = broadcast.parse_args()
        
        assert args.dj == 'julie'
        assert args.days == 7
        assert args.hours is None
    
    def test_parse_args_hours(self, monkeypatch):
        """Test argument parsing with --hours option"""
        test_args = [
            'broadcast.py',
            '--dj', 'vegas',
            '--hours', '24'
        ]
        monkeypatch.setattr(sys, 'argv', test_args)
        
        args = broadcast.parse_args()
        
        assert args.dj == 'vegas'
        assert args.hours == 24
        assert args.days is None
    
    def test_parse_args_validation_options(self, monkeypatch):
        """Test argument parsing with validation options"""
        test_args = [
            'broadcast.py',
            '--dj', 'julie',
            '--hours', '4',
            '--enable-validation',
            '--validation-mode', 'hybrid',
            '--validation-model', 'custom-model'
        ]
        monkeypatch.setattr(sys, 'argv', test_args)
        
        args = broadcast.parse_args()
        
        assert args.enable_validation is True
        assert args.validation_mode == 'hybrid'
        assert args.validation_model == 'custom-model'
    
    def test_parse_args_story_options(self, monkeypatch):
        """Test argument parsing with story system options"""
        test_args = [
            'broadcast.py',
            '--dj', 'julie',
            '--hours', '4',
            '--enable-stories'
        ]
        monkeypatch.setattr(sys, 'argv', test_args)
        
        args = broadcast.parse_args()
        
        assert args.enable_stories is True
        assert args.disable_stories is False
    
    def test_print_header(self, capsys):
        """Test print_header function"""
        class Args:
            quiet = False
            start_hour = 8
            segments_per_hour = 2
            enable_stories = True
            enable_validation = True
            validation_mode = 'hybrid'
        
        args = Args()
        broadcast.print_header(
            args=args,
            dj_name="Julie (2102, Appalachia)",
            duration_hours=24,
            enable_validation=True
        )
        
        captured = capsys.readouterr()
        assert 'Julie' in captured.out
        assert '24 hours' in captured.out
        assert 'ENABLED' in captured.out
    
    def test_print_header_quiet_mode(self, capsys):
        """Test that print_header doesn't output in quiet mode"""
        class Args:
            quiet = True
            start_hour = 8
            segments_per_hour = 2
            enable_stories = False
            enable_validation = False
            validation_mode = 'rules'
        
        args = Args()
        broadcast.print_header(
            args=args,
            dj_name="Julie (2102, Appalachia)",
            duration_hours=24
        )
        
        captured = capsys.readouterr()
        assert captured.out == ''
    
    def test_print_summary(self, capsys):
        """Test print_summary function"""
        segments = [
            {'segment_type': 'weather'},
            {'segment_type': 'news'},
            {'segment_type': 'gossip'},
            {'segment_type': 'weather'},
        ]
        stats = {
            'total_time': 20.5,
            'avg_time_per_segment': 5.125,
            'validation_failures': 0
        }
        
        broadcast.print_summary(
            segments=segments,
            stats=stats,
            output_file=Path('test_output.json'),
            quiet=False
        )
        
        captured = capsys.readouterr()
        assert 'GENERATION COMPLETE' in captured.out
        assert '4' in captured.out  # Total segments
        assert 'weather' in captured.out
        assert '20.5' in captured.out  # Total time


@pytest.mark.mock
class TestBroadcastHelpers:
    """Test suite for broadcast.py helper functions"""
    
    def test_dj_shortcuts_complete(self):
        """Test that all DJ shortcuts are defined"""
        expected_shortcuts = ['julie', 'vegas', 'travis', 'travis-confident', 'threedog', '3dog']
        for shortcut in expected_shortcuts:
            assert shortcut in broadcast.DJ_SHORTCUTS
    
    def test_available_djs_list(self):
        """Test that all available DJs are listed"""
        assert len(broadcast.AVAILABLE_DJS) >= 4
        
        # Check for main DJs
        dj_names = ' '.join(broadcast.AVAILABLE_DJS)
        assert 'Julie' in dj_names
        assert 'Mr. New Vegas' in dj_names or 'Mr New Vegas' in dj_names
        assert 'Travis Miles' in dj_names
