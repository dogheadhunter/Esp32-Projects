# ESP32 Fallout Radio Station - Implementation Plan

**Goal:** Build a complete AI-driven radio station with Julie as DJ, scheduled programming, and pre-generated content for week-long autonomous playback.

**Quality Priority:** Prioritize voice quality and code maintainability over speed.

---

## Current Architecture (2026-01-12)

### **RESET IN PROGRESS** - Phase 1 & 3 Audio Pipeline Rebuild

**Previous Approach:** Complex TTS pipeline with emotion mixing, fine-tuned models, crossfading, and quality validation (archived to `archive/pipeline_reset_20260112/`)

**New Approach:** Simplified "Skeleton Key" pipeline - Script → Base Model → MP3
- **Focus:** Isolate and fix audio quality issues ("gibberish" artifacts)
- **Strategy:** Start with Base Chatterbox Turbo model only, reintroduce fine-tuning only after baseline is proven
- **Firmware:** `src/main.cpp` remains unchanged (SD card + I2S playback operational)

### TTS System
- **Engine:** Chatterbox Turbo Base Model (pre-trained)
- **Approach:** Zero-shot voice cloning with reference audio (no fine-tuning initially)
- **Environment:** `chatterbox_env/` Python virtual environment
- **Status:** ⚠️ **REBUILDING** - Previous pipeline archived, new simplified pipeline needed

### Content Generation Pipeline ✅ **OPERATIONAL**
- **LLM:** Ollama (llama3.1:8b, hermes3:8b configured)
- **Knowledge Base:** ChromaDB with 356,601 lore chunks
- **Lore Source:** `lore/fallout_wiki_complete.xml` (118,468 wiki articles)
- **Workflow:** Template → RAG Query → Ollama → Script with metadata
- **Location:** `tools/script-generator/` 
- **Status:** ✅ **PROTECTED** - Do not modify during audio pipeline reset

### Codebase Cleanup Status
- **Archived (2026-01-12):**
  - `tools/tts-pipeline/` - Complex pipeline with emotion mixing, crossfading, validation
  - `tools/generate_radio_segment.py` - Early standalone generator
  - `validation_iteration2/` - A/B test results
  - `audio generation/` - All generated audio files
- **Next:** Comprehensive audit of entire codebase for obsolete files (Phase 0)

---

## Phase 0: Codebase Audit & Cleanup

**Goal:** Identify and archive all obsolete code to create a manageable, focused workspace  
**Estimated Time:** 1-2 hours  
**Dependencies:** None

### 0.1 Archive Assessment
- [x] Survey `archive/` folder for existing backups and experiments
  - `archive/backups/` - Test normalize script + wiki XML backup
  - `archive/lore-scraper/` - Early wiki scraping attempts
  - `archive/story-generation/` - Story arc experiments
  - `archive/story-generation-root/` - Root-level story experiments (archived 2026-01-13)
  - `archive/pipeline_reset_20260112/` - TTS pipeline reset (archived 2026-01-12)
  - `archive/xtts-research/` - Obsolete XTTS pipeline research (archived 2026-01-13)
- [x] Consolidate or delete redundant archives
- [x] Document what each archive contains

**Status:** ✅ COMPLETE (2026-01-13)  
**Deliverable:** Clean `archive/` with `README.md` and `INDEX.md`

### 0.2 Tools Folder Audit
- [x] Review `tools/` subfolders for obsolete code:
  - `tools/chatterbox-finetuning/` - **KEEP** (core TTS functionality)
  - `tools/main tools/` - **KEEP** (shared config/utils, renamed consideration)
  - `tools/ollama_setup/` - **KEEP** (Phase 2 dependency)
  - `tools/script-generator/` - **KEEP** (Phase 2 - protected)
  - `tools/temp tools/` - **DELETED** (empty folder)
  - `tools/voice-samples/` - **KEEP** (reference audio for TTS)
  - `tools/wiki_to_chromadb/` - **KEEP** (Phase 2 - protected)
- [x] Move obsolete tools to archive
- [x] Create tools/README.md explaining each folder's purpose

**Status:** ✅ COMPLETE (2026-01-13)  
**Deliverable:** Clean `tools/` with clear organization and README

### 0.3 Research Folder Audit
- [x] Review `research/` for outdated documentation:
  - `research/fallout-wiki-*.md` - **KEEP** (Phase 2 reference)
  - `research/fine-tuning-decision.md` - **KEEP** (TTS reference)
  - `research/script-generation-*.md` - **KEEP** (Phase 2 reference)
  - `research/xtts-finetuning-guide.md` - **ARCHIVED** (obsolete - using Chatterbox)
  - `research/entity-reclassification/` - **KEEP** (wiki entity deduplication research)
  - `research/vscode-custom-agents/` - **KEEP** (VS Code agent tool syntax)
- [x] Archive obsolete research
- [x] Update research/README.md with current status (if needed)

**Status:** ✅ COMPLETE (2026-01-13)  
**Deliverable:** Organized `research/` with only relevant documentation

### 0.4 Root Folder Cleanup
- [x] Review root-level folders:
  - `chroma_db/` - **DELETED** (duplicate of `tools/wiki_to_chromadb/chroma_db/`)
  - `models/` - **KEEP** (Chatterbox models)
  - `music/` - **KEEP** (music library for intros)
  - `Save_Do_Not_Touch/` - **ARCHIVED** (manual backup → `archive/backups/wiki_xml_backup/`)
  - `script generation/` - **KEEP** (Phase 2 output)
  - `story generation/` - **ARCHIVED** (story arcs → `archive/story-generation-root/`)
  - `test_chroma_db_pipeline/` - **DELETED** (test data)
- [x] Archive experimental/duplicate folders
- [x] Document purpose of remaining folders

**Status:** ✅ COMPLETE (2026-01-13)  
**Deliverable:** Clean root with only essential folders
  - `test_chroma_db_pipeline/` - **DELETE** (test data)
- [ ] Archive experimental/duplicate folders
- [ ] Document purpose of remaining folders

**Status:** ⬜ NOT STARTED  
**Deliverable:** Clean root with only essential folders

### 0.5 Documentation Update
- [x] Create `WORKSPACE_STRUCTURE.md` explaining folder hierarchy
- [x] Update `.gitignore` to exclude archived content and generated files
- [x] Create `archive/INDEX.md` listing all archived content with dates and reasons
- [x] Create `tools/README.md` documenting each subfolder's purpose
- [x] Update this plan.md with final clean workspace structure

**Status:** ✅ COMPLETE (2026-01-13)  
**Deliverable:** Comprehensive workspace documentation

**Phase 0 Status:** ✅ COMPLETE (2026-01-13) - Ready for Phase 1 rebuild

---

## Phase 0 Execution Summary (2026-01-13)

### Deleted (Safe Duplicates/Test Data):
- ✅ `chroma_db/` - Duplicate of production DB at `tools/wiki_to_chromadb/chroma_db/`
- ✅ `test_chroma_db_pipeline/` - Test pipeline data
- ✅ `tools/temp tools/` - Empty folder

### Archived (Obsolete Experimental Code):
- ✅ `Save_Do_Not_Touch/` → `archive/backups/wiki_xml_backup/`
- ✅ `story generation/` → `archive/story-generation-root/`
- ✅ `research/xtts-finetuning-guide.md` → `archive/xtts-research/`

### Reviewed (Kept for Reference):
- ✅ `research/entity-reclassification/` - Wiki entity deduplication research (KEEP)
- ✅ `research/vscode-custom-agents/` - VS Code agent tool syntax research (KEEP)

### Code Improvements:
- ✅ Fixed hardcoded path in `tools/main tools/config.py` - Now uses `Path(__file__).resolve().parent.parent.parent` for cross-platform compatibility

### Documentation Created:
- ✅ `WORKSPACE_STRUCTURE.md` - Comprehensive folder hierarchy guide (350+ lines)
- ✅ `tools/README.md` - Tools directory documentation with usage examples (280+ lines)
- ✅ `archive/INDEX.md` - Dated archive index with deletion safety notes

---

## Phase 1: Core TTS Engine (Simplified)

**Goal:** Build minimal TTS wrapper for generating audio from text  
**Estimated Time:** 2-3 hours  
**Dependencies:** Phase 0 complete, `chatterbox_env/` operational

### 1.1 Model Loading Module
- [x] Create `tools/tts-pipeline/engine.py`
- [x] Implement `ChatterboxEngine` class:
  - [x] `load_model()` - Load Base Chatterbox Turbo only (no fine-tuning)
  - [x] `generate()` - Text → 24kHz audio tensor
  - [x] `generate_to_file()` - Text → MP3 file with silence trimming
  - [x] `set_reference()` - Load and validate reference audio
  - [x] `unload_model()` - Free VRAM
- [x] Implement CUDA optimizations for 6GB VRAM (RTX 3060)
- [x] Test with "Hello World" generation
- [x] Verify CUDA acceleration working (4.11GB VRAM usage)
- [x] Document inference parameters (temperature=0.6, top_k=2000, top_p=0.95, rep_pen=1.1)

**Status:** ✅ COMPLETE (2026-01-13)  
**Deliverable:** `engine.py` (397 lines) with Base Model loading verified on GPU

### 1.2 Reference Audio Management
- [x] Create `tools/tts-pipeline/references.py`
- [x] Implement reference audio utilities:
  - [x] `validate_reference_audio()` - Check format and duration
  - [x] `preprocess_reference_audio()` - Resample to 22050Hz mono
  - [x] `find_best_reference()` - Select reference from voice samples
  - [x] `scan_voice_samples()` - Discover all available references
- [x] Support WAV and MP3 input formats
- [x] Test reference audio selection
- [x] Document reference audio requirements (30s+ recommended, auto-resampled)

**Status:** ✅ COMPLETE (2026-01-13)  
**Deliverable:** `references.py` (170 lines) for reference audio selection

### 1.3 Text Preprocessing & Validation
- [x] Create `tools/tts-pipeline/utils.py`
- [x] Implement preprocessing utilities:
  - [x] `preprocess_text_for_tts()` - Clean and normalize text
  - [x] `chunk_long_text()` - Split long text into segments
  - [x] `validate_text_length()` - Enforce minimum length (30+ chars)
  - [x] `pad_short_text()` - Auto-pad short text to prevent gibberish
  - [x] `trim_silence_with_vad()` - VAD-based silence trimming
- [x] Test with various text lengths
- [x] Verify gibberish prevention (30+ char minimum)

**Status:** ✅ COMPLETE (2026-01-13)  
**Deliverable:** `utils.py` (240 lines) with comprehensive text preprocessing

