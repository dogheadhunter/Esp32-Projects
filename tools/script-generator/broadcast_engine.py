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

from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
import json

from session_memory import SessionMemory
from world_state import WorldState
from broadcast_scheduler import BroadcastScheduler, TimeOfDay
from consistency_validator import ConsistencyValidator
from generator import ScriptGenerator

from content_types.weather import select_weather, get_weather_template_vars
from content_types.gossip import GossipTracker, get_gossip_template_vars
from content_types.news import select_news_category, get_news_template_vars
from content_types.time_check import get_time_check_template_vars


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
                 max_session_memory: int = 10):
        """
        Initialize broadcast engine.
        
        Args:
            dj_name: DJ personality name
            templates_dir: Path to Jinja2 templates
            chroma_db_dir: Path to ChromaDB directory
            world_state_path: Path to persistent world state JSON
            enable_validation: Enable consistency validation
            max_session_memory: Maximum scripts to remember
        """
        self.dj_name = dj_name
        self.enable_validation = enable_validation
        
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
        self.validator: Optional[ConsistencyValidator] = None
        if enable_validation:
            from personality_loader import load_personality
            personality = load_personality(dj_name)
            self.validator = ConsistencyValidator(personality)
        
        # Initialize gossip tracker
        self.gossip_tracker = GossipTracker()
        
        # Broadcast metrics
        self.broadcast_start = datetime.now()
        self.segments_generated = 0
        self.validation_failures = 0
        self.total_generation_time = 0.0
        
        print(f"\n🎙️ BroadcastEngine initialized for {dj_name}")
        print(f"   Session memory: {max_session_memory} scripts")
        print(f"   Validation: {'enabled' if enable_validation else 'disabled'}")
    
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
            validation_result = self.validator.validate(result['script'])
            
            if validation_result and isinstance(validation_result, dict) and not validation_result.get('passed', True):
                self.validation_failures += 1
                print(f"⚠️  Validation issues: {len(validation_result.get('violations', []))}")
        
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
