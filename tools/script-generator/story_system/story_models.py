"""
Story System Pydantic Models

Defines the data structures for the multi-temporal story system:
- Story: Complete narrative with acts, timeline, and metadata
- StoryAct: Individual segments of a story (setup, rising, climax, etc.)
- ActiveStory: In-progress story tracking current state
- Enums: StoryTimeline, StoryStatus, StoryActType
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import datetime


class StoryTimeline(str, Enum):
    """Timeline scale for story duration."""
    DAILY = "daily"      # 1 day, 2-6 broadcasts
    WEEKLY = "weekly"    # 7 days, 14-42 broadcasts
    MONTHLY = "monthly"  # 30 days, 60-180 broadcasts
    YEARLY = "yearly"    # 365 days, 700-2000 broadcasts


class StoryStatus(str, Enum):
    """Current status of a story."""
    DORMANT = "dormant"          # Not yet activated
    ACTIVE = "active"            # Currently being broadcast
    CLIMAX = "climax"            # Peak tension phase
    RESOLUTION = "resolution"    # Wrapping up
    COMPLETED = "completed"      # Finished successfully
    ABANDONED = "abandoned"      # Didn't complete (2x over deadline)
    ARCHIVED = "archived"        # Available for callbacks


class StoryActType(str, Enum):
    """Type of narrative act (Freytag's pyramid)."""
    SETUP = "setup"              # Introduction, scene-setting
    RISING = "rising"            # Building tension, development
    CLIMAX = "climax"            # Peak moment, confrontation
    FALLING = "falling"          # Consequences, aftermath
    RESOLUTION = "resolution"    # Conclusion, denouement


class StoryAct(BaseModel):
    """
    Individual segment of a story.
    
    Each act is a narrative beat that can be broadcast independently
    but contributes to the overall story arc.
    """
    act_number: int = Field(..., ge=1, description="Act sequence number (1-based)")
    act_type: StoryActType = Field(..., description="Narrative function of this act")
    title: str = Field(..., min_length=1, max_length=200, description="Act title")
    summary: str = Field(..., min_length=10, description="Brief summary of act content")
    
    # Source content
    source_chunks: List[str] = Field(
        default_factory=list,
        description="ChromaDB chunk IDs used for this act"
    )
    entities: List[str] = Field(
        default_factory=list,
        description="Characters, locations, factions mentioned"
    )
    themes: List[str] = Field(
        default_factory=list,
        description="Thematic tags (e.g., survival, betrayal, hope)"
    )
    
    # Content metadata
    conflict_level: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Tension/conflict intensity (0=calm, 1=intense)"
    )
    emotional_tone: str = Field(
        default="neutral",
        description="Emotional tone (positive, neutral, negative, tense, hopeful)"
    )
    
    # Broadcast tracking
    broadcast_count: int = Field(default=0, ge=0, description="Times this act was broadcast")
    last_broadcast: Optional[datetime] = Field(default=None, description="Last broadcast timestamp")
    
    model_config = ConfigDict(use_enum_values=True)


class Story(BaseModel):
    """
    Complete narrative with acts, timeline, and metadata.
    
    Stories are extracted from ChromaDB content and scheduled across
    multiple broadcasts according to their timeline scale.
    """
    story_id: str = Field(..., description="Unique story identifier")
    title: str = Field(..., min_length=1, max_length=300, description="Story title")
    timeline: StoryTimeline = Field(..., description="Timeline scale")
    
    # Narrative structure
    acts: List[StoryAct] = Field(..., min_length=1, description="Story acts in sequence")
    summary: str = Field(..., min_length=10, description="Overall story summary")
    
    # Content classification
    content_type: str = Field(
        default="quest",
        description="Content type (quest, event, character, faction)"
    )
    themes: List[str] = Field(default_factory=list, description="Overall themes")
    factions: List[str] = Field(default_factory=list, description="Involved factions")
    locations: List[str] = Field(default_factory=list, description="Story locations")
    characters: List[str] = Field(default_factory=list, description="Named characters")
    
    # Timeline & lore metadata
    era: Optional[str] = Field(default=None, description="Game era (fallout_3, fallout_nv, etc.)")
    region: Optional[str] = Field(default=None, description="Geographic region")
    year_min: Optional[int] = Field(default=None, description="Earliest year referenced")
    year_max: Optional[int] = Field(default=None, description="Latest year referenced")
    
    # DJ compatibility
    dj_compatible: List[str] = Field(
        default_factory=list,
        description="DJs who can broadcast this story"
    )
    knowledge_tier: str = Field(
        default="common",
        description="Knowledge access level (common, regional, restricted, classified)"
    )
    suggested_framing: str = Field(
        default="direct",
        description="How DJ should present (direct, report, rumor, speculation)"
    )
    
    # Source tracking
    source_wiki_titles: List[str] = Field(
        default_factory=list,
        description="Wiki page titles used"
    )
    extraction_date: datetime = Field(
        default_factory=datetime.now,
        description="When story was extracted"
    )
    
    # Story metrics
    estimated_broadcasts: int = Field(
        default=3,
        ge=1,
        description="Expected number of broadcasts to complete"
    )
    priority: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Story priority (0=low, 1=high)"
    )
    
    @field_validator("acts")
    @classmethod
    def validate_acts(cls, v):
        """Ensure acts are numbered sequentially."""
        if not v:
            raise ValueError("Story must have at least one act")
        
        expected = 1
        for act in v:
            if act.act_number != expected:
                raise ValueError(f"Act numbers must be sequential, expected {expected}, got {act.act_number}")
            expected += 1
        
        return v
    
    model_config = ConfigDict(use_enum_values=True)


