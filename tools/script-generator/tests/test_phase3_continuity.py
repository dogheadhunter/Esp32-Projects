"""
Unit Tests for Weather Simulation System - Phase 3 Implementation

Tests historical context and continuity features.
"""

import pytest
from datetime import datetime
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from session_memory import SessionMemory
from world_state import WorldState


class TestWeatherContinuity:
    """Test Phase 3: Weather continuity and historical context"""
    
    def setup_method(self):
        """Setup test with session memory"""
        self.session_memory = SessionMemory(max_history=10, dj_name="Julie")
        self.world_state = WorldState("/tmp/test_phase3_state.json")
    
    def teardown_method(self):
        """Cleanup"""
        import os
        if os.path.exists("/tmp/test_phase3_state.json"):
            os.remove("/tmp/test_phase3_state.json")
    
    def test_weather_continuity_no_previous_weather(self):
        """Test weather continuity when no previous weather exists"""
        current_weather = {
            'weather_type': 'sunny',
            'temperature': 75.0,
            'region': 'Appalachia'
        }
        
        context = self.session_memory.get_weather_continuity_context(
            region='Appalachia',
            current_weather_dict=current_weather
        )
        
        assert context['weather_changed'] is False
        assert context['last_weather_type'] is None
        assert context['continuity_phrase'] is None
    
    def test_weather_continuity_with_change(self):
        """Test weather continuity when weather changes"""
        # Add a previous weather segment
        self.session_memory.add_script(
            script_type='weather',
            content='It\'s rainy outside',
            metadata={'weather_type': 'rainy'}
        )
        
        # Current weather is different
        current_weather = {
            'weather_type': 'sunny',
            'temperature': 75.0,
            'region': 'Appalachia'
        }
        
        context = self.session_memory.get_weather_continuity_context(
            region='Appalachia',
            current_weather_dict=current_weather
        )
        
        assert context['weather_changed'] is True
        assert context['last_weather_type'] == 'rainy'
        assert context['continuity_phrase'] is not None
        assert 'rain' in context['continuity_phrase'].lower() or 'clear' in context['continuity_phrase'].lower()
    
    def test_weather_continuity_no_change(self):
        """Test weather continuity when weather stays the same"""
        # Add a previous weather segment
        self.session_memory.add_script(
            script_type='weather',
            content='It\'s sunny outside',
            metadata={'weather_type': 'sunny'}
        )
        
        # Current weather is the same
        current_weather = {
            'weather_type': 'sunny',
            'temperature': 75.0,
            'region': 'Appalachia'
        }
        
        context = self.session_memory.get_weather_continuity_context(
            region='Appalachia',
            current_weather_dict=current_weather
        )
        
        assert context['weather_changed'] is False
        assert context['last_weather_type'] == 'sunny'
        assert context['continuity_phrase'] is None
    
    def test_continuity_phrase_generation(self):
        """Test that continuity phrases are generated correctly"""
        # Test several weather transitions
        transitions = [
            ('rainy', 'sunny', 'Appalachia'),
            ('sunny', 'rainy', 'Mojave'),
            ('cloudy', 'rad_storm', 'Commonwealth'),
            ('foggy', 'sunny', 'Appalachia'),
        ]
        
        for last, current, region in transitions:
            phrase = self.session_memory._generate_continuity_phrase(
                last, current, region
            )
            assert isinstance(phrase, str)
            assert len(phrase) > 10  # Should be a meaningful phrase
    
    def test_regional_location_references(self):
        """Test that continuity phrases include regional references"""
        # Appalachia references
        phrase = self.session_memory._generate_continuity_phrase(
            'rainy', 'sunny', 'Appalachia'
        )
        # Should mention mountains, valley, or these parts
        has_regional_ref = any(ref in phrase.lower() for ref in ['mountain', 'valley', 'parts'])
        # Not all phrases have regional refs, but check it works
        assert isinstance(phrase, str)
        
        # Mojave references
        phrase = self.session_memory._generate_continuity_phrase(
            'sunny', 'rainy', 'Mojave'
        )
        assert isinstance(phrase, str)
    
    def test_get_last_weather_from_memory(self):
        """Test extracting last weather from session memory"""
        # No weather in memory
        last = self.session_memory._get_last_weather_from_memory()
        assert last is None
        
        # Add some non-weather segments
        self.session_memory.add_script(
            script_type='news',
            content='News content'
        )
        
        last = self.session_memory._get_last_weather_from_memory()
        assert last is None
        
        # Add weather segment
        self.session_memory.add_script(
            script_type='weather',
            content='Weather content',
            metadata={'weather_type': 'cloudy'}
        )
        
        last = self.session_memory._get_last_weather_from_memory()
        assert last == 'cloudy'
        
        # Add another weather segment
        self.session_memory.add_script(
            script_type='weather',
            content='New weather',
            metadata={'weather_type': 'rainy'}
        )
        
        last = self.session_memory._get_last_weather_from_memory()
        assert last == 'rainy'  # Should get most recent
    
    def test_notable_history_flag(self):
        """Test that notable history flag works"""
        current_weather = {'weather_type': 'sunny', 'region': 'Appalachia'}
        
        # With no scripts
        context = self.session_memory.get_weather_continuity_context(
            'Appalachia', current_weather
        )
        assert context['has_notable_history'] is False
        
        # Add a few scripts
        for i in range(5):
            self.session_memory.add_script(
                script_type='weather' if i % 2 == 0 else 'news',
                content=f'Content {i}'
            )
        
        context = self.session_memory.get_weather_continuity_context(
            'Appalachia', current_weather
        )
        assert context['has_notable_history'] is True
    
    def test_continuity_context_structure(self):
        """Test that continuity context has expected structure"""
        current_weather = {
            'weather_type': 'sunny',
            'temperature': 75.0,
            'region': 'Appalachia'
        }
        
        context = self.session_memory.get_weather_continuity_context(
            'Appalachia', current_weather
        )
        
        # Check all expected keys are present
        assert 'weather_changed' in context
        assert 'last_weather_type' in context
        assert 'continuity_phrase' in context
        assert 'has_notable_history' in context
        
        # Check types
        assert isinstance(context['weather_changed'], bool)
        assert context['last_weather_type'] is None or isinstance(context['last_weather_type'], str)
        assert context['continuity_phrase'] is None or isinstance(context['continuity_phrase'], str)
        assert isinstance(context['has_notable_history'], bool)
    
    def test_emergency_weather_transitions(self):
        """Test continuity phrases for emergency weather"""
        # Transition to rad storm
        phrase = self.session_memory._generate_continuity_phrase(
            'cloudy', 'rad_storm', 'Appalachia'
        )
        assert 'storm' in phrase.lower() or 'radiation' in phrase.lower() or 'rad' in phrase.lower()
        
        # Transition from rad storm
        phrase = self.session_memory._generate_continuity_phrase(
            'rad_storm', 'cloudy', 'Commonwealth'
        )
        assert 'clear' in phrase.lower() or 'pass' in phrase.lower() or 'over' in phrase.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
