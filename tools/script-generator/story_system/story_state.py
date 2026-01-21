"""
Story State Manager

Manages persistent storage of story system state:
- Story pools (queued stories per timeline)
- Scheduler state (active stories, cooldowns, broadcast counts)
- Completed stories archive
- Escalation history

Provides JSON-based persistence across sessions.
"""

from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime
import json

from .story_models import Story, ActiveStory, StoryTimeline, StoryStatus


class StoryState:
    """
    Persistent storage manager for story system.
    
    Tracks:
    - Story pools for each timeline (stories waiting to be activated)
    - Active stories currently being broadcast
    - Completed stories and escalation history
    - Scheduler metadata (last activation time, broadcast counts)
    """
    
    def __init__(self, persistence_path: str = "./story_state.json"):
        """
        Initialize story state manager.
        
        Args:
            persistence_path: Path to JSON file for state persistence
        """
        self.persistence_path = Path(persistence_path)
        self.persistence_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Story pools by timeline
        self.story_pools: Dict[StoryTimeline, List[Story]] = {
            StoryTimeline.DAILY: [],
            StoryTimeline.WEEKLY: [],
            StoryTimeline.MONTHLY: [],
            StoryTimeline.YEARLY: [],
        }
        
        # Active stories by timeline (one per timeline slot)
        self.active_stories: Dict[StoryTimeline, Optional[ActiveStory]] = {
            StoryTimeline.DAILY: None,
            StoryTimeline.WEEKLY: None,
            StoryTimeline.MONTHLY: None,
            StoryTimeline.YEARLY: None,
        }
        
        # Completed and archived stories
        self.completed_stories: List[Dict[str, Any]] = []
        self.archived_stories: List[Dict[str, Any]] = []
        
        # Escalation tracking
        self.escalation_history: List[Dict[str, Any]] = []
        
        # Per-story beat tracking (Phase 2C)
        # Maps story_id -> list of beat dictionaries with timestamps
        self.beat_history: Dict[str, List[Dict[str, Any]]] = {}
        
        # Scheduler metadata
        self.last_activation: Dict[StoryTimeline, Optional[datetime]] = {
            timeline: None for timeline in StoryTimeline
        }
        self.total_broadcasts_by_timeline: Dict[StoryTimeline, int] = {
            timeline: 0 for timeline in StoryTimeline
        }
        
        # Version for schema migrations
        self.schema_version = "1.0"
        self.created_at = datetime.now().isoformat()
        self.last_modified = None
        
        # Load existing state
        self.load()
    
    def add_to_pool(self, story: Story, timeline: Optional[StoryTimeline] = None):
        """
        Add story to appropriate pool.
        
        Args:
            story: Story to add
            timeline: Override story's timeline (optional)
        """
        target_timeline = timeline or story.timeline
        
        # Check if story already in pool
        existing_ids = [s.story_id for s in self.story_pools[target_timeline]]
        if story.story_id not in existing_ids:
            self.story_pools[target_timeline].append(story)
            self.last_modified = datetime.now().isoformat()
    
    def get_pool(self, timeline: StoryTimeline) -> List[Story]:
        """
        Get stories in pool for timeline.
        
        Args:
            timeline: Timeline to query
            
        Returns:
            List of stories in pool
        """
        return self.story_pools.get(timeline, [])
    
    def remove_from_pool(self, story_id: str, timeline: StoryTimeline) -> bool:
        """
        Remove story from pool.
        
        Args:
            story_id: Story ID to remove
            timeline: Timeline pool to remove from
            
        Returns:
            True if removed, False if not found
        """
        pool = self.story_pools[timeline]
        for i, story in enumerate(pool):
            if story.story_id == story_id:
                pool.pop(i)
                self.last_modified = datetime.now().isoformat()
                return True
        return False
    
    def set_active_story(self, timeline: StoryTimeline, active_story: Optional[ActiveStory]):
        """
        Set active story for timeline slot.
        
        Args:
            timeline: Timeline slot
            active_story: ActiveStory instance or None to clear
        """
        self.active_stories[timeline] = active_story
        if active_story:
            self.last_activation[timeline] = datetime.now()
        self.last_modified = datetime.now().isoformat()
    
    def get_active_story(self, timeline: StoryTimeline) -> Optional[ActiveStory]:
        """
        Get active story for timeline slot.
        
        Args:
            timeline: Timeline to query
            
        Returns:
            ActiveStory or None
        """
        return self.active_stories.get(timeline)
    
    def archive_story(self, active_story: ActiveStory):
        """
        Archive completed story.
        
        Args:
            active_story: Completed ActiveStory to archive
        """
        # Get timeline value (handle both enum and string)
        timeline_value = active_story.story.timeline
        if hasattr(timeline_value, 'value'):
            timeline_value = timeline_value.value
        
        # Get status value (handle both enum and string)  
        status_value = active_story.status
        if hasattr(status_value, 'value'):
            status_value = status_value.value
        
        archive_entry = {
            "story_id": active_story.story.story_id,
            "title": active_story.story.title,
            "timeline": timeline_value,
            "completed_at": datetime.now().isoformat(),
            "total_broadcasts": active_story.total_broadcasts,
            "engagement_score": active_story.engagement_score,
            "escalation_count": active_story.escalation_count,
            "status": status_value
        }
        
        if status_value == "completed" or status_value == StoryStatus.COMPLETED:
            self.completed_stories.append(archive_entry)
        else:
            self.archived_stories.append(archive_entry)
        
        self.last_modified = datetime.now().isoformat()
    
    def record_escalation(self, from_story_id: str, to_story_id: str, 
                          from_timeline: StoryTimeline, to_timeline: StoryTimeline):
        """
        Record story escalation in history.
        
        Args:
            from_story_id: Source story ID
            to_story_id: New escalated story ID
            from_timeline: Source timeline
            to_timeline: Target timeline
        """
        # Handle both enum and string values
        from_value = from_timeline.value if hasattr(from_timeline, 'value') else from_timeline
        to_value = to_timeline.value if hasattr(to_timeline, 'value') else to_timeline
        
        escalation_entry = {
            "from_story_id": from_story_id,
            "to_story_id": to_story_id,
            "from_timeline": from_value,
            "to_timeline": to_value,
            "escalated_at": datetime.now().isoformat()
        }
        
        self.escalation_history.append(escalation_entry)
        self.last_modified = datetime.now().isoformat()
    
    def record_story_beat(self, story_id: str, beat_summary: str, entities: List[str], 
                          act_number: int = 1, conflict_level: float = 0.5):
        """
        Record a story beat in per-story history (Phase 2C).
        
        Args:
            story_id: Story identifier
            beat_summary: What happened in this beat
            entities: Characters/locations/factions mentioned
            act_number: Current act number (default 1)
            conflict_level: Tension/conflict intensity 0.0-1.0
        """
        if story_id not in self.beat_history:
            self.beat_history[story_id] = []
        
        beat_entry = {
            "timestamp": datetime.now().isoformat(),
            "act_number": act_number,
            "beat_summary": beat_summary,
            "entities": entities,
            "conflict_level": conflict_level,
            "token_count": len(beat_summary.split())  # Rough word count
        }
        
        self.beat_history[story_id].append(beat_entry)
        self.last_modified = datetime.now().isoformat()
    
    def get_story_beats(self, story_id: str, recent_count: int = 5) -> List[Dict[str, Any]]:
        """
        Get recent beats for a story with summarization of older beats (Phase 2C).
        
        Returns recent beats in full detail and summarized older beats.
        This reduces token count for LLM context.
        
        Args:
            story_id: Story identifier
            recent_count: Number of recent beats to keep in full detail (default 5)
            
        Returns:
            List of beat dictionaries (recent in full, older summarized)
        """
        if story_id not in self.beat_history:
            return []
        
        all_beats = self.beat_history[story_id]
        
        # If we have fewer beats than threshold, return all in full detail
        if len(all_beats) <= recent_count:
            return all_beats
        
        # Split into recent (keep full) and old (summarize)
        recent_beats = all_beats[-recent_count:]
        old_beats = all_beats[:-recent_count]
        
        # Summarize old beats
        summarized_old = self._summarize_beats(old_beats)
        
        # Return: [summarized_entry] + recent_full_beats
        return [summarized_old] + recent_beats
    
    def _summarize_beats(self, beats: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Summarize multiple beats into single condensed entry.
        
        Reduces token count by ≥50% while preserving key information.
        
        Args:
            beats: List of beat dictionaries to summarize
            
        Returns:
            Single summarized beat dictionary
        """
        if not beats:
            return {
                "timestamp": datetime.now().isoformat(),
                "beat_summary": "(No prior beats)",
                "entities": [],
                "conflict_level": 0.0,
                "token_count": 3,
                "summarized_count": 0
            }
        
        # Collect all entities mentioned
        all_entities = set()
        for beat in beats:
            all_entities.update(beat.get("entities", []))
        
        # Calculate average conflict level
        conflict_levels = [b.get("conflict_level", 0.5) for b in beats]
        avg_conflict = sum(conflict_levels) / len(conflict_levels) if conflict_levels else 0.5
        
        # Create condensed summary (count of beats + entity list)
        beat_count = len(beats)
        entity_list = ", ".join(sorted(all_entities)[:10])  # Limit to 10 entities
        
        if entity_list:
            summary = f"Previous {beat_count} beats involved: {entity_list}"
        else:
            summary = f"Previous {beat_count} beats covered early story development"
        
        return {
            "timestamp": beats[-1].get("timestamp", datetime.now().isoformat()),
            "beat_summary": summary,
            "entities": list(all_entities),
            "conflict_level": avg_conflict,
            "token_count": len(summary.split()),
            "summarized_count": beat_count,
            "is_summary": True
        }
    
    def get_beat_token_count(self, story_id: str) -> int:
        """
        Calculate total token count for story beats (with summarization applied).
        
        Args:
            story_id: Story identifier
            
        Returns:
            Approximate token count for beats
        """
        beats = self.get_story_beats(story_id)
        return sum(beat.get("token_count", 0) for beat in beats)
    
    def get_pool_size(self, timeline: StoryTimeline) -> int:
        """Get number of stories in pool for timeline."""
        return len(self.story_pools[timeline])
    
    def get_total_active_stories(self) -> int:
        """Get count of currently active stories across all timelines."""
        return sum(1 for story in self.active_stories.values() if story is not None)
    
    def save(self):
        """Save state to JSON file."""
        try:
            # Helper to get value from enum or string
            def get_value(obj):
                return obj.value if hasattr(obj, 'value') else obj
            
            # Debug: Count active stories
            active_count = sum(1 for active in self.active_stories.values() if active)
            print(f"[Story State] Saving: {active_count} active stories, {sum(len(pool) for pool in self.story_pools.values())} in pools")
            
            state_dict = {
                "schema_version": self.schema_version,
                "created_at": self.created_at,
                "last_modified": self.last_modified or datetime.now().isoformat(),
                
                "story_pools": {
                    get_value(timeline): [story.model_dump(mode='json') for story in stories]
                    for timeline, stories in self.story_pools.items()
                },
                
                "active_stories": {
                    get_value(timeline): active.model_dump(mode='json') if active else None
                    for timeline, active in self.active_stories.items()
                },
                
                "completed_stories": self.completed_stories,
                "archived_stories": self.archived_stories,
                "escalation_history": self.escalation_history,
                "beat_history": self.beat_history,  # Phase 2C
                
                "last_activation": {
                    get_value(timeline): timestamp.isoformat() if timestamp else None
                    for timeline, timestamp in self.last_activation.items()
                },
                
                "total_broadcasts_by_timeline": {
                    get_value(timeline): count
                    for timeline, count in self.total_broadcasts_by_timeline.items()
                }
            }
            
            # Write with atomic rename for safety
            temp_path = self.persistence_path.with_suffix('.tmp')
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(state_dict, f, indent=2)
            
            temp_path.replace(self.persistence_path)
            
        except Exception as e:
            print(f"Error saving story state: {e}")
    
    def load(self):
        """Load state from JSON file."""
        if not self.persistence_path.exists():
            return
        
        try:
            with open(self.persistence_path) as f:
                state_dict = json.load(f)
            
            # Load metadata
            self.schema_version = state_dict.get("schema_version", "1.0")
            self.created_at = state_dict.get("created_at", self.created_at)
            self.last_modified = state_dict.get("last_modified")
            
            # Load story pools
            for timeline_str, stories_data in state_dict.get("story_pools", {}).items():
                timeline = StoryTimeline(timeline_str)
                self.story_pools[timeline] = [
                    Story(**story_data) for story_data in stories_data
                ]
            
            # Load active stories
            for timeline_str, active_data in state_dict.get("active_stories", {}).items():
                timeline = StoryTimeline(timeline_str)
                if active_data:
                    self.active_stories[timeline] = ActiveStory(**active_data)
            
            # Load archives
            self.completed_stories = state_dict.get("completed_stories", [])
            self.archived_stories = state_dict.get("archived_stories", [])
            self.escalation_history = state_dict.get("escalation_history", [])
            self.beat_history = state_dict.get("beat_history", {})  # Phase 2C
            
            # Load last activation times
            for timeline_str, timestamp_str in state_dict.get("last_activation", {}).items():
                timeline = StoryTimeline(timeline_str)
                if timestamp_str:
                    self.last_activation[timeline] = datetime.fromisoformat(timestamp_str)
            
            # Load broadcast counts
            for timeline_str, count in state_dict.get("total_broadcasts_by_timeline", {}).items():
                timeline = StoryTimeline(timeline_str)
                self.total_broadcasts_by_timeline[timeline] = count
            
        except Exception as e:
            print(f"Error loading story state: {e}")
            # Keep default empty state
    
    def clear_timeline(self, timeline: StoryTimeline):
        """Clear all data for a specific timeline (for testing/debugging)."""
        self.story_pools[timeline] = []
        self.active_stories[timeline] = None
        self.last_activation[timeline] = None
        self.total_broadcasts_by_timeline[timeline] = 0
        self.last_modified = datetime.now().isoformat()
    
    def reset(self):
        """Reset all state to defaults (for testing)."""
        for timeline in StoryTimeline:
            self.clear_timeline(timeline)
        self.completed_stories = []
        self.archived_stories = []
        self.escalation_history = []
        self.last_modified = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert story state to dictionary for checkpoint serialization.
        
        Returns:
            Dictionary representation of story state
        """
        # Helper to get value from enum or string
        def get_value(obj):
            return obj.value if hasattr(obj, 'value') else obj
        
        return {
            "schema_version": self.schema_version,
            "created_at": self.created_at,
            "last_modified": self.last_modified or datetime.now().isoformat(),
            
            "story_pools": {
                get_value(timeline): [story.model_dump(mode='json') for story in stories]
                for timeline, stories in self.story_pools.items()
            },
            
            "active_stories": {
                get_value(timeline): active.model_dump(mode='json') if active else None
                for timeline, active in self.active_stories.items()
            },
            
            "completed_stories": self.completed_stories,
            "archived_stories": self.archived_stories,
            "escalation_history": self.escalation_history,
            "beat_history": self.beat_history,  # Phase 2C
            
            "last_activation": {
                get_value(timeline): timestamp.isoformat() if timestamp else None
                for timeline, timestamp in self.last_activation.items()
            },
            
            "total_broadcasts_by_timeline": {
                get_value(timeline): count
                for timeline, count in self.total_broadcasts_by_timeline.items()
            }
        }
    
    def from_dict(self, data: Dict[str, Any]) -> None:
        """
        Load story state from dictionary (for checkpoint restoration).
        
        Args:
            data: Dictionary representation of story state
        """
        # Load metadata
        self.schema_version = data.get("schema_version", "1.0")
        self.created_at = data.get("created_at", self.created_at)
        self.last_modified = data.get("last_modified")
        
        # Load story pools
        for timeline_str, stories_data in data.get("story_pools", {}).items():
            timeline = StoryTimeline(timeline_str)
            self.story_pools[timeline] = [
                Story(**story_data) for story_data in stories_data
            ]
        
        # Load active stories
        for timeline_str, active_data in data.get("active_stories", {}).items():
            timeline = StoryTimeline(timeline_str)
            if active_data:
                self.active_stories[timeline] = ActiveStory(**active_data)
        
        # Load archives
        self.completed_stories = data.get("completed_stories", [])
        self.archived_stories = data.get("archived_stories", [])
        self.escalation_history = data.get("escalation_history", [])
        self.beat_history = data.get("beat_history", {})  # Phase 2C
        
        # Load last activation times
        for timeline_str, timestamp_str in data.get("last_activation", {}).items():
            timeline = StoryTimeline(timeline_str)
            if timestamp_str:
                self.last_activation[timeline] = datetime.fromisoformat(timestamp_str)
        
        # Load broadcast counts
        for timeline_str, count in data.get("total_broadcasts_by_timeline", {}).items():
            timeline = StoryTimeline(timeline_str)
            self.total_broadcasts_by_timeline[timeline] = count