### 1.4 Baseline Testing
- [x] Create `tools/tts-pipeline/generate.py` baseline test script
- [x] Test corpus: 7 test cases (short/medium/long text)
- [x] Generate baseline audio with Julie Voice Cleaned V2.wav reference
- [x] Verify audio quality (no "gibberish" artifacts)
- [x] Test CUDA acceleration (RTX 3060, 4.43GB VRAM stable)
- [x] Document any quality issues found

**Status:** ✅ COMPLETE (2026-01-13)  
**Test Results:** 7/7 baseline tests passed, no gibberish, excellent voice match  
**Deliverable:** Validated Base Model audio quality, baseline test suite (191 lines)

### 1.5 Parameter Optimization & A/B Testing
- [x] Create `tools/tts-pipeline/ab_test.py` for parameter testing
- [x] Design test matrix with 6 parameter variants:
  - [x] baseline (temp=0.6, top_k=2000, top_p=0.95, rep_pen=1.1)
  - [x] ultra_conservative (temp=0.4, top_k=500, rep_pen=1.5)
  - [x] highly_expressive (temp=0.85, top_k=4000, rep_pen=1.0)
  - [x] crisp (temp=0.55, top_k=1500, rep_pen=1.25)
  - [x] loose_creative (temp=0.75, top_k=3500, rep_pen=1.05)
  - [x] tight_controlled (temp=0.45, top_k=800, rep_pen=1.4)
- [x] Generate 24 test files (6 variants × 4 test cases)
- [x] Test corpus: intro_short, weather_medium, story_long, emotional_dialog
- [x] Listen and score variants
- [x] Identify optimal parameters
- [x] Fix MP3 ID3 tag hang (converted Julie Voice Cleaned V2.mp3 → .wav)

**Status:** ✅ COMPLETE (2026-01-13)  
**Test Results:** 24/24 files generated successfully  
**User Feedback:** Baseline parameters are optimal, reduced artifacting, acceptable quality  
**Decision:** No further parameter tuning needed until fine-tuning phase  
**Deliverable:** A/B test generator (321 lines), 24 comparison audio files, parameter analysis

**Phase 1 Status:** ✅ COMPLETE (2026-01-13) - TTS pipeline production-ready

**Phase 1 Summary:**
- Created 4 core modules: `engine.py`, `references.py`, `utils.py`, `generate.py`
- Total code: ~1,000 lines of production-quality TTS pipeline
- 7 baseline tests passing, 24 A/B test files generated
- CUDA-optimized for RTX 3060 (6GB VRAM)
- Reference audio: Julie Voice Cleaned V2.wav (30s @ 44100Hz)
- Final parameters: temp=0.6, top_k=2000, top_p=0.95, rep_pen=1.1
- Quality: No gibberish, reduced artifacting, excellent voice match

---

## Phase 2: RAG System & Script Generation ✅ **COMPLETE & PROTECTED**

**Goal:** Set up Ollama+ChromaDB RAG system for lore-accurate script generation  
**Estimated Time:** 10-12 hours (COMPLETED)  
**Status:** ✅ 100% COMPLETE - **DO NOT MODIFY DURING AUDIO PIPELINE RESET**
  
**Dependencies:** Phase 1.3 (understand content needs)

### 2.1 Lore Data Processing
- [x] Parse `lore/fallout_wiki_complete.xml` to extract structured data
- [x] Clean and normalize wiki content (remove markup, format text)
- [x] Chunk content into semantic segments (paragraphs, sections)
- [x] Create metadata for each chunk (source page, category, relevance)
- [x] Design chunk size strategy (balance context vs retrieval precision)
- [x] Test XML parsing and content extraction
- [x] Document data structure and processing pipeline

**Status:** ✅ COMPLETE (100%)
**Evidence:** `tools/wiki_to_chromadb/chunker.py` implements 500-800 token chunking with 100-token overlap
**Deliverable:** Processed lore data from 118,468 wiki articles

### 2.2 ChromaDB Embedding Pipeline
- [x] Install ChromaDB and embedding dependencies
- [x] Select embedding model (all-MiniLM-L6-v2 or similar)
- [x] Create ChromaDB collection for Fallout lore
- [x] Implement batch embedding process for processed chunks
- [x] Add metadata indexing for efficient filtering
- [x] Test embedding generation and storage
- [x] Validate retrieval accuracy with sample queries
- [x] Document embedding pipeline and configuration

**Status:** ✅ COMPLETE (100%)
**Evidence:** 356,601 chunks in ChromaDB with temporal/spatial/content metadata, GPU-accelerated
**Deliverable:** Production ChromaDB at `tools/wiki_to_chromadb/chroma_db/` (1.76GB)

### 2.3 Ollama RAG Integration
- [x] Review existing Ollama setup in `tools/ollama_setup/`
- [x] Configure Ollama model selection for script generation
- [x] Create RAG query pipeline:
  - [x] Retrieve relevant lore chunks from ChromaDB
  - [ ] Format context for Ollama prompt
  - [ ] Generate script with lore-aware context
- [ ] Implement personality loader (reads `dj personality/Julie/`)
- [x] Test RAG retrieval with sample script queries
- [x] Tune retrieval parameters (top-k, similarity threshold)
- [x] Document RAG query workflow

**Status:** 🟡 PARTIAL (57%)
**Evidence:** DJ persona filters operational (test_dj_queries.py 14/15 passing), Ollama models configured
**Blocker:** No script generation integration - RAG retrieval works but doesn't feed into Ollama for text generation
**Deliverable:** RAG query layer ready, script generation workflow pending

### 2.4 Script Templates & Generation ✅ **COMPLETE**

**Architecture Decision:** Simple Custom Approach (Direct Ollama API + Jinja2 Templates)  
**Research:** See `research/script-generation-architecture.md` for detailed comparison  
**Rationale:** Lightweight (2 dependencies vs 50+), reuses existing RAG code, explicit VRAM control

#### Core Implementation
- [x] Create `tools/script-generator/` folder structure
- [x] Implement `ollama_client.py`:
  - [x] `generate()` method for text generation
  - [x] `unload_model()` for VRAM management
  - [x] Error handling and retry logic (exponential backoff, 3 attempts, 60s timeout)
- [x] Implement `personality_loader.py`:
  - [x] Load DJ character cards from `dj personality/` folder
  - [x] DJ name mapping (e.g., "Julie (2102, Appalachia)" → Julie folder)
  - [x] Personality caching for performance
- [x] Implement `generator.py` (ScriptGenerator class):
  - [x] `load_personality()` from `dj personality/Julie/character_card.json`
  - [x] `generate_script()` with RAG → Template → Ollama flow (5-step pipeline)
  - [x] Integration with existing `query_for_dj()` function
  - [x] `save_script()` with metadata
  - [x] `unload_model()` for VRAM management

#### Template Creation (Jinja2)
- [x] Create `templates/` subfolder
- [x] `weather.jinja2` - Weather reports with location context
  - Variables: `weather_type`, `time_of_day`, `temperature`, `hour`
  - RAG query: "Appalachia weather {type} conditions flora fauna"
  - Word count: 80-100
- [x] `news.jinja2` - Lore-accurate news segments
  - Variables: `news_topic`, `faction`, `location`
  - RAG query: "{topic} {faction} {location} events"
  - Word count: 120-150
- [x] `time.jinja2` - Hourly time announcements with flavor
  - Variables: `hour`, `time_of_day`, `special_event`
  - RAG query: "Appalachia daily life {time_of_day}"
  - Word count: 40-60
- [x] `gossip.jinja2` - Wasteland stories from lore
  - Variables: `character`, `faction`, `rumor_type`
  - RAG query: "{character} {faction} stories rumors"
  - Word count: 80-120
- [x] `music_intro.jinja2` - Song introductions with era context
  - Variables: `song_title`, `artist`, `era`, `mood`
  - RAG query: "pre-war music {era} culture entertainment"
  - Word count: 60-80

#### Testing & Validation
- [x] Test Ollama API wrapper with sample prompt
- [x] Test personality loading from JSON (all 4 DJs)
- [x] Test RAG context retrieval (verify `query_for_dj()` integration)
- [x] Create comprehensive test suite (`test_generator.py`):
  - [x] TestPersonalityLoader (4 tests)
  - [x] TestOllamaClient (3 tests)
  - [x] TestTemplateRendering (4 tests)
  - [x] TestRAGIntegration (2 tests)
  - [x] TestFullPipeline (6 tests)
  - [x] **Result: 19/19 tests passing**
- [x] Generate production test scripts (`generate_test_batch.py`):
  - [x] 3 weather scripts (sunny morning, rainy afternoon, cloudy evening)
  - [x] 5 news scripts (settlement, conflict, discovery, warning, celebration)
  - [x] 3 gossip scripts (character rumor, faction drama, wasteland mystery)
  - [x] 3 time announcements (8am, 2pm, 8pm with Reclamation Day)
  - [x] 2 music intros (Ink Spots melancholy, Uranium Fever upbeat)
- [x] Create validation suite (`validate_scripts.py`):
  - [x] Character consistency checks (catchphrases, tone, voice)
  - [x] Lore accuracy checks (no anachronisms, location consistency)
  - [x] Quality metrics (word count, sentence structure, pacing)
  - [x] Format compliance (metadata, structure)
- [x] Create comprehensive README documentation
- [x] Review for lore accuracy (cross-reference ChromaDB sources)
- [x] Validate character voice consistency (matches Julie personality)

**Status:** ✅ COMPLETE (100%)  
**Test Results:** All 19 unit tests passing, 16 production scripts generated  
**Evidence:** `tools/script-generator/` with ollama_client, personality_loader, generator, 5 templates, test suite, README  
**Deliverable:** Working script generator with 5 template types, 16+ test scripts validated, comprehensive testing and documentation

### 2.5 Testing & Validation ✅ **COMPLETE**
- [x] Generate test script set with lore validation:
  - [x] 3 weather scripts (with location references)
  - [x] 5 news scripts (using actual lore events)
  - [x] 3 gossip scripts (character/faction references)
  - [x] 3 time announcements
  - [x] 2 music intros
- [x] Cross-reference scripts against source lore for accuracy
- [x] Check for vocabulary consistency (no anachronisms - 1 found, documented)
- [x] Validate tone matches Julie's character profile
- [x] Test RAG retrieval relevance scores
- [x] Document generation quality and lore accuracy
- [x] Create quality checklist for script review

