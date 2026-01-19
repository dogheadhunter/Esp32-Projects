"""
BroadcastEngine - Complete Broadcast Orchestrator

Coordinates all Phase 1-4 modules into a complete broadcast workflow:
- SessionMemory: Track recent scripts
- WorldState: Persistent storylines
- BroadcastScheduler: Time-aware scheduling
- ConsistencyValidator: Quality control
- Content Types: Weather, Gossip, News, TimeCheck

PHASE 5: Integration & Polish
"""

from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from pathlib import Path
import json

from session_memory import SessionMemory
from world_state import WorldState
from broadcast_scheduler import BroadcastScheduler, TimeOfDay
from consistency_validator import ConsistencyValidator
from generator import ScriptGenerator

# LLM validation system (Phase 8 integration)
try:
    from llm_validator import LLMValidator, HybridValidator, ValidationResult
    LLM_VALIDATION_AVAILABLE = True
except ImportError:
    LLM_VALIDATION_AVAILABLE = False

from content_types.weather import select_weather, get_weather_template_vars
from content_types.gossip import GossipTracker, get_gossip_template_vars
from content_types.news import select_news_category, get_news_template_vars
from content_types.time_check import get_time_check_template_vars

# Weather simulation system (Phase 2 integration)
try:
    from weather_simulator import WeatherSimulator
    from regional_climate import get_region_from_dj_name, Region
    WEATHER_SYSTEM_AVAILABLE = True
except ImportError:
    WEATHER_SYSTEM_AVAILABLE = False

# Story system (Phase 7 integration)
try:
    from story_system.story_scheduler import StoryScheduler
    from story_system.story_weaver import StoryWeaver
    from story_system.story_state import StoryState
    STORY_SYSTEM_AVAILABLE = True
except ImportError:
    STORY_SYSTEM_AVAILABLE = False


