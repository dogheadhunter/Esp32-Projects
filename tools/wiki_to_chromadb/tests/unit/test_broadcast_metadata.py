"""
Tests for Phase 6 Task 3: Broadcast Metadata Schema
"""

import pytest
from tools.wiki_to_chromadb.metadata_enrichment_v2 import EnhancedMetadataEnricher
from tools.wiki_to_chromadb.models import Chunk, ChunkMetadata, StructuralMetadata


class TestEmotionalToneClassification:
    """Test emotional tone detection"""
    
    def setup_method(self):
        self.enricher = EnhancedMetadataEnricher()
    
    def test_hopeful_tone(self):
        """Test hopeful tone detection"""
        text = "The community worked together to rebuild their future with hope and optimism."
        tone = self.enricher._determine_emotional_tone(text)
        assert tone == "hopeful"
    
    def test_tragic_tone(self):
        """Test tragic tone detection"""
        text = "The destruction and loss was devastating. Death and despair consumed the survivors."
        tone = self.enricher._determine_emotional_tone(text)
        assert tone == "tragic"
    
    def test_mysterious_tone(self):
        """Test mysterious tone detection"""
        text = "The strange and mysterious anomaly remained unexplained. Hidden secrets and enigmas."
        tone = self.enricher._determine_emotional_tone(text)
        assert tone == "mysterious"
    
    def test_tense_tone(self):
        """Test tense tone detection"""
        text = "Danger approached. The threat was imminent and combat was inevitable."
        tone = self.enricher._determine_emotional_tone(text)
        assert tone == "tense"
    
    def test_neutral_tone(self):
        """Test neutral tone for text without strong emotional markers"""
        text = "The location contained various items and resources for trading."
        tone = self.enricher._determine_emotional_tone(text)
        assert tone == "neutral"
    
    def test_requires_multiple_keywords(self):
        """Test that single keyword is not enough for non-neutral tone"""
        text = "The area had one instance of hope but was otherwise mundane."
        tone = self.enricher._determine_emotional_tone(text)
        assert tone == "neutral"


class TestComplexityTierClassification:
    """Test complexity tier detection"""
    
    def setup_method(self):
        self.enricher = EnhancedMetadataEnricher()
    
    def test_simple_tier_short_text(self):
        """Test simple tier for short text"""
        metadata = ChunkMetadata(
            wiki_title="Test",
            timestamp="2024-01-01",
            section="Test",
            section_level=1,
            chunk_index=0,
            total_chunks=1,
            structural=StructuralMetadata(wikilinks=[])
        )
        
        text = "This is a short text with few words."
        tier = self.enricher._determine_complexity_tier(text, metadata)
        assert tier == "simple"
    
    def test_complex_tier_long_text(self):
        """Test complex tier for long text"""
        metadata = ChunkMetadata(
            wiki_title="Test",
            timestamp="2024-01-01",
            section="Test",
            section_level=1,
            chunk_index=0,
            total_chunks=1,
            structural=StructuralMetadata(wikilinks=[{"target": f"link{i}"} for i in range(15)])
        )
        
        text = " ".join(["word"] * 850)  # 850 words
        tier = self.enricher._determine_complexity_tier(text, metadata)
        assert tier == "complex"
    
    def test_moderate_tier(self):
        """Test moderate tier for medium-length text"""
        metadata = ChunkMetadata(
            wiki_title="Test",
            timestamp="2024-01-01",
            section="Test",
            section_level=1,
            chunk_index=0,
            total_chunks=1,
            structural=StructuralMetadata(wikilinks=[{"target": f"link{i}"} for i in range(5)])
        )
        
        text = " ".join(["word"] * 400)  # 400 words
        tier = self.enricher._determine_complexity_tier(text, metadata)
        assert tier == "moderate"