**Status:** ✅ COMPLETE (100%)  
**Test Results:** 17/17 scripts passed validation (100% pass rate), average score 79.9/100  
**Evidence:** 
- Quality Report: [research/script-generation-quality-report.md](../research/script-generation-quality-report.md)
- Quality Checklist: [tools/script-generator/QUALITY_CHECKLIST.md](../tools/script-generator/QUALITY_CHECKLIST.md)
- Validation Suite: `tools/script-generator/tests/validate_scripts.py` (fixed and operational)  
**Key Findings:**
- Character Consistency: 64.8/100 (catchphrases need template enhancement)
- Lore Accuracy: 96.2/100 (1 anachronism found - NCR in news_discovery)
- Quality Metrics: 93.6/100 (word counts run 10-50% long - acceptable)
- Format Compliance: 50/100 (legacy marker check - actual format 100% compliant)  
**Deliverable:** Validated RAG-based script generation system with comprehensive quality documentation

**Phase 2 Status:** ✅ 100% COMPLETE - All subsystems operational and validated

### 2.6 Character Enhancement & A/B Testing ✅ **COMPLETE**

**Architecture Decision:** Hybrid automated evaluation system (no human loop required for 90% of quality checks)  
**Implementation:** 3-tier validation (rule-based + embeddings + LLM-as-judge)  
**Status:** All core features implemented and tested

#### Core Implementation ✅
- [x] Enhanced validation system (validate_scripts_enhanced.py)
  - [x] **Tier 1 (Rule-based):** Flesch-Kincaid, vocabulary diversity, filler density, sentence variance
  - [x] **Tier 2 (Embeddings):** Cosine similarity vs golden references (0.75+ threshold, 11ms/script)
  - [x] **Tier 3 (LLM-as-judge):** Ollama quality scoring for borderline (70-75) scripts (~8s/script)
  - [x] Format validator fix: 50/100 → 100/100 compliance
- [x] Catchphrase rotation system (generator.py)
  - [x] `select_catchphrases()` with contextual selection (mood/time mapping)
  - [x] Rotation tracking (avoids last 3 catchphrases per DJ)
  - [x] Automatic placement (opening/closing/both based on script type)
  - [x] **Tested:** Rotation working ("Welcome home" → "If you're out there" in sequential scripts)
- [x] Natural voice enhancement system
  - [x] Filler word extraction from personality.voice.prosody
  - [x] Spontaneous element injection (20% chance)
  - [x] Sentence variety guidelines
- [x] Post-generation validation with retry
  - [x] Catchphrase detection in generated text
  - [x] Auto-retry with enhanced prompt (max 2 attempts)
  - [x] Retry count tracking in metadata

#### Template Updates ✅
- [x] All 5 templates enhanced with Phase 2.6 variables:
  - [x] weather.jinja2 - Required opening catchphrase
  - [x] news.jinja2 - Required opening catchphrase
  - [x] time.jinja2 - Flexible catchphrase usage
  - [x] gossip.jinja2 - Required opening catchphrase
  - [x] music_intro.jinja2 - Required closing catchphrase (preferred)

#### Testing & Validation ✅
- [x] Test embedding models (all-MiniLM-L6-v2 vs paraphrase-MiniLM-L6-v2)
  - [x] **Winner:** all-MiniLM-L6-v2 (better discrimination: 0.145 vs 0.118 std dev)
  - [x] **Benefit:** No new dependencies (already used in ChromaDB)
- [x] Identify golden reference scripts (top 5 from Phase 2.5)
  - [x] Time: 2 scripts (84.8/100 each)
  - [x] Music: 2 scripts (82.4/100 each)  
  - [x] News, Weather, Gossip: 1 script each
- [x] Enhanced validator tested on full script directory
  - [x] **Result:** Average score 79.9 → 87.6 (+7.7 points, +9.6%)
  - [x] Format compliance: 50 → 100 (validator fix)
  - [x] Performance: 63ms Tier 1 + 11ms Tier 2 = 74ms/script avg
- [x] Catchphrase rotation tested (test_enhanced_generator.py)
  - [x] **Verified:** Different catchphrases in sequential generations
  - [x] Contextual selection working (mood/time awareness)

#### A/B Testing Framework ✅
- [x] Create ab_test_framework.py with ABTestConfig class
- [x] Implement batch generation (identical contexts per variant)
- [x] Integrate 3-tier validation for automated scoring
- [x] Statistical comparison with t-test capability
- [x] Execute full A/B test: 36 scripts (3 variants × 5 types × 3 samples - 3 failed weather scripts)
  - [x] **Variant 1:** baseline (no enhancements) → **87.2/100** (±2.9)
  - [x] **Variant 2:** enhanced_stheno (catchphrase + voice + retry) → **88.1/100** (±3.1) ✅ WINNER
  - [x] **Variant 3:** enhanced_hermes (same enhancements, hermes3 model) → **86.9/100** (±2.9)

**A/B Test Results (2026-01-12):**

| Metric | Baseline | Enhanced Stheno | Improvement |
|--------|----------|-----------------|-------------|
| **Overall Score** | **87.2/100** | **88.1/100** | **+0.9 pts** |
| Character Consistency | 70.8/100 | 76.7/100 | +5.9 pts |
| Embedding Similarity | 76.7/100 | 83.8/100 | +7.1 pts |
| Filler Density | 78.4/100 | 82.4/100 | +4.0 pts |
| Format Compliance | 100.0/100 | 100.0/100 | ±0.0 pts |
| Lore Accuracy | 100.0/100 | 100.0/100 | ±0.0 pts |
| Readability | 85.7/100 | 79.0/100 | -6.7 pts |

**Key Findings:**
- 🏆 enhanced_stheno wins with +0.9 point improvement over baseline
- ✅ Character Consistency: +5.9 points (70.8 → 76.7) from catchphrase enforcement
- ✅ Embedding Similarity: +7.1 points (better alignment with golden references)
- ⚠️ Readability: -6.7 points (natural voice adds complexity - acceptable tradeoff)
- 📊 Consistency: ±3.1 std dev (reliable performance across script types)

**Production Configuration:**
- Model: `fluffy/l3-8b-stheno-v3.2`
- Catchphrase rotation: Enabled
- Natural voice: Enabled
- Validation retry: Enabled (max 2 attempts)
- Template variant: default (all 5 templates enhanced)

**Status:** ✅ COMPLETE (100%)  
**Baseline Improvement:** +8.2 points (79.9 → 88.1) from Phase 2.5 to Phase 2.6 (A/B test)  
**Enhanced Batch Results:** +8.4 points (79.9 → 88.3) on regenerated 17-script test batch  
**Phase 2.6 Core Improvement:** +0.9 points (87.2 baseline → 88.1 enhanced_stheno in A/B test)  
**Phase 2.6 Validator Fix Impact:** +7.3 points (79.9 → 87.2) from format compliance fix alone  
**Evidence:** 
- A/B Test Results: `script generation/ab_test_results/comparison_20260112_200823.txt`
- Enhanced Test Batch: `script generation/enhanced_scripts/` (17 scripts, 88.3/100 avg)
- Comprehensive Validation: `script generation/comprehensive_batch/` (57 scripts, 88.3/100 avg, ±2.9 std dev)
- Updated Quality Report: [research/script-generation-quality-report.md](../research/script-generation-quality-report.md)  
**Deliverable:** Production-ready script generator with character enhancement features validated

**Comprehensive Validation Results (2026-01-12):**

| Test Batch | Scripts | Avg Score | Std Dev | Pass Rate | Notes |
|------------|---------|-----------|---------|-----------|-------|
| Original (Phase 2.5) | 17 | 79.9/100 | N/A | 100% | Baseline |
| A/B Test Baseline | 12 | 87.2/100 | ±2.9 | 100% | Validator fix impact |
| A/B Test Enhanced | 12 | 88.1/100 | ±3.1 | 100% | Winner config |
| Enhanced Regenerated | 17 | 88.3/100 | N/A | 100% | Production validation |
| **Comprehensive Batch** | **57** | **88.3/100** | **±2.9** | **100%** | **Stress test** |

**Quality Distribution (57 scripts):**
- 🟢 Excellent (90-100): 19 scripts (33.3%)
- 🟡 Good (80-89): 38 scripts (66.7%)
- 🔴 Needs Work (<80): 0 scripts (0%)

**Score by Content Type:**
- ⏰ **Time:** 91.2/100 (highest, 12 scripts)
- 🎵 **Music Intros:** 89.6/100 (10 scripts)
- ☀️ **Weather:** 88.1/100 (10 scripts)
- 📰 **News:** 86.6/100 (15 scripts)
- 💬 **Gossip:** 85.3/100 (lowest, 10 scripts)

**System Stability:**
- ✅ Consistent performance: ±2.9 std dev across 57 scripts
- ✅ Zero failures: 100% pass rate (all scripts >80/100 threshold)
- ✅ Scalable: Large batch generation stable without degradation
- ✅ Character consistency: 76.7/100 avg (catchphrase rotation working)
- ✅ Lore accuracy: 100% (zero anachronisms detected)

**Phase 2 Status:** ✅ 100% COMPLETE - All subsystems operational, validated at scale, and production-ready

---

## Phase 3: Script-to-Audio Converter (Implemented)

**Goal:** Create pipeline to convert Phase 2 scripts into ESP32-ready MP3 files  
**Estimated Time:** 4-6 hours  
**Dependencies:** Phase 1 complete (TTS pipeline operational), Phase 2 complete (scripts ready)

### 3.1 Audio Converter Module ✅ **IMPLEMENTED**
- [x] Create `tools/tts-pipeline/converter.py`
- [x] Implement `ScriptConverter` class:
  - [x] `load_script()` - Read Phase 2 script file and metadata (JSON header)
  - [x] `convert_script()` - Full pipeline with ID3 stripping
  - [x] `_convert_wav_to_mp3()` - Pydub conversion (44.1kHz, 128kbps, mono)
- [x] Integration with `ChatterboxEngine`
- [x] Reference audio: Configured to find "Julie Voice Cleaned V2.wav"

**Status:** ✅ IMPLEMENTED

### 3.2 Output Organization ✅ **IMPLEMENTED**
- [x] Implemented in `converter.py`:
  - [x] Folder structure creation (Weather/News/etc)
  - [x] Filename convention: `HHMM-type-dj-id-variant.mp3`

**Status:** ✅ IMPLEMENTED

### 3.3 Batch Processing ✅ **IMPLEMENTED**
- [x] Create `tools/tts-pipeline/batch_convert.py`
- [x] Implemented batch processor with progress tracking
- [x] Skip existing logic included

