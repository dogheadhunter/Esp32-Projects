"""
Unit tests for world_state.py

Tests the WorldState module with mocked dependencies.
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, mock_open
import json
import tempfile

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "tools" / "script-generator"))

from world_state import WorldState


@pytest.mark.mock
class TestWorldStateInitialization:
    """Test suite for WorldState initialization"""
    
    def test_initialization_default(self, tmp_path):
        """Test WorldState initialization with default path"""
        persistence_path = tmp_path / "test_state.json"
        world = WorldState(persistence_path=str(persistence_path))
        
        assert world.persistence_path == persistence_path
        assert world.broadcast_count == 0
        assert world.total_runtime_hours == 0.0
        assert len(world.ongoing_storylines) == 0
        assert len(world.resolved_gossip) == 0
        assert len(world.major_events) == 0
        assert isinstance(world.faction_relations, dict)
    
    def test_initialization_creates_parent_dir(self, tmp_path):
        """Test that parent directory is created"""
        nested_path = tmp_path / "nested" / "dir" / "state.json"
        world = WorldState(persistence_path=str(nested_path))
        
        assert nested_path.parent.exists()
    
    def test_initialization_weather_state(self, tmp_path):
        """Test weather system state initialization"""
        persistence_path = tmp_path / "test_state.json"
        world = WorldState(persistence_path=str(persistence_path))
        
        assert isinstance(world.weather_calendars, dict)
        assert isinstance(world.current_weather_by_region, dict)
        assert isinstance(world.weather_history_archive, dict)
        assert isinstance(world.calendar_metadata, dict)
        assert isinstance(world.manual_overrides, dict)
    
    def test_creation_date_set(self, tmp_path):
        """Test that creation_date is set on initialization"""
        persistence_path = tmp_path / "test_state.json"
        world = WorldState(persistence_path=str(persistence_path))
        
        assert world.creation_date is not None
        # Should be valid ISO format
        datetime.fromisoformat(world.creation_date)


@pytest.mark.mock
class TestWorldStateStorylines:
    """Test suite for storyline management"""
    
    def test_add_storyline(self, tmp_path):
        """Test adding a new storyline"""
        persistence_path = tmp_path / "test_state.json"
        world = WorldState(persistence_path=str(persistence_path))
        
        storyline = world.add_storyline(
            topic="Raiders at Flatwoods",
            initial_development="Raiders spotted near settlement",
            gossip_level="medium"
        )
        
        assert storyline is not None
        assert storyline["topic"] == "Raiders at Flatwoods"
        assert storyline["gossip_level"] == "medium"
        assert storyline["status"] == "ongoing"
        assert len(storyline["developments"]) == 1
        assert len(world.ongoing_storylines) == 1
    
    def test_storyline_id_generation(self, tmp_path):
        """Test that storyline IDs are unique"""
        persistence_path = tmp_path / "test_state.json"
        world = WorldState(persistence_path=str(persistence_path))
        
        story1 = world.add_storyline("Topic 1", "Dev 1")
        story2 = world.add_storyline("Topic 2", "Dev 2")
        
        assert story1["id"] != story2["id"]
        assert "story_" in story1["id"]
    
    def test_storyline_created_date(self, tmp_path):
        """Test that created_date is set"""
        persistence_path = tmp_path / "test_state.json"
        world = WorldState(persistence_path=str(persistence_path))
        
        storyline = world.add_storyline("Topic", "Development")
        
        assert "created_date" in storyline
        datetime.fromisoformat(storyline["created_date"])
    
    def test_continue_storyline(self, tmp_path):
        """Test continuing an existing storyline"""
        persistence_path = tmp_path / "test_state.json"
        world = WorldState(persistence_path=str(persistence_path))
        
        # Add initial storyline
        storyline = world.add_storyline("Topic", "Initial development")
        storyline_id = storyline["id"]
        
        # Continue it
        updated = world.continue_storyline(
            storyline_id,
            "New development in the story"
        )
        
        assert updated is not None
        assert len(updated["developments"]) == 2
        assert updated["developments"][1] == "New development in the story"
        assert "updated_date" in updated
    
    def test_continue_nonexistent_storyline(self, tmp_path):
        """Test continuing a storyline that doesn't exist"""
        persistence_path = tmp_path / "test_state.json"
        world = WorldState(persistence_path=str(persistence_path))
        
        result = world.continue_storyline("invalid_id", "Development")
        
        assert result is None
    
    def test_resolve_storyline(self, tmp_path):
        """Test resolving a storyline"""
        persistence_path = tmp_path / "test_state.json"
        world = WorldState(persistence_path=str(persistence_path))
        
        # Add storyline
        storyline = world.add_storyline("Topic", "Development")
        storyline_id = storyline["id"]
        
        # Resolve it
        resolved = world.resolve_storyline(
            storyline_id,
            "Raiders were defeated"
        )
        
        assert resolved is not None
        assert resolved["status"] == "resolved"
        assert resolved["resolution"] == "Raiders were defeated"
        assert "resolved_date" in resolved
        
        # Should be moved to resolved_gossip
        assert len(world.ongoing_storylines) == 0
        assert len(world.resolved_gossip) == 1
    
    def test_resolve_nonexistent_storyline(self, tmp_path):
        """Test resolving a storyline that doesn't exist"""
        persistence_path = tmp_path / "test_state.json"
        world = WorldState(persistence_path=str(persistence_path))
        
        result = world.resolve_storyline("invalid_id", "Resolution")
        
        assert result is None
    
    def test_get_storylines_for_context(self, tmp_path):
        """Test getting storylines for context"""
        persistence_path = tmp_path / "test_state.json"
        world = WorldState(persistence_path=str(persistence_path))
        
        # Add multiple storylines
        for i in range(5):
            world.add_storyline(f"Topic {i}", f"Development {i}")
        
        # Get last 3
        context_storylines = world.get_storylines_for_context(max_count=3)
        
        assert len(context_storylines) == 3
        # Should be most recent
        assert context_storylines[-1]["topic"] == "Topic 4"
    
    def test_get_storylines_empty(self, tmp_path):
        """Test getting storylines when none exist"""
        persistence_path = tmp_path / "test_state.json"
        world = WorldState(persistence_path=str(persistence_path))
        
        storylines = world.get_storylines_for_context()
        
        assert storylines == []


