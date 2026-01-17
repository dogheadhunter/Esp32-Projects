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
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize session memory to dictionary."""
        return {
            "session_start": self.session_start.isoformat(),
            "segment_count": self.segment_count,
            "recent_scripts": [asdict(s) for s in self.recent_scripts],
            "catchphrase_history": self.catchphrase_history,
            "mentioned_topics": self.mentioned_topics,
        }
    
    def from_dict(self, data: Dict[str, Any]) -> None:
        """Deserialize session memory from dictionary."""
        self.session_start = datetime.fromisoformat(data["session_start"])
        self.segment_count = data["segment_count"]
        self.catchphrase_history = data["catchphrase_history"]
        self.mentioned_topics = data["mentioned_topics"]
        self.recent_scripts = [
            ScriptEntry(**script_data) 
            for script_data in data["recent_scripts"]
        ]
