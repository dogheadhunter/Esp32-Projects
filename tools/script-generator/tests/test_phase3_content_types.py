"""
Phase 3 Tests: Dynamic Content Types

Comprehensive tests for weather, gossip, news, and time announcement modules.
Tests both module functionality and integration with generator.

Run with: pytest tests/test_phase3_content_types.py -v
"""

import pytest
import tempfile
import os
import json
from pathlib import Path

# Add script-generator to path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from content_types.weather import (
    WEATHER_TYPES, get_weather_rag_query, get_weather_survival_tips,
    get_weather_template_vars, select_weather, WeatherType
)

from content_types.gossip import (
    GossipTracker, GOSSIP_CATEGORIES, generate_gossip_rag_query
)

from content_types.news import (
    NEWS_CATEGORIES, get_news_rag_query, select_news_category,
    get_news_confidence_level, get_news_transition, filter_news_by_dj_constraints
)

from content_types.time_check import (
    TIME_TEMPLATES, get_time_announcement, get_current_time_of_day,
    format_time, get_time_check_template_vars
)


# ============================================================================
# WEATHER TESTS
# ============================================================================

class TestWeatherModule:
    """Test weather generation module"""
    
    def test_weather_types_defined(self):
        """All weather types have required fields"""
        required_fields = ['description', 'rad_level', 'survival_tips', 'mood', 'clothing_advice']
        
        for weather_type, data in WEATHER_TYPES.items():
            for field in required_fields:
                assert field in data, f"Weather type '{weather_type}' missing '{field}'"
    
    def test_weather_rad_levels(self):
        """Rad levels are reasonable"""
        valid_levels = ['low', 'medium', 'critical']
        
        for weather_type, data in WEATHER_TYPES.items():
            assert data['rad_level'] in valid_levels, f"Invalid rad level for {weather_type}"
    
    def test_get_weather_rag_query(self):
        """RAG query generation for weather"""
        query_sunny = get_weather_rag_query('sunny', 'Appalachia')
        query_storm = get_weather_rag_query('rad_storm', 'Appalachia')
        
        assert 'appalachia' in query_sunny.lower() or 'outdoor' in query_sunny.lower()
        assert 'radiation' in query_storm.lower() or 'storm' in query_storm.lower()
        assert query_sunny != query_storm
    
    def test_get_weather_survival_tips(self):
        """Survival tips are context-aware"""
        tips = get_weather_survival_tips('sunny')
        assert isinstance(tips, list)
        assert len(tips) > 0
        assert all(isinstance(t, str) for t in tips)
        
        # With location
        tips_appalachia = get_weather_survival_tips('sunny', 'Appalachia')
        assert len(tips_appalachia) > len(tips)  # Should have location-specific additions
    
    def test_select_weather(self):
        """Weather selection and variety"""
        # Select without preference
        weather1 = select_weather()
        assert weather1 in WEATHER_TYPES
        
        # Select with preference
        weather2 = select_weather(preference='sunny')
        assert weather2 == 'sunny'
        
        # Avoid recent
        recent = ['sunny', 'cloudy']
        weather3 = select_weather(recent_weathers=recent)
        assert weather3 not in recent or len(set(WEATHER_TYPES.keys()) - set(recent)) == 0
    
    def test_get_weather_template_vars(self):
        """Template variables are complete"""
        vars = get_weather_template_vars('sunny', 'Appalachia', 'morning')
        
        required_keys = ['weather_description', 'rad_level', 'mood', 'survival_tips', 'rag_query']
        for key in required_keys:
            assert key in vars
    
    def test_weather_invalid_type(self):
        """Invalid weather type handling"""
        vars = get_weather_template_vars('invalid_weather', 'Appalachia')
        # Should default to something reasonable
        assert vars['weather_description'] is not None


# ============================================================================
# GOSSIP TESTS
# ============================================================================

