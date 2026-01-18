"""
Configuration for Julie's AI Script Generation System
"""

from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
LORE_DB_PATH = PROJECT_ROOT / "lore" / "fallout76_canon" / "entities"
CHROMA_DB_PATH = PROJECT_ROOT / "lore" / "julie_chroma_db"
CHARACTER_CARD_PATH = PROJECT_ROOT / "dj personality" / "Julie" / "character_card.json"
STORY_ARCS_PATH = PROJECT_ROOT / "tools" / "story-generation" / "story_arcs"
SCRIPTS_DIR = PROJECT_ROOT / "tools" / "story-generation" / "scripts"
APPROVED_DIR = PROJECT_ROOT / "tools" / "story-generation" / "approved"

# Ollama models to test (in order of preference for quality)
# Using currently installed models:
# - fluffy/l3-8b-stheno-v3.2 (4.9GB) - creative writing focused
# - hermes3 (4.7GB) - reasoning and instruction following
# - dolphin-llama3 (4.7GB) - fast general purpose
OLLAMA_MODELS = {
    "creative": "fluffy/l3-8b-stheno-v3.2:latest",  # Creative writing focused
    "quality": "hermes3:latest",                     # Best reasoning/accuracy
    "speed": "dolphin-llama3:latest",                # Fastest generation
}

# RAG settings
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
LORE_RETRIEVAL_COUNT = 15  # Number of entities to retrieve per query
MIN_SIMILARITY_SCORE = 0.3  # Minimum relevance threshold

# Script generation settings
GENERATE_WEEK_AT_ONCE = True  # Maintain narrative flow
MAX_RETRIES = 3  # Retry generation on failure
TEMPERATURE = 0.7  # Ollama temperature (0.6-0.8 for creative but consistent)

# Content segment lengths (in seconds)
SEGMENT_LENGTHS = {
    "gossip": (90, 120),      # 1.5-2 min
    "news": (120, 180),       # 2-3 min
    "weather": (30, 60),      # 30-60 sec
    "fireside": (300, 600),   # 5-10 min
    "music_intro": (15, 30),  # 15-30 sec
    "ad": (30, 60),           # 30-60 sec
}

# Timeline constraints
JULIE_START_YEAR = 2102
JULIE_KNOWLEDGE_CUTOFF = 2152  # 50 years from start
RECLAMATION_DAY = "2102-10-23"  # Vault 76 opening

# Review severity levels
SEVERITY_ERROR = "ERROR"      # Must fix before approval
SEVERITY_WARNING = "WARNING"  # Should review but can approve
SEVERITY_INFO = "INFO"        # FYI only
