"""
World State Module

Manages long-term broadcast continuity across sessions using persistent storage.
Tracks ongoing storylines, resolved gossip, and overall world state.
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime, timedelta
import json

# Import weather simulator types
try:
    from weather_simulator import WeatherState
except ImportError:
    WeatherState = None  # Graceful fallback if not available


class WorldState:
    """
    Manages persistent world state across broadcast sessions.
    
    Tracks:
    - Ongoing storylines and gossip threads
    - Resolved gossip and completed narratives
    - Broadcast statistics (total count, runtime hours)
    - General world state (major events, faction relations)
    """
    
    def __init__(self, persistence_path: str = "./broadcast_state.json"):
        """
        Initialize world state with optional persistence.
        
        Args:
            persistence_path: Path to JSON file for state persistence
        """
        self.persistence_path = Path(persistence_path)
        self.persistence_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Core state
        self.ongoing_storylines: List[Dict[str, Any]] = []
        self.resolved_gossip: List[Dict[str, Any]] = []
        self.broadcast_count = 0
        self.total_runtime_hours = 0.0
        self.major_events: List[Dict[str, Any]] = []
        self.faction_relations: Dict[str, float] = {}  # Faction: relation score (-1 to 1)
        
        # Weather system state (NEW - Phase 1)
        self.weather_calendars: Dict[str, Dict] = {}  # {region: {date: {time_of_day: weather_dict}}}
        self.current_weather_by_region: Dict[str, Dict] = {}  # {region: weather_dict}
        self.weather_history_archive: Dict[str, Dict] = {}  # {region: {date: {time: weather_dict}}}
        self.calendar_metadata: Dict[str, Dict] = {}  # {region: {generated_date, seed, etc}}
        self.manual_overrides: Dict[str, Optional[Dict]] = {}  # {region: weather_dict or None}
        
        # Story system state (Phase 7)
        self.story_state_path: Optional[str] = None
        
        # Session tracking
        self.last_broadcast = None
        self.creation_date = datetime.now().isoformat()
        
        # Try to load existing state
        self.load()
    
    def add_storyline(self, 
                     topic: str, 
                     initial_development: str,
                     gossip_level: str = "medium") -> Dict[str, Any]:
        """
        Add a new ongoing storyline/gossip thread.
        
        Args:
            topic: Main topic of the storyline
            initial_development: Initial storyline development
            gossip_level: Confidence level (low, medium, high)
        
        Returns:
            The created storyline entry
        """
        storyline = {
            "id": f"story_{len(self.ongoing_storylines)}_{int(datetime.now().timestamp())}",
            "topic": topic,
            "created_date": datetime.now().isoformat(),
            "gossip_level": gossip_level,
            "developments": [initial_development],
            "status": "ongoing"
        }
        
        self.ongoing_storylines.append(storyline)
        self.save()
        return storyline
    
    def continue_storyline(self, 
                          storyline_id: str, 
                          development: str) -> Optional[Dict[str, Any]]:
        """
        Add a new development to an ongoing storyline.
        
        Args:
            storyline_id: ID of the storyline to continue
            development: New development in the story
        
        Returns:
            Updated storyline or None if not found
        """
        for storyline in self.ongoing_storylines:
            if storyline["id"] == storyline_id:
                storyline["developments"].append(development)
                storyline["updated_date"] = datetime.now().isoformat()
                self.save()
                return storyline
        
        return None
    
    def resolve_storyline(self, 
                         storyline_id: str, 
                         resolution: str) -> Optional[Dict[str, Any]]:
        """
        Mark a storyline as resolved and move to completed gossip.
        
        Args:
            storyline_id: ID of the storyline to resolve
            resolution: Final resolution of the story
        
        Returns:
            Resolved storyline or None if not found
        """
        resolved = None
        
        # Find and remove from ongoing
        for i, storyline in enumerate(self.ongoing_storylines):
            if storyline["id"] == storyline_id:
                storyline["status"] = "resolved"
                storyline["resolution"] = resolution
                storyline["resolved_date"] = datetime.now().isoformat()
                resolved = storyline
                self.ongoing_storylines.pop(i)
                break
        
        if resolved:
            self.resolved_gossip.append(resolved)
            self.save()
        
        return resolved
    
    def add_major_event(self, 
                       event_type: str, 
                       description: str,
                       affected_factions: Optional[List[str]] = None) -> None:
        """
        Record a major world event.
        
        Args:
            event_type: Type of event (faction_conflict, discovery, etc.)
            description: Description of the event
            affected_factions: Factions affected by this event
        """
        event = {
            "id": f"event_{len(self.major_events)}_{int(datetime.now().timestamp())}",
            "type": event_type,
            "description": description,
            "date": datetime.now().isoformat(),
            "affected_factions": affected_factions or []
        }
        
        self.major_events.append(event)
        self.save()
    
    def update_broadcast_stats(self, runtime_hours: float) -> None:
        """
        Update broadcast statistics after a segment.
        
        Args:
            runtime_hours: Hours of broadcast time (typically 0.05-0.2 for a segment)
        """
        self.broadcast_count += 1
        self.total_runtime_hours += runtime_hours
        self.last_broadcast = datetime.now().isoformat()
        self.save()
    
    def get_storylines_for_context(self, max_count: int = 3) -> List[Dict[str, Any]]:
        """
        Get recent ongoing storylines for prompt context.
        
        Args:
            max_count: Maximum number of storylines to return
        
        Returns:
            List of recent ongoing storylines
        """
        # Return most recent storylines
        return self.ongoing_storylines[-max_count:] if self.ongoing_storylines else []
    
    # Weather System Methods (NEW - Phase 1)
    
    def get_current_weather(self, region: str) -> Optional[Dict]:
        """
        Get current weather for a region.
        
        Args:
            region: Region name (e.g., "Appalachia")
        
        Returns:
            Weather state dict or None
        """
        # Check manual override first
        if region in self.manual_overrides and self.manual_overrides[region]:
            return self.manual_overrides[region]
        
        return self.current_weather_by_region.get(region)
    
    def update_weather_state(self, region: str, weather_dict: Dict) -> None:
        """
        Update current weather state for a region.
        
        Args:
            region: Region name
            weather_dict: Weather state as dictionary
        """
        self.current_weather_by_region[region] = weather_dict
        self.save()
    
    def log_weather_history(self, region: str, timestamp: datetime, weather_dict: Dict) -> None:
        """
        Log weather to historical archive.
        
        Args:
            region: Region name
            timestamp: When this weather occurred
            weather_dict: Weather state dictionary
        """
        if region not in self.weather_history_archive:
            self.weather_history_archive[region] = {}
        
        date_str = timestamp.strftime("%Y-%m-%d")
        time_str = timestamp.strftime("%H:%M")
        
        if date_str not in self.weather_history_archive[region]:
            self.weather_history_archive[region][date_str] = {}
        
        self.weather_history_archive[region][date_str][time_str] = weather_dict
        self.save()
    
    def get_weather_history(self, 
                           region: str,
                           start_date: Optional[datetime] = None,
                           end_date: Optional[datetime] = None) -> List[Dict]:
        """
        Query historical weather for a region.
        
        Args:
            region: Region name
            start_date: Optional start date filter
            end_date: Optional end date filter
        
        Returns:
            List of weather state dicts
        """
        if region not in self.weather_history_archive:
            return []
        
        history = []
        for date_str, times in self.weather_history_archive[region].items():
            # Filter by date range if specified
            if start_date or end_date:
                date_obj = datetime.fromisoformat(date_str)
                if start_date and date_obj < start_date:
                    continue
                if end_date and date_obj > end_date:
                    continue
            
            for time_str, weather_dict in times.items():
                history.append(weather_dict)
        
        return history
    
    def get_notable_weather_events(self, region: str, days_back: int = 30) -> List[Dict]:
        """
        Get notable weather events from recent history.
        
        Args:
            region: Region name
            days_back: How many days back to search
        
        Returns:
            List of notable weather events
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        history = self.get_weather_history(region, start_date, end_date)
        notable = [w for w in history if w.get("notable_event", False)]
        
        return notable
    
    def set_manual_weather_override(self, region: str, weather_dict: Dict) -> None:
        """
        Set manual weather override for a region.
        
        Args:
            region: Region name
            weather_dict: Weather state dictionary
        """
        self.manual_overrides[region] = weather_dict
        self.save()
    
    def clear_manual_override(self, region: str) -> None:
        """
        Clear manual weather override for a region.
        
        Args:
            region: Region name
        """
        if region in self.manual_overrides:
            self.manual_overrides[region] = None
        self.save()
    
    def get_calendar_for_region(self, region: str) -> Optional[Dict]:
        """
        Get weather calendar for a region.
        
        Args:
            region: Region name
        
        Returns:
            Calendar dict or None
        """
        return self.weather_calendars.get(region)
    
    def save(self) -> None:
        """Persist world state to JSON file."""
        state_dict = {
            "creation_date": self.creation_date,
            "last_broadcast": self.last_broadcast,
            "broadcast_count": self.broadcast_count,
            "total_runtime_hours": self.total_runtime_hours,
            "ongoing_storylines": self.ongoing_storylines,
            "resolved_gossip": self.resolved_gossip,
            "major_events": self.major_events,
            "faction_relations": self.faction_relations,
            # Weather system state (NEW)
            "weather_calendars": self.weather_calendars,
            "current_weather_by_region": self.current_weather_by_region,
            "weather_history_archive": self.weather_history_archive,
            "calendar_metadata": self.calendar_metadata,
            "manual_overrides": self.manual_overrides,
        }
        
        with open(self.persistence_path, 'w') as f:
            json.dump(state_dict, f, indent=2)
    
    def load(self) -> None:
        """Load world state from JSON file if it exists."""
        if not self.persistence_path.exists():
            return
        
        try:
            with open(self.persistence_path, 'r') as f:
                state_dict = json.load(f)
            
            self.creation_date = state_dict.get("creation_date", self.creation_date)
            self.last_broadcast = state_dict.get("last_broadcast")
            self.broadcast_count = state_dict.get("broadcast_count", 0)
            self.total_runtime_hours = state_dict.get("total_runtime_hours", 0.0)
            self.ongoing_storylines = state_dict.get("ongoing_storylines", [])
            self.resolved_gossip = state_dict.get("resolved_gossip", [])
            self.major_events = state_dict.get("major_events", [])
            self.faction_relations = state_dict.get("faction_relations", {})
            
            # Weather system state (NEW - backward compatible)
            self.weather_calendars = state_dict.get("weather_calendars", {})
            self.current_weather_by_region = state_dict.get("current_weather_by_region", {})
            self.weather_history_archive = state_dict.get("weather_history_archive", {})
            self.calendar_metadata = state_dict.get("calendar_metadata", {})
            self.manual_overrides = state_dict.get("manual_overrides", {})
            
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not load world state: {e}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert world state to dictionary."""
        return {
            "creation_date": self.creation_date,
            "last_broadcast": self.last_broadcast,
            "broadcast_count": self.broadcast_count,
            "total_runtime_hours": self.total_runtime_hours,
            "ongoing_storylines": self.ongoing_storylines,
            "resolved_gossip": self.resolved_gossip,
            "major_events": self.major_events,
            "faction_relations": self.faction_relations,
            # Weather system state (NEW)
            "weather_calendars": self.weather_calendars,
            "current_weather_by_region": self.current_weather_by_region,
            "weather_history_archive": self.weather_history_archive,
            "calendar_metadata": self.calendar_metadata,
            "manual_overrides": self.manual_overrides,
        }
