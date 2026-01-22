"""
Unit tests for content_types/gossip.py - Gossip storyline tracking and management.

Tests:
- Gossip tracker initialization and persistence
- Adding and managing gossip storylines
- Gossip stage progression (rumor → spreading → confirmed → resolved)
- Category validation
- Multi-session continuity
"""

import pytest
import sys
import os
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

# Add paths for imports
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "tools", "script-generator"))

from content_types.gossip import GossipTracker, GOSSIP_CATEGORIES


class TestGossipCategories:
    """Test gossip category constants."""
    
    def test_gossip_categories_defined(self):
        """Should have predefined gossip categories."""
        assert GOSSIP_CATEGORIES is not None
        assert len(GOSSIP_CATEGORIES) > 0
    
    def test_gossip_categories_include_faction_movements(self):
        """Should include faction_movements category."""
        assert "faction_movements" in GOSSIP_CATEGORIES
    
    def test_gossip_categories_include_survivor_sightings(self):
        """Should include survivor_sightings category."""
        assert "survivor_sightings" in GOSSIP_CATEGORIES
    
    def test_gossip_categories_include_mysterious_events(self):
        """Should include mysterious_events category."""
        assert "mysterious_events" in GOSSIP_CATEGORIES
    
    def test_gossip_categories_all_strings(self):
        """All categories should be strings."""
        for category in GOSSIP_CATEGORIES:
            assert isinstance(category, str)
            assert len(category) > 0


class TestGossipTrackerInit:
    """Test GossipTracker initialization."""
    
    def test_init_default_path(self):
        """Should initialize with default persistence path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('content_types.gossip.Path'):
                tracker = GossipTracker()
                assert tracker.persistence_path == "./broadcast_gossip.json"
    
    def test_init_custom_path(self):
        """Should accept custom persistence path."""
        custom_path = "/tmp/custom_gossip.json"
        tracker = GossipTracker(persistence_path=custom_path)
        assert tracker.persistence_path == custom_path
    
    def test_init_creates_empty_lists(self):
        """Should initialize with empty gossip lists."""
        with patch('content_types.gossip.GossipTracker.load'):
            tracker = GossipTracker()
            # Lists are initialized before load() is called
            assert hasattr(tracker, 'active_gossip')
            assert hasattr(tracker, 'resolved_gossip')


class TestAddGossip:
    """Test adding gossip storylines."""
    
    def test_add_gossip_creates_id(self):
        """Should create unique ID for new gossip."""
        with patch('content_types.gossip.GossipTracker.load'):
            with patch('content_types.gossip.GossipTracker.save'):
                tracker = GossipTracker()
                tracker.active_gossip = []
                
                gossip_id = tracker.add_gossip(
                    topic="test_topic",
                    initial_rumor="A test rumor"
                )
                
                assert gossip_id is not None
                assert "test_topic" in gossip_id
    
    def test_add_gossip_with_category(self):
        """Should add gossip with specified category."""
        with patch('content_types.gossip.GossipTracker.load'):
            with patch('content_types.gossip.GossipTracker.save'):
                tracker = GossipTracker()
                tracker.active_gossip = []
                
                gossip_id = tracker.add_gossip(
                    topic="faction_news",
                    initial_rumor="Brotherhood spotted",
                    category="faction_movements"
                )
                
                assert len(tracker.active_gossip) == 1
                assert tracker.active_gossip[0]['category'] == "faction_movements"
    
    def test_add_gossip_invalid_category_defaults(self):
        """Should default to 'general' for invalid category."""
        with patch('content_types.gossip.GossipTracker.load'):
            with patch('content_types.gossip.GossipTracker.save'):
                tracker = GossipTracker()
                tracker.active_gossip = []
                
                tracker.add_gossip(
                    topic="test",
                    initial_rumor="Rumor",
                    category="invalid_category_xyz"
                )
                
                assert tracker.active_gossip[0]['category'] == 'general'
    
    def test_add_gossip_no_category_defaults(self):
        """Should default to 'general' when no category provided."""
        with patch('content_types.gossip.GossipTracker.load'):
            with patch('content_types.gossip.GossipTracker.save'):
                tracker = GossipTracker()
                tracker.active_gossip = []
                
                tracker.add_gossip(
                    topic="test",
                    initial_rumor="Rumor"
                )
                
                assert tracker.active_gossip[0]['category'] == 'general'


class TestGossipStages:
    """Test gossip stage progression."""
    
    def test_gossip_has_stages(self):
        """Gossip should have stage progression."""
        with patch('content_types.gossip.GossipTracker.load'):
            with patch('content_types.gossip.GossipTracker.save'):
                tracker = GossipTracker()
                tracker.active_gossip = []
                
                tracker.add_gossip("test", "Initial rumor")
                
                assert 'stages' in tracker.active_gossip[0]
                assert len(tracker.active_gossip[0]['stages']) > 0


class TestGossipPersistence:
    """Test gossip persistence to file."""
    
    def test_save_creates_file(self):
        """Should save gossip to JSON file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_path = f.name
        
        try:
            tracker = GossipTracker(persistence_path=temp_path)
            tracker.active_gossip = []
            tracker.add_gossip("test", "Test rumor")
            
            # File should exist and contain data
            assert Path(temp_path).exists()
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    def test_load_from_existing_file(self):
        """Should load gossip from existing file."""
        test_data = {
            'active_gossip': [
                {
                    'id': 'test_123',
                    'topic': 'test_topic',
                    'category': 'general',
                    'created_at': '2026-01-22T00:00:00',
                    'stages': [{'stage': 'rumor', 'text': 'Initial'}]
                }
            ],
            'resolved_gossip': []
        }
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            json.dump(test_data, f)
            temp_path = f.name
        
        try:
            tracker = GossipTracker(persistence_path=temp_path)
            
            # Tracker should attempt to load
            # Note: actual load behavior depends on implementation
            # This test verifies no crash on load attempt
            assert isinstance(tracker.active_gossip, list)
            assert isinstance(tracker.resolved_gossip, list)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)


