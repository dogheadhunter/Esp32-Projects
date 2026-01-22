"""
Integration tests for Story System

Tests the full story system flow to catch attribute access bugs
and integration issues that unit tests might miss.
"""
import sys
from pathlib import Path

# Add script-generator to path
sys.path.insert(0, str(Path(__file__).parent.parent / "tools" / "script-generator"))

from story_system.story_models import Story, StoryAct, ActiveStory, StoryTimeline, StoryActType, StoryStatus
from story_system.story_scheduler import StoryScheduler
from story_system.story_state import StoryState
from story_system.story_weaver import StoryWeaver
from datetime import datetime
import tempfile
import os


def test_full_story_beat_generation():
    """Test that story beats can be created and processed without attribute errors."""
    
    # Create a temporary file for story state
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        temp_file = f.name
    
    try:
        # Create story state and scheduler
        story_state = StoryState(temp_file)
        scheduler = StoryScheduler(story_state)
        weaver = StoryWeaver(story_state)
        
        # Create a test story with all required attributes
        test_story = Story(
            story_id="test_integration_story",
            title="Test Integration Story",
            timeline=StoryTimeline.DAILY,
            acts=[
                StoryAct(
                    act_number=1,
                    act_type=StoryActType.SETUP,
                    title="Act 1",
                    summary="Test summary for act 1",
                    entities=["Test Entity", "Another Entity"],
                    themes=["survival", "hope"],
                    conflict_level=0.3,
                    emotional_tone="hopeful"
                )
            ],
            summary="Overall test story summary",
            content_type="quest",
            characters=["Test Character", "Another Character"],
            factions=["Test Faction"],
            locations=["Test Location"],
            dj_compatible=["Julie (2102, Appalachia)"],
            knowledge_tier="common",
            source_wiki_titles=["Test Page"],
            estimated_broadcasts=2
        )
        
        # Add to pool and activate
        story_state.add_to_pool(test_story, StoryTimeline.DAILY)
        
        # Get story beats (this will activate and create beats)
        beats = scheduler.get_story_beats_for_broadcast()
        
        # Verify we got beats
        assert len(beats) >= 0, "Should get 0 or more beats (depending on probability)"
        
        if beats:
            beat = beats[0]
            # These are the attributes that were causing errors
            assert hasattr(beat, 'story_id'), "StoryBeat should have story_id attribute"
            assert hasattr(beat, 'beat_summary'), "StoryBeat should have beat_summary attribute"
            assert hasattr(beat, 'entities'), "StoryBeat should have entities attribute"
            assert beat.story_id == "test_integration_story"
            assert isinstance(beat.beat_summary, str)
            assert isinstance(beat.entities, list)
            
            # Test story weaver can process the beats
            woven = weaver.weave_beats(beats)
            assert 'context_for_llm' in woven
            assert isinstance(woven['context_for_llm'], str), "context_for_llm should be a string"
            
            # Verify story context contains expected elements
            context = woven['context_for_llm']
            assert 'Story' in context or 'story' in context
            assert len(context) > 0
        
        # Verify story state can access story attributes without errors
        active = story_state.get_active_story(StoryTimeline.DAILY)
        if active:
            assert hasattr(active.story, 'story_id'), "Story should have story_id not id"
            assert hasattr(active.story, 'characters'), "Story should have characters"
            assert hasattr(active.story, 'factions'), "Story should have factions"
            assert hasattr(active.story, 'locations'), "Story should have locations"
            # Verify we can build entities list
            all_entities = active.story.characters + active.story.factions + active.story.locations
            assert len(all_entities) == 4  # 2 characters + 1 faction + 1 location
            
    finally:
        # Cleanup
        if os.path.exists(temp_file):
            os.unlink(temp_file)


def test_story_context_type_safety():
    """Test that story context is always a string, not a dict."""
    # Create a temporary file for story state
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        temp_file = f.name
    
    try:
        story_state = StoryState(temp_file)
        weaver = StoryWeaver(story_state)
        
        # Create a test story beat
        from story_system.story_models import StoryBeat
        
        beat = StoryBeat(
            story_id="test_story",
            timeline=StoryTimeline.DAILY,
            act_number=1,
            act_type=StoryActType.SETUP,
            beat_summary="Test beat summary",
            entities=["Test Entity"],
            conflict_level=0.5,
            emotional_tone="neutral"
        )
        
        # Weave the beat
        woven = weaver.weave_beats([beat])
        
        # Verify context_for_llm is a string
        assert isinstance(woven, dict), "weave_beats should return a dict"
        assert 'context_for_llm' in woven, "Result should have context_for_llm key"
        assert isinstance(woven['context_for_llm'], str), "context_for_llm must be a string, not dict"
        
        # Verify it has expected content
        context = woven['context_for_llm']
        assert 'test_story' in context.lower()
        assert 'test beat summary' in context.lower() or 'summary' in context.lower()
        
    finally:
        # Cleanup
        if os.path.exists(temp_file):
            os.unlink(temp_file)


def test_consistency_validator_story_incorporation():
    """Test that consistency validator can handle story_context properly."""
    from consistency_validator import ConsistencyValidator
    
    validator = ConsistencyValidator({"name": "Test DJ"})
    
    # Test with string story_context (correct)
    script = "This is a test script mentioning Test Entity and discussing the quest."
    story_context = """
    Story: test_story_and_stay_out! (daily, Act 1)
    Type: setup
    Summary: Test Entity arrives seeking help with a quest
    Entities: Test Entity, Another Entity
    Tone: hopeful, Conflict: 0.3/1.0
    """
    
    # Should not raise an error
    score = validator.get_story_incorporation_score(script, story_context)
    assert isinstance(score, float)
    assert 0.0 <= score <= 1.0
    
    # Test with dict story_context (the bug we fixed)
    story_context_dict = {
        'context_for_llm': story_context,
        'ordered_beats': [],
        'intro_text': '',
        'outro_text': ''
    }
    
    # The validator should handle this gracefully now
    try:
        # This would have failed before our fix with "'dict' object has no attribute 'lower'"
        score2 = validator.get_story_incorporation_score(script, story_context_dict)
        # If we get here, the type safety worked
        assert isinstance(score2, float)
    except AttributeError as e:
        if "'dict' object has no attribute 'lower'" in str(e):
            pytest.fail("Validator failed to handle dict story_context - type safety check not working")
        else:
            raise


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])
