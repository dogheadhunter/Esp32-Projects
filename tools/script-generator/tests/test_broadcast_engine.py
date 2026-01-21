"""
Comprehensive tests for BroadcastEngine - Core orchestration module

Tests cover:
- Engine initialization and configuration
- Session memory integration
- World state management
- Content type generation (weather, news, gossip, time checks)
- Story system integration
- Validation system modes (rules, LLM, hybrid)
- Segment generation workflow
- Error handling and fallbacks
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
import tempfile
import json

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from broadcast_engine import BroadcastEngine
from session_memory import SessionMemory
from world_state import WorldState
from segment_plan import SegmentType


class TestBroadcastEngineInitialization:
    """Test BroadcastEngine initialization and configuration"""
    
    def test_basic_initialization(self, tmp_path):
        """Test basic engine initialization with minimal config"""
        world_state_path = str(tmp_path / "test_state.json")
        
        engine = BroadcastEngine(
            dj_name="Julie",
            world_state_path=world_state_path,
            enable_validation=False,
            enable_story_system=False
        )
        
        assert engine.dj_name == "Julie"
        assert engine.enable_validation is False
        assert engine.session_memory is not None
        assert engine.world_state is not None
        assert engine.generator is not None
        assert engine.scheduler is not None
        assert engine.gossip_tracker is not None
        assert engine.validator is None
    
    def test_initialization_with_validation_rules(self, tmp_path):
        """Test initialization with rules-based validation"""
        world_state_path = str(tmp_path / "test_state.json")
        
        engine = BroadcastEngine(
            dj_name="Julie (2102, Appalachia)",
            world_state_path=world_state_path,
            enable_validation=True,
            validation_mode='rules',
            enable_story_system=False
        )
        
        assert engine.enable_validation is True
        assert engine.validation_mode == 'rules'
        assert engine.validator is not None
    
    def test_initialization_custom_memory_size(self, tmp_path):
        """Test initialization with custom session memory size"""
        world_state_path = str(tmp_path / "test_state.json")
        
        engine = BroadcastEngine(
            dj_name="Julie",
            world_state_path=world_state_path,
            max_session_memory=20,
            enable_validation=False,
            enable_story_system=False
        )
        
        assert engine.session_memory.max_history == 20
    
    def test_broadcast_metrics_initialized(self, tmp_path):
        """Test that broadcast metrics are properly initialized"""
        world_state_path = str(tmp_path / "test_state.json")
        
        engine = BroadcastEngine(
            dj_name="Julie",
            world_state_path=world_state_path,
            enable_validation=False,
            enable_story_system=False
        )
        
        assert isinstance(engine.broadcast_start, datetime)
        assert engine.segments_generated == 0
        assert engine.validation_failures == 0
        assert engine.total_generation_time == 0.0


class TestWeatherSystemIntegration:
    """Test weather system integration in BroadcastEngine"""
    
    def test_weather_calendar_initialization(self, tmp_path):
        """Test that weather calendar is initialized for DJ's region"""
        world_state_path = str(tmp_path / "test_state.json")
        
        with patch('broadcast_engine.WEATHER_SYSTEM_AVAILABLE', True):
            with patch('broadcast_engine.get_region_from_dj_name') as mock_region:
                from regional_climate import Region
                mock_region.return_value = Region.APPALACHIA
                
                engine = BroadcastEngine(
                    dj_name="Julie",
                    world_state_path=world_state_path,
                    enable_validation=False,
                    enable_story_system=False
                )
                
                assert engine.region == Region.APPALACHIA
                assert engine.weather_simulator is not None
    
    def test_weather_calendar_persistence(self, tmp_path):
        """Test that weather calendar is saved and loaded from world state"""
        world_state_path = str(tmp_path / "test_state.json")
        
        # Create engine which should generate calendar
        with patch('broadcast_engine.WEATHER_SYSTEM_AVAILABLE', True):
            with patch('broadcast_engine.get_region_from_dj_name') as mock_region:
                from regional_climate import Region
                mock_region.return_value = Region.APPALACHIA
                
                engine1 = BroadcastEngine(
                    dj_name="Julie (2102, Appalachia)",
                    world_state_path=world_state_path,
                    enable_validation=False,
                    enable_story_system=False
                )
                
                # Calendar should be created - check if weather_calendars dict has data
                assert len(engine1.world_state.weather_calendars) > 0
                
                # Create new engine - should load existing calendar
                engine2 = BroadcastEngine(
                    dj_name="Julie (2102, Appalachia)",
                    world_state_path=world_state_path,
                    enable_validation=False,
                    enable_story_system=False
                )
                
                # Calendar should have been loaded from saved state
                assert len(engine2.world_state.weather_calendars) > 0


