"""
Tests for Phase 6 Task 6: Enhanced Query Filters & Integration
"""

import pytest
from dj_knowledge_profiles import DJKnowledgeProfile, JulieProfile
from query_helpers import (
    ComplexitySequencer, SubjectTracker,
    get_tones_for_weather, get_tones_for_time, get_tones_for_context,
    get_complexity_sequence_pattern
)


class TestFreshnessFilter:
    """Test freshness filtering"""
    
    def test_default_freshness_filter(self):
        """Test default freshness filter (0.3)"""
        profile = JulieProfile()
        filter_dict = profile.get_freshness_filter()
        
        assert "freshness_score" in filter_dict
        assert "$gte" in filter_dict["freshness_score"]
        assert filter_dict["freshness_score"]["$gte"] == 0.3
    
    def test_custom_freshness_filter(self):
        """Test custom freshness threshold"""
        profile = JulieProfile()
        
        for threshold in [0.0, 0.3, 0.5, 0.7, 1.0]:
            filter_dict = profile.get_freshness_filter(threshold)
            assert filter_dict["freshness_score"]["$gte"] == threshold
    
    def test_freshness_prevents_recent_content(self):
        """Test that high freshness threshold excludes recent content"""
        profile = JulieProfile()
        
        # High threshold (0.9) should exclude content used in last ~6.7 days
        filter_dict = profile.get_freshness_filter(0.9)
        assert filter_dict["freshness_score"]["$gte"] == 0.9


class TestToneFilter:
    """Test emotional tone filtering"""
    
    def test_single_tone_filter(self):
        """Test filtering for single tone"""
        profile = JulieProfile()
        filter_dict = profile.get_tone_filter(["hopeful"])
        
        assert "emotional_tone" in filter_dict
        assert "$in" in filter_dict["emotional_tone"]
        assert filter_dict["emotional_tone"]["$in"] == ["hopeful"]
    
    def test_multiple_tones_filter(self):
        """Test filtering for multiple tones"""
        profile = JulieProfile()
        tones = ["hopeful", "neutral", "mysterious"]
        filter_dict = profile.get_tone_filter(tones)
        
        assert filter_dict["emotional_tone"]["$in"] == tones
    
    def test_all_valid_tones(self):
        """Test all valid emotional tones"""
        profile = JulieProfile()
        all_tones = ["hopeful", "tragic", "mysterious", "comedic", "tense", "neutral"]
        filter_dict = profile.get_tone_filter(all_tones)
        
        assert filter_dict["emotional_tone"]["$in"] == all_tones


class TestSubjectExclusionFilter:
    """Test subject diversity filtering"""
    
    def test_exclude_single_subject(self):
        """Test excluding one subject"""
        profile = JulieProfile()
        filter_dict = profile.get_subject_exclusion_filter(["water"])
        
        assert "primary_subject_0" in filter_dict
        assert "$nin" in filter_dict["primary_subject_0"]
        assert filter_dict["primary_subject_0"]["$nin"] == ["water"]
    
    def test_exclude_multiple_subjects(self):
        """Test excluding multiple subjects"""
        profile = JulieProfile()
        subjects = ["water", "radiation", "weapons"]
        filter_dict = profile.get_subject_exclusion_filter(subjects)
        
        assert filter_dict["primary_subject_0"]["$nin"] == subjects
    
    def test_subject_diversity(self):
        """Test that exclusion promotes diversity"""
        profile = JulieProfile()
        
        # Exclude recently used subjects
        recent = ["factions", "military", "weapons"]
        filter_dict = profile.get_subject_exclusion_filter(recent)
        
        assert len(filter_dict["primary_subject_0"]["$nin"]) == 3