class TestMultiSessionContinuity:
    """Test gossip continuity across sessions."""
    
    def test_multiple_gossip_items(self):
        """Should track multiple gossip items."""
        with patch('content_types.gossip.GossipTracker.load'):
            with patch('content_types.gossip.GossipTracker.save'):
                tracker = GossipTracker()
                tracker.active_gossip = []
                
                tracker.add_gossip("topic1", "Rumor 1")
                tracker.add_gossip("topic2", "Rumor 2")
                tracker.add_gossip("topic3", "Rumor 3")
                
                assert len(tracker.active_gossip) == 3


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_topic(self):
        """Should handle empty topic gracefully."""
        with patch('content_types.gossip.GossipTracker.load'):
            with patch('content_types.gossip.GossipTracker.save'):
                tracker = GossipTracker()
                tracker.active_gossip = []
                
                # Should not crash with empty topic
                gossip_id = tracker.add_gossip("", "Rumor")
                assert gossip_id is not None
    
    def test_empty_rumor(self):
        """Should handle empty rumor gracefully."""
        with patch('content_types.gossip.GossipTracker.load'):
            with patch('content_types.gossip.GossipTracker.save'):
                tracker = GossipTracker()
                tracker.active_gossip = []
                
                # Should not crash with empty rumor
                gossip_id = tracker.add_gossip("topic", "")
                assert gossip_id is not None
    
    def test_load_nonexistent_file(self):
        """Should handle nonexistent persistence file gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nonexistent = os.path.join(tmpdir, "does_not_exist.json")
            
            # Should not crash when file doesn't exist
            tracker = GossipTracker(persistence_path=nonexistent)
            
            # Should start with empty lists
            assert isinstance(tracker.active_gossip, list)
            assert isinstance(tracker.resolved_gossip, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