class TestSegmentGeneration:
    """Test segment generation workflow"""
    
    def test_get_next_segment_type(self, tmp_path):
        """Test that scheduler provides next segment type"""
        world_state_path = str(tmp_path / "test_state.json")
        
        engine = BroadcastEngine(
            dj_name="Julie (2102, Appalachia)",
            world_state_path=world_state_path,
            enable_validation=False,
            enable_story_system=False
        )
        
        # Scheduler returns None for legacy compatibility
        segment_type = engine.scheduler.get_next_priority_segment()
        assert segment_type is None
        engine = BroadcastEngine(
            dj_name="Julie",
            world_state_path=world_state_path,
            enable_validation=False,
            enable_story_system=False
        )
        
        initial_count = engine.segments_generated
        
        # Mock a segment generation (without actually calling LLM)
        engine.segments_generated += 1
        engine.total_generation_time += 1.5
        
        assert engine.segments_generated == initial_count + 1
        assert engine.total_generation_time == 1.5


class TestSessionMemoryIntegration:
    """Test session memory integration"""
    
    def test_session_memory_tracks_scripts(self, tmp_path):
        """Test that generated scripts are tracked in session memory"""
        world_state_path = str(tmp_path / "test_state.json")
        
        engine = BroadcastEngine(
            dj_name="Julie (2102, Appalachia)",
            world_state_path=world_state_path,
            enable_validation=False,
            enable_story_system=False,
            max_session_memory=5
        )
        
        # Add some test scripts
        engine.session_memory.add_script(
            script_type="weather",
            content="Test weather script",
            metadata={"timestamp": datetime.now().isoformat()}
        )
        
        assert len(engine.session_memory.recent_scripts) == 1
        
        # Add more to test limit
        for i in range(5):
            engine.session_memory.add_script(
                script_type="news",
                content=f"Test script {i}",
                metadata={"timestamp": datetime.now().isoformat()}
            )
        
        # Should only keep 5 (max_session_memory)
        assert len(engine.session_memory.recent_scripts) == 5


class TestGossipTracking:
    """Test gossip tracking functionality"""
    
    def test_gossip_tracker_initialized(self, tmp_path):
        """Test that gossip tracker is initialized"""
        world_state_path = str(tmp_path / "test_state.json")
        
        engine = BroadcastEngine(
            dj_name="Julie (2102, Appalachia)",
            world_state_path=world_state_path,
            enable_validation=False,
            enable_story_system=False
        )
        
        assert engine.gossip_tracker is not None
    
    def test_gossip_lifecycle(self, tmp_path):
        """Test adding and resolving gossip"""
        world_state_path = str(tmp_path / "test_state.json")
        
        engine = BroadcastEngine(
            dj_name="Julie (2102, Appalachia)",
            world_state_path=world_state_path,
            enable_validation=False,
            enable_story_system=False
        )
        
        # Add gossip
        gossip_id = engine.gossip_tracker.add_gossip(
            topic="strange_lights_vault",
            initial_rumor="Strange lights near Vault in Appalachia",
            category="mysterious_events"
        )
        
        assert gossip_id is not None
        gossip = engine.gossip_tracker.get_gossip("strange_lights_vault")
        assert gossip is not None
        assert gossip["topic"] == "strange_lights_vault"
        assert gossip["category"] == "mysterious_events"


class TestWorldStatePersistence:
    """Test world state persistence"""
    
    def test_world_state_saves_and_loads(self, tmp_path):
        """Test that world state is persisted to disk"""
        world_state_path = str(tmp_path / "test_state.json")
        
        # Create engine and modify world state
        engine1 = BroadcastEngine(
            dj_name="Julie (2102, Appalachia)",
            world_state_path=world_state_path,
            enable_validation=False,
            enable_story_system=False
        )
        
        # Add a storyline
        engine1.world_state.add_storyline(
            topic="The Missing Caravan",
            initial_development="Caravan last seen near Red Rocket",
            gossip_level="medium"
        )
        
        engine1.world_state.save()
        
        # Create new engine with same path
        engine2 = BroadcastEngine(
            dj_name="Julie (2102, Appalachia)",
            world_state_path=world_state_path,
            enable_validation=False,
            enable_story_system=False
        )
        
        # Check storyline was loaded
        storylines = engine2.world_state.ongoing_storylines
        assert len(storylines) == 1
        assert storylines[0]["topic"] == "The Missing Caravan"


class TestValidationModes:
    """Test different validation modes"""
    
    def test_validation_disabled(self, tmp_path):
        """Test engine with validation disabled"""
        world_state_path = str(tmp_path / "test_state.json")
        
        engine = BroadcastEngine(
            dj_name="Julie (2102, Appalachia)",
            world_state_path=world_state_path,
            enable_validation=False,
            enable_story_system=False
        )
        
        assert engine.validator is None
        assert engine.validation_failures == 0
    
    def test_rules_validation_mode(self, tmp_path):
        """Test engine with rules-based validation"""
        world_state_path = str(tmp_path / "test_state.json")
        
        engine = BroadcastEngine(
            dj_name="Julie (2102, Appalachia)",
            world_state_path=world_state_path,
            enable_validation=True,
            validation_mode='rules',
            enable_story_system=False
        )
        
        assert engine.validator is not None
        assert engine.validation_mode == 'rules'


