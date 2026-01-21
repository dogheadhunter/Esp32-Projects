"""
Variety Manager Module

Implements cooldown-based variety tracking to prevent repetition of phrases,
topics, weather, and structure patterns across broadcast segments.

Phase 2B: Prevents boring, repetitive content during 30-day autonomous operation.
"""

from typing import Dict, List, Any, Optional, Set
from datetime import datetime
from collections import deque
import logging

logger = logging.getLogger(__name__)


# Cooldown rules (in number of segments)
PHRASE_COOLDOWN = 10      # Same phrase can't repeat within 10 segments
TOPIC_COOLDOWN = 5        # Same topic can't repeat within 5 segments
WEATHER_CONSECUTIVE_LIMIT = 3  # Max 3 consecutive same weather type
STRUCTURE_NO_REPEAT = 2   # Structure pattern can't repeat immediately


class VarietyManager:
    """
    Tracks content usage and enforces variety constraints via cooldowns.
    
    Prevents repetition across multiple dimensions:
    - Phrases: Opening lines, catchphrases, signature expressions
    - Topics: News categories, gossip subjects, story themes
    - Weather: Weather types (clear, rainy, radstorm, etc.)
    - Structure: Segment flow patterns (news→weather→gossip, etc.)
    
    Uses sliding windows and cooldown periods to ensure variety while
    allowing natural recurrence over longer timeframes.
    """
    
    def __init__(self):
        """Initialize variety tracking structures."""
        # Phrase tracking: {phrase: last_used_segment_index}
        self.phrase_usage: Dict[str, int] = {}
        
        # Topic tracking: {topic: last_used_segment_index}
        self.topic_usage: Dict[str, int] = {}
        
        # Weather consecutive tracking: deque of recent weather types
        self.weather_history: deque = deque(maxlen=WEATHER_CONSECUTIVE_LIMIT)
        
        # Structure pattern tracking: deque of recent segment types
        self.structure_history: deque = deque(maxlen=STRUCTURE_NO_REPEAT)
        
        # Current segment index (increments with each segment)
        self.current_segment_index = 0
        
        # Statistics for monitoring
        self.phrase_blocks = 0
        self.topic_blocks = 0
        self.weather_blocks = 0
        self.structure_blocks = 0
    
    def check_phrase_variety(self, phrase: str) -> bool:
        """
        Check if phrase can be used (not in cooldown).
        
        Args:
            phrase: Phrase to check (normalized lowercase)
        
        Returns:
            True if phrase can be used, False if in cooldown
        """
        if not phrase:
            return True
        
        phrase_normalized = phrase.lower().strip()
        
        if phrase_normalized in self.phrase_usage:
            last_used = self.phrase_usage[phrase_normalized]
            segments_since_use = self.current_segment_index - last_used
            
            if segments_since_use < PHRASE_COOLDOWN:
                logger.debug(
                    f"Phrase '{phrase}' blocked: used {segments_since_use} segments ago "
                    f"(cooldown: {PHRASE_COOLDOWN})"
                )
                self.phrase_blocks += 1
                return False
        
        return True
    
    def check_topic_variety(self, topic: str) -> bool:
        """
        Check if topic can be used (not in cooldown).
        
        Args:
            topic: Topic to check (e.g., 'settlement_news', 'raider_activity')
        
        Returns:
            True if topic can be used, False if in cooldown
        """
        if not topic:
            return True
        
        topic_normalized = topic.lower().strip()
        
        if topic_normalized in self.topic_usage:
            last_used = self.topic_usage[topic_normalized]
            segments_since_use = self.current_segment_index - last_used
            
            if segments_since_use < TOPIC_COOLDOWN:
                logger.debug(
                    f"Topic '{topic}' blocked: used {segments_since_use} segments ago "
                    f"(cooldown: {TOPIC_COOLDOWN})"
                )
                self.topic_blocks += 1
                return False
        
        return True
    
    def check_weather_variety(self, weather_type: str) -> bool:
        """
        Check if weather type can be used (not consecutive limit).
        
        Args:
            weather_type: Weather type (e.g., 'clear', 'rainy', 'radstorm')
        
        Returns:
            True if weather can be used, False if would exceed consecutive limit
        """
        if not weather_type:
            return True
        
        weather_normalized = weather_type.lower().strip()
        
        # Check if this weather type appears in all recent history
        if len(self.weather_history) >= WEATHER_CONSECUTIVE_LIMIT - 1:
            # Check if all recent weather matches this type
            if all(w == weather_normalized for w in self.weather_history):
                logger.debug(
                    f"Weather '{weather_type}' blocked: would be {WEATHER_CONSECUTIVE_LIMIT}+ consecutive"
                )
                self.weather_blocks += 1
                return False
        
        return True
    
    def check_structure_variety(self, segment_type: str) -> bool:
        """
        Check if segment type can be used (not immediate repeat).
        
        Args:
            segment_type: Segment type (e.g., 'gossip', 'news', 'weather')
        
        Returns:
            True if structure can be used, False if would repeat immediately
        """
        if not segment_type:
            return True
        
        type_normalized = segment_type.lower().strip()
        
        # Check if last segment was same type (no immediate repeats)
        if len(self.structure_history) > 0:
            if self.structure_history[-1] == type_normalized:
                logger.debug(
                    f"Structure '{segment_type}' blocked: would repeat immediately after same type"
                )
                self.structure_blocks += 1
                return False
        
        return True
    
    def check_variety_constraints(
        self,
        phrase: Optional[str] = None,
        topic: Optional[str] = None,
        weather_type: Optional[str] = None,
        segment_type: Optional[str] = None
    ) -> Dict[str, bool]:
        """
        Check all variety constraints for a segment.
        
        Args:
            phrase: Optional phrase to check
            topic: Optional topic to check
            weather_type: Optional weather type to check
            segment_type: Optional segment type to check
        
        Returns:
            Dict with results: {
                'phrase_ok': bool,
                'topic_ok': bool,
                'weather_ok': bool,
                'structure_ok': bool,
                'all_ok': bool
            }
        """
        results = {
            'phrase_ok': True,
            'topic_ok': True,
            'weather_ok': True,
            'structure_ok': True
        }
        
        if phrase:
            results['phrase_ok'] = self.check_phrase_variety(phrase)
        
        if topic:
            results['topic_ok'] = self.check_topic_variety(topic)
        
        if weather_type:
            results['weather_ok'] = self.check_weather_variety(weather_type)
        
        if segment_type:
            results['structure_ok'] = self.check_structure_variety(segment_type)
        
        results['all_ok'] = all([
            results['phrase_ok'],
            results['topic_ok'],
            results['weather_ok'],
            results['structure_ok']
        ])
        
        return results
    
    def record_usage(
        self,
        phrase: Optional[str] = None,
        topic: Optional[str] = None,
        weather_type: Optional[str] = None,
        segment_type: Optional[str] = None
    ) -> None:
        """
        Record usage of content items and advance segment index.
        
        Call this AFTER generating a segment to update tracking.
        
        Args:
            phrase: Phrase used in segment
            topic: Topic used in segment
            weather_type: Weather type used in segment
            segment_type: Segment type used
        """
        if phrase:
            phrase_normalized = phrase.lower().strip()
            self.phrase_usage[phrase_normalized] = self.current_segment_index
            logger.debug(f"Recorded phrase usage: '{phrase}' at segment {self.current_segment_index}")
        
        if topic:
            topic_normalized = topic.lower().strip()
            self.topic_usage[topic_normalized] = self.current_segment_index
            logger.debug(f"Recorded topic usage: '{topic}' at segment {self.current_segment_index}")
        
        if weather_type:
            weather_normalized = weather_type.lower().strip()
            self.weather_history.append(weather_normalized)
            logger.debug(f"Recorded weather: '{weather_type}' (history: {list(self.weather_history)})")
        
        if segment_type:
            type_normalized = segment_type.lower().strip()
            self.structure_history.append(type_normalized)
            logger.debug(f"Recorded structure: '{segment_type}' (history: {list(self.structure_history)})")
        
        # Advance segment index
        self.current_segment_index += 1
    
    def get_variety_hints(self) -> List[str]:
        """
        Generate variety hints for LLM prompt.
        
        Returns:
            List of hint strings to inject into generation prompt
        """
        hints = []
        
        # Phrase hints
        recent_phrases = [
            phrase for phrase, idx in self.phrase_usage.items()
            if self.current_segment_index - idx < PHRASE_COOLDOWN
        ]
        if recent_phrases:
            hints.append(
                f"Avoid recently used phrases: {', '.join(list(recent_phrases)[:5])}"
            )
        
        # Topic hints
        recent_topics = [
            topic for topic, idx in self.topic_usage.items()
            if self.current_segment_index - idx < TOPIC_COOLDOWN
        ]
        if recent_topics:
            hints.append(
                f"Avoid recently discussed topics: {', '.join(list(recent_topics)[:5])}"
            )
        
        # Weather hints
        if len(self.weather_history) >= 2:
            if all(w == self.weather_history[0] for w in self.weather_history):
                hints.append(
                    f"Consider varying weather (recent: {self.weather_history[0]} × {len(self.weather_history)})"
                )
        
        # Structure hints
        if len(self.structure_history) > 0:
            hints.append(
                f"Last segment type: {self.structure_history[-1]} (vary structure)"
            )
        
        return hints
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get variety tracking statistics.
        
        Returns:
            Dict with statistics for monitoring
        """
        return {
            'total_segments': self.current_segment_index,
            'phrase_blocks': self.phrase_blocks,
            'topic_blocks': self.topic_blocks,
            'weather_blocks': self.weather_blocks,
            'structure_blocks': self.structure_blocks,
            'total_blocks': (
                self.phrase_blocks + self.topic_blocks +
                self.weather_blocks + self.structure_blocks
            ),
            'unique_phrases_tracked': len(self.phrase_usage),
            'unique_topics_tracked': len(self.topic_usage),
            'weather_history_length': len(self.weather_history),
            'structure_history_length': len(self.structure_history)
        }
    
    def reset(self) -> None:
        """Reset all variety tracking (for new broadcast session)."""
        self.phrase_usage.clear()
        self.topic_usage.clear()
        self.weather_history.clear()
        self.structure_history.clear()
        self.current_segment_index = 0
        self.phrase_blocks = 0
        self.topic_blocks = 0
        self.weather_blocks = 0
        self.structure_blocks = 0
        logger.info("Variety manager reset")
