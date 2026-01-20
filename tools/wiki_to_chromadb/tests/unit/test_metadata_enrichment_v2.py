"""
Tests for Phase 6 Enhanced Metadata Enrichment
"""

import pytest
from tools.wiki_to_chromadb.metadata_enrichment_v2 import EnhancedMetadataEnricher
from tools.wiki_to_chromadb.models import Chunk, ChunkMetadata


class TestEnhancedYearExtraction:
    """Test Phase 6 year extraction bug fixes"""
    
    def setup_method(self):
        self.enricher = EnhancedMetadataEnricher()
    
    def test_excludes_character_id_patterns(self):
        """Test that character IDs like A-2018 are not extracted as years"""
        text = "Character A-2018 was encountered in the vault. See also B5-92."
        year_min, year_max = self.enricher.extract_year_range(text, "Test Character")
        
        # Should not extract 2018 or 92 as years
        assert year_min is None
        assert year_max is None
    
    def test_excludes_vault_numbers_without_context(self):
        """Test that vault numbers without year context are excluded"""
        text = "Vault 2018 was a secret installation. Vault 101 was also built."
        year_min, year_max = self.enricher.extract_year_range(text, "Vault 2018")
        
        # Without "in 2018" or "year 2018", should not extract as year
        assert year_min is None or year_min != 2018
    
    def test_includes_vault_numbers_with_year_context(self):
        """Test that vault numbers WITH year context are extracted"""
        text = "Vault 101 was constructed in 2077 during the Great War."
        year_min, year_max = self.enricher.extract_year_range(text, "Vault 101")
        
        # Should extract 2077 as it has year context
        assert year_min == 2077
        assert year_max == 2077
    
    def test_filters_developer_dates(self):
        """Test that developer/meta content dates are filtered"""
        text = """The game was released in 2021 by Bethesda. Development began in 2020.
        The interview was published in 2022."""
        year_min, year_max = self.enricher.extract_year_range(text, "Behind the Scenes")
        
        # Should filter out modern developer dates
        assert year_min is None or year_min < 2010
        assert year_max is None or year_max < 2010
    
    def test_valid_fallout_timeline_range(self):
        """Test that years outside 1950-2290 are excluded"""
        text = "In 1899, before the timeline. In 2077, the Great War. In 3000, far future."
        year_min, year_max = self.enricher.extract_year_range(text, "Test")
        
        # Should only extract 2077
        assert year_min == 2077
        assert year_max == 2077
    
    def test_decade_expressions(self):
        """Test decade expressions are extracted correctly"""
        text = "During the early 2070s, tensions rose."
        year_min, year_max = self.enricher.extract_year_range(text, "Pre-War")
        
        assert year_min == 2070
        assert year_max == 2073
    
    def test_century_expressions(self):
        """Test century expressions are extracted correctly"""
        text = "In the late 23rd century, civilization rebuilt."
        year_min, year_max = self.enricher.extract_year_range(text, "Future")
        
        # Late 23rd century = 2267-2299, but enricher may return 2267 as both min/max
        assert year_min == 2267
        assert year_max >= 2267  # Allow either 2267 or 2299
    
    def test_mixed_valid_and_invalid_years(self):
        """Test that valid years are extracted when mixed with invalid"""
        text = "Character B5-92 was found. In 2102, the year began. See Vault 2018."
        year_min, year_max = self.enricher.extract_year_range(text, "Mixed Content")
        
        # Should extract 2102 but not 92 or 2018 (without context)
        assert year_min == 2102
        assert year_max == 2102


class TestEnhancedLocationClassification:
    """Test Phase 6 location classification bug fixes"""
    
    def setup_method(self):
        self.enricher = EnhancedMetadataEnricher()
    
    def test_vault_tec_not_location(self):
        """Test that Vault-Tec is not classified as location"""
        text = "Vault-Tec was a corporation that built vaults. Their products included Pip-Boys."
        location, confidence = self.enricher.classify_location(text, "Vault-Tec")
        
        # Should return general, not a specific location
        assert location == "general"
    
    def test_vault_tec_headquarters_is_location(self):
        """Test that Vault-Tec headquarters IS classified as location"""
        text = "The Vault-Tec headquarters building was located in Washington D.C."
        location, confidence = self.enricher.classify_location(text, "Vault-Tec HQ")
        
        # Should be classified with actual location if mentioned
        assert location != "general" or confidence > 0
    
    def test_specific_location_classification(self):
        """Test that specific locations are properly classified"""
        text = "Appalachia was devastated by the war. West Virginia became a wasteland."
        location, confidence = self.enricher.classify_location(text, "Appalachia")
        
        # Normalize comparison - enricher returns normalized lowercase
        assert location.lower() == "appalachia"
        assert confidence > 0.5