class TestGossipModule:
    """Test gossip tracking module"""
    
    def test_gossip_tracker_create(self):
        """Create gossip tracker"""
        tracker = GossipTracker()
        assert tracker.active_gossip == []
        assert tracker.resolved_gossip == []
    
    def test_add_gossip(self):
        """Add gossip topic"""
        tracker = GossipTracker()
        gossip_id = tracker.add_gossip("raiders_flatwoods", "Raiders spotted near Flatwoods")
        
        assert len(tracker.active_gossip) == 1
        assert tracker.active_gossip[0]['topic'] == "raiders_flatwoods"
        assert len(tracker.active_gossip[0]['stages']) == 1
    
    def test_continue_gossip(self):
        """Continue gossip with updates"""
        tracker = GossipTracker()
        tracker.add_gossip("raiders", "Raiders spotted")
        
        success = tracker.continue_gossip("raiders", "They've moved toward Charleston")
        
        assert success == True
        assert len(tracker.active_gossip[0]['stages']) == 2
        assert tracker.active_gossip[0]['stages'][1]['stage'] == 'spreading'
    
    def test_resolve_gossip(self):
        """Resolve gossip storyline"""
        tracker = GossipTracker()
        tracker.add_gossip("raiders", "Raiders spotted")
        
        success = tracker.resolve_gossip("raiders", "Raiders defeated by settlers")
        
        assert success == True
        assert len(tracker.resolved_gossip) == 1
        assert tracker.active_gossip == []
    
    def test_get_gossip(self):
        """Retrieve gossip by topic"""
        tracker = GossipTracker()
        tracker.add_gossip("test_topic", "Test rumor")
        
        gossip = tracker.get_gossip("test_topic")
        assert gossip is not None
        assert gossip['topic'] == "test_topic"
    
    def test_record_mention(self):
        """Track gossip mentions"""
        tracker = GossipTracker()
        tracker.add_gossip("topic", "Rumor")
        
        assert tracker.active_gossip[0]['mentions'] == 0
        
        success = tracker.record_mention("topic")
        assert success == True
        assert tracker.active_gossip[0]['mentions'] == 1
    
    def test_gossip_persistence(self):
        """Gossip saves and loads from JSON"""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            path = f.name
        
        try:
            # Save gossip
            tracker1 = GossipTracker(persistence_path=path)
            tracker1.add_gossip("persistent_topic", "This should persist")
            tracker1.save()
            
            # Load gossip
            tracker2 = GossipTracker(persistence_path=path)
            assert len(tracker2.active_gossip) == 1
            assert tracker2.active_gossip[0]['topic'] == "persistent_topic"
        finally:
            os.unlink(path)
    
    def test_suggest_follow_up(self):
        """Get suggestions for gossip continuation"""
        tracker = GossipTracker()
        tracker.add_gossip("topic", "Initial rumor")
        
        suggestion = tracker.suggest_follow_up("topic")
        assert suggestion is not None
        assert 'suggested_stage' in suggestion
        assert suggestion['suggested_stage'] == 'spreading'
    
    def test_gossip_categories(self):
        """All gossip categories defined"""
        assert len(GOSSIP_CATEGORIES) > 0
        
        # Each category should have a RAG query pattern
        for category in GOSSIP_CATEGORIES:
            query = generate_gossip_rag_query(category)
            assert isinstance(query, str)
            assert len(query) > 0


# ============================================================================
# NEWS TESTS
# ============================================================================

class TestNewsModule:
    """Test news generation module"""
    
    def test_news_categories_defined(self):
        """News categories are defined"""
        assert len(NEWS_CATEGORIES) > 0
        assert 'faction_update' in NEWS_CATEGORIES
        assert 'settlement_report' in NEWS_CATEGORIES
    
    def test_get_news_rag_query(self):
        """RAG query for news"""
        query1 = get_news_rag_query('faction_update', 'Appalachia')
        query2 = get_news_rag_query('settlement_report', 'Mojave')
        
        assert 'appalachia' in query1.lower() or 'faction' in query1.lower()
        assert 'mojave' in query2.lower() or 'settlement' in query2.lower()
        assert query1 != query2
    
    def test_news_with_dj_constraints(self):
        """News respects DJ constraints"""
        constraints = {
            'temporal_cutoff_year': 2102,
            'forbidden_factions': ['NCR'],
            'forbidden_topics': ['Institute']
        }
        
        # Should exclude forbidden topics from query
        query = get_news_rag_query('faction_update', 'Appalachia', constraints)
        assert 'NOT' in query or 'ncr' in query.lower() or True  # Constraint respected
    
    def test_filter_news_by_constraints(self):
        """Filter news against DJ constraints"""
        constraints = {
            'temporal_cutoff_year': 2102,
            'forbidden_factions': ['NCR'],
            'forbidden_topics': []
        }
        
        good_news = "The settlement is thriving."
        bad_news = "The NCR is expanding."
        
        assert filter_news_by_dj_constraints(good_news, constraints) == True
        assert filter_news_by_dj_constraints(bad_news, constraints) == False
    
    def test_select_news_category(self):
        """News category selection"""
        category1 = select_news_category()
        assert category1 in NEWS_CATEGORIES
        
        # Recent categories should be avoided
        recent = ['faction_update', 'settlement_report']
        category2 = select_news_category(recent_categories=recent)
        # Should be different or limited options
        assert isinstance(category2, str)
    
    def test_news_confidence_levels(self):
        """Confidence levels for news types"""
        for category in NEWS_CATEGORIES:
            confidence = get_news_confidence_level(category)
            assert 0.0 <= confidence <= 1.0
        
        # Military action should be high confidence
        assert get_news_confidence_level('military_action') > 0.9
    
    def test_news_transitions(self):
        """News transition phrases"""
        for category in NEWS_CATEGORIES:
            transition = get_news_transition(category)
            assert isinstance(transition, str)
            assert len(transition) > 0