@pytest.mark.mock
class TestWorldStateMajorEvents:
    """Test suite for major event management"""
    
    def test_add_major_event(self, tmp_path):
        """Test adding a major event"""
        persistence_path = tmp_path / "test_state.json"
        world = WorldState(persistence_path=str(persistence_path))
        
        world.add_major_event(
            event_type="faction_conflict",
            description="Brotherhood attacked settlement",
            affected_factions=["Brotherhood", "Settlers"]
        )
        
        assert len(world.major_events) == 1
        event = world.major_events[0]
        assert event["type"] == "faction_conflict"
        assert event["description"] == "Brotherhood attacked settlement"
        assert len(event["affected_factions"]) == 2
    
    def test_major_event_id_generation(self, tmp_path):
        """Test that event IDs are unique"""
        persistence_path = tmp_path / "test_state.json"
        world = WorldState(persistence_path=str(persistence_path))
        
        world.add_major_event("type1", "Description 1")
        world.add_major_event("type2", "Description 2")
        
        assert world.major_events[0]["id"] != world.major_events[1]["id"]
    
    def test_major_event_without_factions(self, tmp_path):
        """Test adding event without affected factions"""
        persistence_path = tmp_path / "test_state.json"
        world = WorldState(persistence_path=str(persistence_path))
        
        world.add_major_event("discovery", "New vault found")
        
        assert world.major_events[0]["affected_factions"] == []


@pytest.mark.mock
class TestWorldStateBroadcastStats:
    """Test suite for broadcast statistics"""
    
    def test_update_broadcast_stats(self, tmp_path):
        """Test updating broadcast statistics"""
        persistence_path = tmp_path / "test_state.json"
        world = WorldState(persistence_path=str(persistence_path))
        
        world.update_broadcast_stats(runtime_hours=1.5)
        
        assert world.broadcast_count == 1
        assert world.total_runtime_hours == 1.5
        assert world.last_broadcast is not None
    
    def test_update_broadcast_stats_accumulates(self, tmp_path):
        """Test that stats accumulate over multiple updates"""
        persistence_path = tmp_path / "test_state.json"
        world = WorldState(persistence_path=str(persistence_path))
        
        world.update_broadcast_stats(1.0)
        world.update_broadcast_stats(2.0)
        world.update_broadcast_stats(1.5)
        
        assert world.broadcast_count == 3
        assert world.total_runtime_hours == 4.5
    
    def test_last_broadcast_timestamp(self, tmp_path):
        """Test that last_broadcast is ISO timestamp"""
        persistence_path = tmp_path / "test_state.json"
        world = WorldState(persistence_path=str(persistence_path))
        
        world.update_broadcast_stats(1.0)
        
        # Should be valid ISO format
        datetime.fromisoformat(world.last_broadcast)


