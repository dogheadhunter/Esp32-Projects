"""
Unit tests for metadata enrichment module.
"""

import pytest
from tools.wiki_to_chromadb.metadata_enrichment import MetadataEnricher, enrich_chunks
from tools.wiki_to_chromadb.models import Chunk, ChunkMetadata, StructuralMetadata


class TestTimeClassification:
    """Test temporal classification logic"""
    
    def test_pre_war_classification(self):
        enricher = MetadataEnricher()
        text = "Vault 101 was constructed in 2063 by Vault-Tec Corporation."
        title = "Vault 101"
        
        period, confidence = enricher.classify_time_period(text, title)
        
        assert period == "pre-war"
        assert confidence > 0.0
    
    def test_post_war_classification(self):
        enricher = MetadataEnricher()
        text = "In 2277, the Lone Wanderer left the vault."
        title = "Lone Wanderer"
        
        period, confidence = enricher.classify_time_period(text, title)
        
        # Should match one of the post-war periods
        assert period in ["early-post-war", "mid-post-war", "late-post-war", "2241-2287"]
        assert confidence > 0.0
    
    def test_unknown_time_period(self):
        enricher = MetadataEnricher()
        text = "This is a generic article with no temporal references."
        title = "Generic Topic"
        
        period, confidence = enricher.classify_time_period(text, title)
        
        assert period == "unknown"
        assert confidence == 0.0
    
    def test_year_extraction_explicit(self):
        enricher = MetadataEnricher()
        text = "The event occurred between 2077 and 2087."
        
        year_min, year_max = enricher.extract_year_range(text)
        
        assert year_min == 2077
        assert year_max == 2087
    
    def test_year_extraction_decade(self):
        enricher = MetadataEnricher()
        text = "This happened in the early 2070s."
        
        year_min, year_max = enricher.extract_year_range(text)
        
        assert year_min == 2070
        assert year_max == 2073
    
    def test_year_extraction_century(self):
        enricher = MetadataEnricher()
        text = "Events of the 23rd century."
        
        year_min, year_max = enricher.extract_year_range(text)
        
        assert year_min == 2200
        assert year_max == 2299
    
    def test_no_years_found(self):
        enricher = MetadataEnricher()
        text = "A story with no dates."
        
        year_min, year_max = enricher.extract_year_range(text)
        
        assert year_min is None
        assert year_max is None


class TestLocationClassification:
    """Test spatial classification logic"""
    
    def test_west_coast_classification(self):
        enricher = MetadataEnricher()
        text = "The NCR controls much of California."
        title = "New California Republic"
        
        location, confidence = enricher.classify_location(text, title)
        
        # Actual values from constants.py are capitalized: "California", "West Coast"
        assert location in ["California", "West Coast"]
        assert confidence > 0.0
    
    def test_capital_wasteland_classification(self):
        enricher = MetadataEnricher()
        text = "Located in the ruins of Washington DC."
        title = "Rivet City"
        
        location, confidence = enricher.classify_location(text, title)
        
        # Actual value from constants.py is capitalized: "Capital Wasteland"
        assert location == "Capital Wasteland"
        assert confidence > 0.0
    
    def test_general_location_default(self):
        enricher = MetadataEnricher()
        text = "A generic location with no specific references."
        title = "Unknown Place"
        
        location, confidence = enricher.classify_location(text, title)
        
        assert location == "general"
        assert confidence == 0.0


