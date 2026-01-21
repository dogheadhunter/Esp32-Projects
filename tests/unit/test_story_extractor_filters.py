"""
Unit Tests for Story Extractor Filters

Phase 1B: ChromaDB Metadata Filters
Tests DJ-specific temporal/regional filtering logic

Test Requirements:
- test_julie_temporal_filter: Julie only gets ≤2102 content
- test_julie_regional_filter: Julie only gets Appalachia content
- test_forbidden_factions_excluded: NCR/Legion excluded for Julie
- test_multi_layer_discovery: Fuzzy + content-based layers work
"""

import pytest
import sys
import os

# Add paths for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "tools", "script-generator"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "tools", "wiki_to_chromadb"))

from story_system.story_extractor import StoryExtractor
from chromadb_ingest import DJ_QUERY_FILTERS


class TestStoryExtractorFilters:
    """Test DJ-specific filtering logic."""
    
    def test_julie_temporal_filter(self):
        """Test that Julie only gets ≤2102 content."""
        extractor = StoryExtractor()
        dj_name = "Julie (2102, Appalachia)"
        
        # Build quest filter
        quest_filter = extractor._build_quest_filter(dj_name)
        
        # Verify filter structure
        assert quest_filter is not None
        assert "$and" in quest_filter
        
        # Extract temporal constraint
        and_conditions = quest_filter["$and"]
        assert len(and_conditions) >= 2
        
        # Find the DJ filter component
        dj_filter = DJ_QUERY_FILTERS[dj_name]
        assert dj_filter in and_conditions
        
        # Verify temporal constraint in DJ filter
        assert "$and" in dj_filter
        temporal_found = False
        for condition in dj_filter["$and"]:
            if "year_max" in condition:
                assert "$lte" in condition["year_max"]
                assert condition["year_max"]["$lte"] == 2102
                temporal_found = True
                break
        
        assert temporal_found, "Temporal constraint (year_max ≤ 2102) not found in filter"
    
    def test_julie_regional_filter(self):
        """Test that Julie only gets Appalachia content."""
        extractor = StoryExtractor()
        dj_name = "Julie (2102, Appalachia)"
        
        # Build quest filter
        quest_filter = extractor._build_quest_filter(dj_name)
        
        # Verify filter includes regional constraint
        dj_filter = DJ_QUERY_FILTERS[dj_name]
        assert "$and" in dj_filter
        
        # Find the location/region constraint
        regional_found = False
        for condition in dj_filter["$and"]:
            if "$or" in condition:
                # Check for Appalachia in the OR conditions
                or_conditions = condition["$or"]
                for or_cond in or_conditions:
                    if "location" in or_cond and or_cond["location"] == "Appalachia":
                        regional_found = True
                        break
                    if "region" in or_cond and or_cond["region"] == "Appalachia":
                        regional_found = True
                        break
        
        assert regional_found, "Regional constraint (Appalachia) not found in filter"
    
    def test_forbidden_factions_excluded(self):
        """Test that NCR/Legion are excluded for Julie (temporal constraint)."""
        extractor = StoryExtractor()
        dj_name = "Julie (2102, Appalachia)"
        
        # Get DJ filter
        dj_filter = DJ_QUERY_FILTERS[dj_name]
        
        # NCR and Legion don't exist until after 2102 (Julie's limit)
        # So the temporal filter (year_max ≤ 2102) should exclude them
        
        # Verify temporal constraint exists
        assert "$and" in dj_filter
        temporal_constraint_found = False
        
        for condition in dj_filter["$and"]:
            if "year_max" in condition:
                max_year = condition["year_max"]["$lte"]
                assert max_year == 2102
                temporal_constraint_found = True
                
                # NCR formed in 2186, Legion in 2247
                # Both are after 2102, so temporal filter excludes them
                assert max_year < 2186, "Temporal filter doesn't exclude NCR (2186+)"
                assert max_year < 2247, "Temporal filter doesn't exclude Legion (2247+)"
                break
        
        assert temporal_constraint_found, "Temporal constraint not found in DJ filter"
    
    def test_multi_layer_discovery(self):
        """Test that multi-layer quest discovery works (fuzzy + content-based)."""
        extractor = StoryExtractor()
        dj_name = "Julie (2102, Appalachia)"
        
        # Build quest filter
        quest_filter = extractor._build_quest_filter(dj_name)
        
        # Verify multi-layer discovery
        # Should have $and with quest filter + DJ filter
        assert "$and" in quest_filter
        and_conditions = quest_filter["$and"]
        
        # First condition should be the quest type filter
        quest_type_filter = and_conditions[0]
        assert "$or" in quest_type_filter
        
        # Verify multiple discovery methods
        or_conditions = quest_type_filter["$or"]
        assert len(or_conditions) >= 2, "Multi-layer discovery requires at least 2 methods"
        
        # Check for expected discovery layers
        discovery_methods = []
        for condition in or_conditions:
            if "infobox_type" in condition:
                discovery_methods.append("infobox")
            if "content_type" in condition:
                discovery_methods.append("content_type")
        
        assert "infobox" in discovery_methods, "Infobox-based discovery layer missing"
        assert "content_type" in discovery_methods, "Content-type discovery layer missing"
        
        # Verify both discovery methods are present
        assert len(discovery_methods) >= 2, f"Expected ≥2 discovery methods, found {len(discovery_methods)}"
    
    def test_no_dj_filter_fallback(self):
        """Test that extraction works without DJ filter (backwards compatibility)."""
        extractor = StoryExtractor()
        
        # Build quest filter without DJ
        quest_filter = extractor._build_quest_filter(dj_name=None)
        
        # Should return just the quest type filter
        assert quest_filter is not None
        assert "$or" in quest_filter
        
        # Should NOT have DJ temporal/regional constraints
        # (no $and wrapper with DJ filter)
        assert "$and" not in quest_filter or len(quest_filter.get("$and", [])) == 0
    
    def test_event_filter_structure(self):
        """Test that event filter has correct structure."""
        extractor = StoryExtractor()
        dj_name = "Julie (2102, Appalachia)"
        
        # Build event filter
        event_filter = extractor._build_event_filter(dj_name)
        
        # Verify structure
        assert event_filter is not None
        assert "$and" in event_filter
        
        and_conditions = event_filter["$and"]
        assert len(and_conditions) >= 2
        
        # First should be event type filter
        event_type_filter = and_conditions[0]
        assert "$or" in event_type_filter
        
        # Second should be DJ filter
        dj_filter = DJ_QUERY_FILTERS[dj_name]
        assert dj_filter in and_conditions


