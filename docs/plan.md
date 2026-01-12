# ESP32 Fallout Radio Station - Implementation Plan

**Goal:** Build a complete AI-driven radio station with Julie as DJ, scheduled programming, and pre-generated content for week-long autonomous playback.

**Quality Priority:** Prioritize voice quality over speed throughout all phases.

---

## Current Architecture (2026-01-11)

### TTS System
- **Engine:** Chatterbox Turbo (zero-shot voice cloning)
- **Approach:** No fine-tuning required - using reference audio for voice cloning
- **Model:** Pre-trained Chatterbox Turbo v1
- **Environment:** `chatterbox_env/` Python virtual environment
- **Status:** ✅ Operational

### Content Generation Pipeline
- **LLM:** Ollama (installed, models ready)
- **Knowledge Base:** RAG-based system using ChromaDB embeddings
- **Lore Source:** `lore/fallout_wiki_complete.xml` (complete Fallout Wiki export)
- **Workflow:** XML → ChromaDB embeddings → Ollama queries → Lore-accurate scripts
- **Status:** ⬜ Not yet implemented (requires data processing and RAG setup)

### Research Status
- ✅ TTS Voice Cloning (Switched from XTTS v2 to Chatterbox Turbo)
- ✅ ESP32 RTC & Non-Blocking WiFi (Dual-core FreeRTOS pattern)
- ✅ Filename-Based Scheduling (sscanf parsing, binary search)

**Research Documentation:** See `research/` folder (note: XTTS research marked obsolete)

---

## Phase 1: TTS Pipeline Setup & Voice Cloning

**Goal:** Configure Chatterbox Turbo for Julie's zero-shot voice cloning  
**Estimated Time:** 2-4 hours  
**Dependencies:** None

### 1.1 Environment Setup
- [x] Create Python virtual environment (`chatterbox_env/`)
- [x] Install Chatterbox Turbo dependencies
- [x] Test installation with simple TTS generation
- [x] Verify CUDA acceleration on RTX 3060

**Status:** ✅ COMPLETE  
**Deliverable:** Working Chatterbox Turbo environment

### 1.2 Audio Preprocessing
- [ ] Locate Julie's source audio files
- [ ] Convert to required format (WAV, appropriate sample rate)
- [ ] Create reference audio clips (6-30 seconds)
- [ ] Test audio quality for voice cloning
- [ ] Create `tools/voice-samples/julie/` folder structure
- [ ] Document preprocessing steps

**Deliverable:** `tools/voice-samples/julie/` with reference audio

### 1.3 Voice Clone Testing
- [ ] Test zero-shot cloning with reference segments
- [ ] Generate test weather announcement
- [ ] Generate test news segment
- [ ] Generate test time announcement
- [ ] Evaluate voice similarity and quality
- [ ] Adjust reference audio if needed
- [ ] Document optimal reference clips

**Deliverable:** Validated zero-shot voice cloning workflow

### 1.4 Quality Validation
- [ ] Generate 3 music intros with different emotional tones
- [ ] Test inference parameter tuning (temperature, repetition penalty)
- [ ] Convert outputs to 44.1kHz 128kbps MP3
- [ ] Strip ID3 tags from MP3s
- [ ] Test playback on ESP32 hardware
- [ ] Document optimal inference parameters
- [ ] Create quality checklist for future generations

**Deliverable:** 3 test MP3s ready for ESP32, documented quality settings

**Phase 1 Complete:** ✅ Chatterbox Turbo voice cloning ready for production

---

## Phase 2: RAG System & Script Generation

**Goal:** Set up Ollama+ChromaDB RAG system for lore-accurate script generation  
**Estimated Time:** 10-12 hours  
**Dependencies:** Phase 1.3 (understand content needs)

### 2.1 Lore Data Processing
- [ ] Parse `lore/fallout_wiki_complete.xml` to extract structured data
- [ ] Clean and normalize wiki content (remove markup, format text)
- [ ] Chunk content into semantic segments (paragraphs, sections)
- [ ] Create metadata for each chunk (source page, category, relevance)
- [ ] Design chunk size strategy (balance context vs retrieval precision)
- [ ] Test XML parsing and content extraction
- [ ] Document data structure and processing pipeline

**Deliverable:** Processed lore data ready for embedding

### 2.2 ChromaDB Embedding Pipeline
- [ ] Install ChromaDB and embedding dependencies
- [ ] Select embedding model (all-MiniLM-L6-v2 or similar)
- [ ] Create ChromaDB collection for Fallout lore
- [ ] Implement batch embedding process for processed chunks
- [ ] Add metadata indexing for efficient filtering
- [ ] Test embedding generation and storage
- [ ] Validate retrieval accuracy with sample queries
- [ ] Document embedding pipeline and configuration

**Deliverable:** ChromaDB collection with embedded Fallout lore

### 2.3 Ollama RAG Integration
- [ ] Review existing Ollama setup in `tools/ollama_setup/`
- [ ] Configure Ollama model selection for script generation
- [ ] Create RAG query pipeline:
  - [ ] Retrieve relevant lore chunks from ChromaDB
  - [ ] Format context for Ollama prompt
  - [ ] Generate script with lore-aware context