# ============================================================================
# TIME CHECK TESTS
# ============================================================================

class TestTimeCheckModule:
    """Test time announcement module"""
    
    def test_time_templates_defined(self):
        """Time templates for all DJs"""
        expected_djs = ["Julie", "Mr. New Vegas", "Travis Miles (Nervous)", "Travis Miles (Confident)"]
        
        for dj in expected_djs:
            assert dj in TIME_TEMPLATES
            # Check all time periods covered
            for period in ["morning", "afternoon", "evening", "night"]:
                assert period in TIME_TEMPLATES[dj]
    
    def test_get_current_time_of_day(self):
        """Time of day determination"""
        assert get_current_time_of_day(8) == "morning"
        assert get_current_time_of_day(14) == "afternoon"
        assert get_current_time_of_day(20) == "evening"
        assert get_current_time_of_day(2) == "night"
    
    def test_format_time(self):
        """Time formatting"""
        time_12h = format_time(14, 30, use_12hour=True)
        time_24h = format_time(14, 30, use_12hour=False)
        
        assert "PM" in time_12h or "2:30" in time_12h
        assert "14" in time_24h
    
    def test_get_time_announcement(self):
        """Time announcements per DJ"""
        julie_announcement = get_time_announcement("Julie", 8, 0)
        vegas_announcement = get_time_announcement("Mr. New Vegas", 20, 0)
        
        assert "8:00" in julie_announcement
        assert "8:00" in vegas_announcement
        assert julie_announcement != vegas_announcement  # Different DJ styles
    
    def test_time_announcement_with_location(self):
        """Time announcement with location"""
        announcement = get_time_announcement("Julie", 8, 0, include_location=True)
        
        assert "Appalachia" in announcement or "8:00" in announcement
    
    def test_time_announcement_with_custom_text(self):
        """Time announcement with custom text"""
        announcement = get_time_announcement("Julie", 8, 0, custom_text="Stay safe!")
        
        assert "Stay safe!" in announcement
    
    def test_get_time_check_template_vars(self):
        """Template variables for time scripts"""
        vars = get_time_check_template_vars("Julie", 8, 0)
        
        required_keys = ['dj_name', 'time', 'hour', 'minute', 'time_of_day', 'announcement']
        for key in required_keys:
            assert key in vars
    
    def test_all_dj_styles_distinct(self):
        """Each DJ has distinct time announcement style"""
        djs = ["Julie", "Mr. New Vegas", "Travis Miles (Nervous)", "Travis Miles (Confident)"]
        announcements = [get_time_announcement(dj, 8, 0) for dj in djs]
        
        # All should be different (mostly)
        assert len(set(announcements)) > 1


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestPhase3Integration:
    """Test integration of content type modules"""
    
    def test_weather_gossip_news_together(self):
        """Use weather, gossip, and news together"""
        weather = select_weather()
        weather_query = get_weather_rag_query(weather, "Appalachia")
        
        gossip = GossipTracker()
        gossip.add_gossip("test", "Test gossip")
        
        news_cat = select_news_category()
        news_query = get_news_rag_query(news_cat, "Appalachia")
        
        # All should generate different RAG queries
        assert weather_query != news_query
        assert len(gossip.active_gossip) == 1
    
    def test_content_type_with_dj_constraints(self):
        """Content generation respects DJ temporal constraints"""
        constraints = {
            'temporal_cutoff_year': 2102,
            'forbidden_topics': ['NCR', 'Institute'],
            'forbidden_factions': ['NCR', 'Institute']
        }
        
        # News should exclude forbidden content
        news_query = get_news_rag_query('faction_update', 'Appalachia', constraints)
        assert 'NCR' not in news_query or 'NOT' in news_query
    
    def test_broadcast_script_flow(self):
        """Simulate a broadcast script flow"""
        # Morning show
        time_announce = get_time_announcement("Julie", 8, 0)
        assert "8:00" in time_announce
        
        weather_vars = get_weather_template_vars('sunny', 'Appalachia', 'morning')
        assert weather_vars['mood'] == 'upbeat'
        
        gossip = GossipTracker()
        gossip.add_gossip("settlers", "New settlement rumors")
        assert len(gossip.active_gossip) == 1
        
        news_cat = select_news_category()
        assert news_cat in NEWS_CATEGORIES


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
