"""
Story Scheduler

Manages multi-timeline story scheduling and progression:
- 4 concurrent timeline slots (daily, weekly, monthly, yearly)
- Probability-based beat inclusion per broadcast
- Minimum spacing between beats
- Cooldown periods after story completion
- Story activation and progression

Coordinates with StoryState for persistence.
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import random

from .story_models import (
    Story,
    ActiveStory,
    StoryBeat,
    StoryTimeline,
    StoryStatus,
    StoryActType,
)
from .story_state import StoryState


class StoryScheduler:
    """
    Manages scheduling and progression of multi-timeline stories.
    
    Core responsibilities:
    - Activate stories from pools when slots are empty
    - Determine which stories to include in each broadcast
    - Advance story acts based on broadcast counts
    - Apply cooldowns and spacing rules
    - Track engagement metrics
    """
    
    # Minimum broadcasts before advancing to next act
    MIN_BROADCASTS_PER_ACT = {
        StoryTimeline.DAILY: 1,     # Fast progression
        StoryTimeline.WEEKLY: 2,    # Moderate pace
        StoryTimeline.MONTHLY: 3,   # Slower build
        StoryTimeline.YEARLY: 5,    # Epic pacing
    }
    
    # Maximum broadcasts before forcing act advancement
    MAX_BROADCASTS_PER_ACT = {
        StoryTimeline.DAILY: 3,
        StoryTimeline.WEEKLY: 6,
        StoryTimeline.MONTHLY: 15,
        StoryTimeline.YEARLY: 30,
    }
    
    # Probability of including story beat in broadcast
    INCLUSION_PROBABILITY = {
        StoryTimeline.DAILY: 0.8,    # High frequency (tuned)
        StoryTimeline.WEEKLY: 0.5,   # Moderate (tuned)
        StoryTimeline.MONTHLY: 0.3,  # Occasional (tuned)
        StoryTimeline.YEARLY: 0.15,  # Rare (tuned)
    }
    
    # Minimum broadcasts between beats for same story
    MIN_SPACING = {
        StoryTimeline.DAILY: 0,      # Can be every broadcast
        StoryTimeline.WEEKLY: 1,     # Skip at least 1
        StoryTimeline.MONTHLY: 3,    # Spread out
        StoryTimeline.YEARLY: 10,    # Very spaced
    }
    
    # Cooldown broadcasts before activating new story in timeline
    COOLDOWN_BROADCASTS = {
        StoryTimeline.DAILY: 2,
        StoryTimeline.WEEKLY: 5,
        StoryTimeline.MONTHLY: 10,
        StoryTimeline.YEARLY: 20,
    }
    
    def __init__(self, story_state: StoryState):
        """
        Initialize story scheduler.
        
        Args:
            story_state: StoryState instance for persistence
        """
        self.state = story_state
        self.current_broadcast_number = 0
        self.last_beat_broadcast: Dict[StoryTimeline, int] = {
            timeline: -100 for timeline in StoryTimeline
        }
    
    def get_story_beats_for_broadcast(self) -> List[StoryBeat]:
        """
        Select story beats to include in current broadcast.
        
        Returns:
            List of StoryBeat objects for this broadcast
        """
        beats: List[StoryBeat] = []
        self.current_broadcast_number += 1
        
        # Try each timeline in order (daily first, yearly last)
        for timeline in [StoryTimeline.DAILY, StoryTimeline.WEEKLY, 
                        StoryTimeline.MONTHLY, StoryTimeline.YEARLY]:
            
            active_story = self.state.get_active_story(timeline)
            
            # Check if we should include a beat from this timeline
            if self._should_include_beat(timeline, active_story):
                beat = self._create_beat_from_story(active_story)
                if beat:
                    beats.append(beat)
                    self.last_beat_broadcast[timeline] = self.current_broadcast_number
                    
                    # Update story state
                    active_story.total_broadcasts += 1
                    active_story.broadcasts_in_current_act += 1
                    active_story.last_broadcast_at = datetime.now()
                    
                    # Update engagement
                    self._update_engagement(active_story)
                    
                    # Check if act should advance
                    if self._should_advance_act(active_story):
                        if active_story.advance_act():
                            # Still more acts
                            pass
                        else:
                            # Story complete - archive it
                            active_story.status = StoryStatus.COMPLETED
                            self.state.archive_story(active_story)
                            self.state.set_active_story(timeline, None)
            
            # Try to activate new story if slot is empty
            if not self.state.get_active_story(timeline):
                self._try_activate_story(timeline)
        
        # Update state counts
        for timeline in StoryTimeline:
            if self.state.get_active_story(timeline):
                self.state.total_broadcasts_by_timeline[timeline] += 1
        
        return beats
    
    def _should_include_beat(self, timeline: StoryTimeline, 
                            active_story: Optional[ActiveStory]) -> bool:
        """
        Determine if timeline's story should be included in this broadcast.
        
        Args:
            timeline: Timeline to check
            active_story: Currently active story (or None)
            
        Returns:
            True if beat should be included
        """
        if not active_story:
            return False
        
        # Check minimum spacing
        last_broadcast = self.last_beat_broadcast.get(timeline, -100)
        broadcasts_since = self.current_broadcast_number - last_broadcast
        if broadcasts_since < self.MIN_SPACING[timeline]:
            print(f"  [SKIP] {timeline.value}: Spacing check failed (broadcasts since last: {broadcasts_since}, min: {self.MIN_SPACING[timeline]})")
            return False
        
        # Probability-based inclusion
        roll = random.random()
        threshold = self.INCLUSION_PROBABILITY[timeline]
        if roll > threshold:
            print(f"  [ROLL] {timeline.value}: Probability check failed (roll: {roll:.2f} > {threshold})")
            return False
        
        print(f"  [OK] {timeline.value}: Beat will be included (roll: {roll:.2f} <= {threshold})")
        return True
    
    def _should_advance_act(self, active_story: ActiveStory) -> bool:
        """
        Determine if story should advance to next act.
        
        Args:
            active_story: Story to check
            
        Returns:
            True if act should advance
        """
        timeline = active_story.story.timeline
        broadcasts_in_act = active_story.broadcasts_in_current_act
        
        # Force advance if hit max
        if broadcasts_in_act >= self.MAX_BROADCASTS_PER_ACT[timeline]:
            return True
        
        # Don't advance if below minimum
        if broadcasts_in_act < self.MIN_BROADCASTS_PER_ACT[timeline]:
            return False
        
        # Probability-based advancement between min and max
        advance_probability = 0.3  # 30% chance each broadcast after minimum
        return random.random() < advance_probability
    
    def _try_activate_story(self, timeline: StoryTimeline) -> bool:
        """
        Try to activate a new story from the pool.
        
        Args:
            timeline: Timeline slot to fill
            
        Returns:
            True if story was activated
        """
        # Check cooldown
        last_activation = self.state.last_activation.get(timeline)
        if last_activation:
            broadcasts_since = self.state.total_broadcasts_by_timeline[timeline]
            # Simple approximation - in real system would track precisely
            cooldown = self.COOLDOWN_BROADCASTS[timeline]
            if broadcasts_since < cooldown:
                print(f"[COOLDOWN] Story activation blocked: {timeline.value} timeline (broadcasts since: {broadcasts_since}, cooldown: {cooldown})")
                return False
        
        # Get pool
        pool = self.state.get_pool(timeline)
        if not pool:
            print(f"[EMPTY] No stories in pool for {timeline.value} timeline")
            return False
        
        # Select story (for now, just take first)
        # TODO: Could rank by priority, engagement potential, etc.
        story = pool[0]
        
        print(f"[ACTIVATE] Story: {story.title} ({timeline.value} timeline)")
        
        # Activate it
        active_story = ActiveStory(
            story=story,
            status=StoryStatus.ACTIVE,
            current_act_index=0,
            started_at=datetime.now()
        )
        
        self.state.set_active_story(timeline, active_story)
        self.state.remove_from_pool(story.story_id, timeline)
        
        return True
    
    def _create_beat_from_story(self, active_story: ActiveStory) -> Optional[StoryBeat]:
        """
        Create a StoryBeat from current active story state.
        
        Args:
            active_story: Active story to create beat from
            
        Returns:
            StoryBeat or None
        """
        current_act = active_story.current_act
        if not current_act:
            return None
        
        beat = StoryBeat(
            story_id=active_story.story.story_id,
            timeline=active_story.story.timeline,
            act_number=current_act.act_number,
            act_type=current_act.act_type,
            beat_summary=current_act.summary,
            entities=current_act.entities,
            conflict_level=current_act.conflict_level,
            emotional_tone=current_act.emotional_tone,
            intro_suggestion=self._generate_intro_suggestion(active_story),
            outro_suggestion=self._generate_outro_suggestion(active_story)
        )
        
        return beat
    
    def _generate_intro_suggestion(self, active_story: ActiveStory) -> str:
        """Generate intro transition suggestion."""
        current_act = active_story.current_act
        if not current_act:
            return ""
        
        if active_story.broadcasts_in_current_act == 0:
            # First broadcast of this act
            if active_story.current_act_index == 0:
                return "New story beginning"
            else:
                return "Continuing our story"
        else:
            # Ongoing act
            return "As you may recall"
    
    def _generate_outro_suggestion(self, active_story: ActiveStory) -> str:
        """Generate outro transition suggestion."""
        if active_story.is_complete:
            return "And that concludes this tale"
        else:
            return "More on this later"
    
    def _update_engagement(self, active_story: ActiveStory):
        """
        Update simulated engagement score.
        
        Uses heuristics for novelty, pacing, and completion progress.
        """
        # Novelty decays with repeated broadcasts
        broadcasts = active_story.total_broadcasts
        novelty = max(0.5, 1.0 - (broadcasts * 0.05))
        
        # Variety bonus (placeholder - could check theme diversity)
        variety = 1.0
        
        # Pacing penalty (if too frequent)
        pacing = 1.0
        
        # Completion boost (stories near resolution are more engaging)
        completion = 1.0 + (active_story.progress_percentage / 200.0)
        
        # Calculate engagement
        engagement = 0.5 * novelty * variety * pacing * completion
        active_story.engagement_score = max(0.0, min(1.0, engagement))
        active_story.novelty_factor = novelty
    
    def force_complete_story(self, timeline: StoryTimeline):
        """
        Force completion of active story in timeline (for testing/admin).
        
        Args:
            timeline: Timeline slot
        """
        active_story = self.state.get_active_story(timeline)
        if active_story:
            active_story.status = StoryStatus.COMPLETED
            self.state.archive_story(active_story)
            self.state.set_active_story(timeline, None)
    
    def get_scheduler_status(self) -> Dict:
        """
        Get current scheduler status for debugging/monitoring.
        
        Returns:
            Dictionary with scheduler state
        """
        return {
            "current_broadcast": self.current_broadcast_number,
            "active_stories": {
                timeline.value: {
                    "story_id": story.story.story_id if story else None,
                    "title": story.story.title if story else None,
                    "progress": story.progress_percentage if story else 0,
                    "engagement": story.engagement_score if story else 0,
                } for timeline, story in self.state.active_stories.items()
            },
            "pool_sizes": {
                timeline.value: self.state.get_pool_size(timeline)
                for timeline in StoryTimeline
            },
            "total_active": self.state.get_total_active_stories(),
        }