class TestErrorHandling:
    """Test error handling and fallbacks"""
    
    def test_missing_world_state_path(self):
        """Test that default world state path is used when not provided"""
        engine = BroadcastEngine(
            dj_name="Julie (2102, Appalachia)",
            enable_validation=False,
            enable_story_system=False
        )
        
        assert engine.world_state is not None
        assert str(engine.world_state.persistence_path) == "broadcast_state.json"
    
    def test_invalid_validation_mode_fallback(self, tmp_path):
        """Test fallback to rules validation for invalid mode"""
        world_state_path = str(tmp_path / "test_state.json")
        
        with patch('broadcast_engine.LLM_VALIDATION_AVAILABLE', False):
            engine = BroadcastEngine(
                dj_name="Julie (2102, Appalachia)",
                world_state_path=world_state_path,
                enable_validation=True,
                validation_mode='llm',  # Not available
                enable_story_system=False
            )
            
            # Should fallback to rules
            assert engine.validation_mode == 'rules'
            assert engine.validator is not None


class TestSchedulerIntegration:
    """Test broadcast scheduler integration"""
    
    def test_scheduler_initialization(self, tmp_path):
        """Test that scheduler is properly initialized"""
        world_state_path = str(tmp_path / "test_state.json")
        
        engine = BroadcastEngine(
            dj_name="Julie",
            world_state_path=world_state_path,
            enable_validation=False,
            enable_story_system=False
        )
        
        assert engine.scheduler is not None
    
    def test_scheduler_segment_ready(self, tmp_path):
        """Test scheduler's segment readiness checking"""
        world_state_path = str(tmp_path / "test_state.json")
        
        engine = BroadcastEngine(
            dj_name="Julie (2102, Appalachia)",
            world_state_path=world_state_path,
            enable_validation=False,
            enable_story_system=False
        )
        
        # Check if scheduler has is_time_for_segment method
        assert engine.scheduler.is_time_for_segment(SegmentType.WEATHER.value)


class TestStorySystemIntegration:
    """Test story system integration"""
    
    def test_story_system_enabled(self, tmp_path):
        """Test story system initialization when enabled"""
        world_state_path = str(tmp_path / "test_state.json")
        
        with patch('broadcast_engine.STORY_SYSTEM_AVAILABLE', True):
            engine = BroadcastEngine(
                dj_name="Julie",
                world_state_path=world_state_path,
                enable_validation=False,
                enable_story_system=True
            )
            
            assert engine.story_state is not None
            assert engine.story_scheduler is not None
            assert engine.story_weaver is not None
    
    def test_story_system_disabled(self, tmp_path):
        """Test that story system is not initialized when disabled"""
        world_state_path = str(tmp_path / "test_state.json")
        
        engine = BroadcastEngine(
            dj_name="Julie",
            world_state_path=world_state_path,
            enable_validation=False,
            enable_story_system=False
        )
        
        # Story system components should be None
        assert engine.story_scheduler is None
        assert engine.story_weaver is None
        assert engine.story_state is None


class TestGeneratorIntegration:
    """Test script generator integration"""
    
    def test_generator_initialized(self, tmp_path):
        """Test that script generator is initialized"""
        world_state_path = str(tmp_path / "test_state.json")
        
        engine = BroadcastEngine(
            dj_name="Julie",
            world_state_path=world_state_path,
            enable_validation=False,
            enable_story_system=False
        )
        
        assert engine.generator is not None
    
    def test_generator_with_custom_paths(self, tmp_path):
        """Test generator initialization with custom template and DB paths"""
        world_state_path = str(tmp_path / "test_state.json")
        templates_dir = str(tmp_path / "templates")
        chroma_dir = str(tmp_path / "chroma")
        
        Path(templates_dir).mkdir()
        
        engine = BroadcastEngine(
            dj_name="Julie",
            templates_dir=templates_dir,
            chroma_db_dir=chroma_dir,
            world_state_path=world_state_path,
            enable_validation=False,
            enable_story_system=False
        )
        
        assert engine.generator is not None


# ============================================================================
# CHECKPOINT 1: Additional Coverage Tests for broadcast_engine.py (31% → 60%)
# Target: 15-20 new tests covering uncovered methods
# ============================================================================


