"""
Story Extractor

Extracts story-worthy content from ChromaDB and constructs Story objects.
Identifies quests, events, and narrative arcs from wiki content.

Uses metadata filtering and semantic analysis to find coherent narratives.
"""

from typing import List, Dict, Any, Optional
from collections import defaultdict
import re
import sys
import os

# Allow imports from script-generator and tools roots
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TOOLS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
for path in (BASE_DIR, TOOLS_DIR):
    if path not in sys.path:
        sys.path.insert(0, path)

# Add wiki_to_chromadb to path for DJ_QUERY_FILTERS
WIKI_DIR = os.path.abspath(os.path.join(TOOLS_DIR, "wiki_to_chromadb"))
if WIKI_DIR not in sys.path:
    sys.path.insert(0, WIKI_DIR)

from ollama_client import OllamaClient
from shared import project_config

try:
    from chromadb_ingest import DJ_QUERY_FILTERS
except ImportError:
    # Fallback if import fails
    DJ_QUERY_FILTERS = {
        "Julie (2102, Appalachia)": {
            "$and": [
                {"year_max": {"$lte": 2102}},
                {
                    "$or": [
                        {"location": "Appalachia"},
                        {"info_source": "vault-tec"},
                        {"knowledge_tier": "common"}
                    ]
                }
            ]
        }
    }

from .story_models import (
    Story,
    StoryAct,
    StoryTimeline,
    StoryActType,
)
from .narrative_weight import NarrativeWeightScorer


