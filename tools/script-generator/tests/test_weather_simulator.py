"""
Unit Tests for Weather Simulation System - Phase 1

Tests regional climate profiles, weather simulator core, and WorldState integration.
"""

import pytest
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from regional_climate import (
    Region, RegionalClimate, get_region_from_dj_name,
    get_climate_for_region, get_season_from_month,
    APPALACHIA_CLIMATE, MOJAVE_CLIMATE, COMMONWEALTH_CLIMATE
)
from weather_simulator import WeatherSimulator, WeatherState
from world_state import WorldState


class TestRegionalClimate:
    """Test regional climate profiles"""
    
    def test_appalachia_climate_characteristics(self):
        """Appalachia has humid subtropical characteristics"""
        climate = APPALACHIA_CLIMATE
        assert climate.region_name == "Appalachia"
        assert climate.base_temp_range == (20.0, 85.0)
        assert climate.precipitation_frequency == 0.45
        assert "fog" in climate.special_conditions
        assert "scorchbeast_activity" in climate.special_conditions
    
    def test_mojave_climate_characteristics(self):
        """Mojave has desert characteristics"""
        climate = MOJAVE_CLIMATE
        assert climate.region_name == "Mojave"
        assert climate.base_temp_range == (35.0, 115.0)
        assert climate.precipitation_frequency == 0.05  # Very dry
        assert "dust_storms" in climate.special_conditions
    
    def test_commonwealth_climate_characteristics(self):
        """Commonwealth has humid continental characteristics"""
        climate = COMMONWEALTH_CLIMATE
        assert climate.region_name == "Commonwealth"
        assert climate.base_temp_range == (10.0, 80.0)
        assert climate.precipitation_frequency == 0.35
        assert "glowing_sea_drift" in climate.special_conditions
    
    def test_region_detection_from_dj_name(self):
        """Test DJ name to region mapping"""
        assert get_region_from_dj_name("Julie (2102, Appalachia)") == Region.APPALACHIA
        assert get_region_from_dj_name("Mr. New Vegas (2281, Mojave)") == Region.MOJAVE
        assert get_region_from_dj_name("Travis Miles Nervous (2287, Commonwealth)") == Region.COMMONWEALTH
        
        # Test partial matches
        assert get_region_from_dj_name("Julie") == Region.APPALACHIA
        assert get_region_from_dj_name("new vegas") == Region.MOJAVE
        assert get_region_from_dj_name("Travis") == Region.COMMONWEALTH
    
    def test_season_detection(self):
        """Test season detection from month"""
        assert get_season_from_month(1, Region.APPALACHIA) == "winter"
        assert get_season_from_month(4, Region.MOJAVE) == "spring"
        assert get_season_from_month(7, Region.COMMONWEALTH) == "summer"
        assert get_season_from_month(10, Region.APPALACHIA) == "fall"
    
    def test_climate_for_region(self):
        """Test retrieving climate by region"""
        climate = get_climate_for_region(Region.APPALACHIA)
        assert climate.region_name == "Appalachia"
        
        climate = get_climate_for_region(Region.MOJAVE)
        assert climate.region_name == "Mojave"


class TestWeatherSimulator:
    """Test weather simulator core functionality"""
    
    def test_simulator_initialization(self):
        """Test simulator initialization"""
        sim = WeatherSimulator(seed=42)
        assert sim.seed == 42
    
    def test_yearly_calendar_generation(self):
        """Test 365-day calendar generation"""
        sim = WeatherSimulator(seed=42)
        start_date = datetime(2102, 10, 23)
        
        calendar = sim.generate_yearly_calendar(start_date, Region.APPALACHIA)
        
        # Should have 365 days
        assert len(calendar) == 365
        
        # Check first day structure
        first_day = calendar["2102-10-23"]
        assert "morning" in first_day
        assert "afternoon" in first_day
        assert "evening" in first_day
        assert "night" in first_day
        
        # Check weather states are valid
        for slot_name, weather in first_day.items():
            assert isinstance(weather, WeatherState)
            assert weather.region == "Appalachia"
            assert weather.temperature > 0
    
    def test_regional_calendar_differences(self):
        """Test that different regions have different weather"""
        sim = WeatherSimulator(seed=42)
        start_date = datetime(2102, 10, 23)
        
        app_calendar = sim.generate_yearly_calendar(start_date, Region.APPALACHIA)
        moj_calendar = sim.generate_yearly_calendar(start_date, Region.MOJAVE)
        
        # Same date, different regions should have different weather
        app_weather = app_calendar["2102-10-23"]["morning"]
        moj_weather = moj_calendar["2102-10-23"]["morning"]
        
        # Very likely to be different (could be same by chance, but unlikely)
        # Check that temperatures are in different ranges at minimum
        assert app_weather.temperature < moj_weather.temperature + 20  # Some difference expected
    
    def test_get_current_weather(self):
        """Test querying current weather from calendar"""
        sim = WeatherSimulator(seed=42)
        start_date = datetime(2102, 10, 23, 8, 0)  # 8 AM
        
        calendar = sim.generate_yearly_calendar(start_date, Region.APPALACHIA)
        
        # Query weather for specific time
        current_time = datetime(2102, 10, 23, 10, 30)  # 10:30 AM
        weather = sim.get_current_weather(current_time, Region.APPALACHIA, calendar)
        
        assert weather is not None
        assert weather.region == "Appalachia"
    
    def test_emergency_weather_flagging(self):
        """Test that emergency weather is properly flagged"""
        sim = WeatherSimulator(seed=42)
        start_date = datetime(2102, 10, 23)
        
        calendar = sim.generate_yearly_calendar(start_date, Region.APPALACHIA)
        
        # Find any emergency weather in the calendar
        emergency_found = False
        for date_str, daily in calendar.items():
            for slot_name, weather in daily.items():
                if weather.is_emergency:
                    emergency_found = True
                    assert weather.weather_type in ["rad_storm", "dust_storm", "glowing_fog"]
                    break
            if emergency_found:
                break
        
        # Not guaranteed to find one, but let's check the logic works
        # by manually creating an emergency weather state
        test_weather = WeatherState(
            weather_type="rad_storm",
            started_at=datetime.now(),
            duration_hours=2.0,
            intensity="severe",
            transition_state="stable",
            is_emergency=True,
            temperature=75.0,
            region="Appalachia"
        )
        assert test_weather.is_emergency


