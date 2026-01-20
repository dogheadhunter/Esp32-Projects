"""
Broadcast Scheduler Module

Manages time-aware scheduling of different broadcast segment types.
Ensures appropriate content is generated based on time of day and fixed schedules.

UPDATED: Time-based scheduling for time checks, news, and weather.
- Time checks: Every hour on the hour
- News: 6am, 12pm (noon), 5pm
- Weather: 6am (day forecast), 12pm (afternoon update), 5pm (evening + tomorrow forecast)
- Gossip/Story: Fill remaining segments
"""

from enum import Enum
from datetime import datetime, timedelta
from typing import Optional, List


class TimeOfDay(Enum):
    """Enumeration of in-game time periods."""
    MORNING = "morning"      # 6 AM - 10 AM: Fresh start, hope
    MIDDAY = "midday"        # 10 AM - 2 PM: Active hours, activity
    AFTERNOON = "afternoon"  # 2 PM - 6 PM: Trade hours, gossip
    EVENING = "evening"      # 6 PM - 10 PM: Sunset danger, weather
    NIGHT = "night"          # 10 PM - 6 AM: Quiet, reflective


class BroadcastScheduler:
    """
    Manages time-aware scheduling for broadcast segments.
    
    Fixed schedule:
    - Time checks: Every hour on the hour (first segment)
    - News: 6am, 12pm, 5pm
    - Weather: 6am, 12pm, 5pm
    - Gossip/Story: Fill remaining slots
    """
    
    def __init__(self):
        """Initialize broadcast scheduler."""
        # Track which hours have had their required segments
        self.time_check_done_hours = set()
        self.news_done_hours = set()
        self.weather_done_hours = set()
        
        # Fixed schedule for specific segment types
        self.NEWS_HOURS = {6, 12, 17}
        self.WEATHER_HOURS = {6, 12, 17}
    
    def get_current_time_of_day(self) -> TimeOfDay:
        """Determine current time of day from system time."""
        hour = datetime.now().hour
        
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
    
    def get_required_segment_for_hour(self, current_hour: int) -> Optional[str]:
        """Get required segment type for this hour."""
        # Time check first
        if current_hour not in self.time_check_done_hours:
            return "time_check"
        
        # News at specific hours
        if current_hour in self.NEWS_HOURS and current_hour not in self.news_done_hours:
            return "news"
        
        # Weather at specific hours
        if current_hour in self.WEATHER_HOURS and current_hour not in self.weather_done_hours:
            return "weather"
        
        return None
    
    def mark_segment_done(self, segment_type: str, current_hour: int) -> None:
        """Mark that a required segment has been generated."""
        if segment_type == "time_check":
            self.time_check_done_hours.add(current_hour)
        elif segment_type == "news":
            self.news_done_hours.add(current_hour)
        elif segment_type == "weather":
            self.weather_done_hours.add(current_hour)
    
    def is_story_ready(self) -> bool:
        """Check if story should be considered."""
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
    
    def get_segments_status(self) -> dict:
        """Get status of scheduled segments."""
        return {
            "time_checks_done": sorted(list(self.time_check_done_hours)),
            "news_done": sorted(list(self.news_done_hours)),
            "weather_done": sorted(list(self.weather_done_hours)),
            "news_hours": sorted(list(self.NEWS_HOURS)),
            "weather_hours": sorted(list(self.WEATHER_HOURS))
        }
    
    def reset(self) -> None:
        """Reset all segment tracking."""
        self.time_check_done_hours.clear()
        self.news_done_hours.clear()
        self.weather_done_hours.clear()
