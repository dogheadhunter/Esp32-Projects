"""
Phase 6, Task 6: Enhanced Query Helpers

Provides helper functions for Phase 6 enhanced query features:
- Mood-based tone mapping (weather/time → emotional tones)
- Complexity sequencing (simple → moderate → complex rotation)
- Subject tracking for diversity
"""

from typing import List, Optional
from enum import Enum


class ComplexitySequencer:
    """
    Manages complexity tier sequencing for pacing variety.
    
    Implements simple → moderate → complex → simple rotation
    to provide natural pacing variation in broadcasts.
    """
    
    def __init__(self):
        """Initialize sequencer with simple tier"""
        self.sequence = ["simple", "moderate", "complex"]
        self.current_index = 0
        self.last_tier = None
    
    def get_next_tier(self) -> str:
        """
        Get next complexity tier in sequence.
        
        Returns:
            Next complexity tier (simple, moderate, or complex)
        """
        tier = self.sequence[self.current_index]
        self.last_tier = tier
        self.current_index = (self.current_index + 1) % len(self.sequence)
        return tier
    
    def get_current_tier(self) -> Optional[str]:
        """
        Get current complexity tier without advancing.
        
        Returns:
            Current tier or None if never called
        """
        return self.last_tier
    
    def reset(self):
        """Reset sequencer to start of cycle"""
        self.current_index = 0
        self.last_tier = None


class SubjectTracker:
    """
    Tracks recently used subjects for diversity filtering.
    
    Maintains a sliding window of recent subjects to avoid
    repetitive content on the same topics.
    """
    
    def __init__(self, max_history: int = 5):
        """
        Initialize tracker.
        
        Args:
            max_history: Maximum number of recent subjects to remember
        """
        self.max_history = max_history
        self.recent_subjects = []
    
    def add_subject(self, subject: str):
        """
        Add a subject to recent history.
        
        Args:
            subject: Subject name to track
        """
        self.recent_subjects.append(subject)
        
        # Keep only most recent
        if len(self.recent_subjects) > self.max_history:
            self.recent_subjects.pop(0)
    
    def get_exclusions(self) -> List[str]:
        """
        Get list of subjects to exclude.
        
        Returns:
            List of recently used subjects
        """
        return list(set(self.recent_subjects))  # Deduplicate
    
    def clear(self):
        """Clear all tracked subjects"""
        self.recent_subjects = []


def get_tones_for_weather(weather: str) -> List[str]:
    """
    Map weather condition to appropriate emotional tones.
    
    Phase 6 Task 6: Mood-based tone filtering.
    
    Args:
        weather: Weather condition (sunny, cloudy, rainy, rad_storm, etc.)
    
    Returns:
        List of appropriate emotional tones
    """
    weather_lower = weather.lower()
    
    # Rad storm → tense, tragic
    if "rad" in weather_lower or "storm" in weather_lower:
        return ["tense", "tragic", "neutral"]
    
    # Rain → mysterious, neutral
    if "rain" in weather_lower or "fog" in weather_lower:
        return ["mysterious", "neutral"]
    
    # Sunny/Clear → hopeful, neutral
    if "sunny" in weather_lower or "clear" in weather_lower:
        return ["hopeful", "neutral"]
    
    # Cloudy/Overcast → neutral, mysterious
    if "cloud" in weather_lower or "overcast" in weather_lower:
        return ["neutral", "mysterious"]
    
    # Default: neutral
    return ["neutral"]


def get_tones_for_time(hour: int) -> List[str]:
    """
    Map time of day to appropriate emotional tones.
    
    Phase 6 Task 6: Mood-based tone filtering.
    
    Args:
        hour: Hour of day (0-23)
    
    Returns:
        List of appropriate emotional tones
    """
    # Night (10 PM - 5 AM) → mysterious, tense
    if hour >= 22 or hour < 5:
        return ["mysterious", "tense", "neutral"]
    
    # Early morning (5 AM - 8 AM) → hopeful, neutral
    if 5 <= hour < 8:
        return ["hopeful", "neutral"]
    
    # Morning/Afternoon (8 AM - 6 PM) → hopeful, neutral
    if 8 <= hour < 18:
        return ["hopeful", "neutral", "comedic"]
    
    # Evening (6 PM - 10 PM) → neutral, mysterious
    if 18 <= hour < 22:
        return ["neutral", "mysterious"]
    
    # Default
    return ["neutral"]


def get_tones_for_context(weather: Optional[str] = None, 
                          hour: Optional[int] = None) -> List[str]:
    """
    Get emotional tones based on combined context.
    
    Combines weather and time-based tone preferences.
    Returns union of acceptable tones.
    
    Args:
        weather: Weather condition (None = ignore)
        hour: Hour of day (None = ignore)
    
    Returns:
        Combined list of appropriate tones
    """
    tones = set()
    
    if weather:
        tones.update(get_tones_for_weather(weather))
    
    if hour is not None:
        tones.update(get_tones_for_time(hour))
    
    # If no context provided, return neutral
    if not tones:
        return ["neutral"]
    
    return list(tones)


def calculate_subject_weights(recent_subjects: List[str]) -> dict:
    """
    Calculate subject frequency weights for diversity scoring.
    
    Helps identify over-used subjects that should be avoided.
    
    Args:
        recent_subjects: List of recently used subjects
    
    Returns:
        Dictionary of {subject: frequency_count}
    """
    weights = {}
    for subject in recent_subjects:
        weights[subject] = weights.get(subject, 0) + 1
    return weights


def get_complexity_sequence_pattern(length: int, start: str = "simple") -> List[str]:
    """
    Generate a complexity sequence pattern.
    
    Useful for pre-planning segment complexity for an entire broadcast.
    
    Args:
        length: Number of segments
        start: Starting complexity tier
    
    Returns:
        List of complexity tiers
    """
    sequence = ["simple", "moderate", "complex"]
    start_index = sequence.index(start) if start in sequence else 0
    
    pattern = []
    for i in range(length):
        pattern.append(sequence[(start_index + i) % len(sequence)])
    
    return pattern