- [ ] Implement personality loader (reads `dj personality/Julie/`)
- [ ] Test RAG retrieval with sample script queries
- [ ] Tune retrieval parameters (top-k, similarity threshold)
- [ ] Document RAG query workflow

**Deliverable:** Working RAG-based script generator

### 2.4 Script Templates & Generation
- [ ] Create `tools/script-generator/templates/` folder
- [ ] Design weather template (sunny, cloudy, rainy, night variants)
- [ ] Design news template (headline delivery, lore references)
- [ ] Design time template (hourly announcements, time of day flavor)
- [ ] Design gossip template (wasteland stories from lore)
- [ ] Design music intro template (song context, era references)
- [ ] Add personality prompt injection (Julie character card)
- [ ] Add variable placeholders with RAG context
- [ ] Test single script generation with RAG
- [ ] Generate sample scripts for each type
- [ ] Review for lore accuracy and tone consistency
- [ ] Document template format and RAG integration

**Deliverable:** 5 segment templates with RAG integration, sample scripts

### 2.5 Testing & Validation
- [ ] Generate test script set with lore validation:
  - [ ] 3 weather scripts (with location references)
  - [ ] 5 news scripts (using actual lore events)
  - [ ] 3 gossip scripts (character/faction references)
  - [ ] 3 time announcements
- [ ] Cross-reference scripts against source lore for accuracy
- [ ] Check for vocabulary consistency (no anachronisms)
- [ ] Validate tone matches Julie's character profile
- [ ] Test RAG retrieval relevance scores
- [ ] Document generation quality and lore accuracy
- [ ] Create quality checklist for script review

**Deliverable:** Validated RAG-based script generation system

**Phase 2 Complete:** ✅ Lore-accurate script generator operational

---

## Phase 3: Full-Day Content Pipeline

**Goal:** Orchestrate RAG → Script → TTS workflow with VRAM management  
**Estimated Time:** 8-10 hours  
**Dependencies:** Phase 1.4 (TTS ready), Phase 2.5 (RAG script generator ready)

### 3.1 Pipeline Orchestrator
- [ ] Create `tools/orchestrator/` folder
- [ ] Create `generate_day.py` main orchestration script
- [ ] Implement VRAM handoff logic:
  - [ ] Unload Ollama/ChromaDB after script generation
  - [ ] Load Chatterbox Turbo for audio generation
  - [ ] Monitor VRAM usage with nvidia-smi
- [ ] Add progress tracking (X of Y segments complete)
- [ ] Add error handling and logging
- [ ] Implement resume from partial completion (checkpoint system)
- [ ] Test with 5 segment pipeline run

**Deliverable:** Working orchestrator script

### 3.2 Batch TTS Processing
- [ ] Implement speaker latent caching (compute once, reuse)
- [ ] Create batch processor function (processes script list)
- [ ] Implement filename generation: `HHMM-type-dj-id.mp3`
- [ ] Add WAV to MP3 conversion (44.1kHz, 128kbps)
- [ ] Add ID3 tag stripping (critical for ESP32)
- [ ] Organize output into folders:
  - [ ] `audio generation/Weather/`
  - [ ] `audio generation/News/`
  - [ ] `audio generation/Time/`
  - [ ] `audio generation/Gossip/`
  - [ ] `audio generation/Music Intros/`
- [ ] Test with 10 segment batch

**Deliverable:** Batch TTS processor integrated into orchestrator

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

| Phase | Tasks | Duration | Status |
|-------|-------|----------|--------|
| **Phase 1: TTS Setup** | 4 sections, ~15 tasks | 2-4 hours | 🟡 Partially Complete |
| **Phase 2: RAG & Script Generation** | 5 sections, ~35 tasks | 10-12 hours | ⬜ Not Started |
| **Phase 3: Full-Day Pipeline** | 4 sections, 22 tasks | 8-10 hours | ⬜ Not Started |
| **Phase 4: Firmware Enhancement** | 5 sections, 40 tasks | 12-15 hours | ⬜ Not Started |
| **Phase 5: SD Deployment** | 4 sections, 30 tasks | 6-8 hours | ⬜ Not Started |
| **Phase 6: Polish** | 3 sections, 15 tasks | 4-6 hours | ⬜ Not Started |
| **TOTAL** | **~157 tasks** | **42-55 hours** | **~5% Complete** |

---

## Current Status

**Active Phase:** Phase 2 - RAG System & Script Generation (pending)  
**Next Task:** Phase 2.1 - Lore Data Processing  
**Blockers:** None

---

## Notes & Decisions

### Key Architectural Decisions (Updated 2026-01-11)
- **TTS Engine:** Chatterbox Turbo (zero-shot, no fine-tuning)
- **Voice Model:** Julie (using reference audio for cloning)
- **Content Generation:** Ollama + ChromaDB RAG for lore-accurate scripts
- **Lore Source:** `fallout_wiki_complete.xml` (complete wiki export)
- **Filename Format:** `HHMM-type-dj-id-variant.mp3`
- **Schedule Storage:** Static array, 200 max segments, 8KB RAM
- **WiFi Pattern:** Core 0 FreeRTOS task, disconnect after NTP sync
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

**Last Updated:** 2026-01-11  
**Document Version:** 2.0 (Updated for Chatterbox + RAG architecture)
