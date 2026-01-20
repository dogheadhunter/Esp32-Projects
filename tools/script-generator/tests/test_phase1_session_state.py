"""
Phase 1 Tests: Session State Foundation

Tests for SessionMemory, WorldState, and BroadcastScheduler.
Uses real Ollama/ChromaDB when available, gracefully skips otherwise.
"""

import sys
from pathlib import Path
import pytest
import json
import tempfile
from datetime import datetime, timedelta
from unittest.mock import patch

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Import modules to test
from session_memory import SessionMemory, ScriptEntry
from world_state import WorldState
from broadcast_scheduler import BroadcastScheduler, TimeOfDay


# ========== Session Memory Tests ==========

class TestSessionMemory:
    """Test SessionMemory class for continuity tracking."""
    
    def test_session_memory_init(self):
        """Test SessionMemory initialization."""
        memory = SessionMemory(max_history=5, dj_name="Julie")
        
        assert memory.max_history == 5
        assert memory.dj_name == "Julie"
        assert len(memory.recent_scripts) == 0
        assert memory.segment_count == 0
    
    def test_add_script_basic(self):
        """Test adding a script to memory."""
        memory = SessionMemory()
        
        memory.add_script(
            script_type="weather",
            content="The skies are clear today.",
            metadata={"weather_type": "sunny"}
        )
        
        assert len(memory.recent_scripts) == 1
        assert memory.segment_count == 1
        assert memory.recent_scripts[0].script_type == "weather"
        assert memory.recent_scripts[0].content == "The skies are clear today."
    
    def test_add_script_respects_max_history(self):
        """Test that max_history limit is enforced."""
        memory = SessionMemory(max_history=3)
        
        for i in range(5):
            memory.add_script("weather", f"Script {i}", {"index": i})
        
        assert len(memory.recent_scripts) == 3
        assert memory.segment_count == 5  # Count still increases
        # Oldest entries should be removed
        assert memory.recent_scripts[0].metadata["index"] == 2
        assert memory.recent_scripts[-1].metadata["index"] == 4
    
    def test_catchphrase_tracking(self):
        """Test that catchphrases are tracked across scripts."""
        memory = SessionMemory()
        
        catchphrases1 = ["If you're out there", "you are not alone"]
        catchphrases2 = ["Welcome home"]
        
        memory.add_script("weather", "Script 1", catchphrases_used=catchphrases1)
        memory.add_script("news", "Script 2", catchphrases_used=catchphrases2)
        
        recent = memory.get_recent_catchphrases(count=5)
        assert len(recent) == 3
        assert "you are not alone" in recent
        assert "Welcome home" in recent
    
    def test_topic_extraction(self):
        """Test that topics are extracted from scripts."""
        memory = SessionMemory()
        
        script = "The raiders are attacking. Vault construction details are interesting."
        memory.add_script("news", script)
        
        topics = memory.get_mentioned_topics()
        assert "raiders" in topics
        assert "vault" in topics
    
    def test_topic_deduplication(self):
        """Test that topics in same script are counted once."""
        memory = SessionMemory()
        
        # Script with 'raider' twice - should count once
        script = "Raider camps spotted. More raiders arriving daily."
        memory.add_script("news", script)
        
        assert memory.mentioned_topics.get("raiders", 0) == 1
    
    def test_context_for_prompt(self):
        """Test context generation for prompt injection."""
        memory = SessionMemory(max_history=3)
        
        memory.add_script("weather", "Sunny skies", metadata={"type": "weather"})
        memory.add_script("news", "Raiders spotted", metadata={"type": "news"})
        
        context = memory.get_context_for_prompt(include_recent=2)
        
        assert "RECENT BROADCAST CONTEXT" in context
        assert "CONTINUITY REQUIREMENTS" in context
        assert "weather" in context.lower()
        assert "news" in context.lower()
    
    def test_session_duration_tracking(self):
        """Test that session duration is tracked."""
        memory = SessionMemory()
        
        # Duration should be very small initially
        duration = memory._get_session_duration()
        assert "hour" in duration
        assert "0" in duration  # Should be less than 1 hour
    
    def test_serialization(self):
        """Test to_dict and from_dict serialization."""
        memory1 = SessionMemory()
        memory1.add_script("weather", "Test script", catchphrases_used=["phrase1"])
        
        # Serialize
        data = memory1.to_dict()
        
        # Deserialize
        memory2 = SessionMemory()
        memory2.from_dict(data)
        
        assert memory2.segment_count == memory1.segment_count
        assert len(memory2.recent_scripts) == len(memory1.recent_scripts)
        assert memory2.catchphrase_history == memory1.catchphrase_history
    
    def test_reset(self):
        """Test session reset."""
        memory = SessionMemory()
        memory.add_script("weather", "Script 1")
        memory.add_script("news", "Script 2")
        
        assert memory.segment_count == 2
        
        memory.reset()
        
        assert memory.segment_count == 0
        assert len(memory.recent_scripts) == 0
        assert len(memory.catchphrase_history) == 0
        assert len(memory.mentioned_topics) == 0


