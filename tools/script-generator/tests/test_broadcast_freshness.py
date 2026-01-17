"""
Tests for Phase 6 Task 4: Broadcast Freshness Tracking System
"""

import pytest
import time
from broadcast_freshness import BroadcastFreshnessTracker


class TestFreshnessCalculation:
    """Test freshness score calculation"""
    
    def setup_method(self):
        self.tracker = BroadcastFreshnessTracker("test_db")
    
    def test_never_used_is_fresh(self):
        """Test that never-used content has freshness 1.0"""
        freshness = self.tracker.calculate_freshness_score(None)
        assert freshness == 1.0
    
    def test_just_used_is_stale(self):
        """Test that just-used content has freshness 0.0"""
        current = time.time()
        freshness = self.tracker.calculate_freshness_score(current, current)
        assert freshness == 0.0
    
    def test_one_hour_ago(self):
        """Test freshness for content used 1 hour ago"""
        current = time.time()
        one_hour_ago = current - 3600
        freshness = self.tracker.calculate_freshness_score(one_hour_ago, current)
        
        # 1 hour / 168 hours = ~0.006 freshness (very stale)
        assert 0.005 < freshness < 0.007
    
    def test_half_decay_period(self):
        """Test freshness at half decay period (84 hours = 3.5 days)"""
        current = time.time()
        half_period = current - (84 * 3600)  # 84 hours
        freshness = self.tracker.calculate_freshness_score(half_period, current)
        
        # 84 / 168 = 0.5, so freshness should be ~0.5
        assert 0.45 < freshness < 0.55
    
    def test_full_decay_period(self):
        """Test freshness at full recovery period (168 hours = 7 days)"""
        current = time.time()
        full_period = current - (168 * 3600)  # 168 hours
        freshness = self.tracker.calculate_freshness_score(full_period, current)
        
        # 168 / 168 = 1.0, so freshness should be 1.0 (fully fresh again)
        assert freshness == 1.0
    
    def test_beyond_decay_period(self):
        """Test freshness beyond recovery period (8+ days)"""
        current = time.time()
        beyond = current - (200 * 3600)  # 200 hours
        freshness = self.tracker.calculate_freshness_score(beyond, current)
        
        # Should be clamped at 1.0 (fully fresh)
        assert freshness == 1.0
    
    def test_linear_decay(self):
        """Test that freshness recovery is linear"""
        current = time.time()
        
        # Test at 25%, 50%, 75% of recovery period
        test_points = [
            (42 * 3600, 0.25),   # 25% of 168 hours
            (84 * 3600, 0.50),   # 50% of 168 hours
            (126 * 3600, 0.75),  # 75% of 168 hours
        ]
        
        for hours_ago_seconds, expected_freshness in test_points:
            test_time = current - hours_ago_seconds
            freshness = self.tracker.calculate_freshness_score(test_time, current)
            assert abs(freshness - expected_freshness) < 0.01


class TestFreshContentFilter:
    """Test fresh content filter generation"""
    
    def setup_method(self):
        self.tracker = BroadcastFreshnessTracker("test_db")
    
    def test_default_filter(self):
        """Test default filter (min_freshness=0.3)"""
        filter_dict = self.tracker.get_fresh_content_filter()
        
        assert "freshness_score" in filter_dict
        assert "$gte" in filter_dict["freshness_score"]
        assert filter_dict["freshness_score"]["$gte"] == 0.3
    
    def test_custom_filter(self):
        """Test custom min_freshness value"""
        filter_dict = self.tracker.get_fresh_content_filter(min_freshness=0.7)
        
        assert filter_dict["freshness_score"]["$gte"] == 0.7
    
    def test_filter_very_fresh(self):
        """Test filter for very fresh content"""
        filter_dict = self.tracker.get_fresh_content_filter(min_freshness=0.9)
        
        assert filter_dict["freshness_score"]["$gte"] == 0.9


class TestTrackerInitialization:
    """Test tracker initialization"""
    
    def test_init_with_default_path(self):
        """Test initialization with default path"""
        tracker = BroadcastFreshnessTracker()
        assert tracker.chroma_db_path is not None
        assert tracker.FULL_DECAY_HOURS == 168.0
    
    def test_init_with_custom_path(self):
        """Test initialization with custom path"""
        tracker = BroadcastFreshnessTracker("custom/path/to/db")
        assert "custom/path/to/db" in str(tracker.chroma_db_path)
    
    def test_decay_parameters(self):
        """Test that decay parameters are set correctly"""
        tracker = BroadcastFreshnessTracker("test_db")
        assert tracker.FULL_DECAY_HOURS == 168.0  # 7 days


class TestMarkBroadcast:
    """Test marking content as broadcast"""
    
    def setup_method(self):
        self.tracker = BroadcastFreshnessTracker("test_db")
    
    def test_mark_broadcast_without_db(self):
        """Test that marking without DB connection returns 0"""
        # Tracker without DB connection
        result = self.tracker.mark_broadcast(["chunk1", "chunk2"])
        
        # Should return 0 (no updates)
        assert result == 0
    
    def test_mark_broadcast_empty_list(self):
        """Test that marking empty list returns 0"""
        result = self.tracker.mark_broadcast([])
        assert result == 0
    
    def test_mark_broadcast_with_timestamp(self):
        """Test that custom timestamp is accepted"""
        custom_time = time.time() - 3600  # 1 hour ago
        result = self.tracker.mark_broadcast(["chunk1"], timestamp=custom_time)
        
        # Should not error (returns 0 without DB)
        assert result >= 0