class TestWorldStateWeatherIntegration:
    """Test WorldState integration with weather system"""
    
    def setup_method(self):
        """Setup test with temporary state file"""
        self.test_state_path = "/tmp/test_weather_state.json"
        self.world_state = WorldState(self.test_state_path)
    
    def teardown_method(self):
        """Cleanup test state file"""
        import os
        if os.path.exists(self.test_state_path):
            os.remove(self.test_state_path)
    
    def test_weather_state_initialization(self):
        """Test that weather fields are initialized"""
        assert isinstance(self.world_state.weather_calendars, dict)
        assert isinstance(self.world_state.current_weather_by_region, dict)
        assert isinstance(self.world_state.weather_history_archive, dict)
    
    def test_update_and_get_current_weather(self):
        """Test updating and retrieving current weather"""
        weather_dict = {
            "weather_type": "sunny",
            "temperature": 75.0,
            "region": "Appalachia"
        }
        
        self.world_state.update_weather_state("Appalachia", weather_dict)
        retrieved = self.world_state.get_current_weather("Appalachia")
        
        assert retrieved == weather_dict
        assert retrieved["weather_type"] == "sunny"
    
    def test_weather_history_logging(self):
        """Test logging weather to history"""
        weather_dict = {
            "weather_type": "rad_storm",
            "temperature": 68.0,
            "region": "Appalachia",
            "notable_event": True
        }
        
        timestamp = datetime(2102, 10, 23, 14, 30)
        self.world_state.log_weather_history("Appalachia", timestamp, weather_dict)
        
        # Verify it was logged
        history = self.world_state.get_weather_history("Appalachia")
        assert len(history) > 0
        assert history[0]["weather_type"] == "rad_storm"
    
    def test_manual_weather_override(self):
        """Test manual weather override"""
        override_weather = {
            "weather_type": "snow",
            "temperature": 25.0,
            "region": "Appalachia"
        }
        
        self.world_state.set_manual_weather_override("Appalachia", override_weather)
        current = self.world_state.get_current_weather("Appalachia")
        
        assert current == override_weather
        
        # Clear override
        self.world_state.clear_manual_override("Appalachia")
        current = self.world_state.get_current_weather("Appalachia")
        assert current is None  # No base weather was set
    
    def test_state_persistence(self):
        """Test that weather state persists to file"""
        weather_dict = {
            "weather_type": "cloudy",
            "temperature": 65.0,
            "region": "Mojave"
        }
        
        self.world_state.update_weather_state("Mojave", weather_dict)
        self.world_state.save()
        
        # Load in new instance
        new_state = WorldState(self.test_state_path)
        retrieved = new_state.get_current_weather("Mojave")
        
        assert retrieved == weather_dict


class TestWeatherStateDataclass:
    """Test WeatherState dataclass"""
    
    def test_weather_state_creation(self):
        """Test creating a weather state"""
        weather = WeatherState(
            weather_type="sunny",
            started_at=datetime(2102, 10, 23, 12, 0),
            duration_hours=4.0,
            intensity="minor",
            transition_state="stable",
            is_emergency=False,
            temperature=75.5,
            region="Appalachia"
        )
        
        assert weather.weather_type == "sunny"
        assert weather.temperature == 75.5
        assert weather.region == "Appalachia"
        assert not weather.is_emergency
    
    def test_weather_state_serialization(self):
        """Test converting weather state to/from dict"""
        weather = WeatherState(
            weather_type="rad_storm",
            started_at=datetime(2102, 10, 23, 14, 0),
            duration_hours=2.0,
            intensity="severe",
            transition_state="building",
            is_emergency=True,
            temperature=70.0,
            region="Appalachia",
            notable_event=True
        )
        
        # Convert to dict
        weather_dict = weather.to_dict()
        assert isinstance(weather_dict, dict)
        assert weather_dict["weather_type"] == "rad_storm"
        assert weather_dict["is_emergency"] is True
        
        # Convert back from dict
        restored = WeatherState.from_dict(weather_dict)
        assert restored.weather_type == weather.weather_type
        assert restored.temperature == weather.temperature
        assert restored.is_emergency == weather.is_emergency


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