class TestContentTypeClassification:
    """Test content type classification"""
    
    def test_character_classification(self):
        enricher = MetadataEnricher()
        text = "Born in 2220, this character became a leader."
        title = "John Doe"
        
        content_type = enricher.classify_content_type(title, text)
        
        assert content_type == "character"
    
    def test_location_classification(self):
        enricher = MetadataEnricher()
        text = "A settlement built inside an old vault."
        title = "Vault City"
        
        content_type = enricher.classify_content_type(title, text)
        
        assert content_type == "location"
    
    def test_faction_classification(self):
        enricher = MetadataEnricher()
        text = "The Brotherhood of Steel is a military organization."
        title = "Brotherhood of Steel"
        
        content_type = enricher.classify_content_type(title, text)
        
        assert content_type == "faction"
    
    def test_item_classification(self):
        enricher = MetadataEnricher()
        text = "A powerful weapon found in the wasteland."
        title = "Plasma Rifle"
        
        content_type = enricher.classify_content_type(title, text)
        
        assert content_type == "item"
    
    def test_lore_default(self):
        enricher = MetadataEnricher()
        text = "General background information."
        title = "History"
        
        content_type = enricher.classify_content_type(title, text)
        
        assert content_type == "lore"


class TestKnowledgeTier:
    """Test knowledge tier determination"""
    
    def test_classified_tier(self):
        enricher = MetadataEnricher()
        text = "This Vault-Tec experiment was classified."
        
        tier = enricher.determine_knowledge_tier(text, "lore")
        
        assert tier == "classified"
    
    def test_restricted_tier(self):
        enricher = MetadataEnricher()
        text = "According to Brotherhood of Steel codex records."
        
        tier = enricher.determine_knowledge_tier(text, "lore")
        
        assert tier == "restricted"
    
    def test_regional_tier(self):
        enricher = MetadataEnricher()
        text = "A local settlement."
        
        tier = enricher.determine_knowledge_tier(text, "location")
        
        assert tier == "regional"
    
    def test_common_tier(self):
        enricher = MetadataEnricher()
        text = "Widely known information."
        
        tier = enricher.determine_knowledge_tier(text, "character")
        
        assert tier == "common"


class TestInfoSource:
    """Test information source determination"""
    
    def test_vault_tec_source(self):
        enricher = MetadataEnricher()
        text = "Vault-Tec Corporation built this facility."
        title = "Vault 101"
        
        source = enricher.determine_info_source(text, title)
        
        assert source == "vault-tec"
    
    def test_military_source(self):
        enricher = MetadataEnricher()
        text = "The Brotherhood of Steel protects this technology."
        title = "Brotherhood Bunker"
        
        source = enricher.determine_info_source(text, title)
        
        assert source == "military"
    
    def test_corporate_source(self):
        enricher = MetadataEnricher()
        text = "RobCo Industries manufactured this robot."
        title = "Protectron"
        
        source = enricher.determine_info_source(text, title)
        
        assert source == "corporate"
    
    def test_public_source(self):
        enricher = MetadataEnricher()
        text = "Common knowledge among wastelanders."
        title = "Trade Routes"
        
        source = enricher.determine_info_source(text, title)
        
        assert source == "public"