class TestPrimarySubjectExtraction:
    """Test primary subject extraction"""
    
    def setup_method(self):
        self.enricher = EnhancedMetadataEnricher()
    
    def test_extract_water_subject(self):
        """Test water subject extraction"""
        text = "The water purifier provided clean water to the settlement. Aqua pura was distributed."
        subjects = self.enricher._extract_primary_subjects(text)
        assert "water" in subjects
    
    def test_extract_radiation_subject(self):
        """Test radiation subject extraction"""
        text = "Radiation levels were high. Rads contaminated the area and geiger counters went wild."
        subjects = self.enricher._extract_primary_subjects(text)
        assert "radiation" in subjects
    
    def test_extract_multiple_subjects(self):
        """Test extraction of multiple subjects"""
        text = """The faction used weapons and armor in combat. 
        Radiation was a concern. Technology helped survival."""
        subjects = self.enricher._extract_primary_subjects(text)
        
        # Should extract multiple subjects
        assert len(subjects) > 1
        assert any(s in subjects for s in ["weapons", "armor", "factions", "radiation", "technology", "survival"])
    
    def test_limit_to_five_subjects(self):
        """Test that subjects are limited to top 5"""
        text = """Water radiation weapons armor factions creatures survival technology 
        commerce vaults military exploration politics science history."""
        subjects = self.enricher._extract_primary_subjects(text)
        
        # Should be limited to 5
        assert len(subjects) <= 5
    
    def test_no_subjects(self):
        """Test text with no clear subjects"""
        text = "Some generic text without specific subject keywords."
        subjects = self.enricher._extract_primary_subjects(text)
        assert isinstance(subjects, list)


class TestThemeExtraction:
    """Test theme extraction"""
    
    def setup_method(self):
        self.enricher = EnhancedMetadataEnricher()
    
    def test_extract_humanity_theme(self):
        """Test humanity theme extraction"""
        text = "Humanity struggled to maintain civilization and society. People formed communities."
        themes = self.enricher._extract_themes(text, "character")
        assert "humanity" in themes
    
    def test_extract_war_theme(self):
        """Test war theme extraction"""
        text = "War and conflict dominated. Battle after battle, military forces clashed violently."
        themes = self.enricher._extract_themes(text, "event")
        assert "war" in themes
    
    def test_extract_survival_theme(self):
        """Test survival theme extraction"""
        text = "Survival was paramount. They struggled to endure and adapt to harsh conditions."
        themes = self.enricher._extract_themes(text, "lore")
        assert "survival" in themes
    
    def test_content_type_boosting(self):
        """Test that content type boosts relevant themes"""
        text = "Some text about events."
        themes = self.enricher._extract_themes(text, "event")
        
        # Event content type should boost war theme
        # (may not be in result if no war keywords, but shouldn't error)
        assert isinstance(themes, list)
    
    def test_limit_to_three_themes(self):
        """Test that themes are limited to top 3"""
        text = """Humanity technology war survival corruption hope loss redemption 
        freedom power civilization."""
        themes = self.enricher._extract_themes(text, "lore")
        
        # Should be limited to 3
        assert len(themes) <= 3


class TestControversyLevelDetection:
    """Test controversy level detection"""
    
    def setup_method(self):
        self.enricher = EnhancedMetadataEnricher()
    
    def test_controversial_content(self):
        """Test controversial content detection"""
        text = "The practice of slavery and torture was widespread. Executions were common."
        level = self.enricher._determine_controversy_level(text)
        assert level == "controversial"
    
    def test_sensitive_content(self):
        """Test sensitive content detection"""
        text = "Many died in the attack. Death and trauma affected survivors. Victims suffered greatly."
        level = self.enricher._determine_controversy_level(text)
        assert level == "sensitive"
    
    def test_neutral_content(self):
        """Test neutral content detection"""
        text = "The settlement traded goods and maintained relationships with neighbors."
        level = self.enricher._determine_controversy_level(text)
        assert level == "neutral"


