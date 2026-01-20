"""
Tests for segment_plan module.

Tests data structures and methods for broadcast segment planning.
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from segment_plan import (
    Priority,
    SegmentType,
    ValidationConstraints,
    SegmentPlan
)


class TestPriority:
    """Test Priority enum"""
    
    def test_priority_values(self):
        """Test priority level values"""
        assert Priority.CRITICAL.value == 1
        assert Priority.REQUIRED.value == 2
        assert Priority.FILLER.value == 3
    
    def test_priority_ordering(self):
        """Test priority ordering (lower value = higher priority)"""
        assert Priority.CRITICAL.value < Priority.REQUIRED.value
        assert Priority.REQUIRED.value < Priority.FILLER.value


class TestSegmentType:
    """Test SegmentType enum"""
    
    def test_segment_type_values(self):
        """Test segment type string values"""
        assert SegmentType.EMERGENCY_WEATHER.value == "emergency_weather"
        assert SegmentType.TIME_CHECK.value == "time_check"
        assert SegmentType.WEATHER.value == "weather"
        assert SegmentType.NEWS.value == "news"
        assert SegmentType.STORY.value == "story"
        assert SegmentType.GOSSIP.value == "gossip"
        assert SegmentType.MUSIC_INTRO.value == "music_intro"
    
    def test_all_segment_types_exist(self):
        """Test all required segment types are defined"""
        expected_types = {
            "emergency_weather", "time_check", "weather", 
            "news", "story", "gossip", "music_intro"
        }
        actual_types = {st.value for st in SegmentType}
        assert actual_types == expected_types


class TestValidationConstraints:
    """Test ValidationConstraints dataclass"""
    
    def test_empty_constraints(self):
        """Test creating constraints with defaults"""
        constraints = ValidationConstraints()
        assert constraints.max_year is None
        assert constraints.min_year is None
        assert constraints.allowed_regions is None
        assert constraints.forbidden_regions is None
        assert constraints.forbidden_topics == []
        assert constraints.forbidden_factions == []
        assert constraints.required_tone is None
        assert constraints.max_length is None
        assert constraints.min_length is None
        assert constraints.required_elements == []
        assert constraints.dj_knowledge_level is None
        assert constraints.dj_personality_traits == []
    
    def test_constraints_with_values(self):
        """Test creating constraints with values"""
        constraints = ValidationConstraints(
            max_year=2287,
            min_year=2077,
            allowed_regions=["Commonwealth"],
            forbidden_topics=["Institute"],
            max_length=500
        )
        assert constraints.max_year == 2287
        assert constraints.min_year == 2077
        assert constraints.allowed_regions == ["Commonwealth"]
        assert constraints.forbidden_topics == ["Institute"]
        assert constraints.max_length == 500
    
    def test_to_prompt_text_empty(self):
        """Test prompt text generation with no constraints"""
        constraints = ValidationConstraints()
        text = constraints.to_prompt_text()
        assert text == ""
    
    def test_to_prompt_text_temporal(self):
        """Test prompt text with temporal constraints"""
        constraints = ValidationConstraints(max_year=2287, min_year=2200)
        text = constraints.to_prompt_text()
        assert "TEMPORAL CONSTRAINTS:" in text
        assert "Do NOT mention events after year 2287" in text
        assert "Do NOT mention events before year 2200" in text
    
    def test_to_prompt_text_spatial(self):
        """Test prompt text with spatial constraints"""
        constraints = ValidationConstraints(
            forbidden_regions=["Mojave", "New Vegas"],
            allowed_regions=["Commonwealth"]
        )
        text = constraints.to_prompt_text()
        assert "SPATIAL CONSTRAINTS:" in text
        assert "Do NOT reference these regions: Mojave, New Vegas" in text
        assert "ONLY reference these regions: Commonwealth" in text
    
    def test_to_prompt_text_content(self):
        """Test prompt text with content constraints"""
        constraints = ValidationConstraints(
            forbidden_topics=["politics", "religion"],
            forbidden_factions=["Institute"]
        )
        text = constraints.to_prompt_text()
        assert "FORBIDDEN CONTENT:" in text
        assert "Do NOT discuss: politics, religion" in text
        assert "Do NOT mention factions: Institute" in text
    
    def test_to_prompt_text_tone(self):
        """Test prompt text with tone constraint"""
        constraints = ValidationConstraints(required_tone="hopeful")
        text = constraints.to_prompt_text()
        assert "TONE: Maintain a hopeful tone throughout" in text
    
    def test_to_prompt_text_length(self):
        """Test prompt text with length constraint"""
        constraints = ValidationConstraints(max_length=500)
        text = constraints.to_prompt_text()
        assert "LENGTH: Keep under 500 characters" in text
    
    def test_to_prompt_text_required_elements(self):
        """Test prompt text with required elements"""
        constraints = ValidationConstraints(required_elements=["weather", "time"])
        text = constraints.to_prompt_text()
        assert "REQUIRED: Must include weather, time" in text
    
    def test_to_prompt_text_combined(self):
        """Test prompt text with multiple constraints"""
        constraints = ValidationConstraints(
            max_year=2287,
            forbidden_regions=["Mojave"],
            required_tone="serious",
            max_length=400
        )
        text = constraints.to_prompt_text()
        assert "TEMPORAL CONSTRAINTS:" in text
        assert "SPATIAL CONSTRAINTS:" in text
        assert "TONE:" in text
        assert "LENGTH:" in text
    
    def test_to_dict(self):
        """Test conversion to dictionary"""
        constraints = ValidationConstraints(
            max_year=2287,
            min_year=2200,
            allowed_regions=["Commonwealth"],
            forbidden_topics=["Institute"],
            max_length=500,
            dj_knowledge_level="extensive"
        )
        result = constraints.to_dict()
        
        assert result['temporal']['max_year'] == 2287
        assert result['temporal']['min_year'] == 2200
        assert result['spatial']['allowed_regions'] == ["Commonwealth"]
        assert result['content']['forbidden_topics'] == ["Institute"]
        assert result['format']['max_length'] == 500
        assert result['dj']['knowledge_level'] == "extensive"
    
    def test_to_dict_empty(self):
        """Test dictionary conversion with empty constraints"""
        constraints = ValidationConstraints()
        result = constraints.to_dict()
        
        assert result['temporal']['max_year'] is None
        assert result['temporal']['min_year'] is None
        assert result['spatial']['allowed_regions'] is None
        assert result['content']['forbidden_topics'] == []
        assert result['format']['max_length'] is None


class TestSegmentPlan:
    """Test SegmentPlan dataclass"""
    
    def test_basic_plan(self):
        """Test creating basic segment plan"""
        constraints = ValidationConstraints(max_year=2287)
        plan = SegmentPlan(
            segment_type=SegmentType.WEATHER,
            priority=Priority.REQUIRED,
            constraints=constraints
        )
        
        assert plan.segment_type == SegmentType.WEATHER
        assert plan.priority == Priority.REQUIRED
        assert plan.constraints.max_year == 2287
        assert plan.metadata == {}
        assert plan.context == {}
    
    def test_plan_with_metadata(self):
        """Test plan with metadata and context"""
        constraints = ValidationConstraints()
        plan = SegmentPlan(
            segment_type=SegmentType.NEWS,
            priority=Priority.FILLER,
            constraints=constraints,
            metadata={"duration": 120, "dj": "Julie"},
            context={"hour": 8, "weather": "clear"}
        )
        
        assert plan.metadata == {"duration": 120, "dj": "Julie"}
        assert plan.context == {"hour": 8, "weather": "clear"}
    
    def test_str_representation(self):
        """Test string representation"""
        constraints = ValidationConstraints()
        plan = SegmentPlan(
            segment_type=SegmentType.STORY,
            priority=Priority.FILLER,
            constraints=constraints,
            metadata={"topic": "wasteland"}
        )
        
        str_repr = str(plan)
        assert "story" in str_repr
        assert "FILLER" in str_repr
        assert "topic" in str_repr
    
    def test_to_dict(self):
        """Test conversion to dictionary"""
        constraints = ValidationConstraints(max_year=2287)
        plan = SegmentPlan(
            segment_type=SegmentType.WEATHER,
            priority=Priority.REQUIRED,
            constraints=constraints,
            metadata={"dj": "Julie"},
            context={"hour": 12}
        )
        
        result = plan.to_dict()
        
        assert result['segment_type'] == "weather"
        assert result['priority'] == "REQUIRED"
        assert result['metadata'] == {"dj": "Julie"}
        assert result['context'] == {"hour": 12}
        assert 'constraints' in result
        assert result['constraints']['temporal']['max_year'] == 2287
    
    def test_get_rag_topic_weather(self):
        """Test RAG topic for weather segment"""
        plan = SegmentPlan(
            segment_type=SegmentType.WEATHER,
            priority=Priority.REQUIRED,
            constraints=ValidationConstraints()
        )
        assert plan.get_rag_topic() == 'regional_climate'
    
    def test_get_rag_topic_emergency_weather(self):
        """Test RAG topic for emergency weather"""
        plan = SegmentPlan(
            segment_type=SegmentType.EMERGENCY_WEATHER,
            priority=Priority.CRITICAL,
            constraints=ValidationConstraints()
        )
        assert plan.get_rag_topic() == 'regional_climate'
    
    def test_get_rag_topic_news(self):
        """Test RAG topic for news segment"""
        plan = SegmentPlan(
            segment_type=SegmentType.NEWS,
            priority=Priority.FILLER,
            constraints=ValidationConstraints()
        )
        assert plan.get_rag_topic() == 'current_events'
    
    def test_get_rag_topic_gossip(self):
        """Test RAG topic for gossip segment"""
        plan = SegmentPlan(
            segment_type=SegmentType.GOSSIP,
            priority=Priority.FILLER,
            constraints=ValidationConstraints()
        )
        assert plan.get_rag_topic() == 'character_relationships'
    
    def test_get_rag_topic_story(self):
        """Test RAG topic for story segment"""
        plan = SegmentPlan(
            segment_type=SegmentType.STORY,
            priority=Priority.FILLER,
            constraints=ValidationConstraints()
        )
        assert plan.get_rag_topic() == 'story_arc'
    
    def test_get_rag_topic_music_intro(self):
        """Test RAG topic for music intro"""
        plan = SegmentPlan(
            segment_type=SegmentType.MUSIC_INTRO,
            priority=Priority.FILLER,
            constraints=ValidationConstraints()
        )
        assert plan.get_rag_topic() == 'music_knowledge'
    
    def test_get_rag_topic_time_check(self):
        """Test RAG topic for time check (no RAG)"""
        plan = SegmentPlan(
            segment_type=SegmentType.TIME_CHECK,
            priority=Priority.REQUIRED,
            constraints=ValidationConstraints()
        )
        assert plan.get_rag_topic() is None
    
    def test_is_required_critical(self):
        """Test is_required for CRITICAL priority"""
        plan = SegmentPlan(
            segment_type=SegmentType.EMERGENCY_WEATHER,
            priority=Priority.CRITICAL,
            constraints=ValidationConstraints()
        )
        assert plan.is_required() is True
    
    def test_is_required_required(self):
        """Test is_required for REQUIRED priority"""
        plan = SegmentPlan(
            segment_type=SegmentType.WEATHER,
            priority=Priority.REQUIRED,
            constraints=ValidationConstraints()
        )
        assert plan.is_required() is True
    
    def test_is_required_filler(self):
        """Test is_required for FILLER priority"""
        plan = SegmentPlan(
            segment_type=SegmentType.STORY,
            priority=Priority.FILLER,
            constraints=ValidationConstraints()
        )
        assert plan.is_required() is False
    
    def test_is_emergency_critical(self):
        """Test is_emergency for CRITICAL priority"""
        plan = SegmentPlan(
            segment_type=SegmentType.EMERGENCY_WEATHER,
            priority=Priority.CRITICAL,
            constraints=ValidationConstraints()
        )
        assert plan.is_emergency() is True
    
    def test_is_emergency_required(self):
        """Test is_emergency for REQUIRED priority"""
        plan = SegmentPlan(
            segment_type=SegmentType.WEATHER,
            priority=Priority.REQUIRED,
            constraints=ValidationConstraints()
        )
        assert plan.is_emergency() is False
    
    def test_is_emergency_filler(self):
        """Test is_emergency for FILLER priority"""
        plan = SegmentPlan(
            segment_type=SegmentType.STORY,
            priority=Priority.FILLER,
            constraints=ValidationConstraints()
        )
        assert plan.is_emergency() is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
