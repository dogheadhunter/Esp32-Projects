"""
Unit tests for broadcast.py CLI

Tests the command-line interface with mocked dependencies.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock
import json
import io

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


@pytest.mark.mock
class TestBroadcastCLI:
    """Test suite for broadcast.py CLI interface"""
    
    def test_dj_name_resolution(self):
        """Test DJ name resolution from shortcuts"""
        # Import broadcast module with mocked dependencies
        with patch.dict('sys.modules', {
            'broadcast_engine': MagicMock(),
            'tools.script-generator': MagicMock()
        }):
            import broadcast
            
            # Test shortcuts
            assert broadcast.resolve_dj_name('julie') == "Julie (2102, Appalachia)"
            assert broadcast.resolve_dj_name('vegas') == "Mr. New Vegas (2281, Mojave)"
            assert broadcast.resolve_dj_name('travis') == "Travis Miles (Nervous) (2287, Commonwealth)"
    
    def test_dj_name_case_insensitive(self):
        """Test that DJ shortcuts are case-insensitive"""
        with patch.dict('sys.modules', {
            'broadcast_engine': MagicMock(),
            'tools.script-generator': MagicMock()
        }):
            import broadcast
            
            assert broadcast.resolve_dj_name('JULIE') == "Julie (2102, Appalachia)"
            assert broadcast.resolve_dj_name('Vegas') == "Mr. New Vegas (2281, Mojave)"
    
    def test_dj_full_name_resolution(self):
        """Test resolving DJ by full name"""
        with patch.dict('sys.modules', {
            'broadcast_engine': MagicMock(),
            'tools.script-generator': MagicMock()
        }):
            import broadcast
            
            result = broadcast.resolve_dj_name('Julie')
            assert 'Julie' in result
            assert 'Appalachia' in result
    
    def test_invalid_dj_name(self):
        """Test that invalid DJ name exits with error"""
        with patch.dict('sys.modules', {
            'broadcast_engine': MagicMock(),
            'tools.script-generator': MagicMock()
        }):
            import broadcast
            
            with pytest.raises(SystemExit):
                broadcast.resolve_dj_name('invalid_dj')
    
    def test_output_filename_generation(self):
        """Test generation of output filenames"""
        with patch.dict('sys.modules', {
            'broadcast_engine': MagicMock(),
            'tools.script-generator': MagicMock()
        }):
            import broadcast
            
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
            assert 'Mr.' in filename or 'Mr-New-Vegas' in filename
            assert '4hr' in filename
    
    def test_output_filename_with_stories(self):
        """Test filename generation with story system enabled"""
        with patch.dict('sys.modules', {
            'broadcast_engine': MagicMock(),
            'tools.script-generator': MagicMock()
        }):
            import broadcast
            
            filename = broadcast.generate_output_filename(
                dj_name="Julie (2102, Appalachia)",
                duration_hours=56,
                enable_stories=True
            )
            assert '_stories' in filename


@pytest.mark.mock
class TestBroadcastHelpers:
    """Test suite for broadcast.py helper functions"""
    
    def test_dj_shortcuts_complete(self):
        """Test that all DJ shortcuts are defined"""
        with patch.dict('sys.modules', {
            'broadcast_engine': MagicMock(),
            'tools.script-generator': MagicMock()
        }):
            import broadcast
            
            expected_shortcuts = ['julie', 'vegas', 'travis', 'travis-confident', 'threedog', '3dog']
            for shortcut in expected_shortcuts:
                assert shortcut in broadcast.DJ_SHORTCUTS
    
    def test_available_djs_list(self):
        """Test that all available DJs are listed"""
        with patch.dict('sys.modules', {
            'broadcast_engine': MagicMock(),
            'tools.script-generator': MagicMock()
        }):
            import broadcast
            
            assert len(broadcast.AVAILABLE_DJS) >= 4
            
            # Check for main DJs
            dj_names = ' '.join(broadcast.AVAILABLE_DJS)
            assert 'Julie' in dj_names
            assert 'Mr. New Vegas' in dj_names or 'Mr New Vegas' in dj_names
            assert 'Travis Miles' in dj_names
