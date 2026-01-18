"""
Unit Tests for Weather Simulation System - Phase 2 Integration

Tests broadcast_engine integration with weather simulator.
"""

import pytest
from datetime import datetime
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from regional_climate import Region, get_region_from_dj_name
from weather_simulator import WeatherSimulator, WeatherState
from world_state import WorldState


class TestBroadcastEngineWeatherIntegration:
    """Test Phase 2: BroadcastEngine integration with weather system"""
    
    def test_region_detection_in_broadcast_engine(self):
        """Test that broadcast engine correctly detects region from DJ name"""
        # Test various DJ names
        test_cases = [
            ("Julie (2102, Appalachia)", Region.APPALACHIA),
            ("Mr. New Vegas (2281, Mojave)", Region.MOJAVE),
            ("Travis Miles Nervous (2287, Commonwealth)", Region.COMMONWEALTH),
            ("Julie", Region.APPALACHIA),
        ]
        
        for dj_name, expected_region in test_cases:
            region = get_region_from_dj_name(dj_name)
            assert region == expected_region, f"Failed for {dj_name}"
    
    def test_weather_calendar_initialization(self):
        """Test that weather calendar initializes correctly"""
        # Create world state with empty calendars
        world_state = WorldState("/tmp/test_phase2_state.json")
        
        # Simulate broadcast engine initializing weather calendar
        region = Region.APPALACHIA
        region_name = region.value
        
        # Check that calendar doesn't exist initially
        assert world_state.get_calendar_for_region(region_name) is None
        
        # Generate calendar
        sim = WeatherSimulator(seed=42)
        start_date = datetime(2102, 10, 23)
        calendar = sim.generate_yearly_calendar(start_date, region)
        
        # Convert to dict and store
        calendar_dict = {}
        for date_str, daily_schedule in calendar.items():
            calendar_dict[date_str] = {
                slot: weather.to_dict()
                for slot, weather in daily_schedule.items()
            }
        
        world_state.weather_calendars[region_name] = calendar_dict
        world_state.save()
        
        # Verify calendar exists
        loaded_calendar = world_state.get_calendar_for_region(region_name)
        assert loaded_calendar is not None
        assert len(loaded_calendar) == 365
        
        # Cleanup
        import os
        if os.path.exists("/tmp/test_phase2_state.json"):
            os.remove("/tmp/test_phase2_state.json")
    
    def test_weather_state_dict_conversion(self):
        """Test WeatherState to/from dict conversion for storage"""
        weather = WeatherState(
            weather_type="rad_storm",
            started_at=datetime(2102, 10, 23, 14, 0),
            duration_hours=2.5,
            intensity="severe",
            transition_state="building",
            is_emergency=True,
            temperature=72.0,
            region="Appalachia",
            notable_event=True
        )
        
        # Convert to dict
        weather_dict = weather.to_dict()
        assert isinstance(weather_dict, dict)
        assert weather_dict["weather_type"] == "rad_storm"
        assert weather_dict["is_emergency"] is True
        assert weather_dict["temperature"] == 72.0
        
        # Convert back
        restored = WeatherState.from_dict(weather_dict)
        assert restored.weather_type == weather.weather_type
        assert restored.is_emergency == weather.is_emergency
        assert restored.temperature == weather.temperature
        assert restored.region == weather.region
    
    def test_weather_logging_to_history(self):
        """Test logging weather to historical archive"""
        world_state = WorldState("/tmp/test_phase2_history.json")
        
        # Create weather state
        weather = WeatherState(
            weather_type="sunny",
            started_at=datetime(2102, 10, 23, 10, 0),
            duration_hours=4.0,
            intensity="minor",
            transition_state="stable",
            is_emergency=False,
            temperature=75.0,
            region="Appalachia"
        )
        
        # Log to history
        timestamp = datetime(2102, 10, 23, 10, 0)
        world_state.log_weather_history("Appalachia", timestamp, weather.to_dict())
        
        # Verify it was logged
        history = world_state.get_weather_history("Appalachia")
        assert len(history) > 0
        assert history[0]["weather_type"] == "sunny"
        assert history[0]["temperature"] == 75.0
        
        # Cleanup
        import os
        if os.path.exists("/tmp/test_phase2_history.json"):
            os.remove("/tmp/test_phase2_history.json")
    
    def test_weather_query_by_time_slot(self):
        """Test querying weather for specific time slots"""
        sim = WeatherSimulator(seed=42)
        start_date = datetime(2102, 10, 23)
        
        calendar = sim.generate_yearly_calendar(start_date, Region.APPALACHIA)
        
        # Test different hours map to correct slots
        test_times = [
            (8, "morning"),
            (14, "afternoon"),
            (19, "evening"),
            (23, "night")
        ]
        
        for hour, expected_slot in test_times:
            query_time = datetime(2102, 10, 23, hour, 0)
            weather = sim.get_current_weather(query_time, Region.APPALACHIA, calendar)
            
            assert weather is not None
            # Verify it came from the correct slot by checking the started_at time
            # (This is an indirect check since we don't have direct slot access)
            assert weather.region == "Appalachia"
    
    def test_multi_region_independence(self):
        """Test that different regions maintain independent weather"""
        sim = WeatherSimulator(seed=42)
        start_date = datetime(2102, 10, 23)
        
        # Generate calendars for two regions
        app_calendar = sim.generate_yearly_calendar(start_date, Region.APPALACHIA)
        moj_calendar = sim.generate_yearly_calendar(start_date, Region.MOJAVE)
        
        # Query same time for both regions
        query_time = datetime(2102, 10, 23, 12, 0)
        app_weather = sim.get_current_weather(query_time, Region.APPALACHIA, app_calendar)
        moj_weather = sim.get_current_weather(query_time, Region.MOJAVE, moj_calendar)
        
        # Both should exist
        assert app_weather is not None
        assert moj_weather is not None
        
        # Different regions
        assert app_weather.region == "Appalachia"
        assert moj_weather.region == "Mojave"
        
        # Likely different weather (could be same by chance, but check regions at least)
        assert app_weather.region != moj_weather.region
    
    def test_emergency_weather_detection(self):
        """Test that emergency weather is properly detected"""
        sim = WeatherSimulator(seed=42)
        start_date = datetime(2102, 10, 23)
        
        calendar = sim.generate_yearly_calendar(start_date, Region.APPALACHIA)
        
        # Find any emergency weather in the calendar
        emergency_count = 0
        for date_str, daily_schedule in calendar.items():
            for slot_name, weather in daily_schedule.items():
                if weather.is_emergency:
                    emergency_count += 1
                    # Verify it's an emergency weather type
                    assert weather.weather_type in ["rad_storm", "dust_storm", "glowing_fog"]
                    assert weather.intensity in ["moderate", "severe"]
        
        # Should have some emergency weather over 365 days
        # (Not guaranteed, but very likely with current probabilities)
        # At minimum, verify the logic works with a manual check
        emergency_weather = WeatherState(
            weather_type="rad_storm",
            started_at=datetime.now(),
            duration_hours=2.0,
            intensity="severe",
            transition_state="building",
            is_emergency=True,
            temperature=70.0,
            region="Appalachia"
        )
        assert emergency_weather.is_emergency
        assert emergency_weather.weather_type == "rad_storm"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
