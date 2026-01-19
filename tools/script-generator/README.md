# Script Generator

RAG-powered radio script generation system for ESP32 Fallout Radio project.

## Overview

This system generates lore-accurate, character-consistent radio scripts using:
- **ChromaDB RAG**: 356,601 Fallout Wiki chunks for lore context
- **Ollama LLM**: Local text generation (fluffy/l3-8b-stheno-v3.2)
- **Jinja2 Templates**: 5 script types with personality injection
- **DJ Personas**: 4 character personalities with temporal/spatial filtering
- **LLM Validation**: Intelligent script validation with hybrid LLM + rule-based checks

## Installation

```bash
cd tools/script-generator
pip install jinja2  # Only new dependency
```

**Prerequisites:**
- Python 3.10+
- Ollama running (`ollama serve`)
- ChromaDB processed (run `tools/wiki_to_chromadb/process_wiki.py`)
- Model downloaded (`ollama pull fluffy/l3-8b-stheno-v3.2`)

## Quick Start

### Basic Usage

```python
from generator import ScriptGenerator

# Initialize (connects to ChromaDB + Ollama)
generator = ScriptGenerator()

# Generate a weather report
result = generator.generate_script(
    script_type="weather",
    dj_name="Julie (2102, Appalachia)",
    context_query="Appalachia weather sunny conditions",
    weather_type="sunny",
    time_of_day="morning",
    hour=8,
    temperature=72
)

print(result['script'])

# Save to file
generator.save_script(result)

# Unload model (frees ~4.5GB VRAM)
generator.unload_model()
```

### Script Types

**1. Weather** (`weather.jinja2`)
```python
result = generator.generate_script(
    script_type="weather",
    dj_name="Julie (2102, Appalachia)",
    context_query="Appalachia weather rainy conditions",
    weather_type="rainy",      # sunny/rainy/cloudy/foggy
    time_of_day="afternoon",   # morning/afternoon/evening/night
    hour=14,
    temperature=65
)
```

**2. News** (`news.jinja2`)
```python
result = generator.generate_script(
    script_type="news",
    dj_name="Julie (2102, Appalachia)",
    context_query="Appalachia Responders settlement cooperation",
    news_topic="settlement cooperation",
    faction="Responders",           # Optional
    location="Flatwoods"            # Optional
)
```

**3. Time** (`time.jinja2`)
```python
result = generator.generate_script(
    script_type="time",
    dj_name="Julie (2102, Appalachia)",
    context_query="",  # Minimal context needed
    hour=14,
    time_of_day="afternoon",
    special_event="Reclamation Day"  # Optional
)
```

**4. Gossip** (`gossip.jinja2`)
```python
result = generator.generate_script(
    script_type="gossip",
    dj_name="Julie (2102, Appalachia)",
    context_query="Appalachia characters Duchess rumors",
    rumor_type="character discovery",
    character="Duchess",         # Optional
    faction="Settlers"           # Optional
)
```

**5. Music Intro** (`music_intro.jinja2`)
```python
result = generator.generate_script(
    script_type="music_intro",
    dj_name="Julie (2102, Appalachia)",
    context_query="pre-war music 1950s entertainment culture",
    song_title="I Don't Want to Set the World on Fire",
    artist="The Ink Spots",      # Optional
    era="1940s",                 # Optional
    mood="melancholy"            # Optional
)
```

### Available DJs

```python
from personality_loader import get_available_djs

djs = get_available_djs()
# ['Julie (2102, Appalachia)',
#  'Mr. New Vegas (2281, Mojave)',
#  'Travis Miles Nervous (2287, Commonwealth)',
#  'Travis Miles Confident (2287, Commonwealth)']
```

Each DJ has temporal/spatial filtering - Julie only knows Appalachia events ≤2102.

## Advanced Usage

### Custom Generation Parameters