@pytest.mark.mock
class TestWorldStateWeatherSystem:
    """Test suite for weather system state management"""
    
    def test_get_current_weather_none(self, tmp_path):
        """Test getting current weather when none set"""
        persistence_path = tmp_path / "test_state.json"
        world = WorldState(persistence_path=str(persistence_path))
        
        weather = world.get_current_weather("Appalachia")
        
        assert weather is None
    
    def test_update_weather_state(self, tmp_path):
        """Test updating weather state"""
        persistence_path = tmp_path / "test_state.json"
        world = WorldState(persistence_path=str(persistence_path))
        
        weather_dict = {
            "weather_type": "sunny",
            "temperature": 75,
            "region": "Appalachia"
        }
        
        world.update_weather_state("Appalachia", weather_dict)
        
        current = world.get_current_weather("Appalachia")
        assert current == weather_dict
    
    def test_manual_weather_override(self, tmp_path):
        """Test manual weather override"""
        persistence_path = tmp_path / "test_state.json"
        world = WorldState(persistence_path=str(persistence_path))
        
        # Set normal weather
        normal_weather = {"weather_type": "sunny"}
        world.update_weather_state("Appalachia", normal_weather)
        
        # Set override
        override_weather = {"weather_type": "rad_storm"}
        world.set_manual_weather_override("Appalachia", override_weather)
        
        # Override should take precedence
        current = world.get_current_weather("Appalachia")
        assert current == override_weather
    
    def test_clear_manual_override(self, tmp_path):
        """Test clearing manual override"""
        persistence_path = tmp_path / "test_state.json"
        world = WorldState(persistence_path=str(persistence_path))
        
        # Set override
        world.set_manual_weather_override("Appalachia", {"weather_type": "rad_storm"})
        
        # Clear it
        world.clear_manual_override("Appalachia")
        
        # Should return to None (no override)
        assert world.manual_overrides.get("Appalachia") is None
    
    def test_log_weather_history(self, tmp_path):
        """Test logging weather to history"""
        persistence_path = tmp_path / "test_state.json"
        world = WorldState(persistence_path=str(persistence_path))
        
        timestamp = datetime(2102, 8, 15, 14, 30)
        weather_dict = {"weather_type": "sunny", "temperature": 75}
        
        world.log_weather_history("Appalachia", timestamp, weather_dict)
        
        assert "Appalachia" in world.weather_history_archive
        assert "2102-08-15" in world.weather_history_archive["Appalachia"]
    
    def test_get_weather_history(self, tmp_path):
        """Test retrieving weather history"""
        persistence_path = tmp_path / "test_state.json"
        world = WorldState(persistence_path=str(persistence_path))
        
        # Log several weather events
        base_time = datetime(2102, 8, 15, 8, 0)
        for i in range(3):
            timestamp = base_time + timedelta(hours=i*4)
            weather = {"weather_type": f"type_{i}"}
            world.log_weather_history("Appalachia", timestamp, weather)
        
        history = world.get_weather_history("Appalachia")
        
        assert len(history) == 3
    
    def test_get_weather_history_with_date_filter(self, tmp_path):
        """Test retrieving weather history with date filtering"""
        persistence_path = tmp_path / "test_state.json"
        world = WorldState(persistence_path=str(persistence_path))
        
        # Log events on different days
        day1 = datetime(2102, 8, 15, 12, 0)
        day2 = datetime(2102, 8, 16, 12, 0)
        day3 = datetime(2102, 8, 17, 12, 0)
        
        world.log_weather_history("Appalachia", day1, {"day": 1})
        world.log_weather_history("Appalachia", day2, {"day": 2})
        world.log_weather_history("Appalachia", day3, {"day": 3})
        
        # Filter to only day 2 and 3
        history = world.get_weather_history(
            "Appalachia",
            start_date=datetime(2102, 8, 16)
        )
        
        assert len(history) == 2
    
    def test_get_notable_weather_events(self, tmp_path):
        """Test getting notable weather events"""
        persistence_path = tmp_path / "test_state.json"
        world = WorldState(persistence_path=str(persistence_path))
        
        # Log normal and notable events
        base_time = datetime.now() - timedelta(days=1)
        
        world.log_weather_history(
            "Appalachia",
            base_time,
            {"weather_type": "sunny", "notable_event": False}
        )
        world.log_weather_history(
            "Appalachia",
            base_time + timedelta(hours=4),
            {"weather_type": "rad_storm", "notable_event": True}
        )
        
        notable = world.get_notable_weather_events("Appalachia", days_back=7)
        
        # Should only get notable events
        assert len(notable) == 1
        assert notable[0]["weather_type"] == "rad_storm"
    
    def test_get_calendar_for_region(self, tmp_path):
        """Test getting weather calendar for region"""
        persistence_path = tmp_path / "test_state.json"
        world = WorldState(persistence_path=str(persistence_path))
        
        # Initially empty
        calendar = world.get_calendar_for_region("Appalachia")
        assert calendar is None
        
        # Set a calendar
        world.weather_calendars["Appalachia"] = {"date": "weather"}
        
        calendar = world.get_calendar_for_region("Appalachia")
        assert calendar is not None


