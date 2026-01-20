"""
Segment Plan Module

Defines data structures for broadcast segment planning.
Used by BroadcastScheduler to create structured plans with constraints.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any


class Priority(Enum):
    """Segment priority levels."""
    CRITICAL = 1    # Emergency alerts (e.g., rad storm warning)
    REQUIRED = 2    # Fixed schedule segments (time checks, news, weather)
    FILLER = 3      # Flexible content (story, gossip)


class SegmentType(Enum):
    """Types of broadcast segments."""
    EMERGENCY_WEATHER = "emergency_weather"
    TIME_CHECK = "time_check"
    WEATHER = "weather"
    NEWS = "news"
    STORY = "story"
    GOSSIP = "gossip"
    MUSIC_INTRO = "music_intro"


@dataclass
class ValidationConstraints:
    """
    Validation constraints for segment generation.
    
    These constraints are used for both:
    1. Pre-generation: Embedded in LLM prompts to prevent issues
    2. Post-generation: Fast rule-based validation checks
    """
    
    # Temporal constraints
    max_year: Optional[int] = None
    min_year: Optional[int] = None
    
    # Spatial constraints
    allowed_regions: Optional[List[str]] = None
    forbidden_regions: Optional[List[str]] = None
    
    # Content constraints
    forbidden_topics: List[str] = field(default_factory=list)
    forbidden_factions: List[str] = field(default_factory=list)
    required_tone: Optional[str] = None
    
    # Format constraints
    max_length: Optional[int] = None
    min_length: Optional[int] = None
    required_elements: List[str] = field(default_factory=list)
    
    # DJ personality constraints
    dj_knowledge_level: Optional[str] = None  # 'limited', 'moderate', 'extensive'
    dj_personality_traits: List[str] = field(default_factory=list)
    
    def to_prompt_text(self) -> str:
        """
        Convert constraints to text for embedding in LLM prompts.
        
        Returns:
            Formatted constraint text for system prompt
        """
        lines = []
        
        if self.max_year or self.min_year:
            lines.append("TEMPORAL CONSTRAINTS:")
            if self.max_year:
                lines.append(f"  - Do NOT mention events after year {self.max_year}")
            if self.min_year:
                lines.append(f"  - Do NOT mention events before year {self.min_year}")
        
        if self.forbidden_regions:
            lines.append("SPATIAL CONSTRAINTS:")
            lines.append(f"  - Do NOT reference these regions: {', '.join(self.forbidden_regions)}")
        
        if self.allowed_regions:
            lines.append(f"  - ONLY reference these regions: {', '.join(self.allowed_regions)}")
        
        if self.forbidden_topics or self.forbidden_factions:
            lines.append("FORBIDDEN CONTENT:")
            if self.forbidden_topics:
                lines.append(f"  - Do NOT discuss: {', '.join(self.forbidden_topics)}")
            if self.forbidden_factions:
                lines.append(f"  - Do NOT mention factions: {', '.join(self.forbidden_factions)}")
        
        if self.required_tone:
            lines.append(f"TONE: Maintain a {self.required_tone} tone throughout")
        
        if self.max_length:
            lines.append(f"LENGTH: Keep under {self.max_length} characters")
        
        if self.required_elements:
            lines.append(f"REQUIRED: Must include {', '.join(self.required_elements)}")
        
        return "\n".join(lines)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'temporal': {
                'max_year': self.max_year,
                'min_year': self.min_year
            },
            'spatial': {
                'allowed_regions': self.allowed_regions,
                'forbidden_regions': self.forbidden_regions
            },
            'content': {
                'forbidden_topics': self.forbidden_topics,
                'forbidden_factions': self.forbidden_factions,
                'required_tone': self.required_tone
            },
            'format': {
                'max_length': self.max_length,
                'min_length': self.min_length,
                'required_elements': self.required_elements
            },
            'dj': {
                'knowledge_level': self.dj_knowledge_level,
                'personality_traits': self.dj_personality_traits
            }
        }


@dataclass
class SegmentPlan:
    """
    Complete plan for generating a broadcast segment.
    
    Returned by BroadcastScheduler.get_next_segment_plan() and used
    by the generation pipeline to create content with proper constraints.
    """
    
    # Core segment information
    segment_type: SegmentType
    priority: Priority
    
    # Validation constraints (for generation and validation)
    constraints: ValidationConstraints
    
    # Additional metadata for generation
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Context for this specific segment
    context: Dict[str, Any] = field(default_factory=dict)
    
    def __str__(self) -> str:
        """String representation for logging."""
        return (
            f"SegmentPlan(type={self.segment_type.value}, "
            f"priority={self.priority.name}, "
            f"metadata={self.metadata})"
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'segment_type': self.segment_type.value,
            'priority': self.priority.name,
            'constraints': self.constraints.to_dict(),
            'metadata': self.metadata,
            'context': self.context
        }
    
    def get_rag_topic(self) -> Optional[str]:
        """
        Get the RAG cache topic for this segment type.
        
        Returns:
            Topic name for RAG cache, or None if no caching needed
        """
        topic_mapping = {
            SegmentType.WEATHER: 'regional_climate',
            SegmentType.NEWS: 'current_events',
            SegmentType.GOSSIP: 'character_relationships',
            SegmentType.STORY: 'story_arc',
            SegmentType.MUSIC_INTRO: 'music_knowledge',
            SegmentType.TIME_CHECK: None,  # No RAG needed
            SegmentType.EMERGENCY_WEATHER: 'regional_climate'
        }
        return topic_mapping.get(self.segment_type)
    
    def is_required(self) -> bool:
        """Check if this is a required (non-skippable) segment."""
        return self.priority in (Priority.CRITICAL, Priority.REQUIRED)
    
    def is_emergency(self) -> bool:
        """Check if this is an emergency segment."""
        return self.priority == Priority.CRITICAL