class TestDecayFreshnessScores:
    """Test batch freshness decay"""
    
    def setup_method(self):
        self.tracker = BroadcastFreshnessTracker("test_db")
    
    def test_decay_without_db(self):
        """Test that decay without DB connection returns 0"""
        result = self.tracker.decay_freshness_scores()
        assert result == 0
    
    def test_decay_with_custom_time(self):
        """Test that custom current time is accepted"""
        custom_time = time.time() + 3600  # 1 hour in future
        result = self.tracker.decay_freshness_scores(current_time=custom_time)
        
        # Should not error (returns 0 without DB)
        assert result >= 0


class TestFreshnessStats:
    """Test freshness statistics"""
    
    def setup_method(self):
        self.tracker = BroadcastFreshnessTracker("test_db")
    
    def test_stats_without_db(self):
        """Test that stats without DB returns error info"""
        stats = self.tracker.get_freshness_stats()
        
        assert "error" in stats or "total_chunks" in stats
        assert stats.get("total_chunks", 0) == 0


class TestFreshnessScenarios:
    """Test realistic broadcast scenarios"""
    
    def setup_method(self):
        self.tracker = BroadcastFreshnessTracker("test_db")
    
    def test_daily_broadcast_scenario(self):
        """Test content used in daily broadcasts"""
        current = time.time()
        
        # Content used 1 day ago
        yesterday = current - (24 * 3600)
        freshness = self.tracker.calculate_freshness_score(yesterday, current)
        
        # After 24 hours, should have recovered by 24/168 = ~14.3%
        # Freshness should be ~0.143
        assert 0.13 < freshness < 0.15
    
    def test_weekly_broadcast_scenario(self):
        """Test content used in weekly broadcasts"""
        current = time.time()
        
        # Content used 7 days ago
        week_ago = current - (7 * 24 * 3600)
        freshness = self.tracker.calculate_freshness_score(week_ago, current)
        
        # After 7 days (168 hours), should be fully fresh again
        assert freshness == 1.0
    
    def test_immediate_reuse_prevention(self):
        """Test that just-used content has zero freshness"""
        current = time.time()
        freshness = self.tracker.calculate_freshness_score(current, current)
        
        # Should prevent immediate reuse
        assert freshness == 0.0
    
    def test_content_becomes_fresh_again(self):
        """Test that old content becomes fresh again"""
        current = time.time()
        
        # Content used 10 days ago (beyond recovery period)
        old = current - (10 * 24 * 3600)
        freshness = self.tracker.calculate_freshness_score(old, current)
        
        # Should be maximum (1.0) - fully recovered
        assert freshness == 1.0
        
        # Never-used content also has maximum freshness
        never_used_freshness = self.tracker.calculate_freshness_score(None, current)
        assert never_used_freshness == 1.0
    
    def test_gradual_decay_over_week(self):
        """Test that freshness recovery is gradual and predictable"""
        current = time.time()
        
        # Test freshness at each day of the week
        daily_freshness = []
        for day in range(8):  # 0 to 7 days
            hours_ago = day * 24 * 3600
            test_time = current - hours_ago
            freshness = self.tracker.calculate_freshness_score(test_time, current)
            daily_freshness.append(freshness)
        
        # Should be monotonically increasing
        for i in range(len(daily_freshness) - 1):
            assert daily_freshness[i] <= daily_freshness[i + 1]
        
        # Day 0 should be ~0.0, Day 7 should be 1.0
        assert daily_freshness[0] < 0.01
        assert daily_freshness[7] == 1.0


class TestFreshnessFiltering:
    """Test freshness filtering logic"""
    
    def setup_method(self):
        self.tracker = BroadcastFreshnessTracker("test_db")
    
    def test_fresh_filter_includes_never_used(self):
        """Test that fresh filter would include never-used content"""
        # Never used has freshness 1.0
        never_used = self.tracker.calculate_freshness_score(None)
        
        # Default filter is min_freshness=0.3
        assert never_used >= 0.3  # Would be included
    
    def test_fresh_filter_excludes_just_used(self):
        """Test that fresh filter would exclude just-used content"""
        current = time.time()
        just_used = self.tracker.calculate_freshness_score(current, current)
        
        # Just used has freshness 0.0
        assert just_used < 0.3  # Would be excluded
    
    def test_filter_threshold_interpretation(self):
        """Test interpretation of different filter thresholds"""
        current = time.time()
        
        # min_freshness=0.3 means content must have been unused for at least ~2.1 days
        # (0.3 * 168 hours = ~50 hours = ~2.1 days)
        threshold_time = current - (50 * 3600)
        freshness = self.tracker.calculate_freshness_score(threshold_time, current)
        
        # Should be approximately 0.3
        assert 0.28 < freshness < 0.32
