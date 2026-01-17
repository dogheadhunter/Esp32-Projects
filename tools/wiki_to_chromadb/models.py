"""
Data Models for Wiki-to-ChromaDB Pipeline

Pydantic models for type safety and validation throughout the pipeline.
"""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, field_validator
from datetime import datetime


class WikiLink(BaseModel):
    """Represents a MediaWiki [[Link|Display]] structure"""
    target: str = Field(..., description="Link target page")
    display: str = Field(..., description="Display text")
    type: str = Field(..., description="Link type: internal, category, or media")
    
    @field_validator('type')
    @classmethod
    def validate_type(cls, v: str) -> str:
        allowed = {'internal', 'category', 'media'}
        if v not in allowed:
            raise ValueError(f"Link type must be one of {allowed}")
        return v


class SectionInfo(BaseModel):
    """Represents a MediaWiki section header"""
    level: int = Field(..., ge=1, le=6, description="Section level (1-6)")
    title: str = Field(..., description="Section title")
    line_number: Optional[int] = Field(None, description="Line number in source")


class SectionHierarchy(BaseModel):
    """Represents section position in document hierarchy"""
    level: int = Field(..., ge=1, le=6)
    title: str
    path: str = Field(..., description="Breadcrumb path (e.g., 'Overview > Background')")


class Template(BaseModel):
    """Represents a MediaWiki {{Template}} structure"""
    name: str = Field(..., description="Template name")
    positional: Optional[List[str]] = Field(None, description="Positional parameters")
    params: Optional[Dict[str, str]] = Field(None, description="Named parameters")


class Infobox(BaseModel):
    """Represents a MediaWiki {{Infobox ...}} template"""
    type: str = Field(..., description="Infobox type (e.g., 'Infobox character')")
    parameters: Dict[str, str] = Field(default_factory=dict)


class StructuralMetadata(BaseModel):
    """Structural metadata extracted from raw wikitext"""
    raw_categories: List[str] = Field(default_factory=list)
    wikilinks: List[WikiLink] = Field(default_factory=list)
    sections: List[SectionInfo] = Field(default_factory=list)
    infoboxes: List[Infobox] = Field(default_factory=list)
    templates: List[Template] = Field(default_factory=list)
    game_source: List[str] = Field(default_factory=list)


class EnrichedMetadata(BaseModel):
    """Enriched metadata from content analysis"""
    # Temporal classification
    time_period: Optional[str] = None
    time_period_confidence: float = Field(0.0, ge=0.0, le=1.0)
    year_min: Optional[int] = None
    year_max: Optional[int] = None
    is_pre_war: bool = False
    is_post_war: bool = False
    
    # Spatial classification
    location: Optional[str] = None
    location_confidence: float = Field(0.0, ge=0.0, le=1.0)
    region_type: Optional[str] = None
    
    # Content classification
    content_type: Optional[str] = None
    knowledge_tier: Optional[str] = None  # common, regional, restricted, classified
    info_source: Optional[str] = None  # public, military, corporate, vault-tec, faction
    
    # Quality metadata
    chunk_quality: Optional[str] = None  # stub, reference, content, rich
    
    # Phase 6: Broadcast-specific metadata
    emotional_tone: Optional[str] = None  # hopeful, tragic, mysterious, comedic, tense, neutral
    complexity_tier: Optional[str] = None  # simple, moderate, complex
    primary_subjects: List[str] = Field(default_factory=list)  # water, radiation, factions, etc.
    themes: List[str] = Field(default_factory=list)  # humanity, war, survival, etc.
    controversy_level: Optional[str] = None  # neutral, sensitive, controversial
    last_broadcast_time: Optional[float] = None  # Unix timestamp or None
    broadcast_count: int = 0  # Number of times used in broadcasts
    freshness_score: float = Field(1.0, ge=0.0, le=1.0)  # 1.0 = fresh, 0.0 = stale