class StoryExtractor:
    """
    Extracts narratives from ChromaDB and converts to Story objects.
    
    Identifies:
    - Quests (from infobox_type and content_type metadata)
    - Events (temporal markers + conflict keywords)
    - Character arcs (character content with narrative structure)
    - Faction conflicts (faction metadata + conflict themes)
    """

    SETUP_KEYWORDS = [
        "begins",
        "starts",
        "arrives",
        "discovers",
        "finds",
        "meets",
        "introduction",
        "setup",
        "beginning",
        "first",
    ]

    CONFLICT_KEYWORDS = [
        "battle",
        "fight",
        "confrontation",
        "showdown",
        "attack",
        "raid",
        "conflict",
        "war",
        "combat",
        "struggle",
        "versus",
        "against",
    ]

    RESOLUTION_KEYWORDS = [
        "victory",
        "defeat",
        "peace",
        "ended",
        "resolved",
        "concluded",
        "aftermath",
        "outcome",
        "result",
        "consequence",
    ]

    # Phase 1B-R: Title patterns to exclude (false positives)
    QUEST_EXCLUDE_TITLE_PATTERNS = [
        r"^Fallout \d+ (Perks|Stats|Items|Weapons|Armor|Achievements|Quests)$",
        r"^Walkthrough:",
        r"^Category:",
        r"^List of",
        r"^Template:",
        r"^Portal:",
        r".*\(perk\)$",
        r".*\(weapon\)$",
        r".*\(armor\)$",
        r".*\(item\)$",
    ]

    def __init__(self, chroma_collection=None, ollama_client: Optional[OllamaClient] = None):
        """
        Initialize story extractor.

        Args:
            chroma_collection: ChromaDB collection to query (optional for testing)
            ollama_client: OllamaClient instance (optional, will create if None)
        """
        self.collection = chroma_collection
        self.ollama = ollama_client
        self.narrative_scorer = NarrativeWeightScorer()

        if self.ollama is None:
            try:
                ollama_url = project_config.OLLAMA_URL.replace("/api/generate", "")
                self.ollama = OllamaClient(base_url=ollama_url)
            except Exception as exc:  # fallback gracefully
                print(f"[WARN] Failed to initialize Ollama client: {exc}")
                self.ollama = None

    def extract_stories(
        self,
        max_stories: int = 10,
        timeline: Optional[StoryTimeline] = None,
        min_chunks: int = 3,
        max_chunks: int = 10,
        dj_name: Optional[str] = None,
    ) -> List[Story]:
        """
        Extract stories from ChromaDB.

        Args:
            max_stories: Maximum number of stories to extract
            timeline: Specific timeline to extract for (optional)
            min_chunks: Minimum chunks required for a story (phase1: raised to 5)
            max_chunks: Maximum chunks to use per story
            dj_name: DJ name for filtering (e.g., "Julie (2102, Appalachia)")
        """
        if not self.collection:
            return []

        stories: List[Story] = []

        quest_stories = self._extract_quest_stories(
            max_stories // 2, min_chunks, max_chunks, dj_name=dj_name
        )
        stories.extend(quest_stories)

        event_stories = self._extract_event_stories(
            max_stories // 2, min_chunks, max_chunks, dj_name=dj_name
        )
        stories.extend(event_stories)

        if timeline:
            stories = [story for story in stories if story.timeline == timeline]

        return stories[:max_stories]

    def _extract_quest_stories(
        self,
        max_stories: int,
        min_chunks: int,
        max_chunks: int,
        dj_name: Optional[str] = None,
    ) -> List[Story]:
        """Extract stories from quest content with optional DJ filtering."""
        try:
            # Build where filter for quests
            where_filter = self._build_quest_filter(dj_name)
            
            results = self.collection.query(
                query_texts=["quest objective reward walkthrough"],
                n_results=300,
                where=where_filter,
            )
            if not results or not results.get("ids"):
                return []

            chunks_by_title = self._group_chunks_by_title(results)
            sorted_titles = sorted(
                chunks_by_title.items(), key=lambda item: len(item[1]), reverse=True
            )

            stories: List[Story] = []
            for title, chunks in sorted_titles[: max_stories * 2]:
                # Phase 1B-R: Exclude false positive titles
                if self._is_excluded_title(title):
                    print(f"  [FILTER] Excluding non-quest page: {title}")
                    continue
                
                if len(chunks) < min_chunks:
                    continue
                story = self._chunks_to_story(title, chunks[:max_chunks], "quest")
                if story:
                    stories.append(story)
                    if len(stories) >= max_stories:
                        break
            return stories
        except Exception as exc:
            print(f"Error extracting quest stories: {exc}")
            return []

    def _extract_event_stories(
        self,
        max_stories: int,
        min_chunks: int,
        max_chunks: int,
        dj_name: Optional[str] = None,
    ) -> List[Story]:
        """Extract stories from event content with optional DJ filtering."""
        try:
            # Build where filter for events
            where_filter = self._build_event_filter(dj_name)
            
            results = self.collection.query(
                query_texts=["battle conflict war event major incident"],
                n_results=300,
                where=where_filter,
            )
            if not results or not results.get("ids"):
                return []

            chunks_by_title = self._group_chunks_by_title(results)
            sorted_titles = sorted(
                chunks_by_title.items(), key=lambda item: len(item[1]), reverse=True
            )

            stories: List[Story] = []
            for title, chunks in sorted_titles[: max_stories * 2]:
                if len(chunks) < min_chunks:
                    continue
                story = self._chunks_to_story(title, chunks[:max_chunks], "event")
                if story:
                    stories.append(story)
                    if len(stories) >= max_stories:
                        break
            return stories
        except Exception as exc:
            print(f"Error extracting event stories: {exc}")
            return []

    def _group_chunks_by_title(self, results: Dict) -> Dict[str, List[Dict]]:
        """Group query results by wiki_title."""
        chunks_by_title: Dict[str, List[Dict]] = defaultdict(list)
        if not results or "ids" not in results:
            return {}

        num_results = len(results["ids"][0]) if results.get("ids") else 0
        for idx in range(num_results):
            metadata = results.get("metadatas", [{}])[0][idx] if results.get("metadatas") else {}
            title = metadata.get("wiki_title", "unknown")
            chunk = {
                "id": results["ids"][0][idx],
                "text": results.get("documents", [[""]])[0][idx],
                "metadata": metadata,
            }
            chunks_by_title[title].append(chunk)
        return dict(chunks_by_title)

    def _build_quest_filter(self, dj_name: Optional[str]) -> Optional[Dict[str, Any]]:
        """
        Build ChromaDB where filter for quest extraction.
        
        NOTE: ChromaDB metadata filtering limited - infobox_types field exists but
        string operators ($contains) not supported. Rely on semantic search + DJ
        temporal/spatial constraints. Post-filter by title patterns.
        
        Phase 1B-R: Title-based exclusion (post-filter, see _is_excluded_title())
        
        Args:
            dj_name: DJ name (e.g., "Julie (2102, Appalachia)")
        
        Returns:
            ChromaDB where filter dict or None (DJ constraints only)
        """
        # ChromaDB doesn't support $contains for string matching
        # Quest detection relies on semantic search query
        # Return only DJ temporal/spatial constraints
        if not dj_name or dj_name not in DJ_QUERY_FILTERS:
            return None
        
        return DJ_QUERY_FILTERS[dj_name]

    def _build_event_filter(self, dj_name: Optional[str]) -> Optional[Dict[str, Any]]:
        """
        Build ChromaDB where filter for event extraction.
        
        Combines:
        - Event content type identification
        - DJ-specific temporal/spatial constraints
        
        Args:
            dj_name: DJ name (e.g., "Julie (2102, Appalachia)")
        
        Returns:
            ChromaDB where filter dict or None
        """
        # Base event filter
        event_filter = {
            "$or": [
                {"content_type": "event"},
                {"content_type": "battle"},
                {"content_type": "war"}
            ]
        }
        
        # If no DJ specified, return just event filter
        if not dj_name or dj_name not in DJ_QUERY_FILTERS:
            return event_filter
        
        # Combine with DJ filter using $and
        dj_filter = DJ_QUERY_FILTERS[dj_name]
        return {"$and": [event_filter, dj_filter]}

    def _is_excluded_title(self, title: str) -> bool:
        """
        Check if title matches exclusion patterns (Phase 1B-R).
        
        Filters out false positives like:
        - "Fallout 3 Perks" (mechanics pages)
        - "Walkthrough:" pages
        - "Category:" pages
        - Item/weapon/armor pages
        
        Args:
            title: Wiki page title
        
        Returns:
            True if title should be excluded, False otherwise
        """
        for pattern in self.QUEST_EXCLUDE_TITLE_PATTERNS:
            if re.match(pattern, title):
                return True
        return False
    def _chunks_to_story(
        self,
        title: str,
        chunks: List[Dict],
        content_type: str,
    ) -> Optional[Story]:
        """Convert chunks to a Story object."""
        if not chunks:
            return None
        try:
            metadata = chunks[0].get("metadata", {})
            acts = self._build_acts_from_chunks(chunks)
            if not acts:
                return None

            timeline = self._determine_timeline(chunks, content_type)
            summary = self._generate_summary(chunks)
            factions = self._extract_factions(chunks)
            locations = self._extract_locations(chunks)
            characters = self._extract_characters(chunks)
            themes = self._extract_themes(chunks)

            year_min = metadata.get("year_min")
            year_max = metadata.get("year_max")
            era = metadata.get("game", metadata.get("era"))
            region = metadata.get("region")

            dj_compatible = self._determine_dj_compatibility(
                era, region, year_min, year_max, factions
            )

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
                estimated_broadcasts=len(acts) * 2,
            )
            
            # Calculate narrative weight and validate timeline appropriateness
            narrative_weight = self.narrative_scorer.score_story(story)
            if not self._is_story_appropriate_for_timeline(story, narrative_weight):
                print(f"  [FILTER] Story '{title}' (weight {narrative_weight:.1f}) filtered out - inappropriate for {timeline.value} timeline")
                return None
            
            return story
        except Exception as exc:
            print(f"Error converting chunks to story: {exc}")
            return None

    def _generate_acts_with_llm(
        self, chunks: List[Dict], title: str
    ) -> Optional[List[StoryAct]]:
        """Generate a 5-act structure using LLM (phase3)."""
        if not self.ollama:
            return None

        combined_text = "\n\n".join([chunk["text"][:500] for chunk in chunks[:10]])
        if len(combined_text) > 3000:
            combined_text = combined_text[:3000] + "..."

        prompt = f"""Analyze this Fallout story and create a 5-act narrative structure.

Story Title: {title}

Story Content:
{combined_text}

Create exactly 5 acts following this structure:
1. SETUP - Introduction, characters, setting (low conflict)
2. RISING - Complications begin, tension builds (medium conflict)
3. CLIMAX - Peak conflict, major confrontation (high conflict)
4. FALLING - Consequences unfold, tension decreases (medium conflict)
5. RESOLUTION - Conclusion, outcomes (low conflict)

For each act, provide:
- Act Title (3-6 words)
- Summary (1-2 sentences describing what happens)
- Conflict Level (0.0 to 1.0)

Format your response exactly like this:
ACT 1: SETUP
Title: [title]
Summary: [summary]
Conflict: [0.0-1.0]

ACT 2: RISING
Title: [title]
Summary: [summary]
Conflict: [0.0-1.0]

[continue for all 5 acts]

Generate acts now:"""

        try:
            response = self.ollama.generate(
                model=project_config.LLM_MODEL,
                prompt=prompt,
                options={"temperature": 0.7, "top_p": 0.9, "num_predict": 1000},
                timeout=30,
            )
            acts = self._parse_llm_acts(response, chunks)
            if acts and len(acts) == 5:
                return acts
            print(f"[WARN] LLM generated {len(acts) if acts else 0} acts, expected 5")
            return None
        except Exception as exc:
            print(f"[WARN] LLM act generation failed: {exc}")
            return None

    def _parse_llm_acts(self, response: str, chunks: List[Dict]) -> List[StoryAct]:
        """Parse LLM response into StoryAct objects."""
        acts: List[StoryAct] = []
        act_sections = re.split(r"ACT \d+:", response)
        act_types = [
            StoryActType.SETUP,
            StoryActType.RISING,
            StoryActType.CLIMAX,
            StoryActType.FALLING,
            StoryActType.RESOLUTION,
        ]
        chunk_ids = [chunk["id"] for chunk in chunks]
        for idx, section in enumerate(act_sections[1:6]):
            if idx >= len(act_types):
                break
            title_match = re.search(r"Title:\s*(.+?)(?:\n|$)", section, re.IGNORECASE)
            summary_match = re.search(
                r"Summary:\s*(.+?)(?:\n|Conflict)", section, re.IGNORECASE | re.DOTALL
            )
            conflict_match = re.search(r"Conflict:\s*([\d.]+)", section, re.IGNORECASE)

            title = title_match.group(1).strip() if title_match else f"Act {idx + 1}"
            summary = summary_match.group(1).strip() if summary_match else "Story continues."
            conflict = float(conflict_match.group(1)) if conflict_match else 0.5
            conflict = max(0.0, min(1.0, conflict))

            chunks_per_act = max(1, len(chunk_ids) // 5)
            start_idx = idx * chunks_per_act
            end_idx = start_idx + chunks_per_act if idx < 4 else len(chunk_ids)
            act_chunks = chunk_ids[start_idx:end_idx]

            acts.append(
                StoryAct(
                    act_number=idx + 1,
                    act_type=act_types[idx],
                    title=title[:50],
                    summary=summary[:300],
                    source_chunks=act_chunks,
                    conflict_level=conflict,
                )
            )
        return acts

    def _build_acts_from_chunks(self, chunks: List[Dict]) -> List[StoryAct]:
        """Build story acts from chunks based on content analysis."""
        # Prefer LLM even with sparse chunks (>=3)
        if len(chunks) >= 3 and self.ollama:
            llm_acts = self._generate_acts_with_llm(
                chunks, chunks[0].get("metadata", {}).get("wiki_title", "Unknown")
            )
            if llm_acts:
                return llm_acts

        num_chunks = len(chunks)
        
        # Adaptive act generation based on chunk count
        if num_chunks == 0:
            return []
        
        # Single-chunk: One act (brief update)
        if num_chunks == 1:
            chunk = chunks[0]
            text = chunk.get("text", "No content available.")
            summary = text[:200] if len(text) >= 10 else (text + " - Brief story update.")
            if len(text) > 200:
                summary += "..."
            return [StoryAct(
                act_number=1,
                act_type=StoryActType.SETUP,
                title="Story Update",
                summary=summary,
                source_chunks=[chunk.get("id", "")],
                conflict_level=0.5,
                emotional_tone="neutral"
            )]
        
        # 2 chunks: Setup + Resolution
        if num_chunks == 2:
            chunk0_text = chunks[0].get("text", "No content available for setup.")
            chunk1_text = chunks[1].get("text", "No content available for resolution.")
            
            summary0 = chunk0_text[:200] if len(chunk0_text) >= 10 else (chunk0_text + " - Story setup.")
            summary1 = chunk1_text[:200] if len(chunk1_text) >= 10 else (chunk1_text + " - Story resolution.")
            
            if len(chunk0_text) > 200:
                summary0 += "..."
            if len(chunk1_text) > 200:
                summary1 += "..."
            
            return [
                StoryAct(
                    act_number=1,
                    act_type=StoryActType.SETUP,
                    title="Setup",
                    summary=summary0,
                    source_chunks=[chunks[0].get("id", "")],
                    conflict_level=0.3,
                    emotional_tone="neutral"
                ),
                StoryAct(
                    act_number=2,
                    act_type=StoryActType.RESOLUTION,
                    title="Resolution",
                    summary=summary1,
                    source_chunks=[chunks[1].get("id", "")],
                    conflict_level=0.6,
                    emotional_tone="neutral"
                )
            ]
        
        # 3+ chunks: Use 5-act structure
        act_types = [
            (StoryActType.SETUP, "Setup", 0.2),
            (StoryActType.RISING, "Rising Action", 0.5),
            (StoryActType.CLIMAX, "Climax", 0.8),
            (StoryActType.FALLING, "Falling Action", 0.5),
            (StoryActType.RESOLUTION, "Resolution", 0.3),
        ]

        # Map chunks across 5 acts
        acts: List[StoryAct] = []
        def chunk_for_act(i: int) -> Dict:
            # Distribute available chunks across 5 acts fairly
            if num_chunks == 3:
                return [chunks[0], chunks[1], chunks[1], chunks[2], chunks[2]][i]
            if num_chunks == 4:
                return [chunks[0], chunks[1], chunks[2], chunks[2], chunks[3]][i]
            # 5 or more: one per act then spill remaining across middle
            base = chunks[:5]
            return base[i]

        for idx, (act_type, act_title, base_conflict) in enumerate(act_types):
            ch = chunk_for_act(idx)
            text = ch.get("text", "")
            summary = text[:200] + ("..." if len(text) > 200 else "")

            adj_conflict = base_conflict
            if act_type in (StoryActType.RISING, StoryActType.CLIMAX):
                if any(kw in text.lower() for kw in self.CONFLICT_KEYWORDS):
                    adj_conflict = min(1.0, adj_conflict + 0.2)

            acts.append(StoryAct(
                act_number=idx + 1,
                act_type=act_type,
                title=act_title,
                summary=summary,
                source_chunks=[ch.get("id")] if ch.get("id") else [],
                conflict_level=adj_conflict,
            ))

        return acts

    def _determine_timeline(self, chunks: List[Dict], content_type: str) -> StoryTimeline:
        """Determine appropriate timeline scale for story."""
        num_chunks = len(chunks)
        
        # Check metadata for timeline hints
        metadata = chunks[0].get("metadata", {}) if chunks else {}
        content_type_meta = metadata.get("content_type", "")
        
        # Major events and quests tend to be longer arcs
        if "quest" in content_type.lower() or "questline" in content_type_meta.lower():
            if num_chunks >= 5:
                return StoryTimeline.MONTHLY
            if num_chunks >= 3:
                return StoryTimeline.WEEKLY
            # Even small quests can be weekly arcs
            return StoryTimeline.WEEKLY if num_chunks >= 2 else StoryTimeline.DAILY
        
        if content_type == "event":
            if num_chunks >= 5:
                return StoryTimeline.MONTHLY
            if num_chunks >= 3:
                return StoryTimeline.WEEKLY
            # Events are typically weekly unless very small
            return StoryTimeline.WEEKLY if num_chunks >= 2 else StoryTimeline.DAILY
        
        # Default progression based on chunks
        if num_chunks >= 7:
            return StoryTimeline.MONTHLY
        if num_chunks >= 4:
            return StoryTimeline.WEEKLY
        if num_chunks >= 2:
            return StoryTimeline.WEEKLY  # Favor weekly over daily
        return StoryTimeline.DAILY
    
    def _is_story_appropriate_for_timeline(self, story: Story, narrative_weight: float) -> bool:
        """
        Check if a story's narrative weight is appropriate for its assigned timeline.
        
        Thresholds adjusted based on actual score distribution:
        - Daily: 1.0 (any story)
        - Weekly: 3.0 (moderate - was 5.0)
        - Monthly: 6.0 (significant - was 7.0)
        - Yearly: 8.0 (epic - was 9.0)
        
        Previous thresholds were too aggressive and filtered out most valid stories.
        
        Args:
            story: Story object with assigned timeline
            narrative_weight: Calculated narrative weight (1.0-10.0)
        
        Returns:
            True if story meets minimum weight for timeline, False otherwise
        """
        # Minimum narrative weight requirements per timeline
        TIMELINE_MIN_WEIGHT = {
            StoryTimeline.DAILY: 1.0,    # Allow any story for daily content
            StoryTimeline.WEEKLY: 3.0,   # Moderate complexity (lowered from 5.0)
            StoryTimeline.MONTHLY: 6.0,  # Significant stories (lowered from 7.0)
            StoryTimeline.YEARLY: 8.0,   # Epic narratives (lowered from 9.0)
        }
        
        min_weight = TIMELINE_MIN_WEIGHT.get(story.timeline, 1.0)
        passes = narrative_weight >= min_weight
        
        if not passes:
            print(f"  [FILTER] '{story.title}' (weight {narrative_weight:.1f}) needs {min_weight} for {story.timeline.value}")
        
        return passes

    def _generate_summary(self, chunks: List[Dict]) -> str:
        """Generate story summary from chunks."""
        if not chunks:
            return "A story from the wasteland."
        text = chunks[0].get("text", "Story content unavailable.")
        
        # Ensure minimum length for validation
        if len(text) < 10:
            return text + " - Wasteland story."
        
        summary = text[:300]
        if len(text) > 300:
            summary += "..."
        return summary

    def _extract_factions(self, chunks: List[Dict]) -> List[str]:
        factions = set()
        for chunk in chunks:
            metadata = chunk.get("metadata", {})
            if "faction" in metadata:
                factions.add(metadata["faction"])
        return list(factions)

    def _extract_locations(self, chunks: List[Dict]) -> List[str]:
        locations = set()
        for chunk in chunks:
            metadata = chunk.get("metadata", {})
            if "location" in metadata:
                locations.add(metadata["location"])
            if "region" in metadata:
                locations.add(metadata["region"])
        return list(locations)

    def _extract_characters(self, chunks: List[Dict]) -> List[str]:
        characters = set()
        for chunk in chunks:
            metadata = chunk.get("metadata", {})
            if "character" in metadata:
                characters.add(metadata["character"])
        return list(characters)

    def _extract_themes(self, chunks: List[Dict]) -> List[str]:
        themes = set()
        for chunk in chunks:
            metadata = chunk.get("metadata", {})
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
        factions: List[str],
    ) -> List[str]:
        compatible: List[str] = []
        era_to_djs = {
            "fallout_76": ["julie"],
            "fallout_3": ["three_dog"],
            "fallout_nv": ["mr_new_vegas"],
            "fallout_4": ["travis_miles_confident"],
        }
        if era in era_to_djs:
            compatible.extend(era_to_djs[era])
        else:
            compatible = ["julie", "three_dog", "mr_new_vegas", "travis_miles_confident"]
        return compatible

    def _determine_knowledge_tier(self, metadata: Dict) -> str:
        if metadata.get("classified") or metadata.get("secret"):
            return "classified"
        if metadata.get("restricted"):
            return "restricted"
        if metadata.get("regional"):
            return "regional"
        return "common"