# ========== World State Tests ==========

class TestWorldState:
    """Test WorldState class for persistent world continuity."""
    
    def test_world_state_init(self):
        """Test WorldState initialization."""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            path = f.name
        
        try:
            state = WorldState(persistence_path=path)
            
            assert state.broadcast_count == 0
            assert state.total_runtime_hours == 0.0
            assert len(state.ongoing_storylines) == 0
            assert len(state.resolved_gossip) == 0
        finally:
            Path(path).unlink(missing_ok=True)
    
    def test_add_storyline(self):
        """Test adding a storyline."""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            path = f.name
        
        try:
            state = WorldState(persistence_path=path)
            
            storyline = state.add_storyline(
                topic="Mothman sightings",
                initial_development="First reported near Point Pleasant",
                gossip_level="medium"
            )
            
            assert storyline["topic"] == "Mothman sightings"
            assert len(state.ongoing_storylines) == 1
            assert "id" in storyline
        finally:
            Path(path).unlink(missing_ok=True)
    
    def test_continue_storyline(self):
        """Test continuing a storyline."""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            path = f.name
        
        try:
            state = WorldState(persistence_path=path)
            
            storyline = state.add_storyline(
                topic="Faction conflict",
                initial_development="Responders and Raiders clash"
            )
            
            # Continue the storyline
            story_id = storyline["id"]
            state.continue_storyline(story_id, "More attacks reported")
            
            # Check development was added
            updated = [s for s in state.ongoing_storylines if s["id"] == story_id][0]
            assert len(updated["developments"]) == 2
            assert "More attacks" in updated["developments"][1]
        finally:
            Path(path).unlink(missing_ok=True)
    
    def test_resolve_storyline(self):
        """Test resolving a storyline."""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            path = f.name
        
        try:
            state = WorldState(persistence_path=path)
            
            storyline = state.add_storyline(
                topic="Missing supplies",
                initial_development="Caravan lost supplies"
            )
            
            story_id = storyline["id"]
            resolved = state.resolve_storyline(
                story_id,
                resolution="Supplies found and returned"
            )
            
            # Check moved to resolved
            assert len(state.ongoing_storylines) == 0
            assert len(state.resolved_gossip) == 1
            assert state.resolved_gossip[0]["status"] == "resolved"
            assert "returned" in state.resolved_gossip[0]["resolution"]
        finally:
            Path(path).unlink(missing_ok=True)
    
    def test_broadcast_stats_update(self):
        """Test updating broadcast statistics."""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            path = f.name
        
        try:
            state = WorldState(persistence_path=path)
            
            state.update_broadcast_stats(runtime_hours=0.1)
            state.update_broadcast_stats(runtime_hours=0.15)
            
            assert state.broadcast_count == 2
            assert abs(state.total_runtime_hours - 0.25) < 0.001
            assert state.last_broadcast is not None
        finally:
            Path(path).unlink(missing_ok=True)
    
    def test_persistence_save_load(self):
        """Test that world state persists across instances."""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            path = f.name
        
        try:
            # Create and modify state
            state1 = WorldState(persistence_path=path)
            state1.add_storyline("Test topic", "Initial development")
            state1.update_broadcast_stats(runtime_hours=0.2)
            
            # Load in new instance
            state2 = WorldState(persistence_path=path)
            
            assert state2.broadcast_count == 1
            assert abs(state2.total_runtime_hours - 0.2) < 0.001
            assert len(state2.ongoing_storylines) == 1
            assert state2.ongoing_storylines[0]["topic"] == "Test topic"
        finally:
            Path(path).unlink(missing_ok=True)
    
    def test_get_storylines_for_context(self):
        """Test getting storylines for prompt context."""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            path = f.name
        
        try:
            state = WorldState(persistence_path=path)
            
            for i in range(5):
                state.add_storyline(f"Topic {i}", f"Development {i}")
            
            recent = state.get_storylines_for_context(max_count=3)
            
            assert len(recent) == 3
            # Should be most recent
            assert "Topic 4" in recent[-1]["topic"]
        finally:
            Path(path).unlink(missing_ok=True)


