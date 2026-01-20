"""
Enhanced Broadcast Scheduler Module (Phase 2 Refactoring)

Manages time-aware scheduling with priority-based segment planning.
Separates "WHEN/WHAT to broadcast" from "HOW to generate content".

Key improvements:
- Structured segment planning with SegmentPlan dataclass
- Priority-based scheduling (CRITICAL > REQUIRED > FILLER)
- Constraint generation for validation-guided generation
- Clear separation of scheduling logic from generation
- Weather calendar integration for climate caching
- Story arc pacing with timeline-based scheduling

SCHEDULE:
- CRITICAL: Emergency weather alerts (immediate)
- REQUIRED: Time checks (hourly), Weather (6am/12pm/5pm), News (6am/12pm/5pm)
- FILLER: Story segments (when available), Gossip (default)
"""

from enum import Enum
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Set
import random

from segment_plan import (
    SegmentPlan,
    SegmentType,
    Priority,
    ValidationConstraints
)


class TimeOfDay(Enum):
    """Enumeration of in-game time periods."""
    MORNING = "morning"      # 6 AM - 10 AM: Fresh start, hope
    MIDDAY = "midday"        # 10 AM - 2 PM: Active hours, activity
    AFTERNOON = "afternoon"  # 2 PM - 6 PM: Trade hours, gossip
    EVENING = "evening"      # 6 PM - 10 PM: Sunset danger, weather
    NIGHT = "night"          # 10 PM - 6 AM: Quiet, reflective


