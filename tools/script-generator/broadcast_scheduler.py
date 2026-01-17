"""
Broadcast Scheduler Module

Manages time-aware scheduling of different broadcast segment types.
Ensures appropriate content is generated based on time of day and scheduling intervals.
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
    
    Different segment types have different frequencies based on time of day:
    - Weather: Every 30 minutes
    - News: Every 45 minutes
    - Gossip: Every 60 minutes
    - Music Intros: Every song (5-7 minute intervals)
    - Time Checks: Every 15 minutes
    """
    
    def __init__(self):
        """Initialize broadcast scheduler."""
        self.last_segment_times = {
            "weather": None,
            "news": None,
            "gossip": None,
            "music_intro": None,
            "time_check": None,
        }
        
        # Segment intervals in minutes
        self.segment_intervals = {
            "weather": 30,
            "news": 45,
            "gossip": 60,
            "music_intro": 6,      # Every ~6 minutes (song length)
            "time_check": 15,
        }
        
        # Priority adjustments by time of day
        # Higher priority = more likely to be selected
        self.time_of_day_priorities = {
            TimeOfDay.MORNING: {
                "weather": 1.5,
                "news": 1.2,
                "time_check": 2.0,
                "gossip": 0.8,
                "music_intro": 1.0,
            },
            TimeOfDay.MIDDAY: {
                "weather": 1.0,
                "news": 1.3,
                "time_check": 1.0,
                "gossip": 1.2,
                "music_intro": 1.0,
            },
            TimeOfDay.AFTERNOON: {
                "weather": 0.8,
                "news": 1.0,
                "time_check": 0.9,
                "gossip": 1.5,
                "music_intro": 1.0,
            },
            TimeOfDay.EVENING: {
                "weather": 2.0,
                "news": 1.3,
                "time_check": 1.5,
                "gossip": 0.9,
                "music_intro": 1.0,
            },
            TimeOfDay.NIGHT: {
                "weather": 0.5,
                "news": 0.7,
                "time_check": 0.5,
                "gossip": 1.8,
                "music_intro": 1.2,
            },
        }
    
    def get_current_time_of_day(self) -> TimeOfDay:
        """
        Determine current time of day from system time.
        
        Returns:
            TimeOfDay enum representing current period
        """
        hour = datetime.now().hour
        
        if 6 <= hour < 10:
            return TimeOfDay.MORNING
        elif 10 <= hour < 14:
            return TimeOfDay.MIDDAY
        elif 14 <= hour < 18:
            return TimeOfDay.AFTERNOON
        elif 18 <= hour < 22:
            return TimeOfDay.EVENING
        else:  # 22-6
            return TimeOfDay.NIGHT
    
    def is_time_for_segment(self, segment_type: str) -> bool:
        """
        Check if it's time for a specific segment type.
        
        Args:
            segment_type: Type of segment to check (weather, news, etc.)
        
        Returns:
            True if interval has elapsed since last segment of this type
        """
        if segment_type not in self.last_segment_times:
            return True  # Never generated this type
        
        last_time = self.last_segment_times[segment_type]
        if last_time is None:
            return True
        
        interval_minutes = self.segment_intervals.get(segment_type, 30)
        elapsed = datetime.now() - last_time
        
        return elapsed >= timedelta(minutes=interval_minutes)
    
    def record_segment_generated(self, segment_type: str) -> None:
        """
        Record that a segment was just generated.
        
        Args:
            segment_type: Type of segment that was generated
        """
        if segment_type in self.last_segment_times:
            self.last_segment_times[segment_type] = datetime.now()
    
    def get_next_priority_segment(self) -> Optional[str]:
        """
        Determine which segment type should be generated next based on:
        1. Time since last generation (intervals)
        2. Time of day (priority adjustments)
        
        Returns:
            Segment type to generate next, or None if no priority segment
        """
        current_time = self.get_current_time_of_day()
        priorities = self.time_of_day_priorities[current_time]
        
        # Find segments that are ready (interval elapsed)
        ready_segments = [
            segment_type 
            for segment_type in self.segment_intervals.keys()
            if self.is_time_for_segment(segment_type)
        ]
        
        if not ready_segments:
            return None
        
        # Score each ready segment by time-of-day priority
        scored = [
            (segment, priorities.get(segment, 1.0))
            for segment in ready_segments
        ]
        
        # Return highest priority segment
        return max(scored, key=lambda x: x[1])[0]
    
    def get_segments_status(self) -> dict:
        """
        Get status of all segment types (for debugging/monitoring).
        
        Returns:
            Dictionary with segment status information
        """
        status = {}
        
        for segment_type, interval_min in self.segment_intervals.items():
            last_time = self.last_segment_times[segment_type]
            
            if last_time is None:
                time_since = "never"
                is_ready = True
            else:
                elapsed = datetime.now() - last_time
                minutes_elapsed = int(elapsed.total_seconds() / 60)
                time_since = f"{minutes_elapsed} minutes ago"
                is_ready = minutes_elapsed >= interval_min
            
            status[segment_type] = {
                "interval_minutes": interval_min,
                "last_generated": time_since,
                "is_ready": is_ready,
            }
        
        return status
    
    def reset(self) -> None:
        """Reset all segment timers (for testing or session restart)."""
        for segment_type in self.last_segment_times:
            self.last_segment_times[segment_type] = None