class ActiveStory(BaseModel):
    """
    In-progress story tracking current state.
    
    Wraps a Story with runtime state for scheduling and progression.
    """
    story: Story = Field(..., description="The underlying story")
    status: StoryStatus = Field(default=StoryStatus.ACTIVE, description="Current status")
    
    # Progression tracking
    current_act_index: int = Field(default=0, ge=0, description="Index of current act (0-based)")
    total_broadcasts: int = Field(default=0, ge=0, description="Total broadcasts for this story")
    broadcasts_in_current_act: int = Field(
        default=0,
        ge=0,
        description="Broadcasts of current act"
    )
    
    # Scheduling
    started_at: datetime = Field(
        default_factory=datetime.now,
        description="When story was activated"
    )
    last_broadcast_at: Optional[datetime] = Field(
        default=None,
        description="Last broadcast timestamp"
    )
    expected_completion: Optional[datetime] = Field(
        default=None,
        description="Expected completion date"
    )
    
    # Engagement tracking (simulated)
    engagement_score: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Simulated engagement score"
    )
    novelty_factor: float = Field(
        default=1.0,
        ge=0.0,
        le=1.5,
        description="Novelty multiplier (freshness)"
    )
    
    # Escalation tracking
    escalated_from: Optional[str] = Field(
        default=None,
        description="Story ID this was escalated from"
    )
    escalation_count: int = Field(default=0, ge=0, description="Times this story has escalated")
    can_escalate: bool = Field(default=True, description="Whether story can be escalated")
    
    @property
    def current_act(self) -> Optional[StoryAct]:
        """Get the current act being broadcast."""
        if 0 <= self.current_act_index < len(self.story.acts):
            return self.story.acts[self.current_act_index]
        return None
    
    @property
    def is_complete(self) -> bool:
        """Check if all acts have been broadcast."""
        return self.current_act_index >= len(self.story.acts)
    
    @property
    def progress_percentage(self) -> float:
        """Calculate story completion percentage."""
        if not self.story.acts:
            return 100.0
        return (self.current_act_index / len(self.story.acts)) * 100.0
    
    def advance_act(self) -> bool:
        """
        Advance to next act.
        
        Returns:
            True if advanced successfully, False if story was already complete
        """
        if self.is_complete:
            return False
        
        self.current_act_index += 1
        self.broadcasts_in_current_act = 0
        
        # Check if we've advanced past the end
        if self.is_complete:
            return True  # Successfully advanced to completion
        
        # Update status based on new current act type
        if self.current_act.act_type == StoryActType.CLIMAX:
            self.status = StoryStatus.CLIMAX
        elif self.current_act.act_type == StoryActType.RESOLUTION:
            self.status = StoryStatus.RESOLUTION
        
        return True
    
    model_config = ConfigDict(use_enum_values=True)


class StoryBeat(BaseModel):
    """
    Single story segment for inclusion in a broadcast.
    
    Represents one mention/development of an active story within a broadcast.
    """
    story_id: str = Field(..., description="Active story identifier")
    timeline: StoryTimeline = Field(..., description="Story timeline")
    act_number: int = Field(..., ge=1, description="Current act number")
    act_type: StoryActType = Field(..., description="Act type")
    
    # Content for broadcast
    beat_summary: str = Field(..., min_length=10, description="What happens in this beat")
    entities: List[str] = Field(default_factory=list, description="Entities mentioned")
    
    # Context for weaving
    intro_suggestion: str = Field(
        default="",
        description="Suggested intro transition"
    )
    outro_suggestion: str = Field(
        default="",
        description="Suggested outro transition"
    )
    callback_to: Optional[str] = Field(
        default=None,
        description="Story ID to reference (for callbacks)"
    )
    
    # Metadata
    conflict_level: float = Field(default=0.5, ge=0.0, le=1.0)
    emotional_tone: str = Field(default="neutral")
    
    model_config = ConfigDict(use_enum_values=True)
