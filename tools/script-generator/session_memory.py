"""
Session Memory Module

Manages short-term broadcast continuity by tracking recently generated scripts
and mentioned topics to prevent repetition and maintain narrative coherence.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
import json


@dataclass
class ScriptEntry:
    """Single script entry in memory."""
    script_type: str  # weather, news, gossip, music_intro, time_check
    content: str
    timestamp: str
    metadata: Dict[str, Any]
    catchphrases_used: List[str]


class SessionMemory:
    """
    Manages short-term broadcast memory to maintain continuity within sessions.
    
    Prevents repetition of recent topics and catchphrases, tracks mentioned
    subjects, and provides context for prompt injection.
    """
    
    def __init__(self, max_history: int = 10, dj_name: Optional[str] = None):
        """
        Initialize session memory.
        
        Args:
            max_history: Maximum number of recent scripts to keep in memory
            dj_name: DJ name for personality-specific tracking
        """
        self.max_history = max_history
        self.dj_name = dj_name
        self.recent_scripts: List[ScriptEntry] = []
        self.catchphrase_history: List[str] = []
        self.mentioned_topics: Dict[str, int] = {}  # topic: count
        self.session_start = datetime.now()
        self.segment_count = 0
        
        # Phase 7: Story beat tracking (last 10-20 beats)
        self.recent_story_beats: List[Dict[str, Any]] = []
        self.max_story_beats = 15
    
    def add_script(self, 
                  script_type: str, 
                  content: str, 
                  metadata: Optional[Dict[str, Any]] = None,
                  catchphrases_used: Optional[List[str]] = None) -> None:
        """
        Add a newly generated script to memory.
        
        Args:
            script_type: Type of script (weather, news, etc.)
            content: Full script text
            metadata: Additional metadata (RAG sources, weather type, etc.)
            catchphrases_used: List of catchphrases used in this script
        """
        entry = ScriptEntry(
            script_type=script_type,
            content=content,
            timestamp=datetime.now().isoformat(),
            metadata=metadata or {},
            catchphrases_used=catchphrases_used or []
        )
        
        self.recent_scripts.append(entry)
        
        # Enforce max history
        if len(self.recent_scripts) > self.max_history:
            self.recent_scripts.pop(0)
        
        # Track catchphrases
        if catchphrases_used:
            self.catchphrase_history.extend(catchphrases_used)
            # Keep only recent catchphrase history
            if len(self.catchphrase_history) > self.max_history * 3:
                self.catchphrase_history = self.catchphrase_history[-(self.max_history * 3):]
        
        # Extract and track mentioned topics
        self._extract_topics(content)
        
        self.segment_count += 1
    
    def _extract_topics(self, content: str) -> None:
        """
        Extract key topics from script content for deduplication.
        
        This is a simple implementation. In production, could use NLP
        or more sophisticated topic extraction.
        """
        # Common topic keywords to track
        topics_keywords = {
            "raiders": ["raider", "attack", "destroy"],
            "vault": ["vault", "vault-tec", "underground"],
            "factions": ["brotherhood", "responders", "settlers"],
            "locations": ["flatwoods", "appalachia", "morgantown"],
            "weather": ["rad", "storm", "rain", "clear", "sunny"],
            "cryptids": ["mothman", "creature", "beast"],
            "trading": ["trade", "caravan", "merchant", "caps"],
        }
        
        content_lower = content.lower()
        for topic, keywords in topics_keywords.items():
            for keyword in keywords:
                if keyword in content_lower:
                    self.mentioned_topics[topic] = self.mentioned_topics.get(topic, 0) + 1
                    break  # Count topic only once per script
    
    def get_context_for_prompt(self, include_recent: int = 3) -> str:
        """
        Generate context string for prompt injection.
        
        Shows recent scripts to help LLM maintain continuity.
        
        Args:
            include_recent: How many recent scripts to include
        
        Returns:
            Formatted context string for prompt injection
        """
        if not self.recent_scripts:
            return ""
        
        recent = self.recent_scripts[-include_recent:]
        
        context_lines = ["RECENT BROADCAST CONTEXT (for continuity):"]
        context_lines.append(f"Session duration: {self._get_session_duration()}")
        context_lines.append(f"Segments broadcast: {self.segment_count}\n")
        
        for entry in recent:
            context_lines.append(f"[{entry.script_type.upper()}]")
            context_lines.append(entry.content[:200] + ("..." if len(entry.content) > 200 else ""))
            context_lines.append("")
        
        context_lines.extend([
            "CONTINUITY REQUIREMENTS:",
            "- Reference earlier segments when natural (e.g., 'As I mentioned earlier...')",
            "- Avoid repeating topics from recent broadcasts",
            "- Build on unresolved gossip or developing stories",
            "- Vary catchphrase usage (don't repeat recent ones)"
        ])
        
        return "\n".join(context_lines)
    
    def get_mentioned_topics(self) -> List[str]:
        """
        Get list of recently mentioned topics for deduplication.
        
        Returns:
            List of topics mentioned in recent scripts
        """
        return list(self.mentioned_topics.keys())
    
    def get_recent_catchphrases(self, count: int = 5) -> List[str]:
        """
        Get recently used catchphrases to avoid repetition.
        
        Args:
            count: How many recent catchphrases to return
        
        Returns:
            List of recently used catchphrases
        """
        return self.catchphrase_history[-count:] if self.catchphrase_history else []
    
    def reset(self) -> None:
        """Clear session memory and start fresh."""
        self.recent_scripts = []
        self.catchphrase_history = []
        self.mentioned_topics = {}
        self.session_start = datetime.now()
        self.segment_count = 0
    
    def _get_session_duration(self) -> str:
        """Get human-readable session duration."""
        delta = datetime.now() - self.session_start
        hours = delta.total_seconds() / 3600
        return f"{hours:.1f} hours"
    
    # Weather Continuity Methods (Phase 3)
    
    def get_weather_continuity_context(self, region: str, current_weather_dict: Dict) -> Dict:
        """
        Get weather continuity context for DJ references.
        
        Provides information about weather changes and notable events
        for natural DJ continuity in broadcasts.
        
        Args:
            region: Region name (e.g., "Appalachia")
            current_weather_dict: Current weather state dict
        
        Returns:
            Dict with weather continuity information:
            {
                'weather_changed': bool,
                'last_weather_type': str or None,
                'continuity_phrase': str or None,
                'has_notable_history': bool
            }
        """
        # Get last weather from memory
        last_weather = self._get_last_weather_from_memory()
        current_weather_type = current_weather_dict.get('weather_type')
        
        # Detect weather change
        weather_changed = (last_weather is not None and 
                          last_weather != current_weather_type)
        
        # Generate continuity phrase if weather changed
        continuity_phrase = None
        if weather_changed:
            continuity_phrase = self._generate_continuity_phrase(
                last_weather, 
                current_weather_type,
                region
            )
        
        return {
            'weather_changed': weather_changed,
            'last_weather_type': last_weather,
            'continuity_phrase': continuity_phrase,
            'has_notable_history': len(self.recent_scripts) > 2
        }
    
    def _get_last_weather_from_memory(self) -> Optional[str]:
        """
        Get the weather type from the most recent weather segment.
        
        Returns:
            Weather type string or None if no recent weather segments
        """
        for entry in reversed(self.recent_scripts):
            if entry.script_type == 'weather':
                # Try to get weather_type from metadata
                return entry.metadata.get('weather_type')
        
        return None
    
    def _generate_continuity_phrase(self, 
                                   last_weather: str, 
                                   current_weather: str,
                                   region: str) -> str:
        """
        Generate a natural continuity phrase for weather changes.
        
        Args:
            last_weather: Previous weather type
            current_weather: Current weather type
            region: Region name
        
        Returns:
            Natural transition phrase
        """
        import random
        
        # Regional location references
        regional_refs = {
            "Appalachia": ["the mountains", "the valley", "these parts"],
            "Mojave": ["the desert", "the Strip", "the wasteland"],
            "Commonwealth": ["the Commonwealth", "the ruins", "these streets"]
        }
        
        location_ref = regional_refs.get(region, ["the area"])[0]
        
        # Weather transition phrases
        transitions = {
            ('rainy', 'sunny'): [
                f"Looks like that rain finally cleared up over {location_ref}.",
                f"Good news - the storm's passed and we've got clear skies.",
                f"Rain's moved on, sun's breaking through."
            ],
            ('sunny', 'rainy'): [
                f"Weather's turning - rain moving in over {location_ref}.",
                f"Those clear skies didn't last long. Rain's coming.",
                f"Storm clouds rolling in now."
            ],
            ('cloudy', 'rad_storm'): [
                f"Radiation storm detected over {location_ref}. Take shelter.",
                f"We've got a rad storm forming. This is serious, folks.",
                f"Geiger counters are spiking - rad storm incoming."
            ],
            ('foggy', 'sunny'): [
                f"Morning fog's finally burning off.",
                f"That thick fog's clearing out nicely.",
                f"Visibility's improving as the fog lifts."
            ],
            ('rad_storm', 'cloudy'): [
                f"Radiation storm has passed. You can come out now.",
                f"All clear - rad levels dropping back to normal.",
                f"Storm's over, but stay cautious out there."
            ],
            ('snow', 'sunny'): [
                f"Snow's stopped and we're seeing some sun.",
                f"Winter weather's easing up a bit.",
                f"Snowfall's done for now."
            ]
        }
        
        # Try to find specific transition
        transition_key = (last_weather, current_weather)
        if transition_key in transitions:
            return random.choice(transitions[transition_key])
        
        # Generic transitions
        generic = [
            f"Weather's changed since last time.",
            f"Conditions are different now over {location_ref}.",
            f"Update on the weather situation."
        ]
        
        return random.choice(generic)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize session memory to dictionary."""
        return {
            "session_start": self.session_start.isoformat(),
            "segment_count": self.segment_count,
            "recent_scripts": [asdict(s) for s in self.recent_scripts],
            "catchphrase_history": self.catchphrase_history,
            "mentioned_topics": self.mentioned_topics,
            "recent_story_beats": self.recent_story_beats,
        }
    
    def from_dict(self, data: Dict[str, Any]) -> None:
        """Deserialize session memory from dictionary."""
        self.session_start = datetime.fromisoformat(data["session_start"])
        self.segment_count = data["segment_count"]
        self.recent_scripts = [
            ScriptEntry(**entry) for entry in data["recent_scripts"]
        ]
        self.catchphrase_history = data["catchphrase_history"]
        self.mentioned_topics = data["mentioned_topics"]
        self.recent_story_beats = data.get("recent_story_beats", [])
    
    def add_story_beat(self, beat_info: Dict[str, Any]) -> None:
        """
        Add story beat to recent history (Phase 7).
        
        Args:
            beat_info: Dictionary with story beat information
        """
        self.recent_story_beats.append(beat_info)
        
        # Enforce max story beats
        if len(self.recent_story_beats) > self.max_story_beats:
            self.recent_story_beats.pop(0)
    
    def get_recent_story_beats(self, count: int = 5) -> List[Dict[str, Any]]:
        """
        Get recent story beats (Phase 7).
        
        Args:
            count: Number of recent beats to return
            
        Returns:
            List of recent story beat dictionaries
        """
        return self.recent_story_beats[-count:]