class TestComplexityFilter:
    """Test complexity tier filtering"""
    
    def test_simple_complexity_filter(self):
        """Test filtering for simple content"""
        profile = JulieProfile()
        filter_dict = profile.get_complexity_filter("simple")
        
        assert filter_dict == {"complexity_tier": "simple"}
    
    def test_moderate_complexity_filter(self):
        """Test filtering for moderate content"""
        profile = JulieProfile()
        filter_dict = profile.get_complexity_filter("moderate")
        
        assert filter_dict == {"complexity_tier": "moderate"}
    
    def test_complex_complexity_filter(self):
        """Test filtering for complex content"""
        profile = JulieProfile()
        filter_dict = profile.get_complexity_filter("complex")
        
        assert filter_dict == {"complexity_tier": "complex"}


class TestEnhancedFilter:
    """Test combined enhanced filter"""
    
    def test_filter_with_all_enhancements(self):
        """Test filter with all Phase 6 enhancements"""
        profile = JulieProfile()
        
        filter_dict = profile.get_enhanced_filter(
            min_freshness=0.5,
            desired_tones=["hopeful", "neutral"],
            exclude_subjects=["water"],
            complexity_tier="moderate",
            confidence_tier="medium"
        )
        
        # Should have AND combining all filters
        assert "$and" in filter_dict
        assert len(filter_dict["$and"]) == 5  # Base + 4 enhancements
    
    def test_filter_with_partial_enhancements(self):
        """Test filter with only some enhancements"""
        profile = JulieProfile()
        
        filter_dict = profile.get_enhanced_filter(
            min_freshness=0.3,
            confidence_tier="high"
        )
        
        # Should have AND with base + freshness
        assert "$and" in filter_dict
        assert len(filter_dict["$and"]) == 2
    
    def test_filter_without_enhancements(self):
        """Test filter with no Phase 6 enhancements"""
        profile = JulieProfile()
        
        filter_dict = profile.get_enhanced_filter(confidence_tier="low")
        
        # Should just return base filter
        # (no $and if only one filter)
        assert isinstance(filter_dict, dict)


class TestComplexitySequencer:
    """Test complexity sequencing"""
    
    def test_sequencer_initialization(self):
        """Test sequencer starts at simple"""
        sequencer = ComplexitySequencer()
        assert sequencer.get_current_tier() is None
    
    def test_sequencer_rotation(self):
        """Test sequencer rotates through tiers"""
        sequencer = ComplexitySequencer()
        
        assert sequencer.get_next_tier() == "simple"
        assert sequencer.get_next_tier() == "moderate"
        assert sequencer.get_next_tier() == "complex"
        assert sequencer.get_next_tier() == "simple"  # Cycles back
    
    def test_sequencer_current_tier(self):
        """Test getting current tier"""
        sequencer = ComplexitySequencer()
        
        sequencer.get_next_tier()
        assert sequencer.get_current_tier() == "simple"
        
        sequencer.get_next_tier()
        assert sequencer.get_current_tier() == "moderate"
    
    def test_sequencer_reset(self):
        """Test sequencer reset"""
        sequencer = ComplexitySequencer()
        
        sequencer.get_next_tier()
        sequencer.get_next_tier()
        sequencer.reset()
        
        assert sequencer.get_current_tier() is None
        assert sequencer.get_next_tier() == "simple"


class TestSubjectTracker:
    """Test subject tracking for diversity"""
    
    def test_tracker_initialization(self):
        """Test tracker starts empty"""
        tracker = SubjectTracker()
        assert tracker.get_exclusions() == []
    
    def test_tracker_adds_subjects(self):
        """Test adding subjects"""
        tracker = SubjectTracker(max_history=3)
        
        tracker.add_subject("water")
        tracker.add_subject("radiation")
        
        exclusions = tracker.get_exclusions()
        assert "water" in exclusions
        assert "radiation" in exclusions
    
    def test_tracker_max_history(self):
        """Test tracker respects max history"""
        tracker = SubjectTracker(max_history=3)
        
        tracker.add_subject("water")
        tracker.add_subject("radiation")
        tracker.add_subject("weapons")
        tracker.add_subject("factions")  # Should push out "water"
        
        exclusions = tracker.get_exclusions()
        assert len(exclusions) <= 3
        assert "factions" in exclusions
    
    def test_tracker_deduplication(self):
        """Test tracker deduplicates subjects"""
        tracker = SubjectTracker()
        
        tracker.add_subject("water")
        tracker.add_subject("water")
        tracker.add_subject("water")
        
        exclusions = tracker.get_exclusions()
        assert exclusions == ["water"]
    
    def test_tracker_clear(self):
        """Test clearing tracker"""
        tracker = SubjectTracker()
        
        tracker.add_subject("water")
        tracker.add_subject("radiation")
        tracker.clear()
        
        assert tracker.get_exclusions() == []


