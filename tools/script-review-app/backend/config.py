"""Configuration settings for the Script Review App."""

from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Settings
    api_token: str = Field(default="change-me-in-production", validation_alias="SCRIPT_REVIEW_TOKEN")
    allowed_origins: list[str] = ["http://localhost:8000", "http://127.0.0.1:8000"]
    
    # Paths
    scripts_base_path: Path = Path(__file__).parent.parent.parent.parent / "output" / "scripts"
    
    # Server Settings
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
