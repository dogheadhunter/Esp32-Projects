"""Configuration management for Music Identifier."""

import os
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class MusicIdentifierConfig(BaseSettings):
    """Configuration for the music identifier tool.
    
    Settings can be configured via:
    1. Environment variables (ACOUSTID_API_KEY, etc.)
    2. .env file in project root
    3. Direct initialization
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    # API Configuration
    acoustid_api_key: str = Field(
        default="",
        description="AcoustID API key from https://acoustid.org/new-application"
    )
    
    # Rate Limiting (requests per second)
    rate_limit: float = Field(
        default=2.5,
        description="Max requests per second to AcoustID API (stay under 3/sec limit)"
    )
    
    # Retry Configuration
    max_retries: int = Field(
        default=3,
        description="Maximum number of retry attempts for API calls"
    )
    
    retry_delay: float = Field(
        default=1.0,
        description="Base delay in seconds between retries (uses exponential backoff)"
    )
    
    # Paths
    project_root: Path = Field(
        default_factory=lambda: Path(__file__).resolve().parent.parent.parent,
        description="Project root directory"
    )
    
    input_dir: Optional[Path] = None
    identified_dir: Optional[Path] = None
    unidentified_dir: Optional[Path] = None
    
    # Processing Options
    min_confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Minimum confidence score (0.0-1.0) to consider a match valid"
    )
    
    update_existing_tags: bool = Field(
        default=True,
        description="Whether to update existing ID3 tags or skip already-tagged files"
    )
    
    # Chromaprint Configuration
    fpcalc_path: str = Field(
        default="fpcalc",
        description="Path to fpcalc executable (chromaprint fingerprinter)"
    )
    
    fingerprint_duration: int = Field(
        default=120,
        description="Duration in seconds to fingerprint (max 120 for free tier)"
    )
    
    def __init__(self, **kwargs):
        """Initialize config and set default paths."""
        super().__init__(**kwargs)
        
        # Set default paths relative to project root
        if self.input_dir is None:
            self.input_dir = self.project_root / "music" / "input"
        
        if self.identified_dir is None:
            self.identified_dir = self.project_root / "music" / "identified"
        
        if self.unidentified_dir is None:
            self.unidentified_dir = self.project_root / "music" / "unidentified"
    
    def validate_api_key(self) -> bool:
        """Check if API key is configured.
        
        Returns:
            True if API key is set, False otherwise
        """
        return bool(self.acoustid_api_key and self.acoustid_api_key.strip())
    
    def ensure_directories(self) -> None:
        """Create music directories if they don't exist."""
        for directory in [self.input_dir, self.identified_dir, self.unidentified_dir]:
            if directory:
                directory.mkdir(parents=True, exist_ok=True)


def get_config(**overrides) -> MusicIdentifierConfig:
    """Get configuration instance with optional overrides.
    
    Args:
        **overrides: Override specific config values
        
    Returns:
        MusicIdentifierConfig instance
        
    Example:
        >>> config = get_config(rate_limit=1.0, min_confidence=0.8)
    """
    return MusicIdentifierConfig(**overrides)