class TestEnrichmentIntegration:
    """Test full enrichment workflow"""
    
    def test_enrich_dict_chunk(self):
        """Test enrichment of dict-based chunk (backward compatibility)"""
        enricher = MetadataEnricher()
        
        chunk = {
            'text': "Vault 101 was constructed in 2063 by Vault-Tec.",
            'wiki_title': 'Vault 101',
            'section': 'History',
            'content_type': ''
        }
        
        enriched = enricher.enrich_chunk(chunk)
        
        # Verify enrichment fields added
        assert 'time_period' in enriched
        assert 'year_min' in enriched
        assert 'location' in enriched
        assert 'content_type' in enriched
        assert 'knowledge_tier' in enriched
        assert 'info_source' in enriched
        assert 'chunk_quality' in enriched
        
        # Verify values
        assert enriched['time_period'] == 'pre-war'
        assert enriched['year_min'] == 2063
        assert enriched['is_pre_war'] is True
        assert enriched['is_post_war'] is False
    
    def test_enrich_pydantic_chunk(self):
        """Test enrichment of Pydantic Chunk object"""
        enricher = MetadataEnricher()
        
        metadata = ChunkMetadata(
            wiki_title="Vault 101",
            section="History",
            chunk_index=0,
            total_chunks=1,
            content_type="",
            timestamp="2077-10-23T00:00:00Z",
            section_level=2
        )
        
        chunk = Chunk(
            text="Vault 101 was constructed in 2063 by Vault-Tec.",
            metadata=metadata
        )
        
        enriched = enricher.enrich_chunk(chunk)
        
        # Verify it returns a Chunk object
        assert isinstance(enriched, Chunk)
        assert enriched.metadata.enriched is not None
        
        # Verify enrichment values
        assert enriched.metadata.enriched.time_period == 'pre-war'
        assert enriched.metadata.enriched.year_min == 2063
        assert enriched.metadata.enriched.is_pre_war is True
        assert enriched.metadata.enriched.is_post_war is False
        assert enriched.metadata.enriched.info_source == 'vault-tec'
    
    def test_enrich_multiple_chunks(self):
        """Test bulk enrichment function"""
        chunks = [
            {
                'text': "Pre-war text from 2063.",
                'wiki_title': 'Test 1',
                'section': 'Intro'
            },
            {
                'text': "Post-war text from 2277.",
                'wiki_title': 'Test 2',
                'section': 'Intro'
            }
        ]
        
        enriched = enrich_chunks(chunks)
        
        assert len(enriched) == 2
        assert enriched[0]['is_pre_war'] is True
        assert enriched[1]['is_post_war'] is True
    
    def test_chunk_quality_stub(self):
        """Test stub quality detection"""
        enricher = MetadataEnricher()
        
        chunk = {
            'text': "Short stub.",
            'wiki_title': 'Stub',
            'section': 'Intro'
        }
        
        enriched = enricher.enrich_chunk(chunk)
        
        assert enriched['chunk_quality'] == 'stub'
    
    def test_chunk_quality_rich(self):
        """Test rich quality detection"""
        enricher = MetadataEnricher()
        
        chunk = {
            'text': "In 2063, Vault 101 was built in the Capital Wasteland by Vault-Tec as part of an experiment." * 10,
            'wiki_title': 'Vault 101',
            'section': 'History'
        }
        
        enriched = enricher.enrich_chunk(chunk)
        
        assert enriched['chunk_quality'] == 'rich'


class TestPrePostWarFlags:
    """Test pre/post war flag logic"""
    
    def test_pre_war_by_year(self):
        """Test pre-war flag set by year < 2077"""
        enricher = MetadataEnricher()
        
        chunk = {
            'text': "Built in 2060.",
            'wiki_title': 'Test',
            'section': 'History'
        }
        
        enriched = enricher.enrich_chunk(chunk)
        
        assert enriched['is_pre_war'] is True
        assert enriched['is_post_war'] is False
    
    def test_post_war_by_year(self):
        """Test post-war flag set by year >= 2077"""
        enricher = MetadataEnricher()
        
        chunk = {
            'text': "Founded in 2189.",
            'wiki_title': 'Test',
            'section': 'History'
        }
        
        enriched = enricher.enrich_chunk(chunk)
        
        assert enriched['is_pre_war'] is False
        assert enriched['is_post_war'] is True
    
    def test_spanning_both_eras(self):
        """Test year range spanning 2077"""
        enricher = MetadataEnricher()
        
        chunk = {
            'text': "From 2070 to 2080.",
            'wiki_title': 'Test',
            'section': 'History'
        }
        
        enriched = enricher.enrich_chunk(chunk)
        
        # Should be pre-war because year_max < 2077 is False, but year_min < 2077 is True
        # Actually, the logic checks year_max < 2077 for is_pre_war
        # year_max = 2080, so is_pre_war = False
        # year_min = 2070, which is < 2077, but the check is year_min >= 2077
        # So is_post_war = False
        # This represents ambiguous temporal context
        assert enriched['is_pre_war'] is False
        assert enriched['is_post_war'] is False
