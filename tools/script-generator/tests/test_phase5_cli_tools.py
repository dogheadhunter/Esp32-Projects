"""
Phase 5: Manual Override & Debug Tools Tests

Tests for CLI tools that allow manual weather control and history querying.
"""

import unittest
import tempfile
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from io import StringIO

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from world_state import WorldState
from weather_simulator import WeatherState, WeatherSimulator
from regional_climate import REGIONAL_CLIMATES, Region


class TestSetWeatherTool(unittest.TestCase):
    """Test manual weather override functionality"""
    
    def setUp(self):
        """Create temporary test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.original_dir = os.getcwd()
        os.chdir(self.temp_dir)
        self.world_state = WorldState()
    
    def tearDown(self):
        """Clean up test environment"""
        os.chdir(self.original_dir)
        if os.path.exists(os.path.join(self.temp_dir, "broadcast_state.json")):
            os.remove(os.path.join(self.temp_dir, "broadcast_state.json"))
    
    def test_set_manual_override(self):
        """Test setting a manual weather override"""
        # Create override
        weather = WeatherState(
            weather_type="rad_storm",
            started_at=datetime.now(),
            duration_hours=2.0,
            temperature=68.0,
            region="Appalachia",
            intensity="severe",
            transition_state="stable",
            is_emergency=True
        )
        
        weather_dict = weather.to_dict()
        self.world_state.set_manual_weather_override("Appalachia", weather_dict)
        
        # Verify override is set
        self.assertIn("Appalachia", self.world_state.manual_overrides)
        override = self.world_state.manual_overrides["Appalachia"]
        self.assertEqual(override["weather_type"], "rad_storm")
        self.assertEqual(override["temperature"], 68.0)
        self.assertTrue(override["is_emergency"])
    
    def test_clear_manual_override(self):
        """Test clearing a manual weather override"""
        # Set override first
        weather_dict = {
            "weather_type": "sunny",
            "started_at": datetime.now().isoformat(),
            "duration_hours": 4.0,
            "temperature": 75.0,
            "region": "Mojave",
            "is_emergency": False
        }
        self.world_state.set_manual_weather_override("Mojave", weather_dict)
        
        # Clear it
        self.world_state.clear_manual_override("Mojave")
        
        # Verify it's cleared
        override = self.world_state.manual_overrides.get("Mojave")
        self.assertIsNone(override)
    
    def test_override_persists_across_saves(self):
        """Test that overrides persist when saving/loading"""
        # Set override
        weather_dict = {
            "weather_type": "dust_storm",
            "started_at": datetime.now().isoformat(),
            "duration_hours": 3.0,
            "temperature": 95.0,
            "region": "Mojave",
            "is_emergency": True
        }
        self.world_state.set_manual_weather_override("Mojave", weather_dict)
        self.world_state.save()
        
        # Load new instance
        new_state = WorldState()
        override = new_state.manual_overrides.get("Mojave")
        
        # Verify override is loaded
        self.assertIsNotNone(override)
        self.assertEqual(override["weather_type"], "dust_storm")
        self.assertEqual(override["temperature"], 95.0)
    
    def test_multiple_region_overrides(self):
        """Test setting overrides for multiple regions"""
        # Set overrides for all three regions
        regions = ["Appalachia", "Mojave", "Commonwealth"]
        weather_types = ["rainy", "sunny", "snow"]
        
        for region, weather_type in zip(regions, weather_types):
            weather_dict = {
                "weather_type": weather_type,
                "started_at": datetime.now().isoformat(),
                "duration_hours": 2.0,
                "temperature": 60.0,
                "region": region,
                "is_emergency": False
            }
            self.world_state.set_manual_weather_override(region, weather_dict)
        
        # Verify all overrides are independent
        self.assertEqual(
            self.world_state.manual_overrides["Appalachia"]["weather_type"],
            "rainy"
        )
        self.assertEqual(
            self.world_state.manual_overrides["Mojave"]["weather_type"],
            "sunny"
        )
        self.assertEqual(
            self.world_state.manual_overrides["Commonwealth"]["weather_type"],
            "snow"
        )


class TestQueryWeatherHistory(unittest.TestCase):
    """Test weather history query functionality"""
    
    def setUp(self):
        """Create test environment with sample history"""
        self.temp_dir = tempfile.mkdtemp()
        self.original_dir = os.getcwd()
        os.chdir(self.temp_dir)
        self.world_state = WorldState()
        
        # Add sample history
        self._add_sample_history()
    
    def tearDown(self):
        """Clean up test environment"""
        os.chdir(self.original_dir)
        if os.path.exists(os.path.join(self.temp_dir, "broadcast_state.json")):
            os.remove(os.path.join(self.temp_dir, "broadcast_state.json"))
    
    def _add_sample_history(self):
        """Add sample weather history for testing"""
        base_date = datetime(2102, 10, 23, 10, 0)
        weather_types = ["sunny", "cloudy", "rainy", "rad_storm", "foggy"]
        
        for i, weather_type in enumerate(weather_types):
            event_date = base_date + timedelta(days=i)
            event = {
                "weather_type": weather_type,
                "started_at": event_date.isoformat(),
                "duration_hours": 4.0,
                "temperature": 65.0 + i * 5,
                "region": "Appalachia",
                "is_emergency": weather_type == "rad_storm",
                "notable_event": weather_type == "rad_storm"
            }
            # Directly add to history archive
            if "Appalachia" not in self.world_state.weather_history_archive:
                self.world_state.weather_history_archive["Appalachia"] = []
            self.world_state.weather_history_archive["Appalachia"].append(event)
    
    def test_query_all_history(self):
        """Test querying all weather history"""
        history = self.world_state.weather_history_archive.get("Appalachia", [])
        self.assertEqual(len(history), 5)
    
    def test_filter_by_weather_type(self):
        """Test filtering history by weather type"""
        history = self.world_state.weather_history_archive.get("Appalachia", [])
        rad_storms = [e for e in history if e["weather_type"] == "rad_storm"]
        self.assertEqual(len(rad_storms), 1)
    
    def test_filter_notable_events(self):
        """Test filtering for notable events only"""
        history = self.world_state.weather_history_archive.get("Appalachia", [])
        notable = [e for e in history if e.get("notable_event", False)]
        self.assertEqual(len(notable), 1)
        self.assertEqual(notable[0]["weather_type"], "rad_storm")
    
    def test_filter_emergency_events(self):
        """Test filtering for emergency events"""
        history = self.world_state.weather_history_archive.get("Appalachia", [])
        emergencies = [e for e in history if e.get("is_emergency", False)]
        self.assertEqual(len(emergencies), 1)
        self.assertEqual(emergencies[0]["weather_type"], "rad_storm")
    
    def test_date_range_filtering(self):
        """Test filtering by date range"""
        history = self.world_state.weather_history_archive.get("Appalachia", [])
        
        # Filter for first 2 days (inclusive on both ends means Oct 23-24)
        start_date = datetime(2102, 10, 23)
        end_date = datetime(2102, 10, 24, 23, 59, 59)  # End of day 24
        
        filtered = [
            e for e in history
            if start_date <= datetime.fromisoformat(e["started_at"]) <= end_date
        ]
        
        self.assertEqual(len(filtered), 2)


class TestRegenerateCalendar(unittest.TestCase):
    """Test weather calendar regeneration functionality"""
    
    def setUp(self):
        """Create test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.original_dir = os.getcwd()
        os.chdir(self.temp_dir)
        self.world_state = WorldState()
    
    def tearDown(self):
        """Clean up test environment"""
        os.chdir(self.original_dir)
        if os.path.exists(os.path.join(self.temp_dir, "broadcast_state.json")):
            os.remove(os.path.join(self.temp_dir, "broadcast_state.json"))
    
    def test_regenerate_single_region(self):
        """Test regenerating calendar for single region"""
        simulator = WeatherSimulator()
        
        start_date = datetime(2102, 10, 23)
        calendar = simulator.generate_yearly_calendar(start_date, Region.APPALACHIA)
        
        # Verify calendar generated
        self.assertEqual(len(calendar), 365)
        
        # Each day should have 4 time slots
        for day, states in calendar.items():
            self.assertEqual(len(states), 4)
    
    def test_seed_reproducibility(self):
        """Test that same seed produces same calendar"""
        start_date = datetime(2281, 10, 19)
        
        # Generate two calendars with same seed
        sim1 = WeatherSimulator(seed=42)
        calendar1 = sim1.generate_yearly_calendar(start_date, Region.MOJAVE)
        
        sim2 = WeatherSimulator(seed=42)
        calendar2 = sim2.generate_yearly_calendar(start_date, Region.MOJAVE)
        
        # Verify they're identical
        for date_str in calendar1.keys():
            schedule1 = calendar1[date_str]
            schedule2 = calendar2[date_str]
            
            for slot in ["morning", "afternoon", "evening", "night"]:
                self.assertEqual(schedule1[slot].weather_type, schedule2[slot].weather_type)
                self.assertEqual(schedule1[slot].temperature, schedule2[slot].temperature)
    
    def test_different_seeds_produce_different_calendars(self):
        """Test that different seeds produce different calendars"""
        start_date = datetime(2287, 10, 23)
        
        # Generate two calendars with different seeds
        sim1 = WeatherSimulator(seed=1)
        calendar1 = sim1.generate_yearly_calendar(start_date, Region.COMMONWEALTH)
        
        sim2 = WeatherSimulator(seed=2)
        calendar2 = sim2.generate_yearly_calendar(start_date, Region.COMMONWEALTH)
        
        # Count differences
        differences = 0
        for date_str in calendar1.keys():
            schedule1 = calendar1[date_str]
            schedule2 = calendar2[date_str]
            
            for slot in ["morning", "afternoon", "evening", "night"]:
                if schedule1[slot].weather_type != schedule2[slot].weather_type:
                    differences += 1
        
        # Should have significant differences (at least 10%)
        self.assertGreater(differences, 365 * 4 * 0.1)
    
    def test_calendar_persists_to_world_state(self):
        """Test that regenerated calendar persists"""
        simulator = WeatherSimulator(seed=100)
        
        start_date = datetime(2102, 10, 23)
        calendar = simulator.generate_yearly_calendar(start_date, Region.APPALACHIA)
        
        # Convert and store
        calendar_dict = {
            date_str: {
                slot: state.to_dict()
                for slot, state in schedule.items()
            }
            for date_str, schedule in calendar.items()
        }
        
        self.world_state.weather_calendars["Appalachia"] = calendar_dict
        self.world_state.save()
        
        # Load new instance
        new_state = WorldState()
        loaded_calendar = new_state.weather_calendars.get("Appalachia")
        
        # Verify calendar loaded
        self.assertIsNotNone(loaded_calendar)
        self.assertEqual(len(loaded_calendar), 365)


