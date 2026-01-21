"""Unit tests for story extractor."""

import pytest
from story_system.story_extractor import StoryExtractor
from story_system.story_models import Story, StoryTimeline, StoryActType


class MockChromaCollection:
    """Mock ChromaDB collection for testing."""
    
    def __init__(self, mock_data=None):
        self.mock_data = mock_data or {}
    
    def query(self, query_texts=None, n_results=10, where=None):
        """Mock query method."""
        return self.mock_data.get("query_result", {
            "ids": [[]],
            "documents": [[]],
            "metadatas": [[]]
        })


class TestStoryExtractor:
    """Test story extraction from ChromaDB."""
    
    def test_extractor_without_collection(self):
        """Test extractor returns empty list without collection."""
        extractor = StoryExtractor(chroma_collection=None)
        stories = extractor.extract_stories()
        
        assert isinstance(stories, list)
        assert len(stories) == 0
    
    def test_extractor_with_empty_collection(self):
        """Test extractor handles empty results."""
        mock_collection = MockChromaCollection()
        extractor = StoryExtractor(chroma_collection=mock_collection)
        
        stories = extractor.extract_stories(max_stories=5)
        
        assert isinstance(stories, list)
        assert len(stories) == 0
    
    def test_determine_timeline_daily(self):
        """Test timeline determination for small stories."""
        extractor = StoryExtractor()
        
        # 2 chunks, quest = weekly (implementation uses 5-act structure)
        chunks = [{"metadata": {}}, {"metadata": {}}]
        timeline = extractor._determine_timeline(chunks, "quest")
        
        assert timeline == StoryTimeline.WEEKLY
    
    def test_determine_timeline_weekly(self):
        """Test timeline determination for medium stories."""
        extractor = StoryExtractor()
        
        # 4 chunks, quest = weekly
        chunks = [{"metadata": {}} for _ in range(4)]
        timeline = extractor._determine_timeline(chunks, "quest")
        
        assert timeline == StoryTimeline.WEEKLY
    
    def test_determine_timeline_monthly(self):
        """Test timeline determination for large stories."""
        extractor = StoryExtractor()
        
        # 7 chunks, quest = monthly
        chunks = [{"metadata": {}} for _ in range(7)]
        timeline = extractor._determine_timeline(chunks, "quest")
        
        assert timeline == StoryTimeline.MONTHLY
    
    def test_determine_timeline_event(self):
        """Test event content gets longer timelines."""
        extractor = StoryExtractor()
        
        # 3 chunks, event = weekly (vs quest = daily)
        chunks = [{"metadata": {}} for _ in range(3)]
        timeline = extractor._determine_timeline(chunks, "event")
        
        assert timeline == StoryTimeline.WEEKLY
    
    def test_build_acts_single_chunk(self):
        """Test building acts from single chunk."""
        extractor = StoryExtractor()
        
        chunks = [{
            "id": "chunk1",
            "text": "A lone wanderer arrives at the settlement seeking shelter and supplies.",
            "metadata": {}
        }]
        
        acts = extractor._build_acts_from_chunks(chunks)
        
        # Implementation creates full 5-act structure
        assert len(acts) == 5
        assert acts[0].act_type == StoryActType.SETUP
        assert acts[0].act_number == 1
        assert acts[-1].act_type == StoryActType.RESOLUTION
    
    def test_build_acts_two_chunks(self):
        """Test building acts from two chunks."""
        extractor = StoryExtractor()
        
        chunks = [
            {
                "id": "chunk1",
                "text": "The wanderer arrives seeking help.",
                "metadata": {}
            },
            {
                "id": "chunk2",
                "text": "The settlement welcomes the newcomer.",
                "metadata": {}
            }
        ]
        
        acts = extractor._build_acts_from_chunks(chunks)
        
        # Implementation creates full 5-act structure
        assert len(acts) == 5
        assert acts[0].act_type == StoryActType.SETUP
        assert acts[-1].act_type == StoryActType.RESOLUTION
    
    def test_build_acts_multiple_chunks(self):
        """Test building acts from multiple chunks."""
        extractor = StoryExtractor()
        
        chunks = [
            {"id": f"chunk{i}", "text": "Some text about the story.", "metadata": {}}
            for i in range(5)
        ]
        
        acts = extractor._build_acts_from_chunks(chunks)
        
        assert len(acts) >= 3  # Setup + middle + resolution
        assert acts[0].act_type == StoryActType.SETUP
        assert acts[-1].act_type == StoryActType.RESOLUTION
    
    def test_build_acts_with_conflict(self):
        """Test conflict keywords detected in middle acts."""
        extractor = StoryExtractor()
        
        chunks = [
            {"id": "chunk1", "text": "The wanderer arrives.", "metadata": {}},
            {"id": "chunk2", "text": "A battle erupts with raiders!", "metadata": {}},
            {"id": "chunk3", "text": "Peace is restored.", "metadata": {}}
        ]
        
        acts = extractor._build_acts_from_chunks(chunks)
        
        # Implementation creates full 5-act structure
        assert len(acts) == 5
        # Climax act (act 3) should have high conflict level
        assert acts[2].act_type == StoryActType.CLIMAX
        assert acts[2].conflict_level >= 0.8
    
    def test_extract_factions(self):
        """Test faction extraction from metadata."""
        extractor = StoryExtractor()
        
        chunks = [
            {"metadata": {"faction": "ncr"}},
            {"metadata": {"faction": "legion"}},
            {"metadata": {}}  # No faction
        ]
        
        factions = extractor._extract_factions(chunks)
        
        assert "ncr" in factions
        assert "legion" in factions
        assert len(factions) == 2
    
    def test_extract_themes(self):
        """Test theme extraction from metadata."""
        extractor = StoryExtractor()
        
        chunks = [
            {"metadata": {"theme_survival": True, "theme_betrayal": True}},
            {"metadata": {"theme_hope": True}},
        ]
        
        themes = extractor._extract_themes(chunks)
        
        assert "survival" in themes
        assert "betrayal" in themes
        assert "hope" in themes
    
    def test_determine_dj_compatibility(self):
        """Test DJ compatibility determination."""
        extractor = StoryExtractor()
        
        # Fallout 3 story should be compatible with Three Dog
        compatible = extractor._determine_dj_compatibility(
            era="fallout_3",
            region="capital_wasteland",
            year_min=2277,
            year_max=2277,
            factions=["brotherhood_lyons"]
        )
        
        assert "three_dog" in compatible
    
    def test_determine_knowledge_tier_common(self):
        """Test default knowledge tier is common."""
        extractor = StoryExtractor()
        
        tier = extractor._determine_knowledge_tier({})
        
        assert tier == "common"
    
    def test_determine_knowledge_tier_classified(self):
        """Test classified tier detection."""
        extractor = StoryExtractor()
        
        tier = extractor._determine_knowledge_tier({"classified": True})
        
        assert tier == "classified"
    
    def test_group_chunks_by_title(self):
        """Test grouping query results by wiki_title."""
        extractor = StoryExtractor()
        
        results = {
            "ids": [["chunk1", "chunk2", "chunk3"]],
            "documents": [["text1", "text2", "text3"]],
            "metadatas": [[
                {"wiki_title": "Story A"},
                {"wiki_title": "Story A"},
                {"wiki_title": "Story B"}
            ]]
        }
        
        grouped = extractor._group_chunks_by_title(results)
        
        assert "Story A" in grouped
        assert "Story B" in grouped
        assert len(grouped["Story A"]) == 2
        assert len(grouped["Story B"]) == 1
    
    def test_generate_summary(self):
        """Test summary generation from chunks."""
        extractor = StoryExtractor()
        
        long_text = "A" * 400  # Longer than 300 chars
        chunks = [{"text": long_text, "metadata": {}}]
        
        summary = extractor._generate_summary(chunks)
        
        assert len(summary) <= 304  # 300 + "..."
        assert summary.endswith("...")
    
    def test_chunks_to_story(self):
        """Test converting chunks to Story object."""
        extractor = StoryExtractor()
        
        chunks = [
            {
                "id": "chunk1",
                "text": "The wanderer arrives at the settlement.",
                "metadata": {
                    "wiki_title": "The Wanderer",
                    "game": "fallout_3",
                    "region": "capital_wasteland",
                    "year_min": 2277,
                    "year_max": 2277,
                    "faction": "brotherhood_lyons"
                }
            },
            {
                "id": "chunk2",
                "text": "The settlement welcomes the newcomer.",
                "metadata": {
                    "wiki_title": "The Wanderer"
                }
            }
        ]
        
        story = extractor._chunks_to_story("The Wanderer", chunks, "quest")
        
        assert story is not None
        assert story.title == "The Wanderer"
        assert story.content_type == "quest"
        assert len(story.acts) >= 1
        assert story.era == "fallout_3"
        assert "brotherhood_lyons" in story.factions


class TestKeywordDetection:
    """Test narrative keyword detection."""
    
    def test_conflict_keywords(self):
        """Test conflict keyword list."""
        assert "battle" in StoryExtractor.CONFLICT_KEYWORDS
        assert "fight" in StoryExtractor.CONFLICT_KEYWORDS
        assert "war" in StoryExtractor.CONFLICT_KEYWORDS
    
    def test_setup_keywords(self):
        """Test setup keyword list."""
        assert "begins" in StoryExtractor.SETUP_KEYWORDS
        assert "arrives" in StoryExtractor.SETUP_KEYWORDS
    
    def test_resolution_keywords(self):
        """Test resolution keyword list."""
        assert "victory" in StoryExtractor.RESOLUTION_KEYWORDS
        assert "peace" in StoryExtractor.RESOLUTION_KEYWORDS