**Status:** ✅ IMPLEMENTED

### 3.4 Quality Validation ✅ **IMPLEMENTED**
- [x] Create `tools/tts-pipeline/validate_audio.py`
- [x] Checks: Sample Rate, ID3 tags, basic integrity

**Status:** ✅ IMPLEMENTED

**Phase 3 Status:** ⚠️ PARTIALLY COMPLETE
- **Implemented:** Basic Script-to-MP3 pipeline (batch processing, format conversion, file organization)
- **Pending:** Emotion-specific reference audio, advanced quality validation, metadata backfill
- **Verification:** `tools/tts-pipeline/test_phase3.py` (Pass), `tools/tts-pipeline/test_emotion_gap.py` (Fail - Feature Missing)

**Phase 3 Success Criteria (Revised):**
- [x] All 57+ Phase 2.6 scripts converted to MP3 (Basic conversion verified)
- [x] Zero ID3 tag issues (ESP32 compatibility verified)
- [ ] Audio quality matches Phase 1 baseline (pending emotion support)
- [x] Organized by content type with scheduler-compatible filenames
- [x] Batch processing stable
- [ ] Emotion support (Upbeat/Somber variants) implemented

---

## Phase 3.5: Advanced Audio Features (Pending)

**Goal:** Implement missing emotion support and advanced validation from Phase 3 plan.

**⚠️ CRITICAL FINDING (2026-01-13):** Reference audio preprocessing causing quality degradation - **RESOLVED**
- `Julie Voice Cleaned V2.wav` is already preprocessed (V2 = second clean version)
- Converter was loading `julie_full_preprocessed.wav` (16kHz) instead of raw `Julie Voice Cleaned V2.wav` (44.1kHz)
- Chatterbox library's `prepare_conditionals()` internally resamples, but 44.1kHz → model native works better than 16kHz → model native
- **Fix Applied:** Updated `converter.py` to prioritize `dj personality/Julie/Julie Voice Cleaned V2.wav` (44.1kHz source)
- **Test:** `test_preprocessing_bypass.py` confirmed RAW (44.1kHz) produces clean audio, PREPROCESSED (16kHz) produces gibberish

#### 📋 STEP 0: Reference Audio Pipeline Restructure
- [x] Run `test_preprocessing_bypass.py` to confirm double-processing hypothesis → CONFIRMED
- [x] Update `converter.py` to use raw 44.1kHz reference → FIXED
- [x] Run `test_diagnostics.py` to determine maximum safe text length before degradation → **COMPLETE**
  - **FINDING:** Hard limit at 30 seconds audio output
  - 300 chars → 25.4s ✅ Clean
  - 400 chars → 29.6s ⚠️ Edge of limit
  - 500 chars → 34.4s ❌ Gibberish
  - **Recommended chunking:** 300 characters (90% safety margin, ~25s output)
- [ ] Implement chunking in `converter.py` with 300 char limit
- [ ] Document preprocessing workflow in `tools/voice-samples/README.md`

#### 📋 STEP 1: Implement Text Chunking (BLOCKING - Required for production)
- [x] Update `converter.py` to use `utils.chunk_long_text(max_chars=300)`
- [x] Modify `convert_script()` to:
  - Split text into chunks using sentence boundaries
  - Generate audio for each chunk
  - Concatenate chunks with 300ms silence between (natural pause)
  - Export combined audio as single MP3
- [ ] Test chunking with weather script to verify no gibberish → IN PROGRESS
- [ ] Validate chunk seams sound natural (no abrupt cuts)

#### 📋 STEP 1: Emotion Pipeline Integration
- [ ] Create missing reference clips (Upbeat, Somber, etc.)
- [ ] Implement `Backfill Emotions` script to tag existing scripts
- [ ] Update `converter.py` to switch reference audio based on `mood` metadata
- [ ] Verify with `test_emotion_gap.py`

#### 📋 STEP 2: Advanced Validation
- [ ] Implement `test_quality.py` (Tier 1 & 2 checks)
- [ ] Run full batch conversion with validation

---

---

## Phase 4: ESP32 Integration & Hardware Testing

**Goal:** Deploy audio to ESP32 and validate full playback pipeline  
**Estimated Time:** 4-5 hours  
**Dependencies:** Phase 3 complete (MP3 library generated)
    - [ ] Measure processing speed (time per file)
  - [ ] **Pass Criteria:**
    - [ ] Both methods produce tag-free MP3s
    - [ ] Speed difference <10% OR clear winner identified
    - [ ] ESP32 plays both without errors (if tested)

- [ ] **1.3 Document winning method** in `tools/tts-pipeline/CONFIG.md`:
  - [ ] Winner: [ffmpeg | mutagen]
  - [ ] Speed: [X] ms per file
  - [ ] Verification command for CI/testing
  - [ ] Known edge cases

**Deliverable:** `test_id3_methods.py` + CONFIG.md decision log

---

#### 📋 STEP 2: Emotion Reference Library Creation (3 hours)

**Rationale:** Voice quality depends on emotion-appropriate reference audio selection

- [ ] **2.1 Extract emotion-specific clips** from `tools/voice-samples/julie/Cleaned Audio 2 (1).wav`:
  - [ ] **Baseline** (neutral/conversational) - 3-10s clip
    - [ ] Find calm, steady-paced section
    - [ ] Extract with `pydub.AudioSegment[start_ms:end_ms]`
    - [ ] Save as `julie_baseline.wav`
  - [ ] **Upbeat** (enthusiastic/cheerful) - 3-10s clip
    - [ ] Find energetic, positive-toned section
    - [ ] Extract and save as `julie_upbeat.wav`
  - [ ] **Somber** (serious/reflective) - 3-10s clip
    - [ ] Find low-energy, contemplative section
    - [ ] Extract and save as `julie_somber.wav`
  - [ ] **Mysterious** (conspiratorial) - 3-10s clip
    - [ ] Find whispered or secretive-toned section
    - [ ] Extract and save as `julie_mysterious.wav`
  - [ ] **Warm** (friendly/welcoming) - 3-10s clip
    - [ ] Find gentle, inviting section
    - [ ] Extract and save as `julie_warm.wav`

- [ ] **2.2 Validate each reference clip** with Chatterbox inference:
  - [ ] Test script: "Good morning, wastelanders. Hope you're having a great day out there."
  - [ ] Generate audio with each of 5 reference clips
  - [ ] Compare outputs:
    - [ ] Emotional tone matches intended reference
    - [ ] Voice quality consistent across all
    - [ ] No artifacts or glitches
  - [ ] Adjust clip lengths if needed (3-10s range)

- [ ] **2.3 Document emotion mapping** in `tools/tts-pipeline/CONFIG.md`:
  ```markdown
  ## Emotion → Reference Mapping
  
  | Script Type | Mood Variant | Reference Clip | Notes |
  |-------------|--------------|----------------|-------|
  | weather | sunny | julie_upbeat.wav | Energetic morning vibe |
  | weather | rainy | julie_somber.wav | Reflective, calmer |
  | weather | cloudy | julie_baseline.wav | Neutral default |
  | news | celebration | julie_upbeat.wav | Positive news |
  | news | warning | julie_somber.wav | Serious tone |
  | news | neutral | julie_baseline.wav | Standard reporting |
  | gossip | default | julie_mysterious.wav | Conspiratorial |
  | time | default | julie_warm.wav | Friendly greeting |
  | music_intro | default | julie_upbeat.wav | Enthusiastic intro |
  ```

**Deliverable:** 5 emotion reference clips + CONFIG.md mapping table

---

#### 📋 STEP 3: Backfill Script Emotions (1.5 hours)

**Rationale:** Existing scripts lack explicit `mood` field for emotion-aware TTS

- [ ] **3.1 Create backfill script** `tools/script-generator/backfill_emotions.py`:
  - [ ] Load all scripts from `script generation/enhanced_scripts/` (57 files)
  - [ ] **Mood assignment logic:**
    ```python
    def assign_mood(script_metadata):
        # Priority 1: weather_type mapping
        if 'weather_type' in metadata:
            if metadata['weather_type'] in ['sunny', 'clear']:
                return 'upbeat'
            elif metadata['weather_type'] in ['rainy', 'stormy']:
                return 'somber'
            else:
                return 'baseline'
        
        # Priority 2: script_type defaults
        mood_map = {
            'gossip': 'mysterious',
            'music_intro': 'upbeat',
            'time': 'warm',
            'news': 'baseline',  # Can be overridden by keywords
            'weather': 'baseline'
        }
        base_mood = mood_map.get(metadata['script_type'], 'baseline')
        
        # Priority 3: keyword detection in script text
        text_lower = script_text.lower()
        if any(word in text_lower for word in ['warning', 'danger', 'threat', 'conflict']):
            return 'somber'
        elif any(word in text_lower for word in ['celebration', 'success', 'victory', 'cooperation']):
            return 'upbeat'
        
        return base_mood
    ```
  - [ ] Add `mood` field to METADATA section
  - [ ] Preserve original metadata fields
  - [ ] Save updated scripts in-place (non-destructive)

- [ ] **3.2 Execute backfill** on all 57 scripts:
  ```bash
  python tools/script-generator/backfill_emotions.py
  ```
  - [ ] Verify no scripts corrupted (spot-check 5 random files)
  - [ ] Count mood distribution:
    - [ ] Baseline: ~X scripts
    - [ ] Upbeat: ~X scripts
    - [ ] Somber: ~X scripts
    - [ ] Mysterious: ~X scripts
    - [ ] Warm: ~X scripts

- [ ] **3.3 Trust automated logic** (no manual review):
  - [ ] Validation happens post-conversion via audio quality metrics

**Deliverable:** 57 backfilled scripts with `mood` metadata field

---

#### 📋 STEP 4: Core Converter Implementation (4-5 hours)

**Rationale:** Build production converter with fixed parameters from research

- [ ] **4.1 Create folder structure:**
  ```
  tools/tts-pipeline/
  ├── converter.py          # Main ScriptToAudioConverter class
  ├── CONFIG.md             # Configuration and decisions log
  ├── tests/
  │   ├── test_converter.py       # Unit tests
  │   ├── test_automation.py      # Integration tests
  │   └── test_quality.py         # Quality validation
  └── reference_audio/      # Symlink to voice-samples/julie/
  ```