@pytest.mark.mock
class TestWorldStatePersistence:
    """Test suite for save/load functionality"""
    
    def test_save_creates_file(self, tmp_path):
        """Test that save creates JSON file"""
        persistence_path = tmp_path / "test_state.json"
        world = WorldState(persistence_path=str(persistence_path))
        
        world.add_storyline("Topic", "Development")
        world.save()
        
        assert persistence_path.exists()
    
    def test_save_valid_json(self, tmp_path):
        """Test that saved file is valid JSON"""
        persistence_path = tmp_path / "test_state.json"
        world = WorldState(persistence_path=str(persistence_path))
        
        world.add_storyline("Topic", "Development")
        world.save()
        
        # Should be able to load as JSON
        with open(persistence_path, 'r') as f:
            data = json.load(f)
        
        assert isinstance(data, dict)
    
    def test_save_contains_all_fields(self, tmp_path):
        """Test that saved data contains all fields"""
        persistence_path = tmp_path / "test_state.json"
        world = WorldState(persistence_path=str(persistence_path))
        
        world.save()
        
        with open(persistence_path, 'r') as f:
            data = json.load(f)
        
        required_fields = [
            "creation_date",
            "broadcast_count",
            "ongoing_storylines",
            "resolved_gossip",
            "major_events",
            "faction_relations",
            "weather_calendars",
            "current_weather_by_region"
        ]
        
        for field in required_fields:
            assert field in data
    
    def test_load_nonexistent_file(self, tmp_path):
        """Test loading when file doesn't exist"""
        persistence_path = tmp_path / "nonexistent.json"
        world = WorldState(persistence_path=str(persistence_path))
        
        # Should not raise error, just use defaults
        assert world.broadcast_count == 0
    
    def test_load_existing_file(self, tmp_path):
        """Test loading existing state file"""
        persistence_path = tmp_path / "test_state.json"
        
        # Create and save state
        world1 = WorldState(persistence_path=str(persistence_path))
        world1.add_storyline("Topic", "Development")
        world1.update_broadcast_stats(5.0)
        world1.save()
        
        # Load in new instance
        world2 = WorldState(persistence_path=str(persistence_path))
        
        assert len(world2.ongoing_storylines) == 1
        assert world2.broadcast_count == 1
        assert world2.total_runtime_hours == 5.0
    
    def test_load_corrupted_json(self, tmp_path):
        """Test loading corrupted JSON file"""
        persistence_path = tmp_path / "test_state.json"
        
        # Write corrupted JSON
        with open(persistence_path, 'w') as f:
            f.write("{corrupted json")
        
        # Should not crash, just use defaults
        world = WorldState(persistence_path=str(persistence_path))
        assert world.broadcast_count == 0
    
    def test_round_trip_persistence(self, tmp_path):
        """Test complete save/load round trip"""
        persistence_path = tmp_path / "test_state.json"
        
        # Create state with various data
        world1 = WorldState(persistence_path=str(persistence_path))
        world1.add_storyline("Topic 1", "Dev 1")
        world1.add_major_event("event_type", "Description")
        world1.update_broadcast_stats(3.5)
        world1.update_weather_state("Appalachia", {"weather_type": "sunny"})
        world1.save()
        
        # Load in new instance
        world2 = WorldState(persistence_path=str(persistence_path))
        
        # Verify all data
        assert len(world2.ongoing_storylines) == 1
        assert len(world2.major_events) == 1
        assert world2.broadcast_count == 1
        assert world2.total_runtime_hours == 3.5
        assert world2.get_current_weather("Appalachia") is not None


