# Model Configuration

## Current Models

The ESP32 AI Radio project uses two specialized Ollama models:

### Script Generation
- **Model**: `fluffy/l3-8b-stheno-v3.2`
- **Purpose**: Creative roleplay and script writing
- **Size**: 4.9 GB
- **Usage**: Primary model for generating radio scripts with character personality

### Validation
- **Model**: `dolphin-llama3`
- **Purpose**: Script validation and consistency checking
- **Size**: 4.7 GB
- **Usage**: Validates generated scripts for lore accuracy, temporal consistency, and quality

## Configuration Location

Model settings are centralized in:
```
tools/shared/project_config.py
```

```python
# LLM Configuration
LLM_MODEL = "fluffy/l3-8b-stheno-v3.2"  # Script generation model
LLM_VALIDATOR_MODEL = "dolphin-llama3"  # Validation model
```

## Changing Models

To use different models:

1. Pull the model with Ollama:
   ```bash
   ollama pull model-name
   ```

2. Update `tools/shared/project_config.py`:
   ```python
   LLM_MODEL = "your-model-name"
   LLM_VALIDATOR_MODEL = "your-validator-model"
   ```

3. The changes will automatically apply to:
   - Script Generator (`generator.py`)
   - LLM Pipeline (`llm_pipeline.py`)
   - LLM Validator (`llm_validator.py`)

## Model Requirements

For best results, models should:
- Support roleplay and creative writing (script generation)
- Be uncensored for Fallout's mature themes
- Have good instruction-following capabilities
- Be 7B-8B parameter size for balance of quality and speed

## Testing Models

Run tests with specific models:
```bash
$env:OLLAMA_AVAILABLE="true"
$env:CHROMADB_AVAILABLE="true"
python run_tests.py
```

## Available Models

Check currently installed models:
```bash
ollama list
```

Current installation:
- `fluffy/l3-8b-stheno-v3.2:latest` (4.9 GB)
- `dolphin-llama3:latest` (4.7 GB)
- `hermes3:latest` (4.7 GB)