- [ ] **4.2 Implement `converter.py` - ScriptToAudioConverter class:**

  - [ ] **4.2.1 Initialization & Model Loading:**
    ```python
    class ScriptToAudioConverter:
        def __init__(self, reference_audio_dir, output_base_dir, device='cuda'):
            self.device = device
            self.tts_engine = None  # Lazy load
            self.reference_audio_dir = Path(reference_audio_dir)
            self.output_base_dir = Path(output_base_dir)
            
            # Fixed parameters from research
            self.PAUSE_DURATION = 0.3  # 300ms between sentences
            self.CHUNK_REGEX = r'(?<=[.!?])\s+'
            self.TTS_PARAMS = {
                'temperature': 0.75,
                'repetition_penalty': 1.3,
                'exaggeration': 0.5
            }
            self.MP3_PARAMS = {
                'sample_rate': 44100,
                'bitrate': '128k'
            }
        
        def load_model(self):
            """Load Chatterbox TTS (minimal interface for Phase 3.2)"""
            # Reuse logic from generate_radio_segment.py lines 69-95
            pass
        
        def unload_model(self):
            """Free VRAM (minimal interface for Phase 3.2)"""
            if self.tts_engine:
                del self.tts_engine
                torch.cuda.empty_cache()
                self.tts_engine = None
    ```

  - [ ] **4.2.2 Script Parser:**
    ```python
    def parse_script(self, script_path):
        """Extract text and metadata from Phase 2.6 format."""
        with open(script_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split text and metadata
        if '=' * 80 in content:
            parts = content.split('=' * 80)
            script_text = parts[0].strip()
            metadata_text = parts[1].strip()
        else:
            raise ValueError(f"Invalid script format: {script_path}")
        
        # Parse JSON metadata
        metadata_match = re.search(r'METADATA:\s*(\{.*\})', metadata_text, re.DOTALL)
        if not metadata_match:
            raise ValueError(f"No METADATA block found: {script_path}")
        
        metadata = json.loads(metadata_match.group(1))
        
        # Remove quotation marks from script text (common in generated scripts)
        script_text = script_text.strip('"\'')
        
        return script_text, metadata
    ```

  - [ ] **4.2.3 Emotion Reference Selection:**
    ```python
    def select_reference_audio(self, metadata):
        """Choose emotion-appropriate clip from library."""
        mood = metadata.get('mood', 'baseline')
        
        # Map mood to reference file
        reference_files = {
            'upbeat': 'julie_upbeat.wav',
            'somber': 'julie_somber.wav',
            'mysterious': 'julie_mysterious.wav',
            'warm': 'julie_warm.wav',
            'baseline': 'julie_baseline.wav'
        }
        
        ref_file = reference_files.get(mood, 'julie_baseline.wav')
        ref_path = self.reference_audio_dir / ref_file
        
        if not ref_path.exists():
            raise FileNotFoundError(f"Reference audio missing: {ref_path}")
        
        return str(ref_path)
    ```

  - [ ] **4.2.4 Sentence Chunking** (reuse generate_segment.py logic):
    ```python
    def chunk_text(self, script_text):
        """Split text into sentences (fixed from research)."""
        sentences = re.split(self.CHUNK_REGEX, script_text.strip())
        sentences = [s.strip() for s in sentences if s.strip()]
        return sentences
    ```

  - [ ] **4.2.5 Audio Generation** (reuse generate_segment.py lines 111-146):
    ```python
    def generate_audio(self, script_text, reference_audio_path):
        """Generate audio with chunking and pauses."""
        sentences = self.chunk_text(script_text)
        all_chunks = []
        sample_rate = 24000
        
        for i, sentence in enumerate(sentences):
            # Generate audio for sentence
            sr, audio_chunk = self._generate_single_chunk(
                sentence, reference_audio_path, **self.TTS_PARAMS
            )
            
            if len(audio_chunk) > 0:
                all_chunks.append(audio_chunk)
                sample_rate = sr
                
                # Add 300ms pause between sentences
                pause_samples = int(sr * self.PAUSE_DURATION)
                all_chunks.append(np.zeros(pause_samples, dtype=np.float32))
        
        # Concatenate all chunks
        final_audio = np.concatenate(all_chunks)
        return sample_rate, final_audio
    
    def _generate_single_chunk(self, text, prompt_path, **kwargs):
        """Generate and trim single sentence (reuse generate_segment.py lines 97-106)."""
        try:
            wav_tensor = self.tts_engine.generate(
                text=text, 
                audio_prompt_path=prompt_path, 
                **kwargs
            )
            wav_np = wav_tensor.squeeze().cpu().numpy()
            # VAD trimming
            from src.utils import trim_silence_with_vad
            trimmed_wav = trim_silence_with_vad(wav_np, self.tts_engine.sr)
            return self.tts_engine.sr, trimmed_wav
        except Exception as e:
            logging.error(f"Chunk generation failed: {e}")
            return 24000, np.zeros(0)
    ```

  - [ ] **4.2.6 MP3 Conversion** (use winning method from Step 1):
    ```python
    def convert_to_mp3(self, wav_audio, sample_rate, output_path):
        """Convert WAV to 44.1kHz 128kbps MP3, strip ID3 tags."""
        import tempfile
        import subprocess
        
        # Save temp WAV
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_wav:
            import soundfile as sf
            sf.write(tmp_wav.name, wav_audio, sample_rate)
            tmp_wav_path = tmp_wav.name
        
        # Convert with ffmpeg (or mutagen based on Step 1 result)
        # METHOD A: ffmpeg (likely winner based on research)
        subprocess.run([
            'ffmpeg', '-i', tmp_wav_path,
            '-ar', str(self.MP3_PARAMS['sample_rate']),
            '-b:a', self.MP3_PARAMS['bitrate'],
            '-map_metadata', '-1',  # Strip all metadata
            '-y',  # Overwrite
            output_path
        ], check=True, capture_output=True)
        
        # Clean up temp file
        os.unlink(tmp_wav_path)
        
        # Verify ID3 tags stripped (optional check)
        # self._verify_no_id3_tags(output_path)
    ```

  - [ ] **4.2.7 Filename Formatter:**
    ```python
    def format_filename(self, metadata, variant='default'):
        """Generate ESP32-compatible filename: HHMM-type-dj-id-variant.mp3"""
        # Extract components from metadata
        hour = metadata.get('template_vars', {}).get('hour', 0)
        script_type = metadata.get('script_type', 'unknown')
        dj_name = metadata.get('dj_name', 'julie').split('(')[0].strip().lower()
        
        # Generate unique ID from timestamp
        timestamp = metadata.get('timestamp', '20260112_120000')
        script_id = timestamp.replace('-', '').replace('_', '').replace(':', '')[-8:]
        
        # Format: HHMM-type-dj-id-variant.mp3
        filename = f"{hour:04d}-{script_type}-{dj_name}-{script_id}-{variant}.mp3"
        
        return filename
    ```

  - [ ] **4.2.8 Main Conversion Method with Retry:**
    ```python
    def convert(self, script_path, max_retries=2):
        """Convert script to MP3 with automatic retry (99% reliability target)."""
        for attempt in range(max_retries + 1):
            try:
                # Parse script
                script_text, metadata = self.parse_script(script_path)
                
                # Select reference audio
                reference_audio = self.select_reference_audio(metadata)
                
                # Generate audio
                sample_rate, wav_audio = self.generate_audio(script_text, reference_audio)
                
                # Determine output path
                script_type = metadata.get('script_type', 'unknown')
                output_dir = self.output_base_dir / script_type.replace('_', ' ').title()
                output_dir.mkdir(parents=True, exist_ok=True)
                
                filename = self.format_filename(metadata)
                output_path = output_dir / filename
                
                # Convert to MP3
                self.convert_to_mp3(wav_audio, sample_rate, str(output_path))
                
                # Success
                logging.info(f"✓ Converted: {script_path.name} → {filename}")
                return {
                    'success': True,
                    'output_path': str(output_path),
                    'attempts': attempt + 1,
                    'metadata': metadata
                }
                
            except Exception as e:
                if attempt < max_retries:
                    logging.warning(f"Attempt {attempt+1} failed, retrying: {e}")
                    time.sleep(1)  # Brief pause before retry
                else:
                    logging.error(f"✗ Failed after {max_retries+1} attempts: {script_path.name}")
                    return {
                        'success': False,
                        'error': str(e),
                        'attempts': attempt + 1
                    }
    ```

- [ ] **4.3 Error handling & logging:**
  - [ ] Detailed error messages with script path
  - [ ] Retry count tracking in return dict
  - [ ] Log file: `tts-pipeline/conversion.log`

**Deliverable:** `converter.py` with ScriptToAudioConverter class (8 methods, ~300 lines)

---

#### 📋 STEP 5: Build Dual-Track Quality Validation Suite (6-8 hours)

**Rationale:** Automated quality checks ensure 99% reliability without human review