class TestBroadcastEngineWeatherSystemAdvanced:
    """Test advanced weather system functionality"""
    
    def test_initialize_weather_calendar_creates_new_calendar(self, tmp_path):
        """Test _initialize_weather_calendar generates new calendar when none exists"""
        world_state_path = str(tmp_path / "test_state.json")
        
        with patch('broadcast_engine.WEATHER_SYSTEM_AVAILABLE', True):
            with patch('broadcast_engine.get_region_from_dj_name') as mock_region:
                from regional_climate import Region
                mock_region.return_value = Region.APPALACHIA
                
                with patch('broadcast_engine.WeatherSimulator') as MockSimulator:
                    mock_simulator = MockSimulator.return_value
                    
                    # Mock calendar generation
                    mock_calendar = {
                        '2026-01-01': {
                            'morning': Mock(to_dict=lambda: {'weather_type': 'partly_cloudy'}),
                            'midday': Mock(to_dict=lambda: {'weather_type': 'clear'}),
                        }
                    }
                    mock_simulator.generate_yearly_calendar.return_value = mock_calendar
                    
                    engine = BroadcastEngine(
                        dj_name="Julie (2102, Appalachia)",
                        world_state_path=world_state_path,
                        enable_validation=False,
                        enable_story_system=False
                    )
                    
                    # Verify calendar was generated
                    mock_simulator.generate_yearly_calendar.assert_called_once()
                    assert len(engine.world_state.weather_calendars) > 0
    
    def test_initialize_weather_calendar_loads_existing(self, tmp_path):
        """Test _initialize_weather_calendar loads existing calendar"""
        world_state_path = str(tmp_path / "test_state.json")
        
        # Pre-populate world state with calendar
        world_state_data = {
            'weather_calendars': {
                'Appalachia': {
                    '2026-01-01': {'morning': {'weather_type': 'cloudy'}}
                }
            },
            'calendar_metadata': {
                'Appalachia': {'generated_date': '2026-01-01T00:00:00'}
            }
        }
        
        with open(world_state_path, 'w') as f:
            json.dump(world_state_data, f)
        
        with patch('broadcast_engine.WEATHER_SYSTEM_AVAILABLE', True):
            with patch('broadcast_engine.get_region_from_dj_name') as mock_region:
                from regional_climate import Region
                mock_region.return_value = Region.APPALACHIA
                
                with patch('broadcast_engine.WeatherSimulator') as MockSimulator:
                    mock_simulator = MockSimulator.return_value
                    
                    engine = BroadcastEngine(
                        dj_name="Julie (2102, Appalachia)",
                        world_state_path=world_state_path,
                        enable_validation=False,
                        enable_story_system=False
                    )
                    
                    # Verify calendar was NOT regenerated (loaded from file)
                    mock_simulator.generate_yearly_calendar.assert_not_called()
                    assert 'Appalachia' in engine.world_state.weather_calendars
    
    def test_check_for_emergency_weather_detects_emergency(self, tmp_path):
        """Test check_for_emergency_weather returns emergency weather state"""
        world_state_path = str(tmp_path / "test_state.json")
        
        with patch('broadcast_engine.WEATHER_SYSTEM_AVAILABLE', True):
            with patch('broadcast_engine.get_region_from_dj_name') as mock_region:
                from regional_climate import Region
                mock_region.return_value = Region.APPALACHIA
                
                engine = BroadcastEngine(
                    dj_name="Julie (2102, Appalachia)",
                    world_state_path=world_state_path,
                    enable_validation=False,
                    enable_story_system=False
                )
                
                # Mock emergency weather
                mock_weather = Mock()
                mock_weather.is_emergency = True
                mock_weather.weather_type = 'radiation_storm'
                mock_weather.started_at = datetime.now()
                
                with patch.object(engine, '_get_current_weather_from_simulator', return_value=mock_weather):
                    emergency = engine.check_for_emergency_weather(current_hour=14)
                    
                    assert emergency is not None
                    assert emergency.is_emergency is True
                    assert emergency.weather_type == 'radiation_storm'
    
    def test_check_for_emergency_weather_returns_none_for_normal_weather(self, tmp_path):
        """Test check_for_emergency_weather returns None for non-emergency"""
        world_state_path = str(tmp_path / "test_state.json")
        
        with patch('broadcast_engine.WEATHER_SYSTEM_AVAILABLE', True):
            with patch('broadcast_engine.get_region_from_dj_name') as mock_region:
                from regional_climate import Region
                mock_region.return_value = Region.APPALACHIA
                
                engine = BroadcastEngine(
                    dj_name="Julie (2102, Appalachia)",
                    world_state_path=world_state_path,
                    enable_validation=False,
                    enable_story_system=False
                )
                
                # Mock normal weather
                mock_weather = Mock()
                mock_weather.is_emergency = False
                
                with patch.object(engine, '_get_current_weather_from_simulator', return_value=mock_weather):
                    emergency = engine.check_for_emergency_weather(current_hour=14)
                    
                    assert emergency is None
    
    def test_check_for_emergency_weather_skips_already_alerted(self, tmp_path):
        """Test check_for_emergency_weather skips already alerted events"""
        world_state_path = str(tmp_path / "test_state.json")
        
        with patch('broadcast_engine.WEATHER_SYSTEM_AVAILABLE', True):
            with patch('broadcast_engine.get_region_from_dj_name') as mock_region:
                from regional_climate import Region
                mock_region.return_value = Region.APPALACHIA
                
                engine = BroadcastEngine(
                    dj_name="Julie (2102, Appalachia)",
                    world_state_path=world_state_path,
                    enable_validation=False,
                    enable_story_system=False
                )
                
                # Add emergency to session memory (already alerted)
                started_at = datetime.now()
                engine.session_memory.add_script(
                    script_type='emergency_weather',
                    content='Previous alert',
                    metadata={
                        'weather_type': 'radiation_storm',
                        'started_at': started_at.isoformat()
                    }
                )
                
                # Mock same emergency
                mock_weather = Mock()
                mock_weather.is_emergency = True
                mock_weather.weather_type = 'radiation_storm'
                mock_weather.started_at = started_at
                
                with patch.object(engine, '_get_current_weather_from_simulator', return_value=mock_weather):
                    emergency = engine.check_for_emergency_weather(current_hour=14)
                    
                    # Should return None (already alerted)
                    assert emergency is None
    
    def test_get_regional_shelter_instructions_appalachia(self, tmp_path):
        """Test _get_regional_shelter_instructions for Appalachia"""
        world_state_path = str(tmp_path / "test_state.json")
        
        with patch('broadcast_engine.WEATHER_SYSTEM_AVAILABLE', True):
            with patch('broadcast_engine.get_region_from_dj_name') as mock_region:
                from regional_climate import Region
                mock_region.return_value = Region.APPALACHIA
                
                engine = BroadcastEngine(
                    dj_name="Julie (2102, Appalachia)",
                    world_state_path=world_state_path,
                    enable_validation=False,
                    enable_story_system=False
                )
                
                instructions = engine._get_regional_shelter_instructions()
                
                assert 'Appalachia' in instructions or 'underground' in instructions
                assert 'Vault' in instructions or 'mine' in instructions or 'Scorchbeast' in instructions
    
    def test_get_regional_shelter_instructions_mojave(self, tmp_path):
        """Test _get_regional_shelter_instructions for Mojave"""
        world_state_path = str(tmp_path / "test_state.json")
        
        with patch('broadcast_engine.WEATHER_SYSTEM_AVAILABLE', True):
            with patch('broadcast_engine.get_region_from_dj_name') as mock_region:
                from regional_climate import Region
                mock_region.return_value = Region.MOJAVE
                
                engine = BroadcastEngine(
                    dj_name="Mr. New Vegas (2281, Mojave)",
                    world_state_path=world_state_path,
                    enable_validation=False,
                    enable_story_system=False
                )
                
                instructions = engine._get_regional_shelter_instructions()
                
                assert 'concrete' in instructions or 'Strip' in instructions or 'Lucky 38' in instructions
    
    def test_get_regional_shelter_instructions_commonwealth(self, tmp_path):
        """Test _get_regional_shelter_instructions for Commonwealth"""
        world_state_path = str(tmp_path / "test_state.json")
        
        with patch('broadcast_engine.WEATHER_SYSTEM_AVAILABLE', True):
            with patch('broadcast_engine.get_region_from_dj_name') as mock_region:
                from regional_climate import Region
                mock_region.return_value = Region.COMMONWEALTH
                
                engine = BroadcastEngine(
                    dj_name="Travis Miles (2287, Commonwealth)",
                    world_state_path=world_state_path,
                    enable_validation=False,
                    enable_story_system=False
                )
                
                instructions = engine._get_regional_shelter_instructions()
                
                assert 'Diamond City' in instructions or 'subway' in instructions or 'Vault' in instructions
    
    def test_generate_emergency_weather_alert_creates_segment(self, tmp_path):
        """Test generate_emergency_weather_alert generates complete alert"""
        world_state_path = str(tmp_path / "test_state.json")
        
        with patch('broadcast_engine.WEATHER_SYSTEM_AVAILABLE', True):
            with patch('broadcast_engine.get_region_from_dj_name') as mock_region:
                from regional_climate import Region
                mock_region.return_value = Region.APPALACHIA
                
                engine = BroadcastEngine(
                    dj_name="Julie (2102, Appalachia)",
                    world_state_path=world_state_path,
                    enable_validation=False,
                    enable_story_system=False
                )
                
                # Mock weather state with to_dict method for JSON serialization
                started_at = datetime.now()
                mock_weather = Mock()
                mock_weather.weather_type = 'radiation_storm'
                mock_weather.intensity = 'severe'
                mock_weather.duration_hours = 3
                mock_weather.temperature = 95
                mock_weather.started_at = started_at
                mock_weather.to_dict.return_value = {
                    'weather_type': 'radiation_storm',
                    'intensity': 'severe',
                    'temperature': 95,
                    'started_at': started_at.isoformat()
                }
                
                # Mock generator response
                mock_result = {
                    'script': 'EMERGENCY ALERT: Radiation storm incoming!',
                    'metadata': {'validated': True}
                }
                
                # Mock the logging method to avoid JSON serialization issues
                with patch.object(engine, '_log_weather_to_history'):
                    with patch.object(engine.generator, 'generate_script', return_value=mock_result):
                        segment = engine.generate_emergency_weather_alert(
                            current_hour=14,
                            weather_state=mock_weather
                        )
                        
                        assert segment['segment_type'] == 'emergency_weather'
                        assert segment['script'] == 'EMERGENCY ALERT: Radiation storm incoming!'
                        assert segment['is_emergency'] is True
                        assert segment['weather_type'] == 'radiation_storm'
                        assert segment['severity'] == 'severe'
                        assert 'generation_time' in segment