class TestFilterEdgeCases:
    """Test edge cases and error handling."""
    
    def test_unknown_dj_fallback(self):
        """Test that unknown DJ names fall back gracefully."""
        extractor = StoryExtractor()
        
        # Build filter with unknown DJ
        quest_filter = extractor._build_quest_filter("Unknown DJ")
        
        # Should return base quest filter without DJ constraints
        assert quest_filter is not None
        assert "$or" in quest_filter
    
    def test_empty_dj_name(self):
        """Test that empty DJ name is handled."""
        extractor = StoryExtractor()
        
        # Build filter with empty string
        quest_filter = extractor._build_quest_filter("")
        
        # Should return base quest filter
        assert quest_filter is not None
        assert "$or" in quest_filter
    
    def test_all_djs_have_filters(self):
        """Test that all DJs in DJ_QUERY_FILTERS have valid filters."""
        extractor = StoryExtractor()
        
        for dj_name in DJ_QUERY_FILTERS.keys():
            # Build quest filter
            quest_filter = extractor._build_quest_filter(dj_name)
            assert quest_filter is not None, f"Filter is None for {dj_name}"
            
            # Build event filter
            event_filter = extractor._build_event_filter(dj_name)
            assert event_filter is not None, f"Event filter is None for {dj_name}"
            
            # Verify both have $and structure (quest/event + DJ)
            assert "$and" in quest_filter, f"Quest filter missing $and for {dj_name}"
            assert "$and" in event_filter, f"Event filter missing $and for {dj_name}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