class BroadcastSchedulerV2:
    """
    Enhanced broadcast scheduler with priority-based planning.
    
    Returns structured SegmentPlan objects instead of just segment types.
    Generates validation constraints for each segment.
    Integrates with weather calendar and story system.
    """
    
    def __init__(self, story_scheduler=None, weather_calendar=None):
        """
        Initialize enhanced broadcast scheduler.
        
        Args:
            story_scheduler: Optional StoryScheduler for story arc integration
            weather_calendar: Optional WeatherCalendar for climate caching
        """
        # State tracking for required segments
        self.time_check_done_hours: Set[int] = set()
        self.news_done_hours: Set[int] = set()
        self.weather_done_hours: Set[int] = set()
        
        # Fixed schedule configuration
        self.NEWS_HOURS = {6, 12, 17}  # 6am, noon, 5pm
        self.WEATHER_HOURS = {6, 12, 17}  # Same as news
        
        # External integrations
        self.story_scheduler = story_scheduler
        self.weather_calendar = weather_calendar
        
        # Recent segment tracking for variety
        self.recent_news_categories: List[str] = []
        self.recent_gossip_topics: List[str] = []
        
        # Emergency alert tracking
        self.alerted_weather_events: Set[str] = set()
    
    def get_next_segment_plan(
        self,
        hour: int,
        context: Dict[str, Any]
    ) -> SegmentPlan:
        """
        Determine the next segment to broadcast with complete planning data.
        
        This is the main entry point for the scheduler. It returns a complete
        SegmentPlan with type, priority, constraints, and metadata.
        
        Args:
            hour: Current broadcast hour (0-23)
            context: Context dictionary with:
                - dj_name: str - Current DJ name
                - dj_year: int - DJ's temporal context (year)
                - dj_region: str - DJ's spatial context (region)
                - enable_stories: bool - Whether story segments are enabled
                - story_state: Optional story system state
                - weather_state: Optional current weather state
        
        Returns:
            SegmentPlan with complete planning data
        """
        
        # PRIORITY 1: Emergency weather alerts (CRITICAL)
        emergency_plan = self._check_emergency_weather(hour, context)
        if emergency_plan:
            return emergency_plan
        
        # PRIORITY 2: Time checks (REQUIRED - hourly)
        time_plan = self._check_time_segment(hour, context)
        if time_plan:
            return time_plan
        
        # PRIORITY 3: Weather reports (REQUIRED - 3x daily)
        weather_plan = self._check_weather_segment(hour, context)
        if weather_plan:
            return weather_plan
        
        # PRIORITY 4: News broadcasts (REQUIRED - 3x daily)
        news_plan = self._check_news_segment(hour, context)
        if news_plan:
            return news_plan
        
        # PRIORITY 5: Story segments (FILLER - when available)
        story_plan = self._check_story_segment(hour, context)
        if story_plan:
            return story_plan
        
        # PRIORITY 6: Gossip (FILLER - default)
        return self._create_gossip_segment(hour, context)
    
    def _check_emergency_weather(
        self,
        hour: int,
        context: Dict[str, Any]
    ) -> Optional[SegmentPlan]:
        """
        Check for emergency weather that requires immediate alert.
        
        Returns:
            SegmentPlan for emergency weather, or None if no emergency
        """
        weather_state = context.get('weather_state')
        if not weather_state:
            return None
        
        # Check if weather is critical and not already alerted
        weather_id = f"{weather_state.get('type')}_{weather_state.get('date')}"
        is_emergency = weather_state.get('is_emergency', False)
        
        if is_emergency and weather_id not in self.alerted_weather_events:
            self.alerted_weather_events.add(weather_id)
            
            return SegmentPlan(
                segment_type=SegmentType.EMERGENCY_WEATHER,
                priority=Priority.CRITICAL,
                constraints=self._get_weather_constraints(context, is_emergency=True),
                metadata={
                    'weather_type': weather_state.get('type'),
                    'severity': weather_state.get('severity', 'critical'),
                    'time_of_day': self._get_time_of_day(hour).value
                },
                context=context
            )
        
        return None
    
    def _check_time_segment(
        self,
        hour: int,
        context: Dict[str, Any]
    ) -> Optional[SegmentPlan]:
        """
        Check if time check segment is needed (hourly, first segment).
        
        Returns:
            SegmentPlan for time check, or None if already done
        """
        if hour not in self.time_check_done_hours:
            self.time_check_done_hours.add(hour)
            
            return SegmentPlan(
                segment_type=SegmentType.TIME_CHECK,
                priority=Priority.REQUIRED,
                constraints=self._get_time_check_constraints(context),
                metadata={
                    'hour': hour,
                    'time_of_day': self._get_time_of_day(hour).value
                },
                context=context
            )
        
        return None
    
    def _check_weather_segment(
        self,
        hour: int,
        context: Dict[str, Any]
    ) -> Optional[SegmentPlan]:
        """
        Check if weather report is needed (6am/12pm/5pm).
        
        Returns:
            SegmentPlan for weather, or None if not scheduled or already done
        """
        if hour in self.WEATHER_HOURS and hour not in self.weather_done_hours:
            self.weather_done_hours.add(hour)
            
            # Determine weather context based on time
            if hour == 6:
                weather_context = 'morning'  # Day forecast
            elif hour == 12:
                weather_context = 'afternoon'  # Afternoon update
            else:  # hour == 17
                weather_context = 'evening'  # Evening + tomorrow forecast
            
            return SegmentPlan(
                segment_type=SegmentType.WEATHER,
                priority=Priority.REQUIRED,
                constraints=self._get_weather_constraints(context),
                metadata={
                    'hour': hour,
                    'weather_context': weather_context,
                    'time_of_day': self._get_time_of_day(hour).value
                },
                context=context
            )
        
        return None
    
    def _check_news_segment(
        self,
        hour: int,
        context: Dict[str, Any]
    ) -> Optional[SegmentPlan]:
        """
        Check if news broadcast is needed (6am/12pm/5pm).
        
        Returns:
            SegmentPlan for news, or None if not scheduled or already done
        """
        if hour in self.NEWS_HOURS and hour not in self.news_done_hours:
            self.news_done_hours.add(hour)
            
            # Select news category based on time and variety
            category = self._select_news_category(hour)
            self.recent_news_categories.append(category)
            if len(self.recent_news_categories) > 5:
                self.recent_news_categories.pop(0)
            
            return SegmentPlan(
                segment_type=SegmentType.NEWS,
                priority=Priority.REQUIRED,
                constraints=self._get_news_constraints(context, category),
                metadata={
                    'hour': hour,
                    'category': category,
                    'time_of_day': self._get_time_of_day(hour).value
                },
                context=context
            )
        
        return None
    
    def _check_story_segment(
        self,
        hour: int,
        context: Dict[str, Any]
    ) -> Optional[SegmentPlan]:
        """
        Check if story segment should be broadcast.
        
        Stories are filler content with timeline-based pacing:
        - DAILY stories: 4 hours between acts
        - WEEKLY stories: 24 hours between acts
        - MONTHLY stories: 7 days between acts
        
        Returns:
            SegmentPlan for story, or None if no story available
        """
        if not context.get('enable_stories') or not self.story_scheduler:
            return None
        
        # Get story beats from story scheduler
        story_beats = self.story_scheduler.get_story_beats_for_broadcast()
        if not story_beats:
            return None
        
        # Get active story information
        story_state = context.get('story_state')
        if not story_state:
            return None
        
        active_story = story_state.get('active_story')
        if not active_story:
            return None
        
        return SegmentPlan(
            segment_type=SegmentType.STORY,
            priority=Priority.FILLER,
            constraints=self._get_story_constraints(context, active_story),
            metadata={
                'story_id': active_story.get('id'),
                'act_number': story_beats[0].get('act_number'),
                'act_type': story_beats[0].get('act_type'),
                'timeline': active_story.get('timeline'),
                'beats': story_beats
            },
            context=context
        )
    
    def _create_gossip_segment(
        self,
        hour: int,
        context: Dict[str, Any]
    ) -> SegmentPlan:
        """
        Create gossip segment (default filler content).
        
        Returns:
            SegmentPlan for gossip
        """
        return SegmentPlan(
            segment_type=SegmentType.GOSSIP,
            priority=Priority.FILLER,
            constraints=self._get_gossip_constraints(context),
            metadata={
                'hour': hour,
                'time_of_day': self._get_time_of_day(hour).value
            },
            context=context
        )
    
    # ========================================================================
    # CONSTRAINT GENERATION METHODS
    # ========================================================================
    
    def _get_time_check_constraints(self, context: Dict[str, Any]) -> ValidationConstraints:
        """Generate constraints for time check segments."""
        dj_year = context.get('dj_year', 2102)
        dj_region = context.get('dj_region', 'Appalachia')
        
        return ValidationConstraints(
            max_year=dj_year,
            allowed_regions=[dj_region],
            required_tone='casual',
            max_length=300,  # Short and sweet
            required_elements=['hour', 'time_of_day']
        )
    
    def _get_weather_constraints(
        self,
        context: Dict[str, Any],
        is_emergency: bool = False
    ) -> ValidationConstraints:
        """Generate constraints for weather segments."""
        dj_year = context.get('dj_year', 2102)
        dj_region = context.get('dj_region', 'Appalachia')
        dj_name = context.get('dj_name', 'Julie')
        
        # Get DJ-specific forbidden topics
        forbidden_topics = self._get_dj_forbidden_topics(dj_name, dj_year)
        forbidden_factions = self._get_dj_forbidden_factions(dj_name, dj_year)
        
        return ValidationConstraints(
            max_year=dj_year,
            allowed_regions=[dj_region],
            forbidden_topics=forbidden_topics,
            forbidden_factions=forbidden_factions,
            required_tone='urgent' if is_emergency else 'informative',
            max_length=500 if is_emergency else 400
        )
    
    def _get_news_constraints(
        self,
        context: Dict[str, Any],
        category: str
    ) -> ValidationConstraints:
        """Generate constraints for news segments."""
        dj_year = context.get('dj_year', 2102)
        dj_region = context.get('dj_region', 'Appalachia')
        dj_name = context.get('dj_name', 'Julie')
        
        forbidden_topics = self._get_dj_forbidden_topics(dj_name, dj_year)
        forbidden_factions = self._get_dj_forbidden_factions(dj_name, dj_year)
        
        return ValidationConstraints(
            max_year=dj_year,
            allowed_regions=[dj_region],
            forbidden_topics=forbidden_topics,
            forbidden_factions=forbidden_factions,
            required_tone='journalistic',
            max_length=600,
            required_elements=[category]
        )
    
    def _get_story_constraints(
        self,
        context: Dict[str, Any],
        story: Dict[str, Any]
    ) -> ValidationConstraints:
        """Generate constraints for story segments."""
        dj_year = context.get('dj_year', 2102)
        dj_region = context.get('dj_region', 'Appalachia')
        dj_name = context.get('dj_name', 'Julie')
        
        forbidden_topics = self._get_dj_forbidden_topics(dj_name, dj_year)
        forbidden_factions = self._get_dj_forbidden_factions(dj_name, dj_year)
        
        return ValidationConstraints(
            max_year=dj_year,
            allowed_regions=[dj_region],
            forbidden_topics=forbidden_topics,
            forbidden_factions=forbidden_factions,
            required_tone='narrative',
            max_length=800,  # Longer for storytelling
            dj_personality_traits=story.get('required_traits', [])
        )
    
    def _get_gossip_constraints(self, context: Dict[str, Any]) -> ValidationConstraints:
        """Generate constraints for gossip segments."""
        dj_year = context.get('dj_year', 2102)
        dj_region = context.get('dj_region', 'Appalachia')
        dj_name = context.get('dj_name', 'Julie')
        
        forbidden_topics = self._get_dj_forbidden_topics(dj_name, dj_year)
        forbidden_factions = self._get_dj_forbidden_factions(dj_name, dj_year)
        
        return ValidationConstraints(
            max_year=dj_year,
            allowed_regions=[dj_region],
            forbidden_topics=forbidden_topics,
            forbidden_factions=forbidden_factions,
            required_tone='conversational',
            max_length=500
        )
    
    # ========================================================================
    # HELPER METHODS
    # ========================================================================
    
    def _get_time_of_day(self, hour: int) -> TimeOfDay:
        """Determine time of day from hour."""
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
    
    def _select_news_category(self, hour: int) -> str:
        """
        Select news category based on time and variety.
        
        Args:
            hour: Current hour
        
        Returns:
            News category string
        """
        categories = ['combat', 'trade', 'settlements', 'factions', 'technology']
        
        # Avoid repeating recent categories
        available = [c for c in categories if c not in self.recent_news_categories[-2:]]
        if not available:
            available = categories
        
        # Time-based weights
        if hour == 6:  # Morning - settlements, trade
            weights = {'settlements': 0.4, 'trade': 0.3, 'factions': 0.2, 'combat': 0.05, 'technology': 0.05}
        elif hour == 12:  # Midday - balanced mix
            weights = {c: 0.2 for c in categories}
        else:  # Evening - combat, factions
            weights = {'combat': 0.4, 'factions': 0.3, 'settlements': 0.15, 'trade': 0.1, 'technology': 0.05}
        
        # Apply weights to available categories
        category_weights = [weights.get(c, 0.1) for c in available]
        return random.choices(available, weights=category_weights)[0]
    
    def _get_dj_forbidden_topics(self, dj_name: str, year: int) -> List[str]:
        """
        Get forbidden topics for a specific DJ based on their knowledge profile.
        
        This is a simplified version. In production, this would query
        the DJ knowledge system.
        """
        # Example: Julie in 2102 shouldn't know about Institute or Railroad
        if dj_name.lower() == 'julie' and year <= 2102:
            return ['Institute', 'Railroad', 'Synths', 'Commonwealth']
        
        return []
    
    def _get_dj_forbidden_factions(self, dj_name: str, year: int) -> List[str]:
        """
        Get forbidden factions for a specific DJ based on their knowledge profile.
        """
        if dj_name.lower() == 'julie' and year <= 2102:
            return ['Institute', 'Railroad', 'Minutemen']
        
        return []
    
    # ========================================================================
    # STATE MANAGEMENT
    # ========================================================================
    
    def get_segments_status(self) -> Dict[str, Any]:
        """Get status of scheduled segments."""
        return {
            "time_checks_done": sorted(list(self.time_check_done_hours)),
            "news_done": sorted(list(self.news_done_hours)),
            "weather_done": sorted(list(self.weather_done_hours)),
            "news_hours": sorted(list(self.NEWS_HOURS)),
            "weather_hours": sorted(list(self.WEATHER_HOURS)),
            "recent_news_categories": self.recent_news_categories[-5:],
            "alerted_weather_events": len(self.alerted_weather_events)
        }
    
    def reset(self) -> None:
        """Reset all segment tracking."""
        self.time_check_done_hours.clear()
        self.news_done_hours.clear()
        self.weather_done_hours.clear()
        self.recent_news_categories.clear()
        self.recent_gossip_topics.clear()
        self.alerted_weather_events.clear()
    
    def mark_segment_done(self, segment_type: str, hour: int) -> None:
        """
        Mark that a segment has been generated (legacy compatibility).
        
        Note: The new get_next_segment_plan() automatically marks segments
        as done, so this is mainly for backwards compatibility.
        """
        if segment_type == "time_check":
            self.time_check_done_hours.add(hour)
        elif segment_type == "news":
            self.news_done_hours.add(hour)
        elif segment_type == "weather":
            self.weather_done_hours.add(hour)