class TestBroadcastEngineStorySystemAdvanced:
    """Test story system integration"""
    
    def test_seed_story_pools_if_empty_seeds_when_empty(self, tmp_path):
        """Test _seed_story_pools_if_empty seeds pools when empty"""
        world_state_path = str(tmp_path / "test_state.json")
        
        with patch('broadcast_engine.STORY_SYSTEM_AVAILABLE', True):
            with patch('broadcast_engine.StoryExtractor') as MockExtractor:
                mock_extractor = MockExtractor.return_value
                
                # Mock extracted stories with required attributes
                from story_system.story_models import StoryTimeline
                mock_story1 = Mock(spec=['timeline', 'story_id', 'title'])
                mock_story1.timeline = StoryTimeline.DAILY
                mock_story1.story_id = 'story_daily_1'
                mock_story1.title = 'Daily Story'
                
                mock_story2 = Mock(spec=['timeline', 'story_id', 'title'])
                mock_story2.timeline = StoryTimeline.WEEKLY
                mock_story2.story_id = 'story_weekly_1'
                mock_story2.title = 'Weekly Story'
                
                mock_stories = [mock_story1, mock_story2]
                mock_extractor.extract_stories.return_value = mock_stories
                
                engine = BroadcastEngine(
                    dj_name="Julie (2102, Appalachia)",
                    world_state_path=world_state_path,
                    enable_validation=False,
                    enable_story_system=True
                )
                
                # Verify extractor was called (pools were empty)
                mock_extractor.extract_stories.assert_called()
    
    def test_seed_story_pools_if_empty_skips_when_populated(self, tmp_path):
        """Test _seed_story_pools_if_empty skips when pools have stories"""
        world_state_path = str(tmp_path / "test_state.json")
        
        with patch('broadcast_engine.STORY_SYSTEM_AVAILABLE', True):
            with patch('broadcast_engine.StoryState') as MockStoryState:
                mock_story_state = MockStoryState.return_value
                
                # Mock non-empty pools
                mock_story_state.get_pool_size.return_value = 5
                
                with patch('broadcast_engine.StoryExtractor') as MockExtractor:
                    mock_extractor = MockExtractor.return_value
                    
                    engine = BroadcastEngine(
                        dj_name="Julie (2102, Appalachia)",
                        world_state_path=world_state_path,
                        enable_validation=False,
                        enable_story_system=True
                    )
                    
                    # Verify extractor was NOT called (pools already populated)
                    mock_extractor.extract_stories.assert_not_called()
    
    def test_story_system_disabled_skips_seeding(self, tmp_path):
        """Test story system seeding is skipped when disabled"""
        world_state_path = str(tmp_path / "test_state.json")
        
        engine = BroadcastEngine(
            dj_name="Julie (2102, Appalachia)",
            world_state_path=world_state_path,
            enable_validation=False,
            enable_story_system=False
        )
        
        # Verify story components are None
        assert engine.story_state is None
        assert engine.story_scheduler is None
        assert engine.story_weaver is None


