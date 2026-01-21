"""
Shared Project Configuration

Centralized configuration for all Python tools in the ESP32 AI Radio project.
Provides consistent path references and settings across subsystems.
"""

from pathlib import Path

# Project Root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# LLM Configuration
LLM_MODEL = "fluffy/l3-8b-stheno-v3.2"  # Script generation model
LLM_VALIDATOR_MODEL = "dolphin-llama3"  # Validation model
LLM_BACKUP_MODEL = "hermes3"  # Backup model if primary unavailable
OLLAMA_URL = "http://localhost:11434/api/generate"

# Database Paths
CHROMA_DB_PATH = PROJECT_ROOT / "chroma_db"

# Content Source Paths
LORE_PATH = PROJECT_ROOT / "lore" / "fallout_wiki_complete.xml"

# Output Paths
OUTPUT_PATH = PROJECT_ROOT / "output"
SCRIPTS_OUTPUT_DIR = OUTPUT_PATH / "scripts"
AUDIO_OUTPUT_DIR = OUTPUT_PATH / "audio"
LOGS_DIR = PROJECT_ROOT / "logs" / "pipeline"

# Personality Paths
PERSONALITIES_DIR = PROJECT_ROOT / "dj_personalities"

# Legacy paths (for backward compatibility during refactoring)
LEGACY_SCRIPTS_DIR = PROJECT_ROOT / "script generation"
LEGACY_AUDIO_DIR = PROJECT_ROOT / "audio generation"


def ensure_directories():
    """Create all output directories if they don't exist."""
    SCRIPTS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    AUDIO_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
