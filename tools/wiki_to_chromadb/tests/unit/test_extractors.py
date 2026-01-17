"""
Unit tests for structural metadata extraction.

Tests the StructuralExtractor class with various wikitext samples.
"""

import pytest
from tools.wiki_to_chromadb.extractors import StructuralExtractor
from tools.wiki_to_chromadb.tests.fixtures.sample_data import (
    SAMPLE_WIKITEXT_VAULT_101,
    SAMPLE_WIKITEXT_SIMPLE,
    EXPECTED_CATEGORIES_VAULT_101,
    EXPECTED_SECTIONS_VAULT_101,
    EXPECTED_GAME_SOURCE_VAULT_101,
    EXPECTED_INFOBOX_TYPE_VAULT_101,
)


class TestCategoryExtraction:
    """Test category extraction from wikitext"""
    
    def test_extract_multiple_categories(self):
        """Test extracting multiple categories"""
        categories = StructuralExtractor.extract_categories(SAMPLE_WIKITEXT_VAULT_101)
        
        assert len(categories) == 3
        assert set(categories) == set(EXPECTED_CATEGORIES_VAULT_101)
    
    def test_extract_single_category(self):
        """Test extracting single category"""
        categories = StructuralExtractor.extract_categories(SAMPLE_WIKITEXT_SIMPLE)
        
        assert len(categories) == 1
        assert categories[0] == "Weapons"
    
    def test_no_categories(self):
        """Test with no categories"""
        categories = StructuralExtractor.extract_categories("No categories here")
        
        assert len(categories) == 0


class TestWikilinkExtraction:
    """Test wikilink extraction"""
    
    def test_extract_wikilinks(self):
        """Test extracting wikilinks"""
        links = StructuralExtractor.extract_wikilinks(SAMPLE_WIKITEXT_VAULT_101)
        
        assert len(links) > 0
        
        # Check for specific links
        targets = [link.target for link in links]
        assert "Vault-Tec Corporation" in targets
        assert "Great War" in targets
    
    def test_wikilink_types(self):
        """Test wikilink type classification"""
        links = StructuralExtractor.extract_wikilinks(SAMPLE_WIKITEXT_VAULT_101)
        
        # All should be internal links (no File: or Category: links)
        internal_links = [link for link in links if link.type == 'internal']
        assert len(internal_links) > 0
    
    def test_piped_links(self):
        """Test piped links [[Target|Display]]"""
        links = StructuralExtractor.extract_wikilinks(SAMPLE_WIKITEXT_VAULT_101)
        
        # Find Vault-Tec Corporation link (piped as "Vault-Tec")
        vault_tec_link = next((link for link in links if link.target == "Vault-Tec Corporation"), None)
        assert vault_tec_link is not None
        assert vault_tec_link.display == "Vault-Tec"


class TestSectionExtraction:
    """Test section hierarchy extraction"""
    
    def test_extract_sections(self):
        """Test extracting section headers"""
        sections = StructuralExtractor.extract_section_tree(SAMPLE_WIKITEXT_VAULT_101)
        
        assert len(sections) == 6
        
        # Check section titles
        titles = [s.title for s in sections]
        expected_titles = [s["title"] for s in EXPECTED_SECTIONS_VAULT_101]
        assert titles == expected_titles
    
    def test_section_levels(self):
        """Test section level detection"""
        sections = StructuralExtractor.extract_section_tree(SAMPLE_WIKITEXT_VAULT_101)
        
        # Overview should be level 1
        overview = sections[0]
        assert overview.level == 1
        assert overview.title == "Overview"
        
        # Vault Construction should be level 4
        vault_const = next((s for s in sections if s.title == "Vault Construction"), None)
        assert vault_const is not None
        assert vault_const.level == 4
    
    def test_section_path_building(self):
        """Test breadcrumb path generation"""
        sections = StructuralExtractor.extract_section_tree(SAMPLE_WIKITEXT_VAULT_101)
        
        # Find "Vault Construction" (should be under Background > Pre-War Era)
        vault_const_idx = next(
            (i for i, s in enumerate(sections) if s.title == "Vault Construction"),
            None
        )
        assert vault_const_idx is not None
        
        path = StructuralExtractor.build_section_path(sections, vault_const_idx)
        assert "Background" in path
        assert "Pre-War Era" in path
        assert "Vault Construction" in path


class TestTemplateExtraction:
    """Test template and infobox extraction"""
    
    def test_extract_infobox(self):
        """Test infobox extraction"""
        infoboxes = StructuralExtractor.extract_infoboxes(SAMPLE_WIKITEXT_VAULT_101)
        
        assert len(infoboxes) == 1
        
        infobox = infoboxes[0]
        assert infobox.type == EXPECTED_INFOBOX_TYPE_VAULT_101
        assert "name" in infobox.parameters
        assert infobox.parameters["name"] == "Vault 101"
    
    def test_extract_game_template(self):
        """Test extracting Game template"""
        templates = StructuralExtractor.extract_templates(SAMPLE_WIKITEXT_VAULT_101)
        
        # Find Game template
        game_templates = [t for t in templates if t.name.lower() in ['game', 'games']]
        assert len(game_templates) >= 1
    
    def test_game_references(self):
        """Test extracting game references"""
        games = StructuralExtractor.extract_game_references(SAMPLE_WIKITEXT_VAULT_101)
        
        assert len(games) > 0
        assert set(games) == set(EXPECTED_GAME_SOURCE_VAULT_101)
    
    def test_multiple_games(self):
        """Test extracting multiple game references"""
        games = StructuralExtractor.extract_game_references(SAMPLE_WIKITEXT_SIMPLE)
        
        assert len(games) == 2
        assert "Fallout 3" in games
        assert "Fallout 4" in games


class TestCompleteExtraction:
    """Test complete structural metadata extraction"""
    
    def test_extract_all(self):
        """Test extracting all metadata at once"""
        metadata = StructuralExtractor.extract_all(SAMPLE_WIKITEXT_VAULT_101)
        
        # Verify all fields are populated
        assert len(metadata.raw_categories) == 3
        assert len(metadata.sections) == 6
        assert len(metadata.wikilinks) > 0
        assert len(metadata.infoboxes) == 1
        assert len(metadata.game_source) == 1
    
    def test_extract_all_simple(self):
        """Test extraction on simple wikitext"""
        metadata = StructuralExtractor.extract_all(SAMPLE_WIKITEXT_SIMPLE)
        
        assert len(metadata.raw_categories) == 1
        assert len(metadata.game_source) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