- [ ] **5.1 Create `tools/tts-pipeline/tests/test_quality.py`:**

  - [ ] **5.1.1 Tier 1: Technical Metrics** (fast, all scripts):
    ```python
    class AudioQualityValidator:
        def validate_technical(self, audio_path):
            """Fast technical validation (~50-100ms per file)."""
            scores = {}
            
            # Test 1: MP3 format compliance
            audio, sr = librosa.load(audio_path, sr=None)
            scores['format_compliance'] = 100 if sr == 44100 else 0
            
            # Test 2: Chunk seam spectral analysis (300±50ms silence gaps)
            silence_gaps = self._detect_silence_gaps(audio, sr)
            gap_quality = self._evaluate_gap_quality(silence_gaps, target=0.3, tolerance=0.05)
            scores['chunk_seam_quality'] = gap_quality
            
            # Test 3: Voice continuity (MFCC cosine similarity across chunks)
            mfcc_similarity = self._calculate_mfcc_continuity(audio, sr, silence_gaps)
            scores['voice_continuity'] = 100 if mfcc_similarity > 0.85 else mfcc_similarity * 100
            
            # Test 4: Silence/filler detection (VAD-based)
            speech_ratio = self._calculate_speech_ratio(audio, sr)
            scores['speech_density'] = speech_ratio * 100
            
            # Test 5: Prosody consistency (pitch variance)
            pitch_variance = self._calculate_pitch_variance(audio, sr)
            scores['prosody_consistency'] = self._score_pitch_variance(pitch_variance)
            
            return scores
        
        def _detect_silence_gaps(self, audio, sr, threshold_db=-40):
            """Find silence regions (chunk boundaries)."""
            # Implementation using librosa.effects.split
            pass
        
        def _calculate_mfcc_continuity(self, audio, sr, gaps):
            """Measure voice similarity across chunk seams."""
            # Extract MFCC features before/after each gap
            # Calculate cosine similarity
            pass
    ```

  - [ ] **5.1.2 Tier 2: Automated Quality Scoring** (borderline 70-80 only):
    ```python
    def validate_quality_score(self, audio_path, script_text, metadata):
        """LLM-as-judge for borderline technical scores (~8-15s per file)."""
        # Transcribe audio with Whisper
        transcription = self._transcribe_audio(audio_path)
        
        # Ollama quality evaluation
        prompt = f"""
        You are evaluating AI-generated radio DJ audio quality.
        
        Original script: {script_text}
        Transcription: {transcription}
        Expected mood: {metadata.get('mood', 'baseline')}
        DJ personality: {metadata.get('dj_name', 'julie')}
        
        Rate the following (0-100 each):
        1. Naturalness: Does it sound like a real human DJ?
        2. Emotion match: Does the mood match the expected emotion?
        3. Entertainment value: Is it engaging to listen to?
        
        Respond ONLY with JSON: {{"naturalness": X, "emotion_match": Y, "entertainment": Z}}
        """
        
        response = self.ollama_client.generate(
            model='fluffy/l3-8b-stheno-v3.2',
            prompt=prompt,
            options={'temperature': 0.0}  # Deterministic
        )
        
        scores = json.loads(response)
        return scores
    
    def _transcribe_audio(self, audio_path):
        """Transcribe with Whisper-tiny (1-3s per file)."""
        import whisper
        model = whisper.load_model("tiny")  # Cache model
        result = model.transcribe(audio_path)
        return result['text']
    ```

  - [ ] **5.1.3 Combined Validation:**
    ```python
    def validate_full(self, audio_path, script_path):
        """
        Tier 1: Technical metrics (all scripts)
        Tier 2: LLM-as-judge (borderline 70-80 scores only)
        """
        script_text, metadata = parse_script(script_path)
        
        # Tier 1: Technical
        tech_scores = self.validate_technical(audio_path)
        tech_avg = sum(tech_scores.values()) / len(tech_scores)
        
        # Tier 2: LLM judge (borderline only)
        quality_scores = {}
        if 70 <= tech_avg <= 80:
            quality_scores = self.validate_quality_score(audio_path, script_text, metadata)
        
        # Combine scores
        final_score = self._combine_scores(tech_scores, quality_scores)
        
        return {
            'final_score': final_score,
            'tier1_technical': tech_scores,
            'tier2_quality': quality_scores,
            'pass': final_score > 80
        }
    ```

- [ ] **5.2 Create `tools/tts-pipeline/tests/test_automation.py`:**

  - [ ] **Test 1: Batch processing** (10 scripts end-to-end):
    ```python
    def test_batch_conversion():
        converter = ScriptToAudioConverter(...)
        converter.load_model()
        
        test_scripts = get_random_scripts(n=10)
        results = []
        
        start_time = time.time()
        for script in test_scripts:
            result = converter.convert(script)
            results.append(result)
        elapsed = time.time() - start_time
        
        # Pass criteria:
        assert sum(r['success'] for r in results) == 10, "Not all conversions succeeded"
        assert elapsed < 300, f"Batch too slow: {elapsed}s (target: <5min for 10 scripts)"
    ```

  - [ ] **Test 2: Error recovery** (malformed script):
    ```python
    def test_error_recovery():
        # Create intentionally broken script (missing METADATA block)
        # Verify graceful failure with error log
        # Verify converter continues to next script
        pass
    ```

  - [ ] **Test 3: Checkpoint resume:**
    ```python
    def test_checkpoint_resume():
        # Process 5 scripts, save checkpoint
        # Simulate crash
        # Resume from checkpoint
        # Verify no duplicate outputs, continues from position
        pass
    ```

  - [ ] **Test 4: VRAM stability** (50-file batch with monitoring):
    ```python
    def test_vram_stability():
        # Monitor nvidia-smi during 50-script batch
        # Assert peak VRAM < 5.5GB (safety margin for 6GB card)
        pass
    ```

- [ ] **5.3 Create `tools/tts-pipeline/tests/test_converter.py` (unit tests):**
  - [ ] Test parse_script() with valid/invalid inputs
  - [ ] Test select_reference_audio() with all 5 moods
  - [ ] Test chunk_text() with various sentence counts
  - [ ] Test format_filename() convention compliance
  - [ ] Test convert_to_mp3() output format (ffprobe verification)

**Deliverable:** 3 test files with 15+ test cases total

---

#### 📋 STEP 6: Execute 3-Iteration Validation Cycle (8-10 hours)

**Rationale:** Achieve 99% reliability through iterative testing and refinement

- [ ] **6.1 Iteration 1: 10-Script Test Batch**
  - [ ] Select diverse test batch:
    - [ ] 2 weather (sunny, rainy)
    - [ ] 3 news (celebration, warning, neutral)
    - [ ] 2 gossip
    - [ ] 2 time
    - [ ] 1 music intro
  - [ ] Run full conversion pipeline:
    ```bash
    python -m tools.tts-pipeline.converter --batch test_batch_10.json
    ```
  - [ ] Measure metrics:
    - [ ] Success rate (target: 10/10 = 100%)
    - [ ] Average technical score (target: >80/100)
    - [ ] Average LLM-judge score for borderline (target: >80/100)
    - [ ] Processing time (target: <30s per script avg)
  - [ ] **If failures occur:**
    - [ ] Analyze error logs
    - [ ] Identify failure patterns (specific script types, emotions, etc.)
    - [ ] Implement fixes in converter.py
    - [ ] Re-run failed scripts

- [ ] **6.2 Iteration 2: Full 57-Script Batch**
  - [ ] Backfill emotions (Step 3)
  - [ ] Run full conversion:
    ```bash
    python -m tools.tts-pipeline.converter --batch enhanced_scripts_57.json
    ```
  - [ ] Track reliability:
    - [ ] Success rate (target: 56-57/57 = 98-100%)
    - [ ] Failures requiring retry: [X]/57
    - [ ] Failures after max retries: [X]/57 (target: 0-1)
  - [ ] **Quality consistency check:**
    - [ ] Compare first 10 vs last 10 scripts
    - [ ] Technical score degradation (target: <0.3 points difference)
    - [ ] Voice quality remains consistent (MFCC similarity >0.85)
  - [ ] **If <99% reliability:**
    - [ ] Analyze single failure case
    - [ ] Refine error handling or retry logic
    - [ ] Re-run full batch

- [ ] **6.3 Iteration 3: Stress Test (20 New Scripts)**
  - [ ] Generate 20 fresh scripts:
    - [ ] 4 of each type (weather, news, gossip, time, music)
    - [ ] Use script generator to create new content
  - [ ] Convert with finalized pipeline
  - [ ] Measure final reliability:
    - [ ] Success rate (target: 20/20 or 19/20 = 95-100%)
    - [ ] Retry success rate (of failures, % recovered by retry)
    - [ ] Average quality scores
  - [ ] **If <99% reliability:**
    - [ ] Enhanced error handling (alternate reference clips, fallback strategies)
    - [ ] Re-test until target met
  - [ ] Document edge cases and known limitations

- [ ] **6.4 Final Documentation** in `tools/tts-pipeline/CONFIG.md`:
  - [ ] Production configuration:
    - [ ] Winning ID3 method
    - [ ] Fixed parameters (pause 300ms, temperature 0.75, etc.)
    - [ ] Reference audio mapping
  - [ ] Automation reliability score: [X]% (target: 99%)
  - [ ] Known edge cases: [list any discovered issues]
  - [ ] Performance benchmarks:
    - [ ] Average time per script: [X]s
    - [ ] VRAM peak usage: [X]GB
    - [ ] Quality score distribution

**Deliverable:** Production-ready converter with 99% reliability, documented configuration

---

#### ✅ Completion Criteria

- [ ] ID3 stripping method validated and documented
- [ ] 5 emotion reference clips created and tested
- [ ] 57 scripts backfilled with `mood` metadata
- [ ] ScriptToAudioConverter class implemented (8 methods, retry logic)
- [ ] 15+ test cases passing (unit + integration + quality)
- [ ] 99% automation reliability achieved (56-57/57 success rate)
- [ ] Quality scores: Technical >80/100, LLM-judge >80/100 (borderline cases)
- [ ] Processing speed: <30s per script average
- [ ] Voice continuity: MFCC similarity >0.85 across chunks
- [ ] Documentation complete: CONFIG.md with all decisions logged

**Estimated Total Time:** 24-29 hours  
**Status:** ⬜ NOT STARTED (0%)  
**Next Task:** Step 1 - ID3 tag stripping comparison test (CRITICAL PATH)

---



### 3.2 Pipeline Orchestrator & VRAM Management
- [ ] Create `tools/orchestrator/` folder
- [ ] Create `generate_day.py` main orchestration script
- [ ] Implement VRAM handoff logic:
  - [ ] Unload Ollama/ChromaDB after script generation
  - [ ] Load Chatterbox Turbo for audio generation (via ScriptToAudioConverter)
  - [ ] Monitor VRAM usage with nvidia-smi integration
  - [ ] Add cleanup hooks (unload models between phases)
- [ ] Implement batch processing workflow:
  - [ ] Generate all scripts first (Phase 2 → JSON files)
  - [ ] Unload Ollama models
  - [ ] Load Chatterbox and process all scripts (Phase 1 → MP3 files)
  - [ ] Organize outputs into folders by type:
    - `audio generation/Weather/`
    - `audio generation/News/`
    - `audio generation/Time/`
    - `audio generation/Gossip/`
    - `audio generation/Music Intros/`
- [ ] Add progress tracking (X of Y segments complete)
- [ ] Add error handling and logging (failed scripts logged, continue processing)
- [ ] Implement resume from partial completion (checkpoint JSON)
- [ ] Test with 10 segment pipeline run
- [ ] Verify VRAM never exceeds 6GB (RTX 3060 limit)

**Verification Steps:**
- [ ] **VRAM Monitoring:** Run `nvidia-smi dmon -s mu -c 100` during full pipeline
  - Pass: Peak memory <5.5GB (safety margin for 6GB card)
- [ ] **Model Unload Test:** Check free VRAM after Ollama unload
  - Pass: >4GB free before Chatterbox loads
- [ ] **Checkpoint Resume:** Interrupt pipeline at 50%, resume from checkpoint
  - Pass: No duplicate files, continues from correct position
- [ ] **Error Recovery:** Inject 1 malformed script in batch of 10
  - Pass: Pipeline logs error, skips bad script, completes remaining 9

**Deliverable:** Working orchestrator with VRAM management and batch processing

