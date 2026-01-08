# Configuration for Project Output

# LLM Configuration
LLM_MODEL = "fluffy/l3-8b-stheno-v3.2"  # Primary model for roleplay
LLM_Backup_MODEL = "dolphin-llama3"     # Backup Uncensored model

# Server Configuration
OLLAMA_URL = "http://localhost:11434/api/generate"

# Paths
PROJECT_ROOT = "C:/esp32-project"
SCRIPTS_OUTPUT_DIR = f"{PROJECT_ROOT}/script generation"
AUDIO_OUTPUT_DIR = f"{PROJECT_ROOT}/audio generation"
LOGS_DIR = f"{PROJECT_ROOT}/Debug Logs/pipeline"