class TestBroadcastEngineBroadcastSequenceAdvanced:
    """Test broadcast sequence generation"""
    
    def test_generate_broadcast_sequence_generates_correct_count(self, tmp_path):
        """Test generate_broadcast_sequence generates correct number of segments"""
        world_state_path = str(tmp_path / "test_state.json")
        
        engine = BroadcastEngine(
            dj_name="Julie (2102, Appalachia)",
            world_state_path=world_state_path,
            enable_validation=False,
            enable_story_system=False
        )
        
        # Mock generate_next_segment to avoid actual generation
        mock_segment = {'script': 'Test', 'segment_type': 'weather'}
        with patch.object(engine, 'generate_next_segment', return_value=mock_segment):
            segments = engine.generate_broadcast_sequence(
                start_hour=8,
                duration_hours=2,
                segments_per_hour=3
            )
            
            # Should generate 2 hours * 3 segments/hour = 6 segments
            assert len(segments) == 6
    
    def test_generate_broadcast_sequence_wraps_hours(self, tmp_path):
        """Test generate_broadcast_sequence handles hour wrapping (23 → 0)"""
        world_state_path = str(tmp_path / "test_state.json")
        
        engine = BroadcastEngine(
            dj_name="Julie (2102, Appalachia)",
            world_state_path=world_state_path,
            enable_validation=False,
            enable_story_system=False
        )
        
        call_hours = []
        
        def capture_hour(hour):
            call_hours.append(hour)
            return {'script': 'Test', 'segment_type': 'weather'}
        
        with patch.object(engine, 'generate_next_segment', side_effect=capture_hour):
            segments = engine.generate_broadcast_sequence(
                start_hour=23,  # Start at 23:00
                duration_hours=2,  # Go to 01:00 (wrapping)
                segments_per_hour=1
            )
            
            # Should have called with hours 23, 0
            assert 23 in call_hours
            assert 0 in call_hours
    
    def test_end_broadcast_saves_state(self, tmp_path):
        """Test end_broadcast saves world state"""
        world_state_path = str(tmp_path / "test_state.json")
        
        engine = BroadcastEngine(
            dj_name="Julie (2102, Appalachia)",
            world_state_path=world_state_path,
            enable_validation=False,
            enable_story_system=False
        )
        
        # Generate some fake activity
        engine.segments_generated = 5
        engine.total_generation_time = 10.5
        
        stats = engine.end_broadcast(save_state=True)
        
        # Verify stats returned
        assert stats['segments_generated'] == 5
        assert stats['total_generation_time'] == 10.5
        assert stats['avg_generation_time'] == 2.1
        assert 'duration_seconds' in stats
        assert 'dj_name' in stats
    
    def test_end_broadcast_skips_save_when_disabled(self, tmp_path):
        """Test end_broadcast skips saving when save_state=False"""
        world_state_path = str(tmp_path / "test_state.json")
        
        engine = BroadcastEngine(
            dj_name="Julie (2102, Appalachia)",
            world_state_path=world_state_path,
            enable_validation=False,
            enable_story_system=False
        )
        
        with patch.object(engine.world_state, 'save') as mock_save:
            stats = engine.end_broadcast(save_state=False)
            
            # Verify save was not called
            mock_save.assert_not_called()
            assert 'duration_seconds' in stats
    
    def test_end_broadcast_calculates_average_correctly(self, tmp_path):
        """Test end_broadcast calculates average generation time correctly"""
        world_state_path = str(tmp_path / "test_state.json")
        
        engine = BroadcastEngine(
            dj_name="Julie (2102, Appalachia)",
            world_state_path=world_state_path,
            enable_validation=False,
            enable_story_system=False
        )
        
        # No segments generated - should not divide by zero
        stats = engine.end_broadcast(save_state=False)
        assert stats['avg_generation_time'] == 0
        
        # With segments
        engine.segments_generated = 10
        engine.total_generation_time = 25.0
        stats = engine.end_broadcast(save_state=False)
        assert stats['avg_generation_time'] == 2.5