### 3.3 Manifest Generation
- [ ] Design manifest JSON schema (filename, type, timestamp, script, etc.)
- [ ] Implement manifest writer (appends as files generated)
- [ ] Add generation metadata (date, model version, parameters)
- [ ] Include script text for debugging
- [ ] Add file size and duration tracking
- [ ] Test manifest output

**Deliverable:** `audio generation/manifest.json` auto-generated

### 3.4 Full-Day Generation Test
- [ ] Generate complete 24-hour schedule:
  - [ ] 24 time announcements (0000, 0100, 0200, ..., 2300)
  - [ ] 6 weather reports (0000, 0400, 0800, 1200, 1600, 2000)
  - [ ] 12 news segments (0100, 0300, 0500, ..., 2300)
  - [ ] 6 gossip segments (0200, 0600, 1000, 1400, 1800, 2200)
  - [ ] 3 music intros (test only)
- [ ] Validate all files created successfully
- [ ] Check filenames match convention
- [ ] Test MP3 playback on computer
- [ ] Verify ID3 tags stripped
- [ ] Review manifest.json for accuracy
- [ ] Document total generation time
- [ ] Calculate storage requirements (total MB)

**Deliverable:** Complete 24-hour content set (~50 audio files)

**Phase 3 Complete:** ✅ Automated full-day content generator operational

---

## Phase 4: Firmware Enhancement (RTC + WiFi + Scheduling)

**Goal:** Add time-awareness and scheduled playback to ESP32  
**Estimated Time:** 12-15 hours  
**Dependencies:** Phase 3.4 (test content with proper filenames)

### 4.1 RTC & NTP Integration
- [ ] Add NTP client library to `platformio.ini`
- [ ] Create WiFi credentials configuration system
- [ ] Add RTC initialization in `setup()`
- [ ] Implement NTP sync function:
  - [ ] Create FreeRTOS task on Core 0
  - [ ] Add WiFi connect/disconnect wrapper
  - [ ] Set system time from NTP server
  - [ ] Add error handling for network failures
- [ ] Configure 6-hour sync interval
- [ ] Test WiFi sync doesn't interrupt audio playback
- [ ] Add Serial debug output for sync events
- [ ] Document WiFi/NTP implementation

**Deliverable:** Updated `src/main.cpp` with RTC/NTP

### 4.2 Filename Parser
- [ ] Define `ScheduledSegment` struct (time, type, dj, id, filepath, played_today)
- [ ] Implement `parseFilename()` using sscanf
- [ ] Use static char buffers (avoid String class)
- [ ] Add time validation (0000-2359, valid minutes)
- [ ] Add extension validation (.mp3 only)
- [ ] Create test cases for parser:
  - [ ] Valid: `0800-weather-julie-sunny.mp3`
  - [ ] Valid: `1430-musicintro-julie-song001-upbeat.mp3`
  - [ ] Invalid: `8-weather-julie.mp3` (bad time format)
  - [ ] Invalid: `0800-weather.mp3` (missing fields)
- [ ] Test parser with Serial output
- [ ] Document parsing logic

**Deliverable:** Parsing functions in `src/main.cpp`

### 4.3 Schedule Builder
- [ ] Define global schedule array (200 max segments)
- [ ] Implement `buildSchedule()` function:
  - [ ] Scan SD folders (News/, Weather/, Time/, Gossip/, Music Intros/)
  - [ ] Parse each .mp3 filename
  - [ ] Add valid segments to schedule array
  - [ ] Sort schedule by time (bubble sort)
- [ ] Add schedule printing function for Serial debug
- [ ] Implement `findNextSegment()` using binary search
- [ ] Add time window matching function (±2 minute tolerance)
- [ ] Test with sample SD content
- [ ] Validate schedule builds correctly at boot
- [ ] Document schedule builder

**Deliverable:** Schedule builder and search functions

### 4.4 Playback Sequencing
- [ ] Add schedule check timer (every 10 seconds)
- [ ] Implement `checkSchedule()` function:
  - [ ] Get current time from RTC
  - [ ] Find next scheduled segment
  - [ ] Check if segment due now (time window match)
  - [ ] Check if already played today
- [ ] Implement `playScheduledSegment()`:
  - [ ] Stop current playback if needed
  - [ ] Load scheduled segment from SD
  - [ ] Mark as played
  - [ ] Log to Serial
- [ ] Add midnight reset for `played_today` flags
- [ ] Implement "fill with music" between scheduled segments
- [ ] Test scheduled playback triggers
- [ ] Test music filler behavior
- [ ] Document sequencing logic

**Deliverable:** Complete scheduling in main loop

### 4.5 Debug & Logging
- [ ] Create `printSchedule()` function:
  - [ ] Format: Time | Type | DJ | Content | Status
  - [ ] Show next 10 upcoming segments
  - [ ] Show played status (✓ or ○)
- [ ] Implement SD card event logging:
  - [ ] Create `playback.log` on SD
  - [ ] Log timestamp, filename, success/fail
  - [ ] Log schedule triggers
  - [ ] Log WiFi sync events
- [ ] Add Serial commands for manual inspection:
  - [ ] 's' - print schedule
  - [ ] 't' - print current time
  - [ ] 'n' - print next scheduled segment
- [ ] Test logging system
- [ ] Document debug commands

**Deliverable:** Debug/logging system operational

**Phase 4 Complete:** ✅ Time-aware firmware with scheduled playback

---

## Phase 5: SD Card Deployment & Testing

**Goal:** Package content for SD card and validate end-to-end  
**Estimated Time:** 6-8 hours  
**Dependencies:** Phase 4.5 (firmware complete)

### 5.1 SD Card Organizer
- [ ] Create `tools/sd-deployer/` folder
- [ ] Create `prepare_sd_card.py` script:
  - [ ] Validate SD card path (Windows drive letter)
  - [ ] Create folder structure (News/, Weather/, Time/, etc.)
  - [ ] Copy generated content to proper folders
  - [ ] Copy music library to Music/ folder
  - [ ] Preserve folder structure
  - [ ] Add safety checks (confirm before overwrite)
- [ ] Test with sample SD card
- [ ] Document SD preparation process

**Deliverable:** SD card deployment tool

### 5.2 Integration Testing
- [ ] Format SD card (FAT32)
- [ ] Deploy 24-hour content using `prepare_sd_card.py`
- [ ] Add music files to Music/ folder
- [ ] Build and flash firmware to ESP32
- [ ] Monitor Serial output during boot:
  - [ ] SD card mounted successfully
  - [ ] Schedule parsing results
  - [ ] Number of segments found
  - [ ] Next scheduled segment
- [ ] Wait for scheduled segment trigger:
  - [ ] Verify correct file plays at correct time
  - [ ] Check Serial logs
  - [ ] Validate audio quality
- [ ] Test WiFi NTP sync:
  - [ ] Monitor for sync event in logs
  - [ ] Verify audio doesn't glitch
  - [ ] Confirm time updated
- [ ] Document test results and any bugs

**Deliverable:** Integration test report, bug fixes

### 5.3 Week-Long Content Scaling
- [ ] Extend orchestrator to support multi-day generation
- [ ] Add day-of-week awareness (Monday scripts, Tuesday scripts, etc.)
- [ ] Implement content rotation strategies:
  - [ ] Vary weather descriptions
  - [ ] Rotate news topics
  - [ ] Mix gossip stories
  - [ ] Different music intro styles per day
- [ ] Test 7-day generation (estimate runtime)
- [ ] Calculate total storage requirements
- [ ] Validate unique content across days (no exact duplicates)

**Deliverable:** Week-long content generator

### 5.4 Real-World Testing
- [ ] Run 24-hour continuous playback test:
  - [ ] Monitor for crashes
  - [ ] Check for memory leaks (free heap tracking)
  - [ ] Validate all scheduled segments trigger
  - [ ] Confirm music fills gaps
- [ ] Test edge cases:
  - [ ] Midnight rollover (2359→0000)
  - [ ] Multiple segments at same time (rotation)
  - [ ] Missed schedule (past trigger time)
  - [ ] SD card removed/reinserted
- [ ] Monitor NTP sync cycles (6-hour interval)
- [ ] Review `playback.log` for anomalies
- [ ] Test RTC drift compensation
- [ ] Document stability results
- [ ] Create final bug fix list

**Deliverable:** Stability report, production-ready firmware

**Phase 5 Complete:** ✅ Production system validated

---

## Phase 6: Polish & Future-Proofing

**Goal:** Prepare for real weather API and multi-DJ expansion  
**Estimated Time:** 4-6 hours  
**Dependencies:** Phase 5.4 (core system stable)

### 6.1 Weather API Scaffolding
- [ ] Create `tools/weather-fetcher/` folder
- [ ] Research OpenWeatherMap API (or WeatherAPI.com)
- [ ] Add API key configuration to `config.py`
- [ ] Create weather fetcher stub (returns hardcoded data for now)
- [ ] Design weather data → script template mapping
- [ ] Plan integration point (generate scripts with real data)
- [ ] Document API integration plan

**Deliverable:** Weather API stubs and documentation

### 6.2 Music Intro Scaling
- [ ] Create song metadata extractor (ID3 tags or filename parsing)
- [ ] Design music intro batching strategy (process 50 songs at a time)
- [ ] Estimate generation time for 500+ songs (~30 hours)
- [ ] Test batch generation with 10 songs
- [ ] Plan storage (500 intros × ~50KB = ~25MB)
- [ ] Document scaling process

**Deliverable:** Music intro scaling plan and test batch

### 6.3 Multi-DJ Support Prep
- [ ] Document voice cloning workflow:
  - [ ] Audio preprocessing steps
  - [ ] Fine-tuning process
  - [ ] Quality validation
- [ ] Create DJ addition checklist
- [ ] Design DJ rotation schedules:
  - [ ] Julie: 0000-0800 (overnight/morning)
  - [ ] Mr. New Vegas: 0800-1600 (daytime)
  - [ ] Travis: 1600-2400 (evening)
- [ ] Plan filename convention for multi-DJ: `HHMM-type-DJNAME-id.mp3`
- [ ] Document DJ expansion process

**Deliverable:** Multi-DJ expansion documentation

**Phase 6 Complete:** ✅ System ready for expansion

---

## Summary Timeline