class TestCLIToolsIntegration(unittest.TestCase):
    """Integration tests for CLI tools working together"""
    
    def setUp(self):
        """Create test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.original_dir = os.getcwd()
        os.chdir(self.temp_dir)
        self.world_state = WorldState()
    
    def tearDown(self):
        """Clean up test environment"""
        os.chdir(self.original_dir)
        if os.path.exists(os.path.join(self.temp_dir, "broadcast_state.json")):
            os.remove(os.path.join(self.temp_dir, "broadcast_state.json"))
    
    def test_override_and_query_workflow(self):
        """Test workflow: set override -> generate broadcast -> query history"""
        # 1. Set manual override
        override_weather = {
            "weather_type": "rad_storm",
            "started_at": datetime.now().isoformat(),
            "duration_hours": 2.5,
            "temperature": 72.0,
            "region": "Appalachia",
            "is_emergency": True,
            "notable_event": True
        }
        self.world_state.set_manual_weather_override("Appalachia", override_weather)
        
        # 2. Simulate adding to history (as broadcast would)
        if "Appalachia" not in self.world_state.weather_history_archive:
            self.world_state.weather_history_archive["Appalachia"] = []
        self.world_state.weather_history_archive["Appalachia"].append(override_weather)
        self.world_state.save()
        
        # 3. Query history
        history = self.world_state.weather_history_archive.get("Appalachia", [])
        
        # Verify override appears in history
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["weather_type"], "rad_storm")
        self.assertTrue(history[0]["is_emergency"])
    
    def test_regenerate_and_override_priority(self):
        """Test that manual override takes priority over calendar"""
        # 1. Generate calendar
        simulator = WeatherSimulator(seed=50)
        calendar = simulator.generate_yearly_calendar(datetime(2281, 10, 19), Region.MOJAVE)
        
        calendar_dict = {
            date_str: {
                slot: state.to_dict()
                for slot, state in schedule.items()
            }
            for date_str, schedule in calendar.items()
        }
        self.world_state.weather_calendars["Mojave"] = calendar_dict
        
        # 2. Set manual override
        override = {
            "weather_type": "dust_storm",
            "started_at": datetime.now().isoformat(),
            "duration_hours": 3.0,
            "temperature": 105.0,
            "region": "Mojave",
            "is_emergency": True
        }
        self.world_state.set_manual_weather_override("Mojave", override)
        
        # 3. Get current weather (should return override, not calendar)
        current = self.world_state.get_current_weather("Mojave")
        
        # Verify override is used
        self.assertIsNotNone(current)
        self.assertEqual(current["weather_type"], "dust_storm")
        self.assertEqual(current["temperature"], 105.0)


def run_phase5_tests():
    """Run all Phase 5 tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestSetWeatherTool))
    suite.addTests(loader.loadTestsFromTestCase(TestQueryWeatherHistory))
    suite.addTests(loader.loadTestsFromTestCase(TestRegenerateCalendar))
    suite.addTests(loader.loadTestsFromTestCase(TestCLIToolsIntegration))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_phase5_tests()
    sys.exit(0 if success else 1)