class TestWeatherToneMapping:
    """Test weather → tone mapping"""
    
    def test_sunny_weather_tones(self):
        """Test sunny weather maps to hopeful"""
        tones = get_tones_for_weather("sunny")
        assert "hopeful" in tones
        assert "neutral" in tones
    
    def test_rad_storm_tones(self):
        """Test rad storm maps to tense/tragic"""
        tones = get_tones_for_weather("rad_storm")
        assert "tense" in tones or "tragic" in tones
    
    def test_rainy_weather_tones(self):
        """Test rainy weather maps to mysterious"""
        tones = get_tones_for_weather("rainy")
        assert "mysterious" in tones or "neutral" in tones
    
    def test_cloudy_weather_tones(self):
        """Test cloudy weather maps to neutral/mysterious"""
        tones = get_tones_for_weather("cloudy")
        assert "neutral" in tones or "mysterious" in tones


class TestTimeToneMapping:
    """Test time of day → tone mapping"""
    
    def test_night_time_tones(self):
        """Test night maps to mysterious/tense"""
        tones = get_tones_for_time(23)  # 11 PM
        assert "mysterious" in tones or "tense" in tones
    
    def test_morning_time_tones(self):
        """Test morning maps to hopeful"""
        tones = get_tones_for_time(7)  # 7 AM
        assert "hopeful" in tones
    
    def test_afternoon_time_tones(self):
        """Test afternoon includes varied tones"""
        tones = get_tones_for_time(14)  # 2 PM
        assert "hopeful" in tones or "neutral" in tones
    
    def test_evening_time_tones(self):
        """Test evening maps to neutral/mysterious"""
        tones = get_tones_for_time(20)  # 8 PM
        assert "neutral" in tones or "mysterious" in tones


class TestContextToneMapping:
    """Test combined context → tone mapping"""
    
    def test_sunny_morning_tones(self):
        """Test sunny morning combines tones"""
        tones = get_tones_for_context(weather="sunny", hour=7)
        assert "hopeful" in tones
    
    def test_rad_storm_night_tones(self):
        """Test rad storm at night combines tense tones"""
        tones = get_tones_for_context(weather="rad_storm", hour=23)
        assert "tense" in tones or "tragic" in tones or "mysterious" in tones
    
    def test_no_context_default(self):
        """Test no context defaults to neutral"""
        tones = get_tones_for_context()
        assert tones == ["neutral"]


class TestComplexitySequencePattern:
    """Test complexity sequence pattern generation"""
    
    def test_pattern_generation(self):
        """Test generating complexity pattern"""
        pattern = get_complexity_sequence_pattern(6)
        
        assert len(pattern) == 6
        assert pattern == ["simple", "moderate", "complex", "simple", "moderate", "complex"]
    
    def test_pattern_with_start(self):
        """Test pattern starting from moderate"""
        pattern = get_complexity_sequence_pattern(4, start="moderate")
        
        assert len(pattern) == 4
        assert pattern[0] == "moderate"
    
    def test_pattern_cycles(self):
        """Test pattern cycles correctly"""
        pattern = get_complexity_sequence_pattern(10)
        
        # Should cycle through simple→moderate→complex
        assert pattern[0] == "simple"
        assert pattern[3] == "simple"
        assert pattern[6] == "simple"
        assert pattern[9] == "simple"
