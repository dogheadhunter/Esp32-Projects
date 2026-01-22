"""
Unit tests for broadcast_freshness.py - Content freshness tracking system.

Tests:
- Freshness score calculation
- Linear decay over 7 days
- ChromaDB integration
- Content repetition prevention
"""

import pytest
import sys
import os
import time
from unittest.mock import Mock, patch, MagicMock

# Add paths for imports
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "tools", "script-generator"))

from broadcast_freshness import BroadcastFreshnessTracker


class TestFreshnessTrackerInit:
    """Test BroadcastFreshnessTracker initialization."""
    
    def test_init_default_path(self):
        """Should initialize with default ChromaDB path."""
        with patch('broadcast_freshness.CHROMADB_AVAILABLE', False):
            tracker = BroadcastFreshnessTracker()
            assert tracker.chroma_db_path is not None
    
    def test_init_custom_path(self):
        """Should accept custom ChromaDB path."""
        custom_path = "/custom/path/to/chroma"
        with patch('broadcast_freshness.CHROMADB_AVAILABLE', False):
            tracker = BroadcastFreshnessTracker(chroma_db_path=custom_path)
            assert tracker.chroma_db_path == custom_path
    
    def test_init_sets_decay_hours(self):
        """Should set full decay hours to 168 (7 days)."""
        with patch('broadcast_freshness.CHROMADB_AVAILABLE', False):
            tracker = BroadcastFreshnessTracker()
            assert tracker.FULL_DECAY_HOURS == 168.0


class TestFreshnessScoreCalculation:
    """Test freshness score calculation."""
    
    def test_never_used_content_is_fresh(self):
        """Content never used should have freshness 1.0."""
        with patch('broadcast_freshness.CHROMADB_AVAILABLE', False):
            tracker = BroadcastFreshnessTracker()
            
            freshness = tracker.calculate_freshness_score(
                last_broadcast_time=None,
                current_time=time.time()
            )
            
            assert freshness == 1.0
    
    def test_just_used_content_is_stale(self):
        """Content just used should have freshness 0.0."""
        with patch('broadcast_freshness.CHROMADB_AVAILABLE', False):
            tracker = BroadcastFreshnessTracker()
            
            current_time = time.time()
            last_used = current_time  # Just now
            
            freshness = tracker.calculate_freshness_score(
                last_broadcast_time=last_used,
                current_time=current_time
            )
            
            assert freshness == 0.0
    
    def test_half_decay_content_is_moderate(self):
        """Content used 84 hours ago should have freshness 0.5."""
        with patch('broadcast_freshness.CHROMADB_AVAILABLE', False):
            tracker = BroadcastFreshnessTracker()
            
            current_time = time.time()
            last_used = current_time - (84 * 3600)  # 84 hours ago (3.5 days)
            
            freshness = tracker.calculate_freshness_score(
                last_broadcast_time=last_used,
                current_time=current_time
            )
            
            # Should be approximately 0.5 (84/168 = 0.5)
            assert 0.49 < freshness < 0.51
    
    def test_fully_decayed_content_is_fresh(self):
        """Content used 168+ hours ago should have freshness 1.0."""
        with patch('broadcast_freshness.CHROMADB_AVAILABLE', False):
            tracker = BroadcastFreshnessTracker()
            
            current_time = time.time()
            last_used = current_time - (168 * 3600)  # 168 hours ago (7 days)
            
            freshness = tracker.calculate_freshness_score(
                last_broadcast_time=last_used,
                current_time=current_time
            )
            
            assert freshness == 1.0
    
    def test_over_decayed_content_caps_at_1_0(self):
        """Content used >7 days ago should cap at freshness 1.0."""
        with patch('broadcast_freshness.CHROMADB_AVAILABLE', False):
            tracker = BroadcastFreshnessTracker()
            
            current_time = time.time()
            last_used = current_time - (300 * 3600)  # 300 hours ago (12.5 days)
            
            freshness = tracker.calculate_freshness_score(
                last_broadcast_time=last_used,
                current_time=current_time
            )
            
            assert freshness == 1.0


class TestLinearDecay:
    """Test linear freshness decay formula."""
    
    def test_freshness_increases_with_time(self):
        """Freshness should increase as time passes since last use."""
        with patch('broadcast_freshness.CHROMADB_AVAILABLE', False):
            tracker = BroadcastFreshnessTracker()
            
            current_time = time.time()
            
            # Calculate freshness at different time intervals
            freshness_1h = tracker.calculate_freshness_score(
                last_broadcast_time=current_time - (1 * 3600),
                current_time=current_time
            )
            
            freshness_24h = tracker.calculate_freshness_score(
                last_broadcast_time=current_time - (24 * 3600),
                current_time=current_time
            )
            
            freshness_48h = tracker.calculate_freshness_score(
                last_broadcast_time=current_time - (48 * 3600),
                current_time=current_time
            )
            
            # Freshness should increase over time
            assert freshness_1h < freshness_24h < freshness_48h
    
    def test_decay_formula_is_linear(self):
        """Freshness decay should be linear: hours_since_use / 168."""
        with patch('broadcast_freshness.CHROMADB_AVAILABLE', False):
            tracker = BroadcastFreshnessTracker()
            
            current_time = time.time()
            
            # Test specific points on the linear curve
            test_cases = [
                (0, 0.0),       # Just used
                (42, 0.25),     # 1/4 of 7 days
                (84, 0.5),      # 1/2 of 7 days
                (126, 0.75),    # 3/4 of 7 days
                (168, 1.0),     # Full 7 days
            ]
            
            for hours, expected_freshness in test_cases:
                last_used = current_time - (hours * 3600)
                freshness = tracker.calculate_freshness_score(
                    last_broadcast_time=last_used,
                    current_time=current_time
                )
                
                assert abs(freshness - expected_freshness) < 0.01


