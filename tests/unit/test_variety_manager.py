"""
Unit tests for VarietyManager.

Tests the Phase 2B cooldown-based variety tracking system.
"""

import pytest
import sys
from pathlib import Path

# Add tools/script-generator to path
script_gen_path = Path(__file__).parent.parent.parent / "tools" / "script-generator"
sys.path.insert(0, str(script_gen_path))

from variety_manager import (
    VarietyManager,
    PHRASE_COOLDOWN,
    TOPIC_COOLDOWN,
    WEATHER_CONSECUTIVE_LIMIT,
    STRUCTURE_NO_REPEAT
)


class TestVarietyManager:
    """Test suite for VarietyManager cooldown system."""
    
    def test_phrase_cooldown_enforced(self):
        """Test that same phrase is blocked within cooldown period."""
        manager = VarietyManager()
        
        phrase = "Good morning, Appalachia!"
        
        # First use should be allowed
        assert manager.check_phrase_variety(phrase) is True
        
        # Record usage
        manager.record_usage(phrase=phrase)
        
        # Immediate re-use should be blocked (within cooldown)
        for i in range(PHRASE_COOLDOWN - 1):
            assert manager.check_phrase_variety(phrase) is False, \
                f"Phrase should be blocked at segment {i+1}/{PHRASE_COOLDOWN}"
            # Record other content to advance segment index
            manager.record_usage(phrase=f"different phrase {i}")
        
        # After cooldown expires, should be allowed again
        assert manager.check_phrase_variety(phrase) is True
        
        # Verify blocking was tracked
        stats = manager.get_statistics()
        assert stats['phrase_blocks'] >= PHRASE_COOLDOWN - 1
    
    def test_topic_cooldown_enforced(self):
        """Test that same topic is blocked within cooldown period."""
        manager = VarietyManager()
        
        topic = "raider_activity"
        
        # First use should be allowed
        assert manager.check_topic_variety(topic) is True
        
        # Record usage
        manager.record_usage(topic=topic)
        
        # Immediate re-use should be blocked (within cooldown)
        for i in range(TOPIC_COOLDOWN - 1):
            assert manager.check_topic_variety(topic) is False, \
                f"Topic should be blocked at segment {i+1}/{TOPIC_COOLDOWN}"
            # Record other content to advance segment index
            manager.record_usage(topic=f"different_topic_{i}")
        
        # After cooldown expires, should be allowed again
        assert manager.check_topic_variety(topic) is True
        
        # Verify blocking was tracked
        stats = manager.get_statistics()
        assert stats['topic_blocks'] >= TOPIC_COOLDOWN - 1
    
    def test_weather_consecutive_limit(self):
        """Test that 4+ consecutive same weather type is blocked."""
        manager = VarietyManager()
        
        weather = "clear"
        
        # First use: allowed
        assert manager.check_weather_variety(weather) is True
        manager.record_usage(weather_type=weather)
        
        # Second consecutive: allowed
        assert manager.check_weather_variety(weather) is True
        manager.record_usage(weather_type=weather)
        
        # Third consecutive: still allowed (at limit - 1)
        # Weather limit is 3, so after 2 uses, one more is allowed
        # but the check happens before recording, so we need to be careful
        
        # Actually, let's re-read the logic:
        # WEATHER_CONSECUTIVE_LIMIT = 3 means max 3 consecutive
        # check_weather_variety blocks if len(history) >= limit-1 and all match
        # So after 2 uses (history = [clear, clear]), checking 'clear' again:
        #   len(history) = 2 >= 3-1 = 2, and all match -> BLOCKED
        
        # So third consecutive should be blocked
        assert manager.check_weather_variety(weather) is False, \
            "Third consecutive weather should be blocked"
        
        # Use different weather to break the pattern
        manager.record_usage(weather_type="rainy")
        
        # Now 'clear' should be allowed again (pattern broken)
        assert manager.check_weather_variety(weather) is True
        
        # Verify blocking was tracked
        stats = manager.get_statistics()
        assert stats['weather_blocks'] >= 1
    
    def test_structure_no_repeat(self):
        """Test that segment type can't repeat immediately (2x same structure)."""
        manager = VarietyManager()
        
        segment_type = "gossip"
        
        # First use: allowed
        assert manager.check_structure_variety(segment_type) is True
        manager.record_usage(segment_type=segment_type)
        
        # Immediate repeat: blocked
        assert manager.check_structure_variety(segment_type) is False, \
            "Immediate structure repeat should be blocked"
        
        # Use different type to break pattern
        manager.record_usage(segment_type="news")
        
        # Now original type should be allowed again
        assert manager.check_structure_variety(segment_type) is True
        
        # Verify blocking was tracked
        stats = manager.get_statistics()
        assert stats['structure_blocks'] >= 1
    
    def test_check_variety_constraints_all_dimensions(self):
        """Test check_variety_constraints checks all dimensions."""
        manager = VarietyManager()
        
        # Record initial usage
        manager.record_usage(
            phrase="Hello there",
            topic="settlement_news",
            weather_type="clear",
            segment_type="gossip"
        )
        
        # Check all same elements (should all fail)
        results = manager.check_variety_constraints(
            phrase="Hello there",
            topic="settlement_news",
            weather_type="clear",  # Will fail after 2 consecutive
            segment_type="gossip"
        )
        
        # Phrase and topic should be blocked (in cooldown)
        assert results['phrase_ok'] is False, "Phrase should be in cooldown"
        assert results['topic_ok'] is False, "Topic should be in cooldown"
        # Weather won't be blocked yet (only 1 use so far)
        # Structure will be blocked (immediate repeat)
        assert results['structure_ok'] is False, "Structure should be blocked"
        assert results['all_ok'] is False, "Overall should fail"
    
    def test_get_variety_hints(self):
        """Test that variety hints are generated for LLM prompts."""
        manager = VarietyManager()
        
        # Initially no hints
        hints = manager.get_variety_hints()
        assert len(hints) == 0
        
        # Record some usage
        manager.record_usage(
            phrase="Good morning",
            topic="raider_activity",
            weather_type="clear",
            segment_type="gossip"
        )
        
        # Should now have hints
        hints = manager.get_variety_hints()
        assert len(hints) > 0
        
        # Should mention recent phrase and topic
        hints_text = " ".join(hints)
        assert "Good morning" in hints_text.lower() or "phrase" in hints_text.lower()
        assert "raider" in hints_text.lower() or "topic" in hints_text.lower()
        
        # Should mention last structure
        assert "gossip" in hints_text.lower() or "structure" in hints_text.lower()
    
    def test_record_usage_advances_segment_index(self):
        """Test that record_usage increments segment index."""
        manager = VarietyManager()
        
        assert manager.current_segment_index == 0
        
        manager.record_usage(phrase="test")
        assert manager.current_segment_index == 1
        
        manager.record_usage(topic="test_topic")
        assert manager.current_segment_index == 2
        
        manager.record_usage()  # Empty call should still advance
        assert manager.current_segment_index == 3
    
    def test_statistics_tracking(self):
        """Test that statistics are tracked correctly."""
        manager = VarietyManager()
        
        # Initial stats
        stats = manager.get_statistics()
        assert stats['total_segments'] == 0
        assert stats['phrase_blocks'] == 0
        assert stats['total_blocks'] == 0
        
        # Record usage and trigger blocks
        manager.record_usage(phrase="test", topic="topic1")
        
        # Try to re-use (should block)
        manager.check_phrase_variety("test")
        manager.check_topic_variety("topic1")
        
        stats = manager.get_statistics()
        assert stats['total_segments'] == 1
        assert stats['phrase_blocks'] == 1
        assert stats['topic_blocks'] == 1
        assert stats['total_blocks'] == 2
        assert stats['unique_phrases_tracked'] == 1
        assert stats['unique_topics_tracked'] == 1
    
    def test_reset_clears_all_tracking(self):
        """Test that reset clears all variety tracking."""
        manager = VarietyManager()
        
        # Add some usage
        manager.record_usage(
            phrase="test",
            topic="topic1",
            weather_type="clear",
            segment_type="gossip"
        )
        
        # Trigger some blocks
        manager.check_phrase_variety("test")
        
        stats_before = manager.get_statistics()
        assert stats_before['total_segments'] > 0
        assert stats_before['phrase_blocks'] > 0
        
        # Reset
        manager.reset()
        
        # Verify everything cleared
        assert manager.current_segment_index == 0
        assert len(manager.phrase_usage) == 0
        assert len(manager.topic_usage) == 0
        assert len(manager.weather_history) == 0
        assert len(manager.structure_history) == 0
        
        stats_after = manager.get_statistics()
        assert stats_after['total_segments'] == 0
        assert stats_after['total_blocks'] == 0
    
    def test_case_insensitive_matching(self):
        """Test that phrase/topic matching is case-insensitive."""
        manager = VarietyManager()
        
        # Record with mixed case
        manager.record_usage(phrase="Good Morning Appalachia")
        
        # Check with different case (should still be blocked)
        assert manager.check_phrase_variety("good morning appalachia") is False
        assert manager.check_phrase_variety("GOOD MORNING APPALACHIA") is False
        assert manager.check_phrase_variety("Good Morning Appalachia") is False
