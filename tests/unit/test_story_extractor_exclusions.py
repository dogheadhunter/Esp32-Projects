"""
Unit Tests for Phase 1B-R: ChromaDB False Positive Remediation

Tests the exclusion filters added to StoryExtractor to prevent
mechanics pages, meta content, and item pages from being extracted
as quest content.
"""

import pytest
import sys
import os

# Add paths for imports
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "tools", "script-generator"))
sys.path.insert(0, os.path.join(BASE_DIR, "tools", "wiki_to_chromadb"))

from story_system.story_extractor import StoryExtractor
from chromadb_ingest import DJ_QUERY_FILTERS


class TestExclusionPatterns:
    """Test title exclusion patterns for false positive filtering."""
    
    def setup_method(self):
        """Create StoryExtractor instance for testing."""
        self.extractor = StoryExtractor()
    
    def test_exclude_fallout_perks_page(self):
        """Test that 'Fallout 3 Perks' is excluded from quest extraction."""
        assert self.extractor._is_excluded_title("Fallout 3 Perks")
        assert self.extractor._is_excluded_title("Fallout 4 Perks")
        assert self.extractor._is_excluded_title("Fallout 76 Perks")
    
    def test_exclude_mechanics_pages(self):
        """Test that Stats/Items/Weapons/Armor pages are excluded."""
        assert self.extractor._is_excluded_title("Fallout 3 Stats")
        assert self.extractor._is_excluded_title("Fallout 4 Items")
        assert self.extractor._is_excluded_title("Fallout 76 Weapons")
        assert self.extractor._is_excluded_title("Fallout 3 Armor")
        assert self.extractor._is_excluded_title("Fallout 4 Achievements")
        assert self.extractor._is_excluded_title("Fallout 76 Quests")
    
    def test_exclude_walkthrough_pages(self):
        """Test that 'Walkthrough:' pages are excluded."""
        assert self.extractor._is_excluded_title("Walkthrough: Main Quest")
        assert self.extractor._is_excluded_title("Walkthrough: Side Quests")
    
    def test_exclude_category_pages(self):
        """Test that 'Category:' pages are excluded."""
        assert self.extractor._is_excluded_title("Category: Quests")
        assert self.extractor._is_excluded_title("Category: Fallout 3")
    
    def test_exclude_list_pages(self):
        """Test that 'List of' pages are excluded."""
        assert self.extractor._is_excluded_title("List of Fallout 3 quests")
        assert self.extractor._is_excluded_title("List of weapons")
    
    def test_exclude_template_pages(self):
        """Test that 'Template:' pages are excluded."""
        assert self.extractor._is_excluded_title("Template: Quest infobox")
    
    def test_exclude_portal_pages(self):
        """Test that 'Portal:' pages are excluded."""
        assert self.extractor._is_excluded_title("Portal: Fallout 3")
    
    def test_exclude_item_suffix_pages(self):
        """Test that pages with (perk), (weapon), (armor), (item) suffixes are excluded."""
        assert self.extractor._is_excluded_title("Bloody Mess (perk)")
        assert self.extractor._is_excluded_title("Laser Rifle (weapon)")
        assert self.extractor._is_excluded_title("Power Armor (armor)")
        assert self.extractor._is_excluded_title("Stimpak (item)")
    
    def test_valid_quest_titles_not_excluded(self):
        """Test that valid quest titles are not excluded."""
        # Real quest titles from Fallout games
        assert not self.extractor._is_excluded_title("Following in His Footsteps")
        assert not self.extractor._is_excluded_title("The Pitt")
        assert not self.extractor._is_excluded_title("Broken Steel")
        assert not self.extractor._is_excluded_title("Operation: Anchorage")
        assert not self.extractor._is_excluded_title("Mothership Zeta")
        
        # Event titles
        assert not self.extractor._is_excluded_title("Battle of Anchorage")
        assert not self.extractor._is_excluded_title("Great War")
    
    def test_edge_cases(self):
        """Test edge cases for exclusion patterns."""
        # "Fallout 3 Quests" (list page) should be excluded
        assert self.extractor._is_excluded_title("Fallout 3 Quests")
        
        # But "The Replicated Man" (actual quest) should not
        assert not self.extractor._is_excluded_title("The Replicated Man")
        
        # Empty string should not be excluded
        assert not self.extractor._is_excluded_title("")


class TestQuestFilterExclusion:
    """Test _build_quest_filter() structure (Phase 1B-R uses post-filter title exclusion)."""
    
    def setup_method(self):
        """Create StoryExtractor instance for testing."""
        self.extractor = StoryExtractor()
    
    def test_quest_filter_structure_no_dj(self):
        """Test quest filter structure without DJ filter."""
        filter_dict = self.extractor._build_quest_filter(dj_name=None)
        
        # Should be a dict with $or for quest identification
        assert "$or" in filter_dict
        assert {"infobox_type": "infobox quest"} in filter_dict["$or"]
        assert {"content_type": "quest"} in filter_dict["$or"]
        assert {"content_type": "questline"} in filter_dict["$or"]
    
    def test_quest_filter_with_dj(self):
        """Test quest filter combined with DJ filter."""
        filter_dict = self.extractor._build_quest_filter(dj_name="Julie (2102, Appalachia)")
        
        # Should be a $and combining quest filter and DJ filter
        assert "$and" in filter_dict
        assert len(filter_dict["$and"]) == 2
        
        # First element: quest filter
        quest_filter = filter_dict["$and"][0]
        assert "$or" in quest_filter
        assert {"infobox_type": "infobox quest"} in quest_filter["$or"]
        
        # Second element: DJ filter
        dj_filter = filter_dict["$and"][1]
        assert "$and" in dj_filter  # Julie's filter has $and structure
    
    def test_title_based_exclusion_works(self):
        """Test that title-based exclusion is the primary exclusion mechanism (Phase 1B-R)."""
        # The exclusion happens post-query via _is_excluded_title()
        # Not in the ChromaDB filter itself (since ChromaDB doesn't support $nor)
        
        # Verify mechanics pages are excluded by title
        assert self.extractor._is_excluded_title("Fallout 3 Perks")
        assert self.extractor._is_excluded_title("Laser Rifle (weapon)")
        
        # Verify valid quests are not excluded
        assert not self.extractor._is_excluded_title("Following in His Footsteps")
        assert not self.extractor._is_excluded_title("Battle of Anchorage")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
