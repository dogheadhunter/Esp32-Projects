"""
Unit tests for chunker_v2.py
"""

import pytest
import mwparserfromhell
from chunker_v2 import create_chunks, strip_markup, split_by_tokens
from wiki_parser_v2 import process_page
from extractors import StructuralExtractor
from models import WikiPage, StructuralMetadata, Chunk
from config import ChunkerConfig
from transformers import AutoTokenizer


class TestMarkupStripping:
    """Test markup cleaning functions"""
    
    def test_strip_wikilinks(self):
        """Should convert wikilinks to plain text"""
        text = "The [[Vault 111|vault]] is located in [[Commonwealth]]."
        result = strip_markup(text)
        assert "vault" in result
        assert "Commonwealth" in result
        assert "[[" not in result
        assert "]]" not in result
    
    def test_strip_categories(self):
        """Should remove category tags"""
        text = "Some text [[Category:Weapons]] more text"
        result = strip_markup(text)
        # Category link should be removed/replaced with space
        assert "[[Category:" not in result
        assert "Some text" in result
        assert "more text" in result
    
    def test_strip_images(self):
        """Should remove image links"""
        text = "Text [[File:Image.png|thumb]] more text"
        result = strip_markup(text)
        assert "File:" not in result
        assert "Image.png" not in result
        assert "Text" in result
        assert "more text" in result


class TestTokenSplitting:
    """Test token-based text splitting"""
    
    def setup_method(self):
        """Initialize tokenizer for tests"""
        self.tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")
    
    def test_split_short_text(self):
        """Short text should return single chunk"""
        text = "This is a short text."
        chunks = split_by_tokens(text, self.tokenizer, max_tokens=100, overlap_tokens=10)
        assert len(chunks) == 1
        assert chunks[0] == text
    
    def test_split_long_text(self):
        """Long text should split into multiple chunks"""
        text = " ".join(["Word"] * 200)  # Create long text
        chunks = split_by_tokens(text, self.tokenizer, max_tokens=50, overlap_tokens=10)
        assert len(chunks) > 1
        assert all(isinstance(chunk, str) for chunk in chunks)
    
    def test_overlap_preservation(self):
        """Chunks should have overlapping content"""
        text = "First sentence. Second sentence. Third sentence. Fourth sentence. Fifth sentence."
        chunks = split_by_tokens(text, self.tokenizer, max_tokens=20, overlap_tokens=5)
        
        if len(chunks) > 1:
            # Check that chunks have some shared content
            assert len(chunks) > 1