# ========== Broadcast Scheduler Tests ==========

class TestBroadcastScheduler:
    """Test BroadcastScheduler for time-aware segment scheduling."""
    
    def test_scheduler_init(self):
        """Test BroadcastScheduler initialization."""
        scheduler = BroadcastScheduler()
        
        assert scheduler.time_check_done_hours is not None
        assert scheduler.weather_done_hours is not None
        assert scheduler.WEATHER_HOURS == {6, 12, 17, 21}
    
    def test_time_of_day_detection_morning(self):
        """Test time of day detection for morning."""
        scheduler = BroadcastScheduler()
        
        # Mock 8 AM
        with patch('broadcast_scheduler.datetime') as mock_dt:
            mock_dt.now.return_value = datetime(2026, 1, 17, 8, 0)
            assert scheduler.get_current_time_of_day() == TimeOfDay.MORNING
    
    def test_time_of_day_detection_afternoon(self):
        """Test time of day detection for afternoon."""
        scheduler = BroadcastScheduler()
        
        # Mock 3 PM
        with patch('broadcast_scheduler.datetime') as mock_dt:
            mock_dt.now.return_value = datetime(2026, 1, 17, 15, 0)
            assert scheduler.get_current_time_of_day() == TimeOfDay.AFTERNOON
    
    def test_time_of_day_detection_night(self):
        """Test time of day detection for night."""
        scheduler = BroadcastScheduler()
        
        # Mock 11 PM
        with patch('broadcast_scheduler.datetime') as mock_dt:
            mock_dt.now.return_value = datetime(2026, 1, 17, 23, 0)
            assert scheduler.get_current_time_of_day() == TimeOfDay.NIGHT
    
    def test_segment_ready_on_first_call(self):
        """Test that segments are ready when never generated."""
        scheduler = BroadcastScheduler()
        
        # All should be ready since never generated
        assert scheduler.is_time_for_segment("weather") == True
        assert scheduler.is_time_for_segment("news") == True
        assert scheduler.is_time_for_segment("gossip") == True
    
    def test_segment_interval_enforcement(self):
        """Test that hour-based scheduling is enforced."""
        scheduler = BroadcastScheduler()
        current_hour = 12  # Noon - a weather hour
        
        # Mark weather as done for this hour
        scheduler.mark_segment_done("weather", current_hour)
        
        # Weather should be marked as done for hour 12
        assert current_hour in scheduler.weather_done_hours
        
        # Time check should still be available for this hour
        assert current_hour not in scheduler.time_check_done_hours
    
    def test_next_priority_segment(self):
        """Test getting required segment for current hour."""
        scheduler = BroadcastScheduler()
        current_hour = 12  # Noon - a weather hour
        
        # Get required segment for this hour
        required_seg = scheduler.get_required_segment_for_hour(current_hour)
        
        # Should get time_check first (since nothing is done yet)
        assert required_seg == "time_check"
        
        # After marking time check as done, should get weather
        scheduler.mark_segment_done("time_check", current_hour)
        required_seg = scheduler.get_required_segment_for_hour(current_hour)
        assert required_seg == "weather"
    
    def test_segments_status(self):
        """Test getting segments status."""
        scheduler = BroadcastScheduler()
        
        status = scheduler.get_segments_status()
        
        assert "weather_done" in status
        assert "news_done" in status
        assert "weather_hours" in status
        assert status["weather_hours"] == [6, 12, 17, 21]
        assert status["weather_done"] == []  # Nothing done initially
    
    def test_scheduler_reset(self):
        """Test resetting scheduler."""
        scheduler = BroadcastScheduler()
        current_hour = 12
        
        scheduler.mark_segment_done("weather", current_hour)
        assert current_hour in scheduler.weather_done_hours
        
        scheduler.reset()
        assert current_hour not in scheduler.weather_done_hours
        assert len(scheduler.weather_done_hours) == 0
    
    def test_time_priority_variation(self):
        """Test that weather scheduling varies by hour."""
        scheduler = BroadcastScheduler()
        
        # Weather is scheduled at specific hours
        assert 6 in scheduler.WEATHER_HOURS  # Morning
        assert 12 in scheduler.WEATHER_HOURS  # Noon
        assert 17 in scheduler.WEATHER_HOURS  # Evening
        
        # Non-weather hours
        assert 10 not in scheduler.WEATHER_HOURS
        assert 15 not in scheduler.WEATHER_HOURS