class TestBroadcastMetadataIntegration:
    """Test full broadcast metadata enrichment"""
    
    def setup_method(self):
        self.enricher = EnhancedMetadataEnricher()
    
    def test_enrich_chunk_with_broadcast_metadata(self):
        """Test that chunk enrichment includes broadcast metadata"""
        metadata = ChunkMetadata(
            wiki_title="Test Article",
            timestamp="2024-01-01",
            section="Content",
            section_level=1,
            chunk_index=0,
            total_chunks=1,
            structural=StructuralMetadata(wikilinks=[])
        )
        
        chunk = Chunk(
            text="The hopeful community worked to rebuild. Water purification and survival were key.",
            metadata=metadata
        )
        
        enriched = self.enricher.enrich_chunk(chunk)
        
        # Check all broadcast metadata fields exist
        assert enriched.emotional_tone is not None
        assert enriched.complexity_tier is not None
        assert enriched.primary_subjects is not None
        assert enriched.themes is not None
        assert enriched.controversy_level is not None
        assert enriched.last_broadcast_time is None  # Should start as None
        assert enriched.broadcast_count == 0  # Should start at 0
        assert enriched.freshness_score == 1.0  # Should start at 1.0 (fresh)
    
    def test_enriched_metadata_values(self):
        """Test that enriched metadata has sensible values"""
        metadata = ChunkMetadata(
            wiki_title="Hopeful Settlement",
            timestamp="2024-01-01",
            section="Story",
            section_level=1,
            chunk_index=0,
            total_chunks=1,
            structural=StructuralMetadata(wikilinks=[])
        )
        
        chunk = Chunk(
            text="Hope and rebuilding defined the community. Clean water flowed again. Humanity persevered.",
            metadata=metadata
        )
        
        enriched = self.enricher.enrich_chunk(chunk)
        
        # Should detect hopeful tone
        assert enriched.emotional_tone == "hopeful"
        
        # Should extract water subject
        assert "water" in enriched.primary_subjects
        
        # Should extract relevant themes
        assert any(theme in enriched.themes for theme in ["hope", "humanity", "survival"])
        
        # Should be neutral controversy
        assert enriched.controversy_level == "neutral"


class TestModelFlattening:
    """Test that new fields flatten correctly for ChromaDB"""
    
    def test_flatten_primary_subjects(self):
        """Test that primary subjects flatten to indexed fields"""
        from tools.wiki_to_chromadb.models import EnrichedMetadata
        
        enriched = EnrichedMetadata(
            primary_subjects=["water", "radiation", "weapons"]
        )
        
        metadata = ChunkMetadata(
            wiki_title="Test",
            timestamp="2024-01-01",
            section="Test",
            section_level=1,
            chunk_index=0,
            total_chunks=1,
            enriched=enriched
        )
        
        flat = metadata.to_flat_dict()
        
        assert 'primary_subject_0' in flat
        assert flat['primary_subject_0'] == "water"
        assert 'primary_subject_1' in flat
        assert flat['primary_subject_1'] == "radiation"
        assert 'primary_subjects_count' in flat
        assert flat['primary_subjects_count'] == 3
    
    def test_flatten_themes(self):
        """Test that themes flatten to indexed fields"""
        from tools.wiki_to_chromadb.models import EnrichedMetadata
        
        enriched = EnrichedMetadata(
            themes=["humanity", "survival"]
        )
        
        metadata = ChunkMetadata(
            wiki_title="Test",
            timestamp="2024-01-01",
            section="Test",
            section_level=1,
            chunk_index=0,
            total_chunks=1,
            enriched=enriched
        )
        
        flat = metadata.to_flat_dict()
        
        assert 'theme_0' in flat
        assert flat['theme_0'] == "humanity"
        assert 'themes_count' in flat
        assert flat['themes_count'] == 2
    
    def test_flatten_broadcast_fields(self):
        """Test that broadcast tracking fields are flattened"""
        from tools.wiki_to_chromadb.models import EnrichedMetadata
        
        enriched = EnrichedMetadata(
            emotional_tone="hopeful",
            complexity_tier="moderate",
            controversy_level="neutral",
            broadcast_count=5,
            freshness_score=0.7,
            last_broadcast_time=1234567890.0
        )
        
        metadata = ChunkMetadata(
            wiki_title="Test",
            timestamp="2024-01-01",
            section="Test",
            section_level=1,
            chunk_index=0,
            total_chunks=1,
            enriched=enriched
        )
        
        flat = metadata.to_flat_dict()
        
        assert flat['emotional_tone'] == "hopeful"
        assert flat['complexity_tier'] == "moderate"
        assert flat['controversy_level'] == "neutral"
        assert flat['broadcast_count'] == 5
        assert flat['freshness_score'] == 0.7
        assert flat['last_broadcast_time'] == 1234567890.0
