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
            with open(temp_path, 'w') as f:
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