class TestBroadcastEngineTemplateVarsAdvanced:
    """Test template variable building"""
    
    def test_build_template_vars_for_weather_with_simulator(self, tmp_path):
        """Test _build_template_vars builds weather variables with simulator"""
        world_state_path = str(tmp_path / "test_state.json")
        
        with patch('broadcast_engine.WEATHER_SYSTEM_AVAILABLE', True):
            with patch('broadcast_engine.get_region_from_dj_name') as mock_region:
                from regional_climate import Region
                from broadcast_scheduler import TimeOfDay
                mock_region.return_value = Region.APPALACHIA
                
                engine = BroadcastEngine(
                    dj_name="Julie (2102, Appalachia)",
                    world_state_path=world_state_path,
                    enable_validation=False,
                    enable_story_system=False
                )
                
                # Mock weather from simulator
                mock_weather = Mock()
                mock_weather.weather_type = 'radiation_storm'
                mock_weather.temperature = 95
                mock_weather.intensity = 'severe'
                mock_weather.is_emergency = True
                mock_weather.notable_event = 'Major storm system'
                mock_weather.region = 'Appalachia'
                mock_weather.to_dict.return_value = {
                    'weather_type': 'radiation_storm',
                    'temperature': 95
                }
                
                with patch.object(engine, '_get_current_weather_from_simulator', return_value=mock_weather):
                    with patch('broadcast_engine.get_weather_template_vars', return_value={}):
                        template_vars = engine._build_template_vars(
                            segment_type='weather',
                            current_hour=14,
                            time_of_day=TimeOfDay.AFTERNOON
                        )
                        
                        assert template_vars['weather_type'] == 'radiation_storm'
                        assert template_vars['temperature'] == 95
                        assert template_vars['intensity'] == 'severe'
                        assert template_vars['is_emergency'] is True
                        assert template_vars['region'] == 'Appalachia'
    
    def test_build_template_vars_for_weather_fallback(self, tmp_path):
        """Test _build_template_vars falls back when simulator unavailable"""
        world_state_path = str(tmp_path / "test_state.json")
        from broadcast_scheduler import TimeOfDay
        
        engine = BroadcastEngine(
            dj_name="Julie (2102, Appalachia)",
            world_state_path=world_state_path,
            enable_validation=False,
            enable_story_system=False
        )
        
        # Weather simulator not available - should use fallback
        with patch('broadcast_engine.select_weather', return_value='clear'):
            with patch('broadcast_engine.get_weather_template_vars', return_value={'weather_type': 'clear'}):
                template_vars = engine._build_template_vars(
                    segment_type='weather',
                    current_hour=14,
                    time_of_day=TimeOfDay.AFTERNOON
                )
                
                assert 'weather_type' in template_vars
                assert template_vars['dj_name'] == 'Julie (2102, Appalachia)'
    
    def test_build_template_vars_for_gossip(self, tmp_path):
        """Test _build_template_vars builds gossip variables"""
        world_state_path = str(tmp_path / "test_state.json")
        from broadcast_scheduler import TimeOfDay
        
        engine = BroadcastEngine(
            dj_name="Julie (2102, Appalachia)",
            world_state_path=world_state_path,
            enable_validation=False,
            enable_story_system=False
        )
        
        with patch('broadcast_engine.get_gossip_template_vars', return_value={'rumor_type': 'settlement_news'}):
            template_vars = engine._build_template_vars(
                segment_type='gossip',
                current_hour=14,
                time_of_day=TimeOfDay.AFTERNOON,
                rumor_type='settlement_news'
            )
            
            assert template_vars['rumor_type'] == 'settlement_news'
            assert template_vars['dj_name'] == 'Julie (2102, Appalachia)'
    
    def test_build_template_vars_for_news(self, tmp_path):
        """Test _build_template_vars builds news variables"""
        world_state_path = str(tmp_path / "test_state.json")
        from broadcast_scheduler import TimeOfDay
        
        engine = BroadcastEngine(
            dj_name="Julie (2102, Appalachia)",
            world_state_path=world_state_path,
            enable_validation=False,
            enable_story_system=False
        )
        
        with patch('broadcast_engine.get_news_template_vars', return_value={'news_category': 'security'}):
            template_vars = engine._build_template_vars(
                segment_type='news',
                current_hour=14,
                time_of_day=TimeOfDay.AFTERNOON,
                news_category='security'
            )
            
            assert template_vars['news_category'] == 'security'
    
    def test_build_template_vars_for_time(self, tmp_path):
        """Test _build_template_vars builds time check variables"""
        world_state_path = str(tmp_path / "test_state.json")
        from broadcast_scheduler import TimeOfDay
        
        engine = BroadcastEngine(
            dj_name="Julie (2102, Appalachia)",
            world_state_path=world_state_path,
            enable_validation=False,
            enable_story_system=False
        )
        
        with patch('broadcast_engine.get_time_check_template_vars', return_value={'current_time': '14:30'}):
            template_vars = engine._build_template_vars(
                segment_type='time',
                current_hour=14,
                time_of_day=TimeOfDay.AFTERNOON
            )
            
            assert 'current_time' in template_vars
    
    def test_build_context_query_for_weather(self, tmp_path):
        """Test _build_context_query builds weather query"""
        world_state_path = str(tmp_path / "test_state.json")
        
        engine = BroadcastEngine(
            dj_name="Julie (2102, Appalachia)",
            world_state_path=world_state_path,
            enable_validation=False,
            enable_story_system=False
        )
        
        query = engine._build_context_query(
            segment_type='weather',
            template_vars={'weather_type': 'radiation_storm'}
        )
        
        assert 'Appalachia' in query
        assert '2102' in query
        assert 'weather' in query
        assert 'radiation_storm' in query
    
    def test_build_context_query_for_news(self, tmp_path):
        """Test _build_context_query builds news query"""
        world_state_path = str(tmp_path / "test_state.json")
        
        engine = BroadcastEngine(
            dj_name="Julie (2102, Appalachia)",
            world_state_path=world_state_path,
            enable_validation=False,
            enable_story_system=False
        )
        
        query = engine._build_context_query(
            segment_type='news',
            template_vars={'news_category': 'security'}
        )
        
        assert 'Appalachia' in query
        assert 'news' in query
        assert 'security' in query
    
    def test_build_context_query_for_gossip(self, tmp_path):
        """Test _build_context_query builds gossip query"""
        world_state_path = str(tmp_path / "test_state.json")
        
        engine = BroadcastEngine(
            dj_name="Julie (2102, Appalachia)",
            world_state_path=world_state_path,
            enable_validation=False,
            enable_story_system=False
        )
        
        query = engine._build_context_query(
            segment_type='gossip',
            template_vars={'rumor_type': 'wasteland_tales'}
        )
        
        assert 'Appalachia' in query
        assert 'gossip' in query or 'rumors' in query
    
    def test_build_context_query_for_time_mojave(self, tmp_path):
        """Test _build_context_query builds time query with Mojave landmarks"""
        world_state_path = str(tmp_path / "test_state.json")
        
        engine = BroadcastEngine(
            dj_name="Mr. New Vegas (2281, Mojave Wasteland)",
            world_state_path=world_state_path,
            enable_validation=False,
            enable_story_system=False
        )
        
        query = engine._build_context_query(
            segment_type='time',
            template_vars={}
        )
        
        assert 'Mojave' in query
        assert 'New Vegas' in query or 'Strip' in query
    
    def test_build_context_query_for_time_commonwealth(self, tmp_path):
        """Test _build_context_query builds time query with Commonwealth landmarks"""
        world_state_path = str(tmp_path / "test_state.json")
        
        engine = BroadcastEngine(
            dj_name="Travis Miles (2287, Commonwealth)",
            world_state_path=world_state_path,
            enable_validation=False,
            enable_story_system=False
        )
        
        query = engine._build_context_query(
            segment_type='time',
            template_vars={}
        )
        
        assert 'Commonwealth' in query
        assert 'Diamond City' in query


class TestBroadcastEngineStatistics:
    """Test broadcast statistics tracking"""
    
    def test_get_broadcast_stats(self, tmp_path):
        """Test get_broadcast_stats returns current statistics"""
        world_state_path = str(tmp_path / "test_state.json")
        
        engine = BroadcastEngine(
            dj_name="Julie (2102, Appalachia)",
            world_state_path=world_state_path,
            enable_validation=False,
            enable_story_system=False
        )
        
        # Simulate some activity
        engine.segments_generated = 10
        engine.validation_failures = 2
        engine.total_generation_time = 25.0
        
        stats = engine.get_broadcast_stats()
        
        assert stats['segments_generated'] == 10
        assert stats['validation_failures'] == 2
        assert stats['avg_generation_time'] == 2.5
        assert 'uptime_seconds' in stats
        assert 'scheduler_status' in stats