@pytest.mark.mock
class TestWorldStateSerialization:
    """Test suite for to_dict method"""
    
    def test_to_dict_complete(self, tmp_path):
        """Test converting state to dictionary"""
        persistence_path = tmp_path / "test_state.json"
        world = WorldState(persistence_path=str(persistence_path))
        
        world.add_storyline("Topic", "Development")
        world.update_broadcast_stats(2.0)
        
        data = world.to_dict()
        
        assert isinstance(data, dict)
        assert "creation_date" in data
        assert "broadcast_count" in data
        assert "ongoing_storylines" in data
        assert "weather_calendars" in data
    
    def test_to_dict_matches_save_format(self, tmp_path):
        """Test that to_dict matches saved JSON format"""
        persistence_path = tmp_path / "test_state.json"
        world = WorldState(persistence_path=str(persistence_path))
        
        world.add_storyline("Topic", "Development")
        
        # Get dict
        dict_data = world.to_dict()
        
        # Save and load
        world.save()
        with open(persistence_path, 'r') as f:
            file_data = json.load(f)
        
        # Should match (except potentially some type details)
        assert dict_data.keys() == file_data.keys()


@pytest.mark.mock
class TestWorldStateIntegration:
    """Integration-style tests with multiple operations"""
    
    def test_complete_storyline_workflow(self, tmp_path):
        """Test complete storyline creation, continuation, and resolution"""
        persistence_path = tmp_path / "test_state.json"
        world = WorldState(persistence_path=str(persistence_path))
        
        # Create storyline
        story = world.add_storyline("Raiders", "Raiders spotted")
        story_id = story["id"]
        
        # Continue it
        world.continue_storyline(story_id, "Raiders attacked")
        world.continue_storyline(story_id, "Defense organized")
        
        # Resolve it
        world.resolve_storyline(story_id, "Raiders defeated")
        
        # Verify final state
        assert len(world.ongoing_storylines) == 0
        assert len(world.resolved_gossip) == 1
        assert len(world.resolved_gossip[0]["developments"]) == 3
    
    def test_weather_tracking_workflow(self, tmp_path):
        """Test complete weather tracking workflow"""
        persistence_path = tmp_path / "test_state.json"
        world = WorldState(persistence_path=str(persistence_path))
        
        # Set initial weather
        weather1 = {"weather_type": "sunny", "temperature": 75}
        world.update_weather_state("Appalachia", weather1)
        world.log_weather_history("Appalachia", datetime.now(), weather1)
        
        # Change weather
        weather2 = {"weather_type": "rainy", "temperature": 60}
        world.update_weather_state("Appalachia", weather2)
        world.log_weather_history("Appalachia", datetime.now(), weather2)
        
        # Verify
        current = world.get_current_weather("Appalachia")
        assert current["weather_type"] == "rainy"
        
        history = world.get_weather_history("Appalachia")
        # History may be 1 or 2 depending on timestamp granularity
        assert len(history) >= 1
    
    def test_persistence_across_instances(self, tmp_path):
        """Test that state persists across multiple instances"""
        persistence_path = tmp_path / "test_state.json"
        
        # Instance 1: Create and save data
        world1 = WorldState(persistence_path=str(persistence_path))
        world1.add_storyline("Story 1", "Dev 1")
        world1.update_broadcast_stats(1.0)
        world1.save()
        
        # Instance 2: Load and modify
        world2 = WorldState(persistence_path=str(persistence_path))
        world2.add_storyline("Story 2", "Dev 2")
        world2.update_broadcast_stats(2.0)
        world2.save()
        
        # Instance 3: Verify accumulated data
        world3 = WorldState(persistence_path=str(persistence_path))
        assert len(world3.ongoing_storylines) == 2
        assert world3.broadcast_count == 2
        assert world3.total_runtime_hours == 3.0
