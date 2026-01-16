"""
Configuration Management for Wiki-to-ChromaDB Pipeline

Centralized configuration using Pydantic settings.
"""

from typing import Optional, List
from pydantic import Field, ConfigDict
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


class ChunkerConfig(BaseSettings):
    """Configuration for semantic chunking"""
    model_config = SettingsConfigDict(env_prefix="CHUNKER_")
    
    max_tokens: int = Field(800, description="Maximum tokens per chunk")
    overlap_tokens: int = Field(100, description="Overlap between chunks")
    tokenizer_name: str = Field(
        "sentence-transformers/all-MiniLM-L6-v2",
        description="HuggingFace tokenizer model"
    )


class EmbeddingConfig(BaseSettings):
    """Configuration for embedding generation"""
    model_config = SettingsConfigDict(env_prefix="EMBEDDING_")
    
    model_name: str = Field(
        "all-MiniLM-L6-v2",
        description="Sentence transformer model name"
    )
    device: str = Field("cuda", description="Device: cuda or cpu")
    batch_size: int = Field(128, description="Batch size for GPU processing")


class ChromaDBConfig(BaseSettings):
    """Configuration for ChromaDB"""
    model_config = SettingsConfigDict(env_prefix="CHROMADB_")
    
    persist_directory: str = Field("./chroma_db", description="Persist directory")
    collection_name: str = Field("fallout_wiki", description="Collection name")
    distance_metric: str = Field("cosine", description="Distance metric for similarity")


class PipelineConfig(BaseSettings):
    """Main pipeline configuration"""
    model_config = SettingsConfigDict(
        env_prefix="WIKI_PIPELINE_",
        env_nested_delimiter="__"
    )
    
    # Input/Output
    xml_path: Optional[str] = Field(None, description="Path to MediaWiki XML dump")
    output_dir: str = Field("./chroma_db", description="Output directory")
    
    # Processing limits
    page_limit: Optional[int] = Field(None, description="Max pages to process (for testing)")
    batch_size: int = Field(500, description="Batch size for ChromaDB ingestion")
    
    # Logging
    log_level: str = Field("INFO", description="Logging level")
    log_file: Optional[str] = Field(None, description="Log file path")
    
    # Sub-configurations
    chunker: ChunkerConfig = Field(default_factory=ChunkerConfig)
    embedding: EmbeddingConfig = Field(default_factory=EmbeddingConfig)
    chromadb: ChromaDBConfig = Field(default_factory=ChromaDBConfig)
    
    @classmethod
    def from_args(cls, **kwargs):
        """Create configuration from command-line arguments"""
        config_dict = {}
        
        # Map common argument names to config fields
        if 'xml_file' in kwargs:
            config_dict['xml_path'] = kwargs['xml_file']
        if 'output_dir' in kwargs:
            config_dict['output_dir'] = kwargs['output_dir']
        if 'limit' in kwargs:
            config_dict['page_limit'] = kwargs['limit']
        
        # Chunker config
        if 'max_tokens' in kwargs or 'overlap_tokens' in kwargs:
            config_dict['chunker'] = ChunkerConfig(
                max_tokens=kwargs.get('max_tokens', 800),
                overlap_tokens=kwargs.get('overlap_tokens', 100)
            )
        
        # Embedding config
        if 'embedding_batch_size' in kwargs:
            config_dict['embedding'] = EmbeddingConfig(
                batch_size=kwargs['embedding_batch_size']
            )
        
        # ChromaDB config
        if 'collection' in kwargs:
            config_dict['chromadb'] = ChromaDBConfig(
                collection_name=kwargs['collection'],
                persist_directory=kwargs.get('output_dir', './chroma_db')
            )
        
        return cls(**config_dict)
    
    def validate_paths(self) -> List[str]:
        """Validate file paths and return list of errors"""
        errors = []
        
        if self.xml_path:
            xml_file = Path(self.xml_path)
            if not xml_file.exists():
                errors.append(f"XML file not found: {self.xml_path}")
            elif not xml_file.is_file():
                errors.append(f"XML path is not a file: {self.xml_path}")
        
        return errors


# Singleton instance for global access
_config: Optional[PipelineConfig] = None


def get_config() -> PipelineConfig:
    """Get global configuration instance"""
    global _config
    if _config is None:
        _config = PipelineConfig()
    return _config


def set_config(config: PipelineConfig) -> None:
    """Set global configuration instance"""
    global _config
    _config = config


def reset_config() -> None:
    """Reset configuration to default"""
    global _config
    _config = None
