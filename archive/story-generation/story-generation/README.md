# Julie's AI Script Generation System

Complete RAG-powered script generation system for Julie's Fallout 76 radio show.

## Components

### 1. Configuration (`config.py`)
- Project paths (lore database, ChromaDB, character card, output directories)
- Ollama models (creative: qwen2.5:14b, quality: mixtral:8x7b, speed: llama3.1:8b)
- RAG settings (embedding model, retrieval count, similarity threshold)
- Segment lengths, timeline constraints

### 2. Lore Retriever (`lore_retriever.py`)
- Semantic search using ChromaDB + sentence-transformers
- Indexes all lore entities from `lore/fallout76_canon/entities/`
- Retrieves top 15 relevant entities per query with similarity scores
- Returns full entity JSONs for context

### 3. Story Planner (`story_planner.py`)
- 6-month pre-planned arc with 120 episode summaries
- Monthly themes: Responders, Vault 76, Free States, BoS, Raiders, Enclave
- Each day has theme + lore queries for all segment types
- Generates JSON files in `story_arcs/`

### 4. Segment Templates (`templates/`)
- **Gossip** (90-120s): Casual character stories, grapevine intel
- **News** (120-180s): 2-3 informative items, satellite/radio data
- **Weather** (30-60s): Regional conditions + lore tie-ins
- **Fireside** (5-10 min): Philosophical deep-dive, vulnerable Julie

### 5. Script Generator (`script_generator.py`)
- Main LLM interface with Ollama integration
- Builds system prompt from Julie's character card + constraints
- Retrieves lore context via RAG for each segment
- Generates weekly batches for narrative continuity
- Saves to `scripts/monthXX/weekX/`

### 6. Script Reviewer (`script_reviewer.py`)
- Automated quality checks:
  - **Character consistency**: Flags prohibited phrases (e.g., "I went to Flatwoods today")
  - **Timeline validation**: Checks for years > 2152, anachronistic tech
  - **Lore accuracy**: Cross-references mentioned entities
  - **Arc coherence**: Verifies script matches theme
- Categorizes issues by severity (ERROR/WARNING/INFO)

### 7. Review Interface (`review_interface.py`)
- Human-in-loop CLI for approval workflow
- Displays script + automated review report
- Options: Approve, Edit, Regenerate (with different model), Skip
- Saves approved scripts to `approved/` with version control

## Workflow

1. **Generate Arc Files**:
   ```bash
   cd tools/story-generation
   python story_planner.py
   ```

2. **Build ChromaDB Index** (after lore scrape completes):
   ```python
   from lore_retriever import LoreRetriever
   retriever = LoreRetriever(rebuild_index=True)
   ```

3. **Generate Week of Scripts**:
   ```python
   from script_generator import ScriptGenerator
   
   generator = ScriptGenerator(model="creative")  # or "quality" or "speed"
   generator.generate_week(month_num=1, week_num=1)
   ```

4. **Review and Approve**:
   ```bash
   python review_interface.py
   ```

5. **Batch TTS** (after approval):
   - Feed approved scripts to voice cloning system
   - Generate MP3s for ESP32 playback

## Installation

```bash
cd tools/story-generation
pip install -r requirements.txt
```

Ensure Ollama is running with models installed:
```bash
ollama pull qwen2.5:14b
ollama pull mixtral:8x7b
ollama pull llama3.1:8b
```

## Testing

```python
# Test RAG retrieval
from lore_retriever import LoreRetriever
retriever = LoreRetriever()
results = retriever.retrieve_lore("Responders faction formation")

# Test script generation
from script_generator import ScriptGenerator
generator = ScriptGenerator(model="creative")
segment = generator.generate_segment("gossip", theme="Rise of the Responders", queries=["Responders founding members"])

# Test reviewer
from script_reviewer import ScriptReviewer
reviewer = ScriptReviewer()
review = reviewer.review_segment(segment, "Rise of the Responders", "gossip")
```

## Directory Structure

```
story-generation/
├── config.py              # Configuration
├── lore_retriever.py      # RAG system
├── story_planner.py       # Arc planning
├── script_generator.py    # LLM interface
├── script_reviewer.py     # Automated review
├── review_interface.py    # Human approval CLI
├── requirements.txt       # Dependencies
├── templates/             # Segment templates
│   ├── gossip_template.json
│   ├── news_template.json
│   ├── weather_template.json
│   └── fireside_template.json
├── story_arcs/           # Generated arc plans (JSON)
├── scripts/              # Generated scripts
│   └── monthXX/weekX/
└── approved/             # Human-approved scripts
    └── monthXX/weekX/
```

## Julie's Constraints (Critical!)

- **Stationary**: Julie never left her radio station recently. She can reference past ("Back when I was in Vault 76...") but not current field reports ("I went to Flatwoods today").
- **Intel Sources**: Weather satellites, trader visitors, radio chatter, terminals, holotapes - NOT personal visits.
- **Timeline**: 2102-2152 knowledge window (50 years).
- **Voice**: Earnest, hopeful, conversational, uses filler words (um, like, you know).
- **Catchphrase**: "If you're out there, and you're listening... you are not alone."

## Next Steps

1. Wait for lore scrape to complete (~3.3 hours)
2. Run `story_planner.py` to generate arc files
3. Build ChromaDB index
4. Test RAG retrieval with sample queries
5. Generate sample scripts with all 3 models
6. Human review and compare model outputs
7. Refine prompts/templates based on results
8. Once proven working, generate Month 1 (4 weeks = 20 episodes)