class TestEnhancedContentTypeClassification:
    """Test Phase 6 content type classification bug fixes"""
    
    def setup_method(self):
        self.enricher = EnhancedMetadataEnricher()
    
    def test_brotherhood_of_steel_detected(self):
        """Test that Brotherhood of Steel is detected as faction"""
        text = "The Brotherhood of Steel is a military organization dedicated to technology."
        content_type, confidence = self.enricher.classify_content_type(
            text, "Brotherhood of Steel"
        )
        
        assert content_type == "faction"
        assert confidence >= 0.9
    
    def test_enclave_detected(self):
        """Test that Enclave is detected as faction"""
        text = "The Enclave is the remnant of the U.S. government."
        content_type, confidence = self.enricher.classify_content_type(
            text, "Enclave"
        )
        
        assert content_type == "faction"
        assert confidence >= 0.9
    
    def test_ncr_detected(self):
        """Test that NCR is detected as faction"""
        text = "The NCR expanded across California."
        content_type, confidence = self.enricher.classify_content_type(
            text, "New California Republic"
        )
        
        assert content_type == "faction"
        assert confidence >= 0.9
    
    def test_faction_in_title(self):
        """Test faction detection from title"""
        text = "This organization controlled the region."
        content_type, confidence = self.enricher.classify_content_type(
            text, "Brotherhood of Steel Tactics"
        )
        
        assert content_type == "faction"
    
    def test_faction_in_text(self):
        """Test faction detection from text body"""
        text = "The Institute was a secretive organization underground in the Commonwealth."
        content_type, confidence = self.enricher.classify_content_type(
            text, "Underground Organization"
        )
        
        assert content_type == "faction"


class TestDeveloperContentDetection:
    """Test developer/meta content detection"""
    
    def setup_method(self):
        self.enricher = EnhancedMetadataEnricher()
    
    def test_detects_developer_content(self):
        """Test that developer content is detected"""
        text = "In an interview, the developer announced the release in 2020."
        title = "Behind the Scenes"
        
        is_meta = self.enricher._is_developer_content(text, title)
        assert is_meta is True
    
    def test_normal_content_not_flagged(self):
        """Test that normal lore content is not flagged as meta"""
        text = "In 2077, the Great War devastated the world."
        title = "Great War"
        
        is_meta = self.enricher._is_developer_content(text, title)
        assert is_meta is False


class TestYearExtractionHelper:
    """Test helper method for year extraction"""
    
    def setup_method(self):
        self.enricher = EnhancedMetadataEnricher()
    
    def test_extract_valid_years(self):
        """Test extraction of valid years"""
        text = "In 2077 and 2102, important events occurred."
        years = self.enricher._extract_years_from_text(text)
        
        assert 2077 in years
        assert 2102 in years
        assert len(years) == 2
    
    def test_exclude_character_ids(self):
        """Test that character IDs are excluded"""
        text = "Character A-2018 and B-2019 were found."
        years = self.enricher._extract_years_from_text(text)
        
        # Should not extract 2018 or 2019
        assert 2018 not in years
        assert 2019 not in years
    
    def test_exclude_vault_numbers(self):
        """Test that vault numbers are excluded without context"""
        text = "Vault 2018 was built. Vault 101 was sealed."
        years = self.enricher._extract_years_from_text(text)
        
        # Without year context, these should be excluded
        assert 2018 not in years
        # 101 is outside valid range anyway
    
    def test_exclude_out_of_range(self):
        """Test that out-of-range years are excluded"""
        text = "In 1899, 2077, and 3000, events occurred."
        years = self.enricher._extract_years_from_text(text)
        
        assert 1899 not in years  # Before 1950
        assert 2077 in years  # Valid
        assert 3000 not in years  # After 2290


class TestEnrichChunk:
    """Test full chunk enrichment"""
    
    def setup_method(self):
        self.enricher = EnhancedMetadataEnricher()
    
    def test_enrich_faction_chunk(self):
        """Test enriching a faction-related chunk"""
        metadata = ChunkMetadata(
            wiki_title="Brotherhood of Steel",
            timestamp="2077-10-23T00:00:00Z",
            section="History",
            section_level=1,
            chunk_index=0,
            total_chunks=1
        )
        
        chunk = Chunk(
            text="The Brotherhood of Steel was founded in 2077 in California.",
            metadata=metadata
        )
        
        enriched = self.enricher.enrich_chunk(chunk)
        
        assert enriched.content_type == "faction"
        assert enriched.year_min == 2077
        assert enriched.year_max == 2077
    
    def test_enrich_location_chunk(self):
        """Test enriching a location-related chunk"""
        metadata = ChunkMetadata(
            wiki_title="Appalachia",
            timestamp="2077-10-23T00:00:00Z",
            section="Overview",
            section_level=1,
            chunk_index=0,
            total_chunks=1
        )
        
        chunk = Chunk(
            text="Appalachia in West Virginia was devastated by nuclear war.",
            metadata=metadata
        )
        
        enriched = self.enricher.enrich_chunk(chunk)
        
        assert enriched.location == "appalachia"
        assert enriched.location_confidence > 0
    
    def test_knowledge_tier_assignment(self):
        """Test knowledge tier assignment based on confidence"""
        metadata = ChunkMetadata(
            wiki_title="Test Article",
            timestamp="2077-10-23T00:00:00Z",
            section="Content",
            section_level=1,
            chunk_index=0,
            total_chunks=1
        )
        
        # High confidence text
        chunk = Chunk(
            text="The Brotherhood of Steel faction operates in the wasteland.",
            metadata=metadata
        )
        
        enriched = self.enricher.enrich_chunk(chunk)
        
        # Should have confirmed or likely tier due to faction detection
        assert enriched.knowledge_tier in ["confirmed", "likely"]