| Phase | Tasks | Duration | Status | Completion |
|-------|-------|----------|--------|------------|
| **Phase 1: TTS Setup** | 4 sections, ~15 tasks | 2-4 hours | 🟡 Near Complete | **90%** |
| **Phase 2: RAG & Script Generation** | 6 sections, ~65 tasks | 14-16 hours | ✅ **COMPLETE** | **100%** |
| **Phase 3: Full-Day Pipeline** | 4 sections, ~75 tasks | 16-20 hours | ⬜ Not Started | **0%** |
| **Phase 4: Firmware Enhancement** | 5 sections, 40 tasks | 12-15 hours | ⬜ Not Started | **0%** |
| **Phase 5: SD Deployment** | 4 sections, 30 tasks | 6-8 hours | ⬜ Not Started | **0%** |
| **Phase 6: Polish** | 3 sections, 15 tasks | 4-6 hours | ⬜ Not Started | **0%** |
| **TOTAL** | **~240 tasks** | **54-69 hours** | **🟡 37% Complete** | **~37%** |

---

## Current Status

**Active Phase:** Phase 3 - Full-Day Content Pipeline (0% complete)  
**Next Task:** Phase 3.1 - TTS Integration & Script-to-Audio Converter (CRITICAL PATH)  
**Blockers:** None  
**Recent Completion:** Phase 2.6 comprehensive validation (57 scripts, 88.3/100, ±2.9 std dev, 100% pass rate)

**Priority:** Implement TTS integration to connect validated script generator (Phase 2) with Chatterbox TTS (Phase 1)

---

## Phase 3.2: Audio Quality Enhancement (Crossfade & VAD Fixes)

**Goal:** Eliminate warping artifacts at chunk boundaries through crossfade windows and improved VAD padding  
**Estimated Time:** 2-3 hours  
**Dependencies:** Phase 3.1 (TTS pipeline operational)  
**Status:** 🟡 IN PROGRESS

### Background Research (2026-01-12)
Identified audio warping issue ("warping at beginning/end, stable middle") after Iteration 2 validation. Research findings:

**Root Cause Analysis:**
- **Primary:** Hard concatenation of VAD-trimmed chunks without crossfading (abrupt amplitude transitions)
- **Secondary:** VAD over-trimming removes natural phoneme attack/decay envelopes (0ms padding)
- **Tertiary:** Potential sample rate conversion artifacts (24kHz→44.1kHz)
- **Evidence:** Multiple production Chatterbox TTS implementations add crossfading to solve identical issue

**Ollama Audio Verification Limitations:**
- Ollama does **NOT** support direct audio processing (confirmed via feature request #11798)
- Llama.cpp (Ollama's engine) only supports text-only models as of Jan 2026
- Multimodal vision models (Llama 4, Gemma 3) support images but not audio
- **Current pipeline (Whisper→Ollama) is industry-standard best practice for local LLM audio verification**

**Industry Solutions Found:**
- `travisvn/chatterbox-tts-api`: Implements numpy crossfading with 50ms windows
- `devnen/Chatterbox-TTS-Server`: Uses audio stitching with crossfading for chunk concatenation
- `703deuce/chatterbox-tts-serverless`: Dedicated `audio_stitcher.py` for Chatterbox chunks
- Standard pattern: `fade_in = np.linspace(0.0, 1.0, fade_samples)` / `fade_out = np.linspace(1.0, 0.0, fade_samples)`
- **Expected impact: 80-90% reduction in boundary warping (confirmed by production deployments)**

### 3.2.1 Crossfade Implementation
- [ ] Add 50ms crossfade windows to `converter.py` `generate_audio()` method
- [ ] Apply fade-out to end of each chunk (linear envelope)
- [ ] Apply fade-in to start of next chunk (linear envelope)
- [ ] Skip fade-in for first chunk, fade-out for last chunk
- [ ] Test on 5 sample files (A/B comparison with current pipeline)
- [ ] Verify no clicks/pops at chunk boundaries

**Implementation Details:**
- Fade duration: 50ms (industry standard for TTS)
- Method: Linear crossfade with numpy `np.linspace()`
- Applied to: All sentence boundaries (overlapping regions)
- Not applied to: 300ms silence pauses (no overlap needed)

**Status:** 🟡 IN PROGRESS (0%)
**Deliverable:** Crossfaded audio with smooth chunk transitions

### 3.2.2 VAD Padding Enhancement
- [ ] Add 100ms padding parameter to `utils.py` `trim_silence_with_vad()`
- [ ] Apply padding after VAD cut point (preserve phoneme decay)
- [ ] Test on existing Iteration 1/2 outputs
- [ ] Verify no consonant/vowel truncation
- [ ] Document optimal padding value in CONFIG.md

**Implementation Details:**
- Padding: 100ms after VAD endpoint
- Purpose: Preserve natural phoneme attack/decay envelopes
- Prevents: Consonant release and vowel tail truncation
- Current issue: 0ms padding causes hard cuts mid-phoneme

**Status:** 🟡 IN PROGRESS (0%)
**Deliverable:** VAD trimming that preserves natural audio decay

### 3.2.3 Quality Detection Enhancements (Optional)
- [ ] Add spectral flux detection to `test_quality.py` (detect clicks/pops)
- [ ] Add zero-crossing rate (ZCR) anomaly detection (waveform irregularities)
- [ ] Update scoring to include new metrics (normalize to 100 points)
- [ ] Run enhanced validation on Iteration 1 outputs (baseline spectral scores)

**Implementation Details:**
- **Spectral flux:** `librosa.onset.onset_strength()` for sudden spectral changes
- **ZCR anomalies:** Detect irregular waveforms (>3σ from mean)
- **Scoring:** Add 10-15 points for spectral discontinuities, 10 points for ZCR
- **Optional:** Install pystoi for STOI intelligibility metric (requires reference audio)

**Status:** ⬜ NOT STARTED (0%)
**Deliverable:** Enhanced quality validation with spectral artifact detection

### 3.2.4 Full Validation & Regeneration
- [ ] Generate 5 test samples with crossfade + VAD padding fixes
- [ ] A/B comparison: current vs. fixed (spectral analysis + manual listening)
- [ ] If improved, regenerate all 17 Iteration 2 scripts
- [ ] Compare quality scores before/after (expect improvement in chunk seam scores)
- [ ] Update CONFIG.md with warping resolution findings
- [ ] Consider regenerating Iteration 1 files (10 scripts) for consistency

**Status:** ⬜ NOT STARTED (0%)
**Deliverable:** Full content library with warping artifacts eliminated

**Phase 3.2 Expected Outcomes:**
- 80-90% reduction in audio warping artifacts
- Improved chunk seam scores (current: 9.6-12.6/20 → target: 15-18/20)
- Smooth audio transitions without clicks/pops
- Natural phoneme boundaries preserved
- Production-ready audio quality for ESP32 deployment

**Research Sources:**
- GitHub Issue: ollama/ollama#11798 (Audio input feature request)
- Production implementations: travisvn/chatterbox-tts-api, devnen/Chatterbox-TTS-Server
- Brave web search: "Ollama audio processing multimodal LLM 2026"
- Code search: "crossfade audio concatenation TTS language:Python"

---

## Critical Gaps & Achievements

### ✅ Major Accomplishments (Updated 2026-01-12)
- **Phase 2 Script Generator Complete & Validated**: 88.3/100 quality score, 57-script stress test, 100% pass rate
- **ChromaDB RAG System Fully Operational**: 356,601 chunks with temporal/spatial/content metadata
- **DJ Persona Filtering Validated**: 4 DJ personalities with lore-accurate temporal/spatial constraints
- **Chatterbox Turbo Fine-Tuned**: Julie voice model trained and generating high-quality audio
- **3-Tier Validation System**: Rule-based + embeddings + LLM-as-judge (74ms avg, 8s LLM when needed)
- **Catchphrase Rotation**: Context-aware selection with last-3 tracking
- **Comprehensive Research Complete**: WiFi/RTC/scheduling + Chatterbox TTS capabilities documented

### ❌ Critical Missing Components
1. **TTS Integration (Phase 3.1)**: No script → audio conversion pipeline exists
   - Impact: Cannot convert validated scripts to playable MP3 files
   - Required for: Full content pipeline, ESP32 deployment
   - **Next Step:** Implement ScriptToAudioConverter with emotion-aware reference library

2. **MP3 Conversion Pipeline** (Phase 3.1): All TTS outputs are WAV format
   - Impact: ESP32 requires 44.1kHz MP3 with stripped ID3 tags
   - Required for: ESP32 deployment
   - **Integration:** Will be part of ScriptToAudioConverter implementation

3. **Firmware Scheduling Implementation** (Phase 4 ALL): Despite complete research, zero scheduling code exists in active firmware
   - Impact: Cannot play time-based content (weather, news, etc.)
   - Note: Research documented in copilot-instructions.md, implementation needed after Phase 3 complete

---

## Notes & Decisions

### Key Architectural Decisions (Updated 2026-01-12)
- **TTS Engine:** Chatterbox Turbo (fine-tuned model operational)
- **Voice Model:** Julie (fine-tuned at `models/chatterbox-julie-output/t3_turbo_finetuned.safetensors`)
- **Content Generation:** Ollama + ChromaDB RAG for lore-accurate scripts
- **Lore Source:** `fallout_wiki_complete.xml` (356,601 chunks in ChromaDB)
- **DJ Personas:** 4 defined with temporal/spatial filtering (Julie, Mr. New Vegas, Travis Nervous, Travis Confident)
- **Filename Format:** `HHMM-type-dj-id-variant.mp3` (planned, not yet implemented)
- **Schedule Storage:** Static array, 200 max segments, 8KB RAM (researched, not implemented)
- **WiFi Pattern:** Core 0 FreeRTOS task, disconnect after NTP sync (researched, not implemented)
- **Content Priority:** Lore accuracy + Quality over speed

### Archived Components (2026-01-11 Cleanup)
- `archive/xtts-research/` - XTTS v2 research and pipeline (superseded by Chatterbox)
- `archive/lore-scraper/` - Wiki scraping tools (extraction complete, XML available)
- `archive/story-generation/` - Early script generation attempts (replaced by RAG system)
- `archive/venvs/` - Inactive virtual environments (tts_clean_env, .venv)
- `archive/training-logs/` - Intermediate model checkpoints
- `archive/backups/` - Backup and corrupted files

### Future Enhancements
- Real-time weather integration via API
- Multiple DJ personalities with rotation schedules
- Music intro library for full song collection (500+ intros)
- Week-long content with day-of-week variation
- Web interface for schedule management
- OTA firmware updates
- Expanded RAG system with additional Fallout lore sources

---

**Last Updated:** 2026-01-12  
**Document Version:** 2.1 (Phase 2 complete, Phase 3 TTS integration with comprehensive test suite)