class TestCurrentTimeParameter:
    """Test current_time parameter handling."""
    
    def test_uses_provided_current_time(self):
        """Should use provided current_time instead of time.time()."""
        with patch('broadcast_freshness.CHROMADB_AVAILABLE', False):
            tracker = BroadcastFreshnessTracker()
            
            fixed_current_time = 1000000.0
            last_used = fixed_current_time - (84 * 3600)  # 84 hours ago
            
            freshness = tracker.calculate_freshness_score(
                last_broadcast_time=last_used,
                current_time=fixed_current_time
            )
            
            assert 0.49 < freshness < 0.51
    
    def test_defaults_to_time_time_when_none(self):
        """Should use time.time() when current_time is None."""
        with patch('broadcast_freshness.CHROMADB_AVAILABLE', False):
            with patch('time.time') as mock_time:
                mock_time.return_value = 2000000.0
                
                tracker = BroadcastFreshnessTracker()
                
                last_used = 2000000.0 - (84 * 3600)
                
                freshness = tracker.calculate_freshness_score(
                    last_broadcast_time=last_used,
                    current_time=None  # Should use time.time()
                )
                
                assert 0.49 < freshness < 0.51


class TestChromaDBIntegration:
    """Test ChromaDB integration."""
    
    def test_chromadb_not_available_mode(self):
        """Should handle ChromaDB not being available."""
        with patch('broadcast_freshness.CHROMADB_AVAILABLE', False):
            tracker = BroadcastFreshnessTracker()
            
            assert tracker.client is None
            assert tracker.collection is None
    
    def test_chromadb_available_attempts_connection(self):
        """Should attempt ChromaDB connection when available."""
        with patch('broadcast_freshness.CHROMADB_AVAILABLE', True):
            # Mock the chromadb module at package level
            import sys
            mock_chromadb = Mock()
            mock_collection = Mock()
            mock_client_instance = Mock()
            mock_client_instance.get_collection.return_value = mock_collection
            mock_chromadb.PersistentClient.return_value = mock_client_instance
            
            sys.modules['chromadb'] = mock_chromadb
            
            try:
                # Reimport to get new chromadb mock
                import importlib
                import broadcast_freshness
                importlib.reload(broadcast_freshness)
                
                tracker = broadcast_freshness.BroadcastFreshnessTracker()
                
                # Should have attempted connection
                assert tracker.client is not None or tracker.collection is not None
            finally:
                # Clean up
                if 'chromadb' in sys.modules:
                    del sys.modules['chromadb']


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_negative_time_difference(self):
        """Should handle negative time differences gracefully."""
        with patch('broadcast_freshness.CHROMADB_AVAILABLE', False):
            tracker = BroadcastFreshnessTracker()
            
            current_time = time.time()
            future_time = current_time + 3600  # 1 hour in future
            
            # Should handle gracefully - negative hours becomes 0 freshness
            freshness = tracker.calculate_freshness_score(
                last_broadcast_time=future_time,
                current_time=current_time
            )
            
            # Negative time difference should result in 0 or near-0 freshness
            assert freshness <= 0.01  # Allow small negative values to round to near 0
    
    def test_very_large_time_difference(self):
        """Should handle very large time differences."""
        with patch('broadcast_freshness.CHROMADB_AVAILABLE', False):
            tracker = BroadcastFreshnessTracker()
            
            current_time = time.time()
            very_old = current_time - (365 * 24 * 3600)  # 1 year ago
            
            freshness = tracker.calculate_freshness_score(
                last_broadcast_time=very_old,
                current_time=current_time
            )
            
            assert freshness == 1.0


class TestDecayParameters:
    """Test freshness decay parameters."""
    
    def test_full_decay_hours_is_one_week(self):
        """Full decay should be 168 hours (7 days)."""
        with patch('broadcast_freshness.CHROMADB_AVAILABLE', False):
            tracker = BroadcastFreshnessTracker()
            
            assert tracker.FULL_DECAY_HOURS == 168.0
            assert tracker.FULL_DECAY_HOURS == 7 * 24  # 7 days * 24 hours


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