# Maintain backwards compatibility with old scheduler
class BroadcastScheduler(BroadcastSchedulerV2):
    """
    Backwards compatible scheduler that wraps BroadcastSchedulerV2.
    
    Provides legacy methods while using new enhanced implementation.
    """
    
    def __init__(self):
        """Initialize with default configuration for backwards compatibility."""
        super().__init__(story_scheduler=None, weather_calendar=None)
    
    def get_required_segment_for_hour(self, current_hour: int) -> Optional[str]:
        """
        Legacy method: Get required segment type for this hour.
        
        Returns segment type string or None.
        """
        # Create minimal context
        context = {
            'dj_name': 'Julie',
            'dj_year': 2102,
            'dj_region': 'Appalachia',
            'enable_stories': False
        }
        
        plan = self.get_next_segment_plan(current_hour, context)
        
        # Convert SegmentType enum to string
        if plan.segment_type == SegmentType.TIME_CHECK:
            return "time_check"
        elif plan.segment_type == SegmentType.NEWS:
            return "news"
        elif plan.segment_type == SegmentType.WEATHER:
            return "weather"
        elif plan.segment_type == SegmentType.EMERGENCY_WEATHER:
            return "weather"
        elif plan.segment_type == SegmentType.STORY:
            return "story"
        elif plan.segment_type == SegmentType.GOSSIP:
            return "gossip"
        
        return None
    
    def get_current_time_of_day(self) -> TimeOfDay:
        """Determine current time of day from system time."""
        hour = datetime.now().hour
        return self._get_time_of_day(hour)
    
    def is_story_ready(self) -> bool:
        """Legacy method - always True for flexible segments."""
        return True
    
    def is_time_for_segment(self, segment_type: str) -> bool:
        """Legacy method - always ready for flexible segments."""
        return True
    
    def record_segment_generated(self, segment_type: str) -> None:
        """Legacy method - kept for backward compatibility."""
        pass
    
    def get_next_priority_segment(self) -> Optional[str]:
        """Legacy method - returns None."""
        return None
