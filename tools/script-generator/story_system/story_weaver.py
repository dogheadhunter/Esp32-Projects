"""
Story Weaver

Combines story beats into broadcast-ready narrative text:
- Orders stories by timeline (daily → weekly → monthly → yearly)
- Generates intro/outro transitions
- Creates cross-timeline callbacks (20-30% probability)
- Builds context strings for LLM prompts

Uses Fichtean curve for pacing (multiple rising crises).
"""

from typing import List, Dict, Optional, Tuple
from datetime import datetime
import random

from .story_models import StoryBeat, StoryTimeline, StoryActType
from .story_state import StoryState


class StoryWeaver:
    """
    Weaves story beats into coherent broadcast narratives.
    
    Responsibilities:
    - Order beats by timeline priority
    - Generate transitions between story beats
    - Create callbacks to previously broadcast stories
    - Build context strings for LLM prompt injection
    """
    
    # Probability of callback when related stories exist
    CALLBACK_PROBABILITY = 0.25  # 25% chance
    
    # Timeline ordering priority (smaller = higher priority)
    TIMELINE_PRIORITY = {
        StoryTimeline.DAILY: 1,
        StoryTimeline.WEEKLY: 2,
        StoryTimeline.MONTHLY: 3,
        StoryTimeline.YEARLY: 4,
    }
    
    def __init__(self, story_state: StoryState):
        """
        Initialize story weaver.
        
        Args:
            story_state: StoryState instance for accessing archived stories
        """
        self.state = story_state
    
    def weave_beats(self, beats: List[StoryBeat]) -> Dict[str, any]:
        """
        Weave story beats into broadcast structure.
        
        Args:
            beats: List of StoryBeat objects for this broadcast
            
        Returns:
            Dictionary with:
            - ordered_beats: Beats sorted by timeline priority
            - intro_text: Opening transition
            - outro_text: Closing transition
            - context_for_llm: Context string for LLM prompts
            - callbacks: List of callback references
        """
        if not beats:
            return {
                "ordered_beats": [],
                "intro_text": "",
                "outro_text": "",
                "context_for_llm": "",
                "callbacks": []
            }
        
        # Order beats by timeline priority
        ordered_beats = self._order_beats(beats)
        
        # Generate intro/outro
        intro = self._generate_intro(ordered_beats)
        outro = self._generate_outro(ordered_beats)
        
        # Generate callbacks
        callbacks = self._generate_callbacks(ordered_beats)
        
        # Build LLM context string
        context = self._build_llm_context(ordered_beats, callbacks)
        
        return {
            "ordered_beats": ordered_beats,
            "intro_text": intro,
            "outro_text": outro,
            "context_for_llm": context,
            "callbacks": callbacks
        }
    
    def _order_beats(self, beats: List[StoryBeat]) -> List[StoryBeat]:
        """
        Order beats by timeline priority (daily first, yearly last).
        
        Args:
            beats: Unordered list of beats
            
        Returns:
            Sorted list of beats
        """
        return sorted(beats, key=lambda b: self.TIMELINE_PRIORITY[b.timeline])
    
    def _generate_intro(self, beats: List[StoryBeat]) -> str:
        """
        Generate opening transition text.
        
        Args:
            beats: Ordered list of beats
            
        Returns:
            Intro text for DJ to use
        """
        if not beats:
            return ""
        
        # Count stories by type
        count = len(beats)
        has_climax = any(b.act_type == StoryActType.CLIMAX for b in beats)
        
        if count == 1:
            beat = beats[0]
            if has_climax:
                return f"[STORY INTRO: Major development in story {beat.story_id}]"
            else:
                return f"[STORY INTRO: Update on story {beat.story_id}]"
        else:
            if has_climax:
                return f"[STORY INTRO: {count} stories today, including some major developments]"
            else:
                return f"[STORY INTRO: {count} stories from across the wasteland]"
    
    def _generate_outro(self, beats: List[StoryBeat]) -> str:
        """
        Generate closing transition text.
        
        Args:
            beats: Ordered list of beats
            
        Returns:
            Outro text for DJ to use
        """
        if not beats:
            return ""
        
        count = len(beats)
        if count == 1:
            return "[STORY OUTRO: More on this as it develops]"
        else:
            return f"[STORY OUTRO: That's {count} stories for now, stay tuned for more]"
    
    def _generate_callbacks(self, beats: List[StoryBeat]) -> List[Dict[str, str]]:
        """
        Generate callbacks to related archived stories.
        
        Callbacks reference shared entities, themes, or locations from
        previously broadcast stories. 20-30% probability when related.
        
        Args:
            beats: Current beats being broadcast
            
        Returns:
            List of callback dictionaries with story_id, reference_text, relationship
        """
        callbacks = []
        
        for beat in beats:
            # Check if we should generate a callback
            if random.random() > self.CALLBACK_PROBABILITY:
                continue
            
            # Find related archived stories
            related = self._find_related_archived_stories(beat)
            
            if related:
                # Pick one random related story
                archived_story = random.choice(related)
                callback = self._create_callback(beat, archived_story)
                if callback:
                    callbacks.append(callback)
        
        return callbacks
    
    def _find_related_archived_stories(self, beat: StoryBeat) -> List[Dict[str, any]]:
        """
        Find archived stories related to current beat.
        
        Related means sharing:
        - Same entities (characters, factions, locations)
        - Same timeline (for thematic coherence)
        
        Args:
            beat: Current story beat
            
        Returns:
            List of related archived stories
        """
        related = []
        
        for archived in self.state.archived_stories:
            story = archived.story
            
            # Check for shared entities
            shared_entities = set(beat.entities) & set(story.characters + story.locations + story.factions)
            
            # Check for shared themes (if story has themes)
            shared_themes = set(story.themes) if hasattr(story, 'themes') else set()
            
            # Check for same timeline (stories at similar scale)
            same_timeline = story.timeline == beat.timeline
            
            # Related if any overlap
            if shared_entities or same_timeline:
                related.append({
                    "archived_story": archived,
                    "shared_entities": list(shared_entities),
                    "shared_themes": list(shared_themes),
                    "same_timeline": same_timeline
                })
        
        return related
    
    def _create_callback(self, beat: StoryBeat, related: Dict[str, any]) -> Optional[Dict[str, str]]:
        """
        Create callback reference text.
        
        Args:
            beat: Current beat
            related: Related archived story info
            
        Returns:
            Callback dictionary or None
        """
        archived = related["archived_story"]
        story = archived.story
        
        # Determine relationship type
        if related["shared_entities"]:
            entity = related["shared_entities"][0]
            relationship = f"entity:{entity}"
            reference = f"Remember the {story.title}? {entity} is involved in this new situation."
        elif related["shared_themes"]:
            theme = related["shared_themes"][0]
            relationship = f"theme:{theme}"
            reference = f"This reminds me of the {story.title} - same kind of {theme} situation."
        elif related["same_timeline"]:
            timeline_str = story.timeline if isinstance(story.timeline, str) else story.timeline.value
            relationship = f"timeline:{timeline_str}"
            reference = f"Another {timeline_str} story, just like the {story.title}."
        else:
            return None
        
        return {
            "story_id": story.story_id,
            "story_title": story.title,
            "reference_text": reference,
            "relationship": relationship
        }
    
    def _build_llm_context(self, beats: List[StoryBeat], callbacks: List[Dict[str, str]]) -> str:
        """
        Build context string for LLM prompt injection.
        
        This provides the LLM with story information to incorporate
        naturally into the broadcast script.
        
        Args:
            beats: Ordered story beats
            callbacks: Generated callbacks
            
        Returns:
            Context string for LLM prompt
        """
        if not beats and not callbacks:
            return ""
        
        context_parts = []
        
        # Add story beats context
        if beats:
            context_parts.append("STORY BEATS FOR THIS BROADCAST:")
            for i, beat in enumerate(beats, 1):
                # Handle enum or string timeline
                timeline_str = beat.timeline if isinstance(beat.timeline, str) else beat.timeline.value
                act_type_str = beat.act_type if isinstance(beat.act_type, str) else beat.act_type.value
                
                context_parts.append(f"\n{i}. Story {beat.story_id} ({timeline_str}, Act {beat.act_number})")
                context_parts.append(f"   Type: {act_type_str}")
                context_parts.append(f"   Summary: {beat.beat_summary}")
                
                if beat.entities:
                    context_parts.append(f"   Entities: {', '.join(beat.entities[:3])}")
                
                context_parts.append(f"   Tone: {beat.emotional_tone}, Conflict: {beat.conflict_level:.1f}/1.0")
        
        # Add callbacks context
        if callbacks:
            context_parts.append("\n\nCALLBACKS TO PREVIOUS STORIES:")
            for cb in callbacks:
                context_parts.append(f"\n- {cb['reference_text']}")
        
        # Add usage instructions
        context_parts.append("\n\nDIRECTIONS:")
        context_parts.append("- Weave these stories naturally into your broadcast segments")
        context_parts.append("- Maintain your DJ personality while delivering the story content")
        context_parts.append("- Use callbacks to create continuity with previous broadcasts")
        context_parts.append("- Respect the emotional tone and conflict level of each beat")
        
        return "\n".join(context_parts)
    
    def get_story_summary(self, beats: List[StoryBeat]) -> str:
        """
        Get brief summary of stories for logging/debugging.
        
        Args:
            beats: Story beats
            
        Returns:
            Brief summary string
        """
        if not beats:
            return "No stories"
        
        summaries = []
        for beat in beats:
            timeline_str = beat.timeline if isinstance(beat.timeline, str) else beat.timeline.value
            summaries.append(f"Story {beat.story_id} ({timeline_str})")
        
        return " | ".join(summaries)
