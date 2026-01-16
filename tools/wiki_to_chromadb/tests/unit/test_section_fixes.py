"""
Unit tests for section extraction bug fixes.

Tests the fixes for:
1. Filtering decorative separator lines (====)
2. Stripping markup from section titles before matching
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from extractors import StructuralExtractor
from chunker_v2 import strip_section_title_markup


class TestDecorativeSeparatorFiltering:
    """Test that decorative separators are filtered out"""
    
    def test_filter_equals_only_sections(self):
        """Should filter out sections that are only equals signs"""
        wikitext = """
== Real Section ==
Some content

====== ===================================== ======
More content

== Another Real Section ==
"""
        sections = StructuralExtractor.extract_section_tree(wikitext)
        
        # Should only have 2 real sections, not the separator
        assert len(sections) == 2
        assert sections[0].title == "Real Section"
        assert sections[1].title == "Another Real Section"
    
    def test_mixed_decorators(self):
        """Should filter various decorator patterns"""
        wikitext = """
== Valid Section ==
===============================
==================
===== Another Valid =====
=== Third Valid ===
"""
        sections = StructuralExtractor.extract_section_tree(wikitext)
        
        # Only sections with actual text
        titles = [s.title for s in sections]
        assert "Valid Section" in titles
        assert "Another Valid" in titles
        assert "Third Valid" in titles
        assert len(sections) == 3


class TestSectionTitleMarkupStripping:
    """Test stripping wiki markup from section titles"""
    
    def test_strip_wikilinks(self):
        """Should strip [[wikilinks]] from section titles"""
        title = "[[Caravan Pack]]"
        cleaned = strip_section_title_markup(title)
        assert cleaned == "Caravan Pack"
        assert "[[" not in cleaned
    
    def test_strip_piped_wikilinks(self):
        """Should use display text from piped links"""
        title = "[[Brian Fitzgerald|Fitzgerald, B.]]"
        cleaned = strip_section_title_markup(title)
        assert cleaned == "Fitzgerald, B."
    
    def test_strip_templates(self):
        """Should strip {{templates}} from section titles"""
        title = "Items {{Icon|gun}}"
        cleaned = strip_section_title_markup(title)
        assert "Icon" not in cleaned
        assert "{{" not in cleaned
        assert "Items" in cleaned
    
    def test_wikilink_with_possessive(self):
        """Should handle possessives after wikilinks"""
        title = "[[Gristle]]'s terminal"
        cleaned = strip_section_title_markup(title)
        assert cleaned == "Gristle's terminal"
    
    def test_complex_section_title(self):
        """Should handle complex titles with multiple markup types"""
        title = "Storm_MQ02_IntroPt1 - [[Into Lands Unknown]]"
        cleaned = strip_section_title_markup(title)
        assert cleaned == "Storm_MQ02_IntroPt1 - Into Lands Unknown"
    
    def test_quote_prefix(self):
        """Should handle quote prefix in section titles"""
        title = "> [[Brian Fitzgerald|Fitzgerald, B.]]"
        cleaned = strip_section_title_markup(title)
        assert cleaned == "> Fitzgerald, B."


class TestEmptySectionHandling:
    """Test handling of sections that become empty after cleaning"""
    
    def test_section_with_only_links(self):
        """Sections containing only wikilinks should be detectable"""
        # This would be detected during chunking when section title
        # isn't found in plain text (because it becomes empty)
        wikitext = "== See Also ==\n* [[Related Page]]\n* [[Another Page]]"
        
        # The section should be extracted from raw wikitext
        sections = StructuralExtractor.extract_section_tree(wikitext)
        assert len(sections) == 1
        assert sections[0].title == "See Also"
        
        # But when cleaned, the content disappears
        from wiki_parser_v2 import clean_wikitext
        plain_text, _ = clean_wikitext(wikitext)
        
        # Section title should be in plain text
        assert "See Also" in plain_text
        # But the link content is stripped
        assert "Related Page" in plain_text or "Another Page" in plain_text


class TestRealWorldCases:
    """Test real-world problematic cases from the log"""
    
    def test_community_center_decorators(self):
        """Test the Community Center Terminal Entries case"""
        wikitext = """
== Abandoned Terminal ==
======================================
== Intra-Mail ==
======================================
"""
        sections = StructuralExtractor.extract_section_tree(wikitext)
        
        # Should only have real sections, not decorators
        titles = [s.title for s in sections]
        assert "Abandoned Terminal" in titles
        assert "Intra-Mail" in titles
        assert len(sections) == 2  # Only 2 real sections
        # Decorator lines should be filtered
        for title in titles:
            assert not all(c == '=' for c in title.strip())
    
    def test_courier_stash_wikilinks(self):
        """Test Courier's Stash section with wikilinks"""
        section_title = "[[Caravan Pack]]"
        cleaned = strip_section_title_markup(section_title)
        
        assert cleaned == "Caravan Pack"
        assert "[[" not in cleaned
    
    def test_cooper_howard_episode_links(self):
        """Test Cooper Howard episode section links"""
        titles = [
            "[[S1E1 - The End]]",
            "[[S1E2 - The Target]]",
            "[[Vault 24]]"
        ]
        
        for title in titles:
            cleaned = strip_section_title_markup(title)
            assert "[[" not in cleaned
            assert "]]" not in cleaned
            # Should preserve the actual text content
            assert len(cleaned) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