class BroadcastEngine:
    """
    Complete broadcast orchestration engine.
    
    Manages an entire broadcast session from initialization through multiple
    segments to final cleanup.
    
    Features:
    - Automatic session state management
    - Smart segment scheduling
    - Content type selection
    - Quality validation
    - Performance tracking
    """
    
    def __init__(self,
                 dj_name: str,
                 templates_dir: Optional[str] = None,
                 chroma_db_dir: Optional[str] = None,
                 world_state_path: Optional[str] = None,
                 enable_validation: bool = True,
                 validation_mode: str = 'rules',
                 llm_validation_config: Optional[Dict[str, Any]] = None,
                 max_session_memory: int = 10,
                 enable_story_system: bool = True):
        """
        Initialize broadcast engine.
        
        Args:
            dj_name: DJ personality name
            templates_dir: Path to Jinja2 templates
            chroma_db_dir: Path to ChromaDB directory
            world_state_path: Path to persistent world state JSON
            enable_validation: Enable consistency validation
            validation_mode: Validation strategy ('rules', 'llm', 'hybrid')
            llm_validation_config: Optional LLM validator configuration dict
            max_session_memory: Maximum scripts to remember
            enable_story_system: Enable multi-temporal story system (Phase 7)
        """
        self.dj_name = dj_name
        self.enable_validation = enable_validation
        self.validation_mode = validation_mode
        self.enable_story_system = enable_story_system
        
        # Initialize script generator
        self.generator = ScriptGenerator(
            templates_dir=templates_dir,
            chroma_db_dir=chroma_db_dir
        )
        
        # Initialize session components
        self.session_memory = SessionMemory(
            max_history=max_session_memory,
            dj_name=dj_name
        )
        
        self.world_state = WorldState(
            persistence_path=world_state_path or "./broadcast_state.json"
        )
        
        self.scheduler = BroadcastScheduler()
        
        # Initialize validator if enabled
        self.validator: Optional[Union[ConsistencyValidator, HybridValidator, LLMValidator]] = None
        if enable_validation:
            from personality_loader import load_personality
            personality = load_personality(dj_name)
            
            if validation_mode == 'rules':
                self.validator = ConsistencyValidator(personality)
            elif validation_mode == 'llm' and LLM_VALIDATION_AVAILABLE:
                try:
                    llm_config = llm_validation_config or {}
                    self.validator = LLMValidator(**llm_config)
                except ConnectionError:
                    print("⚠️  Ollama unavailable, falling back to rules-based validation")
                    self.validator = ConsistencyValidator(personality)
                    self.validation_mode = 'rules'
            elif validation_mode == 'hybrid' and LLM_VALIDATION_AVAILABLE:
                try:
                    llm_config = llm_validation_config or {}
                    # Extract HybridValidator-specific params
                    use_llm = llm_config.pop('use_llm', True)
                    use_rules = llm_config.pop('use_rules', True)
                    # Remaining params go to LLMValidator
                    llm_validator = LLMValidator(**llm_config) if llm_config else None
                    self.validator = HybridValidator(
                        llm_validator=llm_validator,
                        use_llm=use_llm,
                        use_rules=use_rules
                    )
                except ConnectionError:
                    print("⚠️  Ollama unavailable, falling back to rules-based validation")
                    self.validator = ConsistencyValidator(personality)
                    self.validation_mode = 'rules'
            else:
                # Fallback to rules if LLM not available
                if validation_mode in ['llm', 'hybrid'] and not LLM_VALIDATION_AVAILABLE:
                    print(f"⚠️  LLM validation not available, falling back to rules")
                    self.validation_mode = 'rules'
                self.validator = ConsistencyValidator(personality)
        
        # Initialize gossip tracker
        self.gossip_tracker = GossipTracker()
        
        # Weather simulation system (Phase 2 integration)
        self.weather_simulator: Optional[WeatherSimulator] = None
        self.region: Optional[Region] = None
        if WEATHER_SYSTEM_AVAILABLE:
            self.region = get_region_from_dj_name(dj_name)
            self.weather_simulator = WeatherSimulator()
            self._initialize_weather_calendar()
        
        # Story system (Phase 7 integration)
        self.story_scheduler: Optional[StoryScheduler] = None
        self.story_weaver: Optional[StoryWeaver] = None
        self.story_state: Optional[StoryState] = None
        if STORY_SYSTEM_AVAILABLE and enable_story_system:
            story_state_path = world_state_path.replace('.json', '_stories.json') if world_state_path else './broadcast_state_stories.json'
            self.story_state = StoryState(persistence_path=story_state_path)
            self.story_scheduler = StoryScheduler(story_state=self.story_state)
            self.story_weaver = StoryWeaver(story_state=self.story_state)
        
        # Broadcast metrics
        self.broadcast_start = datetime.now()
        self.segments_generated = 0
        self.validation_failures = 0
        self.total_generation_time = 0.0
        
        # Print initialization summary
        print(f"\n🎙️ BroadcastEngine initialized for {dj_name}")
        print(f"   Session memory: {max_session_memory} scripts")
        if enable_validation:
            print(f"   Validation: enabled (mode: {self.validation_mode})")
        else:
            print(f"   Validation: disabled")
        if WEATHER_SYSTEM_AVAILABLE and self.region:
            print(f"   Weather System: enabled ({self.region.value})")
        else:
            print(f"   Weather System: disabled (using random selection)")
        if STORY_SYSTEM_AVAILABLE and enable_story_system:
            print(f"   Story System: enabled")
        else:
            print(f"   Story System: disabled")
    
    def _initialize_weather_calendar(self) -> None:
        """
        Initialize or load weather calendar for DJ's region.
        
        Called during broadcast engine initialization if weather system is available.
        Checks if calendar exists in WorldState, generates if missing.
        """
        if not self.weather_simulator or not self.region:
            return
        
        region_name = self.region.value
        
        # Check if calendar exists in world state
        existing_calendar = self.world_state.get_calendar_for_region(region_name)
        
        if not existing_calendar:
            # Generate new calendar starting from current date
            print(f"[Weather System] Generating yearly calendar for {region_name}...")
            start_date = datetime.now().replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            
            calendar = self.weather_simulator.generate_yearly_calendar(
                start_date=start_date,
                region=self.region
            )
            
            # Convert WeatherState objects to dicts for JSON storage
            calendar_dict = {}
            for date_str, daily_schedule in calendar.items():
                calendar_dict[date_str] = {
                    slot: weather.to_dict() 
                    for slot, weather in daily_schedule.items()
                }
            
            # Store in world state
            self.world_state.weather_calendars[region_name] = calendar_dict
            self.world_state.calendar_metadata[region_name] = {
                "generated_date": datetime.now().isoformat(),
                "start_date": start_date.isoformat(),
                "region": region_name
            }
            self.world_state.save()
            print(f"[Weather System] Calendar generated and saved for {region_name}")
        else:
            print(f"[Weather System] Loaded existing calendar for {region_name}")
    
    def _get_current_weather_from_simulator(self, current_hour: int) -> Optional[Any]:
        """
        Get current weather from simulator for this hour.
        
        Args:
            current_hour: Current hour (0-23)
        
        Returns:
            WeatherState object or None if not available
        """
        if not self.weather_simulator or not self.region:
            return None
        
        # Check for manual override first
        region_name = self.region.value
        override = self.world_state.get_current_weather(region_name)
        if override:
            # Manual override exists, use it
            from weather_simulator import WeatherState
            return WeatherState.from_dict(override)
        
        # Get calendar for this region
        calendar_dict = self.world_state.get_calendar_for_region(region_name)
        if not calendar_dict:
            return None
        
        # Query weather for current datetime
        current_datetime = datetime.now().replace(hour=current_hour, minute=0, second=0, microsecond=0)
        
        # Convert calendar dict back to WeatherState objects for querying
        from weather_simulator import WeatherState
        calendar = {}
        for date_str, daily_schedule in calendar_dict.items():
            calendar[date_str] = {
                slot: WeatherState.from_dict(weather_dict)
                for slot, weather_dict in daily_schedule.items()
            }
        
        weather = self.weather_simulator.get_current_weather(
            current_datetime,
            self.region,
            calendar
        )
        
        return weather
    
    def _log_weather_to_history(self, weather_state: Any, current_hour: int) -> None:
        """
        Log weather to historical archive.
        
        Args:
            weather_state: WeatherState object
            current_hour: Current hour for timestamping
        """
        if not self.region:
            return
        
        timestamp = datetime.now().replace(hour=current_hour, minute=0, second=0, microsecond=0)
        self.world_state.log_weather_history(
            self.region.value,
            timestamp,
            weather_state.to_dict()
        )
    
    # Phase 4: Emergency Weather System
    
    def check_for_emergency_weather(self, current_hour: int) -> Optional[Any]:
        """
        Check if current weather requires emergency alert.
        
        Args:
            current_hour: Current hour to check
        
        Returns:
            WeatherState object if emergency alert needed, None otherwise
        """
        if not self.weather_simulator or not self.region:
            return None
        
        current_weather = self._get_current_weather_from_simulator(current_hour)
        
        if current_weather and current_weather.is_emergency:
            # Check if we already alerted for this specific event
            if not self._already_alerted_for_event(current_weather):
                return current_weather
        
        return None
    
    def _already_alerted_for_event(self, weather_state: Any) -> bool:
        """
        Check if we've already broadcast an alert for this specific weather event.
        
        Args:
            weather_state: WeatherState to check
        
        Returns:
            True if already alerted, False otherwise
        """
        # Check recent session memory for emergency weather alerts
        for entry in reversed(self.session_memory.recent_scripts):
            if entry.script_type == 'emergency_weather':
                # Check if it's the same event (within same hour and same type)
                event_meta = entry.metadata
                if (event_meta.get('weather_type') == weather_state.weather_type and
                    event_meta.get('started_at') == weather_state.started_at.isoformat()):
                    return True
        
        return False
    
    def _get_regional_shelter_instructions(self) -> str:
        """
        Get region-specific shelter instructions for emergencies.
        
        Returns:
            Shelter instruction string
        """
        if not self.region:
            return "Seek immediate shelter in the nearest secure structure."
        
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
        
        return regional_instructions.get(
            self.region.value,
            "Seek immediate shelter in the nearest secure structure."
        )
    
    def generate_emergency_weather_alert(self, 
                                        current_hour: int,
                                        weather_state: Any) -> Dict[str, Any]:
        """
        Generate emergency weather alert segment.
        
        Args:
            current_hour: Current hour
            weather_state: Emergency WeatherState
        
        Returns:
            Alert segment dict
        """
        from datetime import datetime
        from broadcast_scheduler import TimeOfDay
        
        start_time = datetime.now()
        
        # Determine time of day from hour
        if 6 <= current_hour < 10:
            time_of_day = TimeOfDay.MORNING
        elif 10 <= current_hour < 14:
            time_of_day = TimeOfDay.MIDDAY
        elif 14 <= current_hour < 18:
            time_of_day = TimeOfDay.AFTERNOON
        elif 18 <= current_hour < 22:
            time_of_day = TimeOfDay.EVENING
        else:
            time_of_day = TimeOfDay.NIGHT
        
        # Build template variables
        base_vars = {
            'dj_name': self.dj_name,
            'emergency_type': weather_state.weather_type,
            'location': self.region.value if self.region else 'the area',
            'severity': weather_state.intensity,
            'duration_hours': weather_state.duration_hours,
            'temperature': weather_state.temperature,
            'shelter_instructions': self._get_regional_shelter_instructions(),
            'year': 2102 if self.region and self.region.value == "Appalachia" else 2287,
            'hour': current_hour,
            'time_of_day': time_of_day.name.lower()
        }
        
        # Get RAG context for emergency (shelter locations, safety protocols)
        rag_context = self._get_emergency_rag_context(weather_state)
        base_vars['rag_context'] = rag_context
        
        # Generate emergency alert
        result = self.generator.generate_script(
            template_name='emergency_weather',
            template_vars=base_vars,
            temperature=0.6,  # More focused for emergencies
            max_words=75  # Keep it brief and urgent
        )
        
        # Track in session memory
        self.session_memory.add_script(
            script_type='emergency_weather',
            content=result.get('script', ''),
            metadata={
                'weather_type': weather_state.weather_type,
                'severity': weather_state.intensity,
                'started_at': weather_state.started_at.isoformat(),
                'is_emergency': True
            }
        )
        
        # Log to history
        self._log_weather_to_history(weather_state, current_hour)
        
        # Update metrics
        generation_time = (datetime.now() - start_time).total_seconds()
        self.total_generation_time += generation_time
        self.segments_generated += 1
        
        return {
            'segment_type': 'emergency_weather',
            'script': result.get('script', ''),
            'weather_type': weather_state.weather_type,
            'severity': weather_state.intensity,
            'is_emergency': True,
            'generation_time': generation_time,
            'metadata': result.get('metadata', {})
        }
    
    def _get_emergency_rag_context(self, weather_state: Any) -> str:
        """
        Get RAG context for emergency weather alerts.
        
        Args:
            weather_state: Emergency WeatherState
        
        Returns:
            RAG context string with shelter locations and safety info
        """
        if not self.region:
            return "Seek shelter immediately in any secure structure."
        
        # Regional emergency context
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
        
        return regional_context.get(
            self.region.value,
            "Seek shelter immediately in any secure structure."
        )
    
    def start_broadcast(self) -> Dict[str, Any]:
        """
        Start a new broadcast session.
        
        Returns:
            Session info dict
        """
        self.broadcast_start = datetime.now()
        self.segments_generated = 0
        self.validation_failures = 0
        self.total_generation_time = 0.0
        
        # Reset scheduler
        self.scheduler.reset()
        
        print(f"\n▶️  Broadcast started at {self.broadcast_start.strftime('%H:%M:%S')}")
        
        return {
            'dj_name': self.dj_name,
            'start_time': self.broadcast_start.isoformat(),
            'session_id': f"{self.dj_name}_{self.broadcast_start.timestamp()}"
        }
    
    def generate_next_segment(self,
                             current_hour: int,
                             force_type: Optional[str] = None,
                             **kwargs) -> Dict[str, Any]:
        """
        Generate the next appropriate broadcast segment.
        
        Args:
            current_hour: Current hour (0-23)
            force_type: Force specific segment type (optional)
            **kwargs: Additional template variables
        
        Returns:
            Generated segment result with metadata
        """
        start_time = datetime.now()
        
        # Phase 4: Check for emergency weather first (highest priority)
        if not force_type and self.weather_simulator and self.region:
            emergency_weather = self.check_for_emergency_weather(current_hour)
            if emergency_weather:
                print(f"⚠️  EMERGENCY WEATHER DETECTED: {emergency_weather.weather_type}")
                return self.generate_emergency_weather_alert(current_hour, emergency_weather)
        
        # Phase 7: Get story beats for this broadcast
        story_beats = []
        story_context = ""
        if self.story_scheduler and self.story_weaver:
            story_beats = self.story_scheduler.get_story_beats_for_broadcast()
            if story_beats:
                woven_result = self.story_weaver.weave_beats(story_beats)
                story_context = woven_result.get('context_for_llm', '')
                print(f"📖 Story beats: {self.story_weaver.get_story_summary(story_beats)}")
        
        # Determine segment type
        if force_type:
            segment_type = force_type
        else:
            segment_type = self.scheduler.get_next_priority_segment()
            if segment_type is None:
                segment_type = 'gossip'

        # Map scheduler alias to generator template name
        generator_script_type = 'time' if segment_type == 'time_check' else segment_type
        
        print(f"\n🎬 Generating {segment_type} segment (Hour: {current_hour})")
        
        # Get time of day from hour
        def hour_to_time_of_day(hour: int):
            from broadcast_scheduler import TimeOfDay
            if 6 <= hour < 10:
                return TimeOfDay.MORNING
            elif 10 <= hour < 14:
                return TimeOfDay.MIDDAY
            elif 14 <= hour < 18:
                return TimeOfDay.AFTERNOON
            elif 18 <= hour < 22:
                return TimeOfDay.EVENING
            else:
                return TimeOfDay.NIGHT
        
        time_of_day = hour_to_time_of_day(current_hour)
        
        # Build template variables based on type
        template_vars = self._build_template_vars(
            generator_script_type,
            current_hour,
            time_of_day,
            **kwargs
        )
        
        # Build context query
        context_query = self._build_context_query(generator_script_type, template_vars)
        
        # Add session context to template vars
        session_context = self.session_memory.get_context_for_prompt()
        if session_context:
            template_vars['session_context'] = session_context
        
        # Add story context to template vars
        if story_context:
            template_vars['story_context'] = story_context
        
        # Generate script (avoid duplicate dj_name in template vars)
        safe_template_vars = {k: v for k, v in template_vars.items() if k != 'dj_name'}
        result = self.generator.generate_script(
            script_type=generator_script_type,
            dj_name=self.dj_name,
            context_query=context_query,
            **safe_template_vars
        )
        
        # Validate if enabled
        validation_result = None
        if self.enable_validation and self.validator and result.get('script'):
            # Build context for validation
            validation_context = self._build_validation_context(
                template_vars=template_vars,
                segment_type=segment_type,
                current_hour=current_hour
            )
            
            # Run validation (supports both old and new validators)
            if isinstance(self.validator, (HybridValidator, LLMValidator)) if LLM_VALIDATION_AVAILABLE else False:
                # New LLM validators return ValidationResult
                from personality_loader import load_personality
                personality = load_personality(self.dj_name)
                val_result = self.validator.validate(
                    script=result['script'],
                    character_card=personality,
                    context=validation_context
                )
                # Store summary only (not full ValidationResult)
                validation_result = {
                    'is_valid': val_result.is_valid,
                    'score': val_result.overall_score,
                    'critical_count': len(val_result.get_critical_issues()),
                    'warnings_count': len(val_result.get_warnings()),
                    'suggestions_count': len(val_result.get_suggestions()),
                    'mode': self.validation_mode
                }
                is_valid = val_result.is_valid
            else:
                # Old ConsistencyValidator returns bool
                is_valid = self.validator.validate(result['script'])
                validation_result = {
                    'is_valid': is_valid,
                    'violations': self.validator.get_violations() if hasattr(self.validator, 'get_violations') else [],
                    'warnings': self.validator.get_warnings() if hasattr(self.validator, 'get_warnings') else [],
                    'mode': 'rules'
                }
            
            if not is_valid:
                self.validation_failures += 1
                issue_count = validation_result.get('critical_count', len(validation_result.get('violations', [])))
                print(f"⚠️  Validation issues: {issue_count}")
        
        # Update session memory (normalize segment type aliases)
        segment_type_recorded = 'time' if segment_type == 'time_check' else segment_type
        self.session_memory.add_script(
            script_type=segment_type_recorded,
            content=result.get('script', ''),
            metadata={
                'hour': current_hour,
                'time_of_day': time_of_day.name,
                **template_vars
            }
        )
        
        # Update scheduler
        self.scheduler.record_segment_generated(segment_type)
        
        # Update world state if applicable
        if segment_type == 'gossip' and result.get('script'):
            # Extract gossip topic and add to tracker
            topic = template_vars.get('rumor_type', 'general gossip')
            self.gossip_tracker.add_gossip(topic, result['script'][:100])
        
        # Track metrics
        generation_time = (datetime.now() - start_time).total_seconds()
        self.segments_generated += 1
        self.total_generation_time += generation_time
        
        # Compile result
        segment_result = {
            'segment_type': segment_type,
            'script': result.get('script', ''),
            'metadata': {
                'hour': current_hour,
                'time_of_day': time_of_day.name,
                'generation_time': generation_time,
                'segment_number': self.segments_generated,
                'template_vars': template_vars,
                'validation': validation_result
            }
        }
        
        print(f"✅ Generated in {generation_time:.2f}s")
        
        return segment_result
    
    def _build_validation_context(self,
                                  template_vars: Dict[str, Any],
                                  segment_type: str,
                                  current_hour: int) -> Dict[str, Any]:
        """
        Build rich context for LLM validation.
        
        Packages all available metadata for context-aware validation.
        
        Args:
            template_vars: Template variables used for generation
            segment_type: Type of segment (weather, gossip, news, etc.)
            current_hour: Current broadcast hour
        
        Returns:
            Context dict for LLM validator
        """
        context = {
            'segment_type': segment_type,
            'hour': current_hour,
            'time_of_day': template_vars.get('time_of_day'),
        }
        
        # Add weather context if applicable
        if segment_type == 'weather':
            context['weather'] = {
                'type': template_vars.get('weather_type'),
                'intensity': template_vars.get('intensity'),
                'temperature': template_vars.get('temperature'),
                'is_emergency': template_vars.get('is_emergency', False),
                'description': template_vars.get('weather_description')
            }
        
        # Add session context
        context['recent_broadcasts'] = self.session_memory.get_context_for_prompt(include_recent=2)
        context['recent_topics'] = self.session_memory.get_mentioned_topics()
        
        # Add region if available
        if self.region:
            context['region'] = self.region.value
        
        # Add story context if available
        if template_vars.get('story_context'):
            context['story_context'] = template_vars.get('story_context')
        
        # Add any other relevant context from template vars
        for key in ['rumor_type', 'news_category', 'location']:
            if key in template_vars:
                context[key] = template_vars[key]
        
        return context
    
    def generate_broadcast_sequence(self,
                                   start_hour: int,
                                   duration_hours: int,
                                   segments_per_hour: int = 2) -> List[Dict[str, Any]]:
        """
        Generate a complete broadcast sequence.
        
        Args:
            start_hour: Starting hour (0-23)
            duration_hours: Broadcast duration in hours
            segments_per_hour: Segments to generate per hour
        
        Returns:
            List of generated segments
        """
        print(f"\n📻 Generating {duration_hours}-hour broadcast sequence")
        print(f"   Start: {start_hour}:00")
        print(f"   Segments per hour: {segments_per_hour}")
        
        segments = []
        
        for hour_offset in range(duration_hours):
            current_hour = (start_hour + hour_offset) % 24
            
            print(f"\n⏰ Hour {current_hour}:00")
            
            for segment_num in range(segments_per_hour):
                segment = self.generate_next_segment(current_hour)
                segments.append(segment)
        
        print(f"\n✅ Broadcast sequence complete: {len(segments)} segments")
        
        return segments
    
    def end_broadcast(self, save_state: bool = True) -> Dict[str, Any]:
        """
        End broadcast session and gather statistics.
        
        Args:
            save_state: Save world state to disk
        
        Returns:
            Broadcast session statistics
        """
        duration = datetime.now() - self.broadcast_start
        
        # Save world state
        if save_state:
            self.world_state.update_broadcast_stats(
                runtime_hours=duration.total_seconds() / 3600
            )
            self.world_state.save()
        
        stats = {
            'dj_name': self.dj_name,
            'duration_seconds': duration.total_seconds(),
            'segments_generated': self.segments_generated,
            'validation_failures': self.validation_failures,
            'total_generation_time': self.total_generation_time,
            'avg_generation_time': (
                self.total_generation_time / self.segments_generated
                if self.segments_generated > 0 else 0
            ),
            'session_memory_size': len(self.session_memory.recent_scripts),
            'mentioned_topics': list(self.session_memory.mentioned_topics)
        }
        
        print(f"\n⏹️  Broadcast ended")
        print(f"   Duration: {duration.total_seconds():.1f}s")
        print(f"   Segments: {self.segments_generated}")
        print(f"   Avg time: {stats['avg_generation_time']:.2f}s/segment")
        
        if self.validation_failures > 0:
            print(f"   ⚠️  Validation issues: {self.validation_failures}")
        
        return stats
    
    def _build_template_vars(self,
                           segment_type: str,
                           current_hour: int,
                           time_of_day: TimeOfDay,
                           **kwargs) -> Dict[str, Any]:
        """Build template variables for segment type"""
        base_vars = {
                        'dj_name': self.dj_name,
            'hour': current_hour,
            'time_of_day': time_of_day.name.lower()
        }
        
        if segment_type == 'weather':
            # Phase 2: Use weather simulator if available
            if self.weather_simulator and self.region:
                current_weather = self._get_current_weather_from_simulator(current_hour)
                if current_weather:
                    # Use simulated weather
                    weather_vars = {
                        'weather_type': current_weather.weather_type,
                        'weather_description': current_weather.weather_type,
                        'temperature': current_weather.temperature,
                        'intensity': current_weather.intensity,
                        'is_emergency': current_weather.is_emergency,
                        'notable_event': current_weather.notable_event,
                        'region': current_weather.region,
                        'location': current_weather.region,
                        'time_of_day': time_of_day.name.lower()
                    }
                    
                    # Phase 3: Add weather continuity context
                    weather_continuity = self.session_memory.get_weather_continuity_context(
                        region=self.region.value,
                        current_weather_dict=current_weather.to_dict()
                    )
                    weather_vars['weather_continuity'] = weather_continuity
                    
                    # Phase 3: Add notable recent weather events
                    notable_events = self.world_state.get_notable_weather_events(
                        region=self.region.value,
                        days_back=30
                    )
                    if notable_events:
                        # Convert to simple dicts for template
                        notable_list = []
                        for event in notable_events[:3]:  # Max 3 events
                            notable_list.append({
                                'weather_type': event.get('weather_type'),
                                'date': event.get('started_at', 'recent'),
                                'intensity': event.get('intensity', 'moderate')
                            })
                        weather_vars['notable_weather_events'] = notable_list
                    
                    # Get additional weather template vars (survival tips, etc.)
                    additional_vars = get_weather_template_vars(
                        current_weather.weather_type,
                        time_of_day.name.lower(),
                        current_hour
                    )
                    weather_vars.update(additional_vars)
                    base_vars.update(weather_vars)
                    
                    # Log weather to history
                    self._log_weather_to_history(current_weather, current_hour)
                else:
                    # Fallback to old random selection
                    weather_type = kwargs.get('weather_type') or select_weather()
                    weather_vars = get_weather_template_vars(
                        weather_type,
                        time_of_day.name.lower(),
                        current_hour
                    )
                    base_vars.update(weather_vars)
            else:
                # Weather system not available, use old method
                weather_type = kwargs.get('weather_type')
                if not weather_type:
                    weather_type = select_weather()
                
                weather_vars = get_weather_template_vars(
                    weather_type,
                    time_of_day.name.lower(),
                    current_hour
                )
                base_vars.update(weather_vars)
        
        elif segment_type == 'gossip':
            gossip_vars = get_gossip_template_vars(
                self.gossip_tracker,
                kwargs.get('rumor_type', 'wasteland rumors')
            )
            base_vars.update(gossip_vars)
        
        elif segment_type == 'news':
            category = kwargs.get('news_category')
            if not category:
                category = select_news_category()
            
            news_vars = get_news_template_vars(
                category,
                region='Appalachia',
                dj_name=self.dj_name
            )
            base_vars.update(news_vars)
        
        elif segment_type == 'time':
            time_vars = get_time_check_template_vars(
                self.dj_name,
                current_hour,  # hour parameter
                None  # minute parameter (will use current minute)
            )
            base_vars.update(time_vars)
        
        # Add any custom kwargs
        base_vars.update(kwargs)
        
        return base_vars
    
    def _build_context_query(self,
                            segment_type: str,
                            template_vars: Dict[str, Any]) -> str:
        """Build RAG context query for segment type"""
        # Extract location and year from DJ name
        # Format: "DJ Name (YEAR, Location)"
        import re
        match = re.search(r'\((\d+),\s*([^)]+)\)', self.dj_name)
        if match:
            year = match.group(1)
            location = match.group(2).strip()
        else:
            # Fallback to Appalachia if parsing fails
            year = "2102"
            location = "Appalachia West Virginia"
        
        base_query = f"{location} {year}"
        
        if segment_type == 'weather':
            weather_type = template_vars.get('weather_type', 'general')
            return f"{base_query} weather {weather_type} conditions survival"
        
        elif segment_type == 'news':
            category = template_vars.get('news_category', 'general')
            return f"{base_query} news {category} events recent"
        
        elif segment_type == 'gossip':
            rumor_type = template_vars.get('rumor_type', 'rumors')
            return f"{base_query} gossip {rumor_type} rumors stories"
        
        elif segment_type == 'time':
            # Use location-specific landmarks
            if 'Mojave' in location:
                return f"{base_query} New Vegas Strip casinos daily life"
            elif 'Commonwealth' in location:
                return f"{base_query} Diamond City settlement schedule"
            else:
                return f"{base_query} Vault 76 schedule daily life"
        
        return base_query
    
    def get_broadcast_stats(self) -> Dict[str, Any]:
        """Get current broadcast statistics"""
        return {
            'segments_generated': self.segments_generated,
            'validation_failures': self.validation_failures,
            'avg_generation_time': (
                self.total_generation_time / self.segments_generated
                if self.segments_generated > 0 else 0
            ),
            'uptime_seconds': (datetime.now() - self.broadcast_start).total_seconds(),
            'scheduler_status': self.scheduler.get_segments_status()
        }


# Example usage
if __name__ == "__main__":
    print("BroadcastEngine Example\\n")
    
    try:
        # Initialize engine
        engine = BroadcastEngine(
            dj_name="Julie (2102, Appalachia)",
            enable_validation=True
        )
        
        # Start broadcast
        engine.start_broadcast()
        
        # Generate a few segments
        segments = engine.generate_broadcast_sequence(
            start_hour=8,
            duration_hours=2,
            segments_per_hour=2
        )
        
        # End broadcast
        stats = engine.end_broadcast()
        
        print("\n" + "="*80)
        print("BROADCAST STATISTICS")
        print("="*80)
        print(json.dumps(stats, indent=2))
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