```python
result = generator.generate_script(
    script_type="weather",
    dj_name="Julie (2102, Appalachia)",
    context_query="Appalachia weather",
    
    # Ollama parameters
    model="fluffy/l3-8b-stheno-v3.2",  # Custom model
    temperature=0.9,                    # Creativity (0.0-1.0)
    top_p=0.95,                        # Nucleus sampling
    
    # RAG parameters
    n_results=10,                      # RAG results to retrieve
    context_chunks=5,                  # Top chunks to use in prompt
    
    # Template variables
    weather_type="sunny",
    time_of_day="morning",
    hour=8,
    temperature=72
)
```

### Batch Generation

```python
scripts = []
for hour in range(0, 24, 2):  # Every 2 hours
    time_of_day = "morning" if hour < 12 else ("afternoon" if hour < 18 else "evening")
    
    result = generator.generate_script(
        script_type="time",
        dj_name="Julie (2102, Appalachia)",
        context_query="",
        hour=hour,
        time_of_day=time_of_day
    )
    
    scripts.append(result)
    generator.save_script(result)

# Unload after batch
generator.unload_model()
```

### RAG Query Optimization

```python
# Weather: Focus on environment
context_query="Appalachia weather sunny conditions flora fauna radiation"

# News: Target specific factions/locations
context_query="Appalachia Responders Flatwoods settlement cooperation events"

# Gossip: Character-focused
context_query="Rose Top of the World Raiders rumors stories"

# Music: Cultural context
context_query="pre-war music 1950s entertainment culture American history"
```

## Architecture

### Pipeline Flow

```
1. Load DJ Personality (character_card.json)
   └─> personality data (tone, voice, constraints)

2. RAG Query (ChromaDB)
   └─> query_for_dj(dj_name, context_query)
   └─> filtered by DJ's temporal/spatial constraints
   └─> returns top-k lore chunks

3. Render Template (Jinja2)
   └─> inject personality + lore context + template vars
   └─> generates system prompt + user prompt

4. Generate (Ollama)
   └─> POST to http://localhost:11434/api/generate
   └─> returns generated script text

5. Save + Unload
   └─> save to script generation/scripts/
   └─> unload model from VRAM (keep_alive=0)
```

### File Structure

```
tools/script-generator/
├── generator.py              # Main ScriptGenerator class
├── ollama_client.py          # Ollama API wrapper
├── personality_loader.py     # DJ character card loader
├── templates/
│   ├── weather.jinja2
│   ├── news.jinja2
│   ├── time.jinja2
│   ├── gossip.jinja2
│   └── music_intro.jinja2
└── tests/
    ├── test_generator.py     # Unit tests
    └── validate_scripts.py   # Quality validation
```

### VRAM Management

The RTX 3060 (6GB) requires careful VRAM management:

```python
# Script generation phase (uses ~4.5GB)
generator = ScriptGenerator()
for script_type in ['weather', 'news', 'time']:
    result = generator.generate_script(...)
    generator.save_script(result)

# Unload Ollama
generator.unload_model()  # Frees ~4.5GB

# TTS generation phase (uses ~2.5GB)
# tts_engine.load()
# tts_engine.generate_batch(scripts)
```

## Testing

### Run Unit Tests

```bash
cd tools/script-generator/tests
python test_generator.py
python test_llm_validator.py  # NEW: LLM validation tests
```

**Tests:**
- Personality loading (4 DJs)
- Template rendering (5 templates)
- RAG queries (filtered by DJ)
- Ollama generation
- Full pipeline integration
- Error handling
- LLM validation (rule-based, LLM, hybrid)

### Validate Scripts

```bash
# Old validation (rules only)
python validate_scripts.py

# New LLM validation examples
python examples/llm_validation_demo.py
```

**Validation Checks:**
- Character consistency (tone, catchphrases, voice)
- Lore accuracy (references real content)
- Temporal consistency (timeline, knowledge boundaries)
- Script quality (word count, flow, engagement)
- RAG integration (context relevance)

## Script Validation

### New: LLM-Based Validation

The system now includes intelligent LLM-based validation in addition to rule-based checks:

```python
from generator import ScriptGenerator

generator = ScriptGenerator()

# Generate with automatic LLM validation
result = generator.generate_and_validate(
    script_type="weather",
    dj_name="Julie (2102, Appalachia)",
    context_query="Appalachia weather",
    validation_strategy="hybrid",  # "llm", "rules", or "hybrid"
    max_validation_retries=3,
    weather_type="sunny"
)

# Check validation results
validation = result["validation"]
print(f"Valid: {validation['is_valid']}")
print(f"Score: {validation['overall_score']}")
```

**Validation Strategies:**
- **"rules"**: Fast rule-based checks (temporal, forbidden topics)
- **"llm"**: LLM-powered quality and context assessment
- **"hybrid"**: Both approaches (recommended)

**See:**
- [LLM_VALIDATION_GUIDE.md](LLM_VALIDATION_GUIDE.md) - Complete documentation
- [VALIDATION_MIGRATION_GUIDE.md](VALIDATION_MIGRATION_GUIDE.md) - Migration help
- [examples/llm_validation_demo.py](examples/llm_validation_demo.py) - Examples

## Troubleshooting

### "Cannot connect to Ollama"

```bash
# Start Ollama server
ollama serve

# Verify model is downloaded
ollama list
ollama pull fluffy/l3-8b-stheno-v3.2
```

### "ChromaDB not found"

```bash
cd tools/wiki_to_chromadb
python process_wiki.py ../../lore/fallout_wiki_complete.xml
# Takes ~15-20 minutes, processes 118,468 articles
```

### "Template not found"

Check templates directory exists:
```bash
ls tools/script-generator/templates/
# Should see: weather.jinja2, news.jinja2, time.jinja2, gossip.jinja2, music_intro.jinja2
```

### "Generation timeout"

Increase timeout or reduce context:
```python
result = generator.generate_script(
    ...,
    n_results=3,        # Fewer RAG results
    context_chunks=2    # Less context in prompt
)
```

### "Out of memory" (VRAM)

```python
# Unload model between operations
generator.unload_model()

# Or use smaller model
model="dolphin-llama3"  # Smaller backup model
```

### Unicode errors (Windows)

Already fixed - using `[OK]` instead of emojis in output.

## Integration with Phase 3 (Orchestrator)

```python
# Phase 3.1 orchestrator pattern
from generator import ScriptGenerator

# Initialize once
generator = ScriptGenerator()

# Generate all scripts for 24-hour cycle
schedule = [
    ('weather', 6, 'sunny', 'morning'),
    ('news', 7, 'settlement news', 'Flatwoods'),
    ('time', 8, None, 'morning'),
    # ... more scheduled segments
]

scripts = []
for script_type, hour, *args in schedule:
    result = generator.generate_script(
        script_type=script_type,
        dj_name="Julie (2102, Appalachia)",
        context_query=f"Appalachia {script_type} {args[0] if args else ''}",
        hour=hour,
        **template_vars_from_schedule(script_type, args)
    )
    scripts.append(result)

# Unload Ollama (critical: frees VRAM for TTS)
generator.unload_model()

# Now safe to load TTS engine
# (TTS generation continues with freed VRAM)
```

## Performance

**Generation Speed:**
- Weather: ~5-8 seconds (with RAG query)
- News: ~8-12 seconds (more context)
- Time: ~3-5 seconds (minimal context)
- Gossip: ~6-10 seconds
- Music Intro: ~4-7 seconds

**Resource Usage:**
- ChromaDB: ~500MB RAM (persistent)
- Ollama: ~4.5GB VRAM (unloadable)
- Total: <1GB RAM + 4.5GB VRAM during generation

## Configuration

Edit [tools/main tools/config.py](../main tools/config.py):

```python
# LLM Configuration
LLM_MODEL = "fluffy/l3-8b-stheno-v3.2"  # Primary model
LLM_Backup_MODEL = "dolphin-llama3"     # Fallback

# Server Configuration
OLLAMA_URL = "http://localhost:11434/api/generate"

# Paths
SCRIPTS_OUTPUT_DIR = "C:/esp32-project/script generation"
```

## License

Part of ESP32 AI Radio project. See project root LICENSE.

## Credits

- Fallout Wiki (fallout.wiki) - Lore source
- Ollama - Local LLM inference
- ChromaDB - Vector database
- Jinja2 - Template engine