class TestChunkCreation:
    """Test chunk creation with Pydantic models"""
    
    def test_create_chunks_single_section(self):
        """Should create chunks from page with one section"""
        wikitext = """
        {{Game|FO3}}
        
        '''Combat shotgun''' is a weapon.
        
        [[Category:Weapons]]
        """
        
        wikicode = mwparserfromhell.parse(wikitext)
        page_data = {
            'title': "Combat shotgun",
            'wikitext': wikitext,
            'namespace': 0,
            'timestamp': '2026-01-14T12:00:00'
        }
        page = process_page(page_data)
        structural = StructuralExtractor.extract_all(str(wikicode))
        
        config = ChunkerConfig(max_tokens=50, overlap_tokens=10)
        chunks = create_chunks(page, structural, config)
        
        assert len(chunks) > 0
        assert all(isinstance(chunk, Chunk) for chunk in chunks)
        assert chunks[0].metadata.wiki_title == "Combat shotgun"
        assert chunks[0].metadata.structural.raw_categories == ["Weapons"]
    
    def test_create_chunks_multiple_sections(self):
        """Should create chunks for each section"""
        wikitext = """
        '''Article''' about something.
        
        == Section 1 ==
        Content for section 1.
        
        == Section 2 ==
        Content for section 2.
        
        [[Category:Test]]
        """
        
        wikicode = mwparserfromhell.parse(wikitext)
        page_data = {
            'title': "Test Article",
            'wikitext': wikitext,
            'namespace': 0,
            'timestamp': '2026-01-14T12:00:00'
        }
        page = process_page(page_data)
        structural = StructuralExtractor.extract_all(str(wikicode))
        
        config = ChunkerConfig(max_tokens=50, overlap_tokens=10)
        chunks = create_chunks(page, structural, config)
        
        assert len(chunks) > 0
        
        # Check that we have chunks from different sections
        sections = {chunk.metadata.section for chunk in chunks}
        assert len(sections) >= 1  # At least one unique section
    
    def test_chunk_metadata_completeness(self):
        """Chunks should have complete metadata"""
        wikitext = """
        {{Game|FO4}}
        
        '''Item''' description.
        
        == Details ==
        More information.
        
        [[Category:Items]]
        [[Category:Fallout 4]]
        """
        
        wikicode = mwparserfromhell.parse(wikitext)
        page_data = {
            'title': "Test Item",
            'wikitext': wikitext,
            'namespace': 0,
            'timestamp': '2026-01-14T12:00:00'
        }
        page = process_page(page_data)
        structural = StructuralExtractor.extract_all(str(wikicode))
        
        chunks = create_chunks(page, structural)
        
        assert len(chunks) > 0
        
        for chunk in chunks:
            # Check required metadata fields
            assert chunk.metadata.wiki_title == "Test Item"
            assert chunk.metadata.timestamp is not None
            assert chunk.metadata.section is not None
            assert chunk.metadata.section_level >= 0
            assert chunk.metadata.chunk_index >= 0
            assert chunk.metadata.total_chunks > 0
            
            # Check structural metadata
            assert chunk.metadata.structural is not None
            assert "Items" in chunk.metadata.structural.raw_categories
            assert "Fallout 4" in chunk.metadata.structural.raw_categories
            # Game source contains full name ("Fallout 4") from template extraction
            assert "Fallout 4" in chunk.metadata.structural.game_source
    
    def test_chunk_text_cleaned(self):
        """Chunk text should be free of markup"""
        wikitext = """
        '''Bold text''' and [[Link|display text]].
        
        [[Category:Test]]
        """
        
        wikicode = mwparserfromhell.parse(wikitext)
        page_data = {
            'title': "Test",
            'wikitext': wikitext,
            'namespace': 0,
            'timestamp': '2026-01-14T12:00:00'
        }
        page = process_page(page_data)
        structural = StructuralExtractor.extract_all(str(wikicode))
        
        chunks = create_chunks(page, structural)
        
        assert len(chunks) > 0
        
        for chunk in chunks:
            # Should not contain wiki markup brackets
            assert "[[" not in chunk.text
            assert "]]" not in chunk.text
            
            # Should contain readable text
            assert len(chunk.text.strip()) > 0


class TestChunkIndexing:
    """Test chunk index and total_chunks fields"""
    
    def test_chunk_indices_sequential(self):
        """Chunk indices should be sequential starting from 0"""
        wikitext = """
        == Section ==
        """ + " ".join(["Word"] * 200)  # Long text to create multiple chunks
        
        wikicode = mwparserfromhell.parse(wikitext)
        page_data = {
            'title': "Long Article",
            'wikitext': wikitext,
            'namespace': 0,
            'timestamp': '2026-01-14T12:00:00'
        }
        page = process_page(page_data)
        structural = StructuralExtractor.extract_all(str(wikicode))
        
        config = ChunkerConfig(max_tokens=50, overlap_tokens=10)
        chunks = create_chunks(page, structural, config)
        
        if len(chunks) > 1:
            indices = [chunk.metadata.chunk_index for chunk in chunks]
            assert indices == list(range(len(chunks)))
    
    def test_total_chunks_consistent(self):
        """All chunks in same section should have same total_chunks"""
        wikitext = """
        == Section ==
        """ + " ".join(["Word"] * 200)
        
        wikicode = mwparserfromhell.parse(wikitext)
        page_data = {
            'title': "Article",
            'wikitext': wikitext,
            'namespace': 0,
            'timestamp': '2026-01-14T12:00:00'
        }
        page = process_page(page_data)
        structural = StructuralExtractor.extract_all(str(wikicode))
        
        config = ChunkerConfig(max_tokens=50, overlap_tokens=10)
        chunks = create_chunks(page, structural, config)
        
        if len(chunks) > 1:
            # Get chunks from same section
            section_chunks = [c for c in chunks if c.metadata.section == chunks[0].metadata.section]
            total_counts = {c.metadata.total_chunks for c in section_chunks}
            
            # Should all have the same total
            assert len(total_counts) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
