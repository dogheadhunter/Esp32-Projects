"""
Escalation Engine

Transforms stories from one timeline to another (e.g., daily → weekly):
- Escalation criteria (engagement > 0.8, minimum broadcasts met)
- Story transformation (expand acts, add subplots)
- Probability calculation with faction/location bonuses
- Escalation history tracking

Escalation formula: base_prob * engagement * faction_bonus * location_bonus
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime
import random
import copy

from .story_models import (
    Story,
    StoryAct,
    ActiveStory,
    StoryTimeline,
    StoryStatus,
    StoryActType,
)
from .story_state import StoryState


class EscalationEngine:
    """
    Manages story escalation from shorter to longer timelines.
    
    Stories that perform well can escalate:
    - daily → weekly: Expand acts, add depth
    - weekly → monthly: Add subplots, complications
    - monthly → yearly: Epic scope, multiple threads
    
    Escalation is based on engagement scores and story characteristics.
    """
    
    # Minimum engagement score to consider escalation
    MIN_ENGAGEMENT_FOR_ESCALATION = 0.75
    
    # Minimum broadcasts before eligible for escalation
    MIN_BROADCASTS_FOR_ESCALATION = {
        StoryTimeline.DAILY: 2,     # Quick escalation possible
        StoryTimeline.WEEKLY: 5,    # Need more development
        StoryTimeline.MONTHLY: 15,  # Substantial investment
        StoryTimeline.YEARLY: 0,    # Cannot escalate further
    }
    
    # Base probability of escalation (before modifiers)
    BASE_ESCALATION_PROBABILITY = {
        StoryTimeline.DAILY: 0.2,    # 20% base chance
        StoryTimeline.WEEKLY: 0.15,  # 15% base chance
        StoryTimeline.MONTHLY: 0.1,  # 10% base chance
        StoryTimeline.YEARLY: 0.0,   # Cannot escalate
    }
    
    # Faction involvement bonus (multiplier)
    FACTION_BONUS = {
        "brotherhood_of_steel": 1.3,
        "ncr": 1.25,
        "caesar_legion": 1.25,
        "enclave": 1.2,
        "institute": 1.2,
        "railroad": 1.15,
        "raiders": 1.1,
        "super_mutants": 1.1,
    }
    
    # Location importance bonus (multiplier)
    LOCATION_BONUS = {
        "capital_wasteland": 1.2,
        "mojave_wasteland": 1.2,
        "commonwealth": 1.2,
        "appalachia": 1.15,
        "new_vegas": 1.25,
        "hoover_dam": 1.3,
        "diamond_city": 1.15,
    }
    
    def __init__(self, story_state: StoryState):
        """
        Initialize escalation engine.
        
        Args:
            story_state: StoryState instance for tracking escalations
        """
        self.state = story_state
        self.escalation_history: List[Dict[str, any]] = []
    
    def check_escalation(self, active_story: ActiveStory) -> bool:
        """
        Check if story should escalate to next timeline.
        
        Args:
            active_story: Currently active story
            
        Returns:
            True if story should escalate
        """
        timeline = active_story.story.timeline
        
        # Cannot escalate yearly stories
        if timeline == StoryTimeline.YEARLY:
            return False
        
        # Cannot escalate if not allowed
        if not active_story.can_escalate:
            return False
        
        # Check minimum broadcasts
        min_broadcasts = self.MIN_BROADCASTS_FOR_ESCALATION[timeline]
        if active_story.total_broadcasts < min_broadcasts:
            return False
        
        # Check minimum engagement
        if active_story.engagement_score < self.MIN_ENGAGEMENT_FOR_ESCALATION:
            return False
        
        # Calculate escalation probability
        probability = self._calculate_escalation_probability(active_story)
        
        # Roll for escalation
        return random.random() < probability
    
    def _calculate_escalation_probability(self, active_story: ActiveStory) -> float:
        """
        Calculate probability of escalation.
        
        Formula: base_prob * engagement * faction_bonus * location_bonus
        
        Args:
            active_story: Story to evaluate
            
        Returns:
            Escalation probability (0.0-1.0)
        """
        story = active_story.story
        timeline = story.timeline
        
        # Start with base probability
        prob = self.BASE_ESCALATION_PROBABILITY[timeline]
        
        # Multiply by engagement (0.75-1.0 → 1.0-1.33x multiplier)
        engagement_multiplier = active_story.engagement_score / self.MIN_ENGAGEMENT_FOR_ESCALATION
        prob *= engagement_multiplier
        
        # Apply faction bonus (highest if multiple factions)
        faction_multiplier = 1.0
        for faction in story.factions:
            faction_key = faction.lower().replace(" ", "_")
            if faction_key in self.FACTION_BONUS:
                faction_multiplier = max(faction_multiplier, self.FACTION_BONUS[faction_key])
        prob *= faction_multiplier
        
        # Apply location bonus (highest if multiple locations)
        location_multiplier = 1.0
        for location in story.locations:
            location_key = location.lower().replace(" ", "_")
            if location_key in self.LOCATION_BONUS:
                location_multiplier = max(location_multiplier, self.LOCATION_BONUS[location_key])
        prob *= location_multiplier
        
        # Cap at 0.95 (always some uncertainty)
        return min(prob, 0.95)
    
    def escalate_story(self, active_story: ActiveStory) -> Story:
        """
        Escalate story to next timeline level.
        
        Transforms story structure:
        - daily → weekly: Expand each act
        - weekly → monthly: Add subplot acts
        - monthly → yearly: Multiple story threads
        
        Args:
            active_story: Story to escalate
            
        Returns:
            New Story object for next timeline
        """
        current_timeline = active_story.story.timeline
        
        # Determine next timeline
        next_timeline = self._get_next_timeline(current_timeline)
        if not next_timeline:
            return active_story.story  # Cannot escalate
        
        # Create escalated story
        escalated = self._transform_story(active_story.story, next_timeline)
        
        # Track escalation
        self._record_escalation(active_story, escalated)
        
        return escalated
    
    def _get_next_timeline(self, current: StoryTimeline) -> Optional[StoryTimeline]:
        """Get next timeline level."""
        timeline_order = [
            StoryTimeline.DAILY,
            StoryTimeline.WEEKLY,
            StoryTimeline.MONTHLY,
            StoryTimeline.YEARLY
        ]
        
        try:
            current_index = timeline_order.index(current)
            if current_index < len(timeline_order) - 1:
                return timeline_order[current_index + 1]
        except ValueError:
            pass
        
        return None
    
    def _transform_story(self, story: Story, new_timeline: StoryTimeline) -> Story:
        """
        Transform story structure for new timeline.
        
        Args:
            story: Original story
            new_timeline: Target timeline
            
        Returns:
            Transformed story
        """
        # Deep copy story to avoid modifying original
        new_story = copy.deepcopy(story)
        
        # Update timeline
        new_story.timeline = new_timeline
        
        # Generate new story ID - handle both enum and string
        if isinstance(new_timeline, StoryTimeline):
            timeline_str = new_timeline.value
        elif hasattr(new_timeline, 'value'):
            timeline_str = new_timeline.value
        else:
            timeline_str = str(new_timeline)
        new_story.story_id = f"{story.story_id}_escalated_{timeline_str}"
        
        # Transform acts based on timeline transition
        current_timeline = story.timeline
        if isinstance(current_timeline, StoryTimeline):
            current_str = current_timeline.value
        elif hasattr(current_timeline, 'value'):
            current_str = current_timeline.value
        else:
            current_str = str(current_timeline)
        
        if current_timeline == StoryTimeline.DAILY and new_timeline == StoryTimeline.WEEKLY:
            # Expand acts: each act becomes more detailed
            new_story.acts = self._expand_acts(story.acts)
            new_story.estimated_broadcasts = len(new_story.acts) * 3
            
        elif current_timeline == StoryTimeline.WEEKLY and new_timeline == StoryTimeline.MONTHLY:
            # Add subplot acts between existing acts
            new_story.acts = self._add_subplot_acts(story.acts)
            new_story.estimated_broadcasts = len(new_story.acts) * 5
            
        elif current_timeline == StoryTimeline.MONTHLY and new_timeline == StoryTimeline.YEARLY:
            # Create epic multi-thread structure
            new_story.acts = self._create_epic_structure(story.acts)
            new_story.estimated_broadcasts = len(new_story.acts) * 10
        
        # Update metadata
        new_story.title = f"{story.title} (Extended)"
        new_story.summary = f"{story.summary} [Escalated from {current_str} to {timeline_str}]"
        
        return new_story
    
    def _expand_acts(self, acts: List[StoryAct]) -> List[StoryAct]:
        """
        Expand acts for daily → weekly escalation.
        
        Each act gets more depth and detail.
        
        Args:
            acts: Original acts
            
        Returns:
            Expanded acts
        """
        expanded = []
        
        for i, act in enumerate(acts):
            # Create expanded version
            expanded_act = copy.deepcopy(act)
            expanded_act.act_number = i + 1
            expanded_act.summary = f"{act.summary} [Expanded with more detail and character development]"
            expanded_act.conflict_level = min(act.conflict_level + 0.1, 1.0)
            expanded.append(expanded_act)
        
        return expanded
    
    def _add_subplot_acts(self, acts: List[StoryAct]) -> List[StoryAct]:
        """
        Add subplot acts for weekly → monthly escalation.
        
        Inserts subplot/complication acts between main acts.
        
        Args:
            acts: Original acts
            
        Returns:
            Acts with subplots
        """
        with_subplots = []
        
        for i, act in enumerate(acts):
            # Add main act
            main_act = copy.deepcopy(act)
            main_act.act_number = len(with_subplots) + 1
            with_subplots.append(main_act)
            
            # Add subplot act after each non-resolution act
            if act.act_type != StoryActType.RESOLUTION and i < len(acts) - 1:
                subplot = self._create_subplot_act(act, len(with_subplots) + 1)
                with_subplots.append(subplot)
        
        return with_subplots
    
    def _create_subplot_act(self, main_act: StoryAct, act_number: int) -> StoryAct:
        """Create a subplot act related to main act."""
        return StoryAct(
            act_number=act_number,
            act_type=StoryActType.RISING,  # Subplots are usually complications
            title=f"{main_act.title} - Complications",
            summary=f"Subplot complicating {main_act.title}: additional challenges and character development",
            source_chunks=main_act.source_chunks,
            entities=main_act.entities,
            themes=main_act.themes + ["complication"],
            conflict_level=min(main_act.conflict_level + 0.15, 1.0),
            emotional_tone="tense"
        )
    
    def _create_epic_structure(self, acts: List[StoryAct]) -> List[StoryAct]:
        """
        Create epic structure for monthly → yearly escalation.
        
        Multiple story threads with parallel development.
        
        Args:
            acts: Original acts
            
        Returns:
            Epic multi-thread acts
        """
        epic_acts = []
        
        # Expand each act into a mini-arc
        for i, act in enumerate(acts):
            # Main thread
            main_act = copy.deepcopy(act)
            main_act.act_number = len(epic_acts) + 1
            main_act.summary = f"Thread A: {act.summary}"
            epic_acts.append(main_act)
            
            # Parallel thread (except for setup and resolution)
            if act.act_type not in [StoryActType.SETUP, StoryActType.RESOLUTION]:
                parallel = copy.deepcopy(act)
                parallel.act_number = len(epic_acts) + 1
                parallel.title = f"{act.title} - Parallel Events"
                parallel.summary = f"Thread B: Parallel events related to {act.title}"
                parallel.themes = parallel.themes + ["parallel_story"]
                epic_acts.append(parallel)
        
        return epic_acts
    
    def _record_escalation(self, original: ActiveStory, escalated: Story):
        """
        Record escalation in history.
        
        Args:
            original: Original active story
            escalated: New escalated story
        """
        record = {
            "timestamp": datetime.now(),
            "original_id": original.story.story_id,
            "original_timeline": original.story.timeline.value if hasattr(original.story.timeline, 'value') else str(original.story.timeline),
            "escalated_id": escalated.story_id,
            "escalated_timeline": escalated.timeline.value if hasattr(escalated.timeline, 'value') else str(escalated.timeline),
            "engagement_score": original.engagement_score,
            "total_broadcasts": original.total_broadcasts
        }
        
        self.escalation_history.append(record)
    
    def get_escalation_stats(self) -> Dict[str, any]:
        """
        Get escalation statistics.
        
        Returns:
            Dictionary with escalation metrics
        """
        if not self.escalation_history:
            return {
                "total_escalations": 0,
                "by_timeline": {},
                "average_engagement": 0.0
            }
        
        by_timeline = {}
        total_engagement = 0.0
        
        for record in self.escalation_history:
            timeline_val = record["original_timeline"]
            # Handle both string and enum values
            if hasattr(timeline_val, 'value'):
                timeline = timeline_val.value
            else:
                timeline = str(timeline_val)
            by_timeline[timeline] = by_timeline.get(timeline, 0) + 1
            total_engagement += record["engagement_score"]
        
        return {
            "total_escalations": len(self.escalation_history),
            "by_timeline": by_timeline,
            "average_engagement": total_engagement / len(self.escalation_history)
        }