class ChunkMetadata(BaseModel):
    """Complete metadata for a single chunk"""
    # Page-level metadata
    wiki_title: str
    timestamp: str
    
    # Chunk-level metadata
    section: str
    section_level: int
    section_hierarchy: Optional[SectionHierarchy] = None
    chunk_index: int
    total_chunks: int  # Total chunks in this section
    
    # Structural metadata
    structural: StructuralMetadata = Field(default_factory=StructuralMetadata)
    
    # Enriched metadata
    enriched: EnrichedMetadata = Field(default_factory=EnrichedMetadata)
    
    def to_flat_dict(self) -> Dict[str, Any]:
        """
        Convert to flat dictionary for ChromaDB compatibility.
        
        ChromaDB has limitations with nested structures, so we flatten
        complex fields into strings or simple types.
        """
        flat = {
            'wiki_title': self.wiki_title,
            'timestamp': self.timestamp,
            'section': self.section,
            'section_level': self.section_level,
            'chunk_index': self.chunk_index,
            'total_chunks': self.total_chunks,
        }
        
        # Add section hierarchy
        if self.section_hierarchy:
            flat['section_path'] = self.section_hierarchy.path
            flat['section_hierarchy_level'] = self.section_hierarchy.level
        
        # Add structural metadata (flattened)
        flat['raw_categories'] = self.structural.raw_categories
        flat['category_count'] = len(self.structural.raw_categories)
        flat['wikilink_count'] = len(self.structural.wikilinks)
        flat['infobox_count'] = len(self.structural.infoboxes)
        flat['template_count'] = len(self.structural.templates)
        flat['game_source'] = self.structural.game_source
        
        # Add infobox types
        if self.structural.infoboxes:
            flat['infobox_types'] = [ib.type for ib in self.structural.infoboxes]
        
        # Add enriched metadata
        if self.enriched.time_period:
            flat['time_period'] = self.enriched.time_period
            flat['time_period_confidence'] = self.enriched.time_period_confidence
        
        if self.enriched.location:
            flat['location'] = self.enriched.location
            flat['location_confidence'] = self.enriched.location_confidence
        
        if self.enriched.region_type:
            flat['region_type'] = self.enriched.region_type
        
        if self.enriched.content_type:
            flat['content_type'] = self.enriched.content_type
        
        if self.enriched.year_min is not None:
            flat['year_min'] = self.enriched.year_min
        
        if self.enriched.year_max is not None:
            flat['year_max'] = self.enriched.year_max
        
        if self.enriched.knowledge_tier:
            flat['knowledge_tier'] = self.enriched.knowledge_tier
        
        if self.enriched.info_source:
            flat['info_source'] = self.enriched.info_source
        
        if self.enriched.chunk_quality:
            flat['chunk_quality'] = self.enriched.chunk_quality
        
        # Add pre/post war flags
        flat['is_pre_war'] = self.enriched.is_pre_war
        flat['is_post_war'] = self.enriched.is_post_war
        
        # Phase 6: Add broadcast metadata
        if self.enriched.emotional_tone:
            flat['emotional_tone'] = self.enriched.emotional_tone
        
        if self.enriched.complexity_tier:
            flat['complexity_tier'] = self.enriched.complexity_tier
        
        if self.enriched.controversy_level:
            flat['controversy_level'] = self.enriched.controversy_level
        
        # Flatten list fields for ChromaDB compatibility
        if self.enriched.primary_subjects:
            for i, subject in enumerate(self.enriched.primary_subjects[:5]):  # Limit to 5
                flat[f'primary_subject_{i}'] = subject
            flat['primary_subjects_count'] = len(self.enriched.primary_subjects)
        
        if self.enriched.themes:
            for i, theme in enumerate(self.enriched.themes[:3]):  # Limit to 3
                flat[f'theme_{i}'] = theme
            flat['themes_count'] = len(self.enriched.themes)
        
        # Broadcast tracking fields
        if self.enriched.last_broadcast_time is not None:
            flat['last_broadcast_time'] = self.enriched.last_broadcast_time
        
        flat['broadcast_count'] = self.enriched.broadcast_count
        flat['freshness_score'] = self.enriched.freshness_score
        
        return flat


class Chunk(BaseModel):
    """Represents a single text chunk with metadata"""
    text: str = Field(..., min_length=1)
    metadata: ChunkMetadata
    
    def to_chromadb_format(self) -> Dict[str, Any]:
        """Convert to ChromaDB ingestion format"""
        return {
            'text': self.text,
            'metadata': self.metadata.to_flat_dict()
        }


class WikiPage(BaseModel):
    """Represents a processed wiki page"""
    title: str
    namespace: int = Field(0, description="MediaWiki namespace")
    timestamp: str
    raw_wikitext: str = Field(..., description="Original wikitext")
    plain_text: str = Field(..., description="Cleaned plain text")
    metadata: StructuralMetadata = Field(default_factory=StructuralMetadata)
    
    @field_validator('timestamp')
    @classmethod
    def validate_timestamp(cls, v: str) -> str:
        """Validate timestamp format"""
        try:
            # Try to parse as ISO format
            datetime.fromisoformat(v.replace('Z', '+00:00'))
        except ValueError:
            pass  # Allow other formats, just validate it's a string
        return v


class ProcessingStats(BaseModel):
    """Statistics for pipeline processing"""
    pages_processed: int = 0
    pages_failed: int = 0
    chunks_created: int = 0
    chunks_ingested: int = 0
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    
    @property
    def elapsed_seconds(self) -> float:
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0.0
    
    @property
    def elapsed_minutes(self) -> float:
        return self.elapsed_seconds / 60.0
    
    @property
    def pages_per_second(self) -> float:
        if self.elapsed_seconds > 0:
            return self.pages_processed / self.elapsed_seconds
        return 0.0


class CollectionStats(BaseModel):
    """Statistics for ChromaDB collection"""
    name: str
    total_chunks: int
    persist_directory: Optional[str] = None
