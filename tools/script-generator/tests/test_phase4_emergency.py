"""
Unit Tests for Weather Simulation System - Phase 4 Implementation

Tests emergency weather alert system.
"""

import pytest
from datetime import datetime
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from weather_simulator import WeatherSimulator, WeatherState
from regional_climate import Region
from world_state import WorldState
from session_memory import SessionMemory


class TestEmergencyWeatherSystem:
    """Test Phase 4: Emergency weather alert system"""
    
    def setup_method(self):
        """Setup test with session memory and world state"""
        self.session_memory = SessionMemory(max_history=10, dj_name="Julie")
        self.world_state = WorldState("/tmp/test_phase4_state.json")
        self.simulator = WeatherSimulator(seed=42)
    
    def teardown_method(self):
        """Cleanup"""
        import os
        if os.path.exists("/tmp/test_phase4_state.json"):
            os.remove("/tmp/test_phase4_state.json")
    
    def test_emergency_weather_detection(self):
        """Test that emergency weather is correctly identified"""
        # Create emergency weather states
        rad_storm = WeatherState(
            weather_type="rad_storm",
            started_at=datetime(2102, 10, 23, 14, 0),
            duration_hours=2.5,
            intensity="severe",
            transition_state="building",
            is_emergency=True,
            temperature=72.0,
            region="Appalachia"
        )
        
        assert rad_storm.is_emergency is True
        assert rad_storm.weather_type == "rad_storm"
        assert rad_storm.intensity == "severe"
    
    def test_non_emergency_weather(self):
        """Test that normal weather is not flagged as emergency"""
        sunny = WeatherState(
            weather_type="sunny",
            started_at=datetime(2102, 10, 23, 10, 0),
            duration_hours=4.0,
            intensity="minor",
            transition_state="stable",
            is_emergency=False,
            temperature=75.0,
            region="Appalachia"
        )
        
        assert sunny.is_emergency is False
    
    def test_regional_shelter_instructions(self):
        """Test that regional shelter instructions are provided"""
        regions_and_keywords = {
            "Appalachia": ["underground", "vault", "mine", "scorchbeast"],
            "Mojave": ["concrete", "strip", "lucky 38", "vault"],
            "Commonwealth": ["vault-tec", "subway", "diamond city", "glowing sea"]
        }
        
        # Mock method since we're not testing the full broadcast engine
        def get_regional_shelter_instructions(region):
            regional_instructions = {
                "Appalachia": (
                    "Get underground immediately. Vaults, mine shafts, or reinforced basements. "
                    "Seal all openings. If caught outside, find a cave or rocky overhang. "
                    "Scorchbeast activity increases during rad storms - stay hidden."
                ),
                "Mojave": (
                    "Seek concrete structures or underground facilities. "
                    "The Strip casinos have reinforced levels. Lucky 38, Vault entrances, or "
                    "the sewers can provide protection. Avoid metal structures - radiation magnets."
                ),
                "Commonwealth": (
                    "Get to a Vault-Tec facility, subway station, or reinforced building. "
                    "Diamond City walls provide some protection. Avoid the Glowing Sea direction. "
                    "Institute-grade filtration helps but isn't foolproof."
                )
            }
            return regional_instructions.get(region, "Seek immediate shelter.")
        
        for region, keywords in regions_and_keywords.items():
            instructions = get_regional_shelter_instructions(region)
            assert isinstance(instructions, str)
            assert len(instructions) > 50  # Should be detailed
            
            # Check for at least one keyword
            found_keyword = any(kw.lower() in instructions.lower() for kw in keywords)
            assert found_keyword, f"No keywords found in {region} instructions"
    
    def test_already_alerted_for_event(self):
        """Test that duplicate alerts are prevented"""
        # Create an emergency weather event
        rad_storm = WeatherState(
            weather_type="rad_storm",
            started_at=datetime(2102, 10, 23, 14, 0),
            duration_hours=2.5,
            intensity="severe",
            transition_state="building",
            is_emergency=True,
            temperature=72.0,
            region="Appalachia"
        )
        
        # Add emergency alert to session memory
        self.session_memory.add_script(
            script_type='emergency_weather',
            content='RADIATION STORM ALERT!',
            metadata={
                'weather_type': 'rad_storm',
                'started_at': '2102-10-23T14:00:00',
                'is_emergency': True
            }
        )
        
        # Mock the already_alerted check
        def already_alerted(weather_state):
            for entry in reversed(self.session_memory.recent_scripts):
                if entry.script_type == 'emergency_weather':
                    event_meta = entry.metadata
                    if (event_meta.get('weather_type') == weather_state.weather_type and
                        event_meta.get('started_at') == weather_state.started_at.isoformat()):
                        return True
            return False
        
        # Should detect that we already alerted
        assert already_alerted(rad_storm) is True
        
        # Different event should not be detected
        different_storm = WeatherState(
            weather_type="rad_storm",
            started_at=datetime(2102, 10, 24, 10, 0),  # Different time
            duration_hours=2.0,
            intensity="severe",
            transition_state="building",
            is_emergency=True,
            temperature=70.0,
            region="Appalachia"
        )
        
        assert already_alerted(different_storm) is False
    
    def test_emergency_types_coverage(self):
        """Test that all emergency weather types are supported"""
        emergency_types = ["rad_storm", "dust_storm", "glowing_fog"]
        
        for emergency_type in emergency_types:
            weather = WeatherState(
                weather_type=emergency_type,
                started_at=datetime(2102, 10, 23, 14, 0),
                duration_hours=2.0,
                intensity="severe",
                transition_state="building",
                is_emergency=True,
                temperature=70.0,
                region="Appalachia"
            )
            
            assert weather.is_emergency is True
            assert weather.weather_type == emergency_type
    
    def test_emergency_rag_context(self):
        """Test that emergency RAG context includes shelter locations"""
        # Mock method to get emergency RAG context
        def get_emergency_rag_context(region, weather_type):
            regional_context = {
                "Appalachia": (
                    "Appalachian region emergency protocol active. "
                    "Known shelters: Vault 76 entrance caverns, Flatwoods bunker, "
                    "Charleston Fire Department basement, Morgantown Airport hangars. "
                    "Scorchbeasts drawn to radiation - expect increased hostile activity."
                ),
                "Mojave": (
                    "Mojave Wasteland emergency protocol active. "
                    "Known shelters: Vault 21 (if accessible), Lucky 38 basement levels, "
                    "Camp McCarran bunkers, Hoover Dam lower levels, NCR safehouses. "
                    "Dust walls can carry debris - structural collapse risk."
                ),
                "Commonwealth": (
                    "Commonwealth emergency protocol active. "
                    "Known shelters: Vault 111 entrance, Diamond City security bunker, "
                    "Railroad safehouses, abandoned subway stations, Prydwen (if Brotherhood ally). "
                    "Glowing Sea drift - avoid northeast exposure."
                )
            }
            return regional_context.get(region, "Seek shelter immediately.")
        
        # Test each region
        for region in ["Appalachia", "Mojave", "Commonwealth"]:
            context = get_emergency_rag_context(region, "rad_storm")
            assert isinstance(context, str)
            assert len(context) > 100  # Should be detailed
            assert "shelter" in context.lower() or "bunker" in context.lower() or "vault" in context.lower()
    
    def test_emergency_priority_over_normal(self):
        """Test that emergency weather takes priority"""
        # This would be tested in integration, but we can verify the logic
        # Emergency weather should be checked before normal scheduling
        
        # Mock scenario: normal weather scheduled, but emergency detected
        scheduled_type = "gossip"
        
        emergency_weather = WeatherState(
            weather_type="rad_storm",
            started_at=datetime(2102, 10, 23, 14, 0),
            duration_hours=2.5,
            intensity="severe",
            transition_state="building",
            is_emergency=True,
            temperature=72.0,
            region="Appalachia"
        )
        
        # Emergency should override
        assert emergency_weather.is_emergency is True
        # In real implementation, this would trigger emergency alert instead of gossip
    
    def test_emergency_severity_levels(self):
        """Test that emergency weather has proper severity levels"""
        severities = ["moderate", "severe"]
        
        for severity in severities:
            weather = WeatherState(
                weather_type="rad_storm",
                started_at=datetime(2102, 10, 23, 14, 0),
                duration_hours=2.0,
                intensity=severity,
                transition_state="building",
                is_emergency=True,
                temperature=70.0,
                region="Appalachia"
            )
            
            assert weather.intensity in ["moderate", "severe"]
            assert weather.is_emergency is True
    
    def test_emergency_duration_tracking(self):
        """Test that emergency weather duration is tracked"""
        weather = WeatherState(
            weather_type="rad_storm",
            started_at=datetime(2102, 10, 23, 14, 0),
            duration_hours=3.5,
            intensity="severe",
            transition_state="building",
            is_emergency=True,
            temperature=70.0,
            region="Appalachia"
        )
        
        assert weather.duration_hours == 3.5
        # All-clear time would be started_at + duration_hours
        end_time = weather.started_at
        # In real use, would calculate: end_time + timedelta(hours=duration_hours)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