# ========== Integration Tests ==========

class TestPhase1Integration:
    """Integration tests for Phase 1 components working together."""
    
    def test_session_and_world_state_together(self):
        """Test SessionMemory and WorldState working together."""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            path = f.name
        
        try:
            memory = SessionMemory(max_history=5, dj_name="Julie")
            world = WorldState(persistence_path=path)
            scheduler = BroadcastScheduler()
            
            # Generate some scripts
            for i in range(3):
                memory.add_script(f"type_{i}", f"Script content {i}")
                world.update_broadcast_stats(0.1)
                scheduler.record_segment_generated("weather")
            
            assert memory.segment_count == 3
            assert world.broadcast_count == 3
            
            # Get context
            context = memory.get_context_for_prompt()
            assert "CONTINUITY" in context
            assert len(context) > 0
        finally:
            Path(path).unlink(missing_ok=True)
    
    def test_end_to_end_broadcast_session(self):
        """Test complete broadcast session lifecycle."""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            path = f.name
        
        try:
            # Session initialization
            memory = SessionMemory(dj_name="Julie")
            world = WorldState(persistence_path=path)
            scheduler = BroadcastScheduler()
            
            # Broadcast segments
            scripts = [
                ("weather", "Weather report content"),
                ("news", "News update content"),
                ("gossip", "Gossip about raiders"),
            ]
            
            for script_type, content in scripts:
                memory.add_script(script_type, content)
                world.update_broadcast_stats(0.1)
                scheduler.record_segment_generated(script_type)
            
            # Check final state
            assert memory.segment_count == 3
            assert world.broadcast_count == 3
            assert "raiders" in memory.get_mentioned_topics()
            
            # Session should persist
            world.save()
            
            # New instance should load state
            world2 = WorldState(persistence_path=path)
            assert world2.broadcast_count == 3
        finally:
            Path(path).unlink(missing_ok=True)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
