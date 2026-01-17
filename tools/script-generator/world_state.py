"""
World State Module

Manages long-term broadcast continuity across sessions using persistent storage.
Tracks ongoing storylines, resolved gossip, and overall world state.
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime
import json


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
        }
