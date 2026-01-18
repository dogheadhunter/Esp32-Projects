"""
Story Extractor

Extracts story-worthy content from ChromaDB and constructs Story objects.
Identifies quests, events, and narrative arcs from wiki content.

Uses metadata filtering and semantic analysis to find coherent narratives.
"""

from typing import List, Dict, Any, Optional, Set, Tuple
from collections import defaultdict
import re

from .story_models import (
    Story,
    StoryAct,
    StoryTimeline,
    StoryActType,
)


class StoryExtractor:
    """
    Extracts narratives from ChromaDB and converts to Story objects.
    
    Identifies:
    - Quests (from infobox_type and content_type metadata)
    - Events (temporal markers + conflict keywords)
    - Character arcs (character content with narrative structure)
    - Faction conflicts (faction metadata + conflict themes)
    """
    
    # Keywords for detecting narrative acts
    SETUP_KEYWORDS = [
        "begins", "starts", "arrives", "discovers", "finds", "meets",
        "introduction", "setup", "beginning", "first"
    ]
    
    CONFLICT_KEYWORDS = [
        "battle", "fight", "confrontation", "showdown", "attack", "raid",
        "conflict", "war", "combat", "struggle", "versus", "against"
    ]
    
    RESOLUTION_KEYWORDS = [
        "victory", "defeat", "peace", "ended", "resolved", "concluded",
        "aftermath", "outcome", "result", "consequence"
    ]
    
    def __init__(self, chroma_collection=None):
        """
        Initialize story extractor.
        
        Args:
            chroma_collection: ChromaDB collection to query (optional for testing)
        """
        self.collection = chroma_collection
    
    def extract_stories(
        self,
        max_stories: int = 10,
        timeline: Optional[StoryTimeline] = None,
        min_chunks: int = 2,
        max_chunks: int = 10
    ) -> List[Story]:
        """
        Extract stories from ChromaDB.
        
        Args:
            max_stories: Maximum number of stories to extract
            timeline: Specific timeline to extract for (optional)
            min_chunks: Minimum chunks required for a story
            max_chunks: Maximum chunks to use per story
            
        Returns:
            List of extracted Story objects
        """
        if not self.collection:
            return []
        
        stories = []
        
        # Extract quest-based stories
        quest_stories = self._extract_quest_stories(max_stories // 2, min_chunks, max_chunks)
        stories.extend(quest_stories)
        
        # Extract event-based stories
        event_stories = self._extract_event_stories(max_stories // 2, min_chunks, max_chunks)
        stories.extend(event_stories)
        
        # Filter by timeline if specified
        if timeline:
            stories = [s for s in stories if s.timeline == timeline]
        
        return stories[:max_stories]
    
    def _extract_quest_stories(
        self,
        max_stories: int,
        min_chunks: int,
        max_chunks: int
    ) -> List[Story]:
        """Extract stories from quest content."""
        try:
            # Query for quest content
            results = self.collection.query(
                query_texts=["quest objective reward walkthrough"],
                n_results=max_chunks * max_stories,
                where={
                    "$or": [
                        {"content_type": "quest"},
                        {"infobox_type": "infobox quest"}
                    ]
                }
            )
            
            if not results or not results.get("ids"):
                return []
            
            # Group chunks by wiki_title
            chunks_by_title = self._group_chunks_by_title(results)
            
            # Convert to stories
            stories = []
            for title, chunks in list(chunks_by_title.items())[:max_stories]:
                if len(chunks) < min_chunks:
                    continue
                
                story = self._chunks_to_story(title, chunks[:max_chunks], "quest")
                if story:
                    stories.append(story)
            
            return stories
            
        except Exception as e:
            print(f"Error extracting quest stories: {e}")
            return []
    
    def _extract_event_stories(
        self,
        max_stories: int,
        min_chunks: int,
        max_chunks: int
    ) -> List[Story]:
        """Extract stories from event content."""
        try:
            # Query for event content
            results = self.collection.query(
                query_texts=["battle conflict war event major incident"],
                n_results=max_chunks * max_stories,
                where={
                    "$or": [
                        {"content_type": "event"},
                        {"has_year": True}
                    ]
                }
            )
            
            if not results or not results.get("ids"):
                return []
            
            # Group chunks by wiki_title
            chunks_by_title = self._group_chunks_by_title(results)
            
            # Convert to stories
            stories = []
            for title, chunks in list(chunks_by_title.items())[:max_stories]:
                if len(chunks) < min_chunks:
                    continue
                
                story = self._chunks_to_story(title, chunks[:max_chunks], "event")
                if story:
                    stories.append(story)
            
            return stories
            
        except Exception as e:
            print(f"Error extracting event stories: {e}")
            return []
    
    def _group_chunks_by_title(self, results: Dict) -> Dict[str, List[Dict]]:
        """Group query results by wiki_title."""
        chunks_by_title = defaultdict(list)
        
        if not results or "ids" not in results:
            return {}
        
        num_results = len(results["ids"][0]) if results["ids"] else 0
        
        for i in range(num_results):
            metadata = results["metadatas"][0][i] if results.get("metadatas") else {}
            title = metadata.get("wiki_title", "unknown")
            
            chunk = {
                "id": results["ids"][0][i],
                "text": results["documents"][0][i] if results.get("documents") else "",
                "metadata": metadata
            }
            
            chunks_by_title[title].append(chunk)
        
        return dict(chunks_by_title)
    
    def _chunks_to_story(
        self,
        title: str,
        chunks: List[Dict],
        content_type: str
    ) -> Optional[Story]:
        """
        Convert chunks to a Story object.
        
        Args:
            title: Story title (usually wiki_title)
            chunks: List of chunk dictionaries
            content_type: Type of content (quest, event, etc.)
            
        Returns:
            Story object or None if conversion fails
        """
        if not chunks:
            return None
        
        try:
            # Extract metadata from first chunk
            metadata = chunks[0]["metadata"]
            
            # Build acts from chunks
            acts = self._build_acts_from_chunks(chunks)
            if not acts:
                return None
            
            # Determine timeline based on content length and type
            timeline = self._determine_timeline(chunks, content_type)
            
            # Extract entities and metadata
            summary = self._generate_summary(chunks)
            factions = self._extract_factions(chunks)
            locations = self._extract_locations(chunks)
            characters = self._extract_characters(chunks)
            themes = self._extract_themes(chunks)
            
            # Get temporal info
            year_min = metadata.get("year_min")
            year_max = metadata.get("year_max")
            era = metadata.get("game", metadata.get("era"))
            region = metadata.get("region")
            
            # Determine DJ compatibility
            dj_compatible = self._determine_dj_compatibility(
                era, region, year_min, year_max, factions
            )
            
            # Create story
            story = Story(
                story_id=f"story_{content_type}_{title.replace(' ', '_').lower()}",
                title=title,
                timeline=timeline,
                acts=acts,
                summary=summary,
                content_type=content_type,
                themes=themes,
                factions=factions,
                locations=locations,
                characters=characters,
                era=era,
                region=region,
                year_min=year_min,
                year_max=year_max,
                dj_compatible=dj_compatible,
                knowledge_tier=self._determine_knowledge_tier(metadata),
                source_wiki_titles=[title],
                estimated_broadcasts=len(acts) * 2  # 2 broadcasts per act on average
            )
            
            return story
            
        except Exception as e:
            print(f"Error converting chunks to story: {e}")
            return None
    
    def _build_acts_from_chunks(self, chunks: List[Dict]) -> List[StoryAct]:
        """Build story acts from chunks based on content analysis."""
        acts = []
        
        # Simple strategy: group chunks into acts
        # First chunk(s) = setup, middle = rising/climax, last = resolution
        
        num_chunks = len(chunks)
        if num_chunks == 1:
            # Single chunk story - make it a simple setup+resolution
            acts = [
                StoryAct(
                    act_number=1,
                    act_type=StoryActType.SETUP,
                    title="The Story",
                    summary=chunks[0]["text"][:200] + "...",
                    source_chunks=[chunks[0]["id"]],
                    conflict_level=0.5
                )
            ]
        elif num_chunks == 2:
            # Two chunks - setup and resolution
            acts = [
                StoryAct(
                    act_number=1,
                    act_type=StoryActType.SETUP,
                    title="Beginning",
                    summary=chunks[0]["text"][:200] + "...",
                    source_chunks=[chunks[0]["id"]],
                    conflict_level=0.3
                ),
                StoryAct(
                    act_number=2,
                    act_type=StoryActType.RESOLUTION,
                    title="Conclusion",
                    summary=chunks[1]["text"][:200] + "...",
                    source_chunks=[chunks[1]["id"]],
                    conflict_level=0.4
                )
            ]
        else:
            # Three or more chunks - full arc
            # First chunk = setup
            acts.append(StoryAct(
                act_number=1,
                act_type=StoryActType.SETUP,
                title="Setup",
                summary=chunks[0]["text"][:200] + "...",
                source_chunks=[chunks[0]["id"]],
                conflict_level=0.2
            ))
            
            # Middle chunks = rising action or climax
            middle_start = 1
            middle_end = num_chunks - 1
            for i in range(middle_start, middle_end):
                # Check if this chunk has conflict keywords
                text = chunks[i]["text"].lower()
                has_conflict = any(kw in text for kw in self.CONFLICT_KEYWORDS)
                
                act_type = StoryActType.CLIMAX if has_conflict else StoryActType.RISING
                conflict_level = 0.8 if has_conflict else 0.5
                
                acts.append(StoryAct(
                    act_number=len(acts) + 1,
                    act_type=act_type,
                    title=f"Act {len(acts) + 1}",
                    summary=chunks[i]["text"][:200] + "...",
                    source_chunks=[chunks[i]["id"]],
                    conflict_level=conflict_level
                ))
            
            # Last chunk = resolution
            acts.append(StoryAct(
                act_number=len(acts) + 1,
                act_type=StoryActType.RESOLUTION,
                title="Resolution",
                summary=chunks[-1]["text"][:200] + "...",
                source_chunks=[chunks[-1]["id"]],
                conflict_level=0.3
            ))
        
        return acts
    
    def _determine_timeline(self, chunks: List[Dict], content_type: str) -> StoryTimeline:
        """Determine appropriate timeline scale for story."""
        # Simple heuristic based on content type and chunk count
        num_chunks = len(chunks)
        
        if content_type == "event":
            # Events tend to be larger scale
            if num_chunks >= 5:
                return StoryTimeline.MONTHLY
            elif num_chunks >= 3:
                return StoryTimeline.WEEKLY
            else:
                return StoryTimeline.DAILY
        else:
            # Quests and other content
            if num_chunks >= 7:
                return StoryTimeline.MONTHLY
            elif num_chunks >= 4:
                return StoryTimeline.WEEKLY
            else:
                return StoryTimeline.DAILY
    
    def _generate_summary(self, chunks: List[Dict]) -> str:
        """Generate story summary from chunks."""
        # Use first chunk's text as summary base
        if not chunks:
            return "A story from the wasteland."
        
        text = chunks[0]["text"]
        # Take first 300 characters
        summary = text[:300]
        if len(text) > 300:
            summary += "..."
        
        return summary
    
    def _extract_factions(self, chunks: List[Dict]) -> List[str]:
        """Extract faction names from chunk metadata."""
        factions = set()
        for chunk in chunks:
            metadata = chunk.get("metadata", {})
            if "faction" in metadata:
                factions.add(metadata["faction"])
            # Could also parse from text
        return list(factions)
    
    def _extract_locations(self, chunks: List[Dict]) -> List[str]:
        """Extract location names from chunk metadata."""
        locations = set()
        for chunk in chunks:
            metadata = chunk.get("metadata", {})
            if "location" in metadata:
                locations.add(metadata["location"])
            if "region" in metadata:
                locations.add(metadata["region"])
        return list(locations)
    
    def _extract_characters(self, chunks: List[Dict]) -> List[str]:
        """Extract character names from chunk metadata."""
        characters = set()
        for chunk in chunks:
            metadata = chunk.get("metadata", {})
            if "character" in metadata:
                characters.add(metadata["character"])
        return list(characters)
    
    def _extract_themes(self, chunks: List[Dict]) -> List[str]:
        """Extract themes from chunk metadata."""
        themes = set()
        for chunk in chunks:
            metadata = chunk.get("metadata", {})
            # Look for theme_* metadata keys
            for key, value in metadata.items():
                if key.startswith("theme_") and value:
                    themes.add(key.replace("theme_", ""))
        return list(themes)
    
    def _determine_dj_compatibility(
        self,
        era: Optional[str],
        region: Optional[str],
        year_min: Optional[int],
        year_max: Optional[int],
        factions: List[str]
    ) -> List[str]:
        """Determine which DJs can broadcast this story."""
        compatible = []
        
        # Simple mapping based on era
        era_to_djs = {
            "fallout_76": ["julie"],
            "fallout_3": ["three_dog"],
            "fallout_nv": ["mr_new_vegas"],
            "fallout_4": ["travis_miles_confident"],
        }
        
        if era in era_to_djs:
            compatible.extend(era_to_djs[era])
        else:
            # Unknown era - all DJs can use (will be filtered by timeline validator)
            compatible = ["julie", "three_dog", "mr_new_vegas", "travis_miles_confident"]
        
        return compatible
    
    def _determine_knowledge_tier(self, metadata: Dict) -> str:
        """Determine knowledge access tier."""
        # Check metadata for tier hints
        if metadata.get("classified") or metadata.get("secret"):
            return "classified"
        elif metadata.get("restricted"):
            return "restricted"
        elif metadata.get("regional"):
            return "regional"
        else:
            return "common"
