# ESP32 AI Radio - Repository Structure

**Last Updated:** January 20, 2026  
**Project:** Fallout-Themed AI Radio DJ Script Generation System

## 📁 Repository Organization

This document provides a complete overview of the repository structure after reorganization.

---

## Root Directory

### Entry Points & Main Scripts
- **`broadcast.py`** - Main CLI for generating broadcasts  
  Usage: `python broadcast.py --dj Julie --days 7 --enable-stories`
- **`run_tests.py`** - Unified test runner with multiple modes  
  Usage: `python run_tests.py unit`, `python run_tests.py e2e`

### Configuration Files
- **`pyproject.toml`** - Python project configuration, pytest settings
- **`platformio.ini`** - ESP32 firmware build configuration  
- **`.gitignore`** - Git ignore patterns
- **`README.md`** - Project overview and quick start guide

### State Files
- **`broadcast_state.json`** - Current broadcast generation state
- **`broadcast_state_stories.json`** - Story system state tracking

---

## 📂 Documentation (`docs/`)

### Guides (`docs/guides/`)
Comprehensive technical guides for development:
- **`VALIDATION_IMPROVEMENT_SUGGESTIONS.md`** - Validation system enhancement proposals (1530 lines)
- **`TESTING_AND_LOGGING_GUIDE.md`** - Testing infrastructure and logging standards
- **`ENHANCED_VALIDATION_GUIDE.md`** - Advanced validation strategies
- **`BROADCAST_ENGINE_REFACTORING_PLAN.md`** - Engine architecture refactoring plans

### Status Reports (`docs/status/`)
Project progress and completion summaries:
- **`PHASE4_STATUS.md`** - Phase 4 completion status
- **`SESSION_COMPLETION_SUMMARY.md`** - Session work summaries
- **`REVIEW_APP_UPDATE_SUMMARY.md`** - Review app update logs
- **`GENERATION_FAILURE_20260120.md`** - Failure analysis and debugging

### Testing Documentation (`docs/testing/`)
Test infrastructure and results:
- **`TEST_INFRASTRUCTURE_SUMMARY.md`** - Complete test framework overview
- **`E2E_IMPLEMENTATION_SUMMARY.md`** - End-to-end testing summary (340 lines)
- **`E2E_TEST_BUGFIXES.md`** - E2E test bug fixes and resolutions
- **`DEBUGGING_RESULTS.md`** - System debugging outcomes
- **`LOCAL_TESTING_PLAN.md`** - Local testing procedures

### Architecture Documentation
Located in root `docs/` directory:
- **`ARCHITECTURE.md`** - System architecture overview
- **`DJ_KNOWLEDGE_SYSTEM.md`** - DJ personality and knowledge management
- **`SYSTEM_SPECS.md`** - Technical specifications
- **`INLAND_ESP32_SPECS.md`** - ESP32 hardware specifications
- **`PHASE5_MOBILE_TEST_RESULTS.md`** - Mobile testing results
- **`PHASE7_COMPLETE.md`** - Phase 7 completion documentation
- **`PHASE7_MULTI_TEMPORAL_STORY_SYSTEM.md`** - Multi-temporal story system design

---

## 🛠️ Tools (`tools/`)

### Script Generator (`tools/script-generator/`)
Core broadcast generation engine:

#### Main Components
- **`broadcast_engine.py`** (437 lines) - Main broadcast generation orchestrator
- **`generator.py`** (402 lines) - LLM script generation
- **`story_scheduler.py`** - Multi-day story arc scheduling
- **`session_memory.py`** - Session state and continuity tracking
- **`world_state.py`** - In-universe state management (year, weather, events)

#### Content Generation (`content_types/`)
- **`gossip.py`** - Gossip segment generation
- **`news.py`** - News segment generation  
- **`weather.py`** - Weather broadcast generation
- **`time_check.py`** - Time announcement generation

#### Validation System
- **`llm_validator.py`** (207 lines) - LLM-based validation
- **`validation_rules.py`** - Rule-based validation engine
- **`consistency_validator.py`** - Cross-segment consistency checks
- **`phase6_validation.py`** - Advanced validation modes

#### LLM Integration
- **`ollama_client.py`** - Ollama API client
- **`llm_pipeline.py`** - LLM generation pipeline with retries
- **`prompt_builder.py`** - Prompt template construction

#### Story System (`story_system/`)
Multi-act narrative management:
- **`story_models.py`** - Story arc data models
- **`story_scheduler.py`** - Story scheduling and progression
- **`story_weaver.py`** - Story beat integration into broadcasts
- **`escalation_engine.py`** - Conflict escalation management
- **`lore_validator.py`** - Lore consistency validation
- **`story_extractor.py`** - Extract story arcs from wiki data

#### Weather System
- **`weather_simulator.py`** - Regional weather pattern generation
- **`regional_climate.py`** - Climate definitions for Fallout regions
- **`query_weather_history.py`** - Weather data retrieval

#### Knowledge & RAG
- **`dj_knowledge_profiles.py`** (175 lines) - DJ-specific knowledge constraints
- **`rag_cache.py`** - RAG query caching layer
- **`query_helpers.py`** - ChromaDB query utilities

#### Testing (`tools/script-generator/tests/`)
Comprehensive test suite:
- **Unit Tests:** `test_generator.py`, `test_ollama_client.py`, `test_llm_validator.py`
- **Integration Tests:** `test_phase4_mocks_and_integration.py`, `test_phase5_integration.py`
- **E2E Tests:** `e2e/test_ollama_setup.py`, `e2e/test_24hour_broadcast.py`

### Script Review App (`tools/script-review-app/`)
Mobile-friendly web UI for script approval:

#### Backend
- **`backend/main.py`** - FastAPI application
- **`backend/storage.py`** - Script storage and state management
- **`backend/routes.py`** - API endpoints

#### Frontend  
- **`frontend/`** - HTML/CSS/JavaScript mobile-optimized UI

#### Testing
- **`tests/test_cloudflare_tunnel.py`** - Tunnel integration testing
- **`tests/test_web_app_with_browser.py`** - Browser automation tests

### Wiki to ChromaDB (`tools/wiki_to_chromadb/`)
Fallout Wiki ingestion pipeline:
- **`chromadb_ingest.py`** - Main ingestion orchestrator
- **`wiki_parser.py`** - MediaWiki XML parsing
- **`chunker.py`** - Intelligent text chunking
- **`metadata_enrichment.py`** - Metadata extraction and tagging
- **`extractors.py`** - Template and infobox extraction

### Shared Utilities (`tools/shared/`)
- **`logging_config.py`** (266 lines) - 3-format logging (console, JSON, historical)
- **`mock_ollama_client.py`** - Mock LLM client for testing
- **`project_config.py`** - Centralized configuration

---

## 🧪 Tests (`tests/`)

### Structure
- **`conftest.py`** - Global fixtures and test configuration
- **`unit/`** - Unit tests with mocks (95%+ coverage target)
- **`integration/`** - Integration tests with real components
- **`e2e/`** - End-to-end pipeline tests

### Test Utilities
- **`fixtures/`** - Test data and sample files
- **`helpers/`** - Test helper functions

---

## 📝 Scripts (`scripts/`)

### Generators (`scripts/generators/`)
DJ-specific broadcast generators:
- **`generate_julie.py`** - Julie (Appalachia 2102) broadcasts
- **`generate_mr_new_vegas.py`** - Mr. New Vegas (Mojave 2281)
- **`generate_travis.py`** - Travis Miles (Commonwealth 2287)
- **`generate_performance_test_scripts.py`** - Performance testing script generator

### Utilities (`scripts/utilities/`)
Maintenance and debugging tools:
- **`reset_world_state.py`** - Reset world state to defaults
- **`debug_systems.py`** - System debugging utilities

### Test Scripts (`scripts/tests/`)
Standalone test runners:
- **`test_7day_story.py`** - 7-day story integration test
- **`test_enhanced_validation.py`** - Validation system test
- **`test_integration.py`** - Integration test runner
- **`test_story_extraction.py`** - Story extraction test
- **`test_phase8_performance.ps1`** - Performance benchmarking (PowerShell)

### Reference
- **`SCRIPTS_REFERENCE.md`** - Documentation for all utility scripts

---

## 💾 Data & Output

### DJ Personalities (`dj_personalities/`)
Character card JSON files:
- **`Julie/`** - Julie's personality, knowledge base, voice characteristics
- **`Mr. New Vegas/`** - Mr. New Vegas configuration
- **`Travis Miles (Confident)/`** - Post-confidence Travis
- **`Travis Miles (Nervous)/`** - Pre-confidence Travis
- **`Mr. Med City/`** - Custom DJ

### Data Files (`data/`)
- **`dj_personalities.json`** - DJ configuration index

### Output (`output/`)
Generated broadcasts (JSON format):
- **`broadcast_Julie_30day_stories_20260120_103258.json`** - Recent 30-day broadcast
- Format: `broadcast_{DJ}_{duration}_{timestamp}.json`

### Lore Data (`lore/`)
Fallout lore reference materials

### ChromaDB (`chroma_db/`)
Vector database storage:
- **`chroma.sqlite3`** - Database file
- **`processing_stats.json`** - Ingestion statistics
- **`fallout_wiki/`** - Collection with 291,343 chunks

### Logs (`logs/`)
- **`ingestion/`** - Wiki ingestion logs
- **`error_report.txt`** - Error aggregation
- **`month_broadcast.err`** - Monthly broadcast errors
- **`test_output.txt`** - Test execution logs

---

## 🔧 Firmware (`firmware/`)

ESP32-specific code:
- **`main.cpp`** - ESP32 main firmware  
- **`README.md`** - Firmware build instructions

---

## 📚 Archive (`archive/`)

Historical backups and deprecated code:
- **`backups/`** - Historical state backups
- **`documentation/`** - Old documentation versions
- **`legacy_scripts/`** - Deprecated scripts
- **`pipeline_reset_20260112/`** - Pipeline reset snapshot
- **`story-generation/`** - Old story system implementation
- **`test_scripts/`** - Historical test scripts
- **`utilities/`** - Archived utility scripts
- **`world_state_YYYYMMDD_HHMMSS/`** - Timestamped world state backups (17 versions)

### Research (`research/`)
- **`mobile-testing-playwright/`** - Mobile testing guides
  - `quick-start.md`
  - `common-pitfalls.md`
  - `android-simulation-guide.md`

---

## 🔬 Development Environment

### Hidden Directories (Not Committed)
- **`.git/`** - Git repository metadata
- **`.github/`** - GitHub workflows and Copilot instructions
- **`.vscode/`** - VS Code workspace settings
- **`.venv/`** - Python virtual environment
- **`.pytest_cache/`** - Pytest cache
- **`.pio/`** - PlatformIO build cache
- **`.playwright-mcp/`** - Playwright browser cache

---

## 📊 Repository Statistics

### Code Coverage
- **Unit Tests:** 390 passing, ~17% coverage baseline
- **Integration Tests:** Mock-based, no external dependencies required
- **E2E Tests:** Requires Ollama + ChromaDB

### Lines of Code (Estimated)
- **Core Engine:** ~3,500 lines
- **Validation System:** ~1,200 lines
- **Story System:** ~1,100 lines  
- **Tests:** ~4,500 lines
- **Documentation:** ~8,000 lines

### Key Metrics
- **291,343** - ChromaDB chunks from Fallout Wiki
- **17 GB** - Vector database size
- **6** - DJ personalities supported
- **95+** - Unit tests passing
- **12** - Test fixtures defined

---

## 🚀 Quick Start Paths

### Run a Broadcast
```bash
python broadcast.py --dj Julie --days 7 --enable-stories
```

### Run Tests
```bash
python run_tests.py unit          # Unit tests only
python run_tests.py integration   # Integration tests
python run_tests.py coverage      # With coverage report
```

### Start Review App
```bash
cd tools/script-review-app
python -m uvicorn backend.main:app --reload
```

### Ingest Wiki Data
```bash
cd tools/wiki_to_chromadb
python chromadb_ingest.py --input fallout_wiki.xml --collection fallout_wiki
```

---

## 🎯 Critical Files (Top 20 by Importance)

1. **`broadcast_engine.py`** - Core orchestrator
2. **`generator.py`** - LLM script generation
3. **`llm_validator.py`** - Quality control
4. **`story_scheduler.py`** - Narrative management
5. **`broadcast.py`** - Main CLI entry
6. **`dj_knowledge_profiles.py`** - Knowledge constraints
7. **`session_memory.py`** - State continuity
8. **`ollama_client.py`** - LLM integration
9. **`weather_simulator.py`** - Weather system
10. **`consistency_validator.py`** - Cross-segment validation
11. **`rag_cache.py`** - RAG performance
12. **`chromadb_ingest.py`** - Knowledge base creation
13. **`world_state.py`** - Universe state
14. **`validation_rules.py`** - Rule engine
15. **`conftest.py`** - Test infrastructure
16. **`logging_config.py`** - Observability
17. **`story_weaver.py`** - Story integration
18. **`llm_pipeline.py`** - Generation pipeline
19. **`mock_ollama_client.py`** - Testing mocks
20. **`run_tests.py`** - Test orchestration

---

## 🐛 Known Issues (Identified During Reorganization)

1. **Story System:** Stories loaded but not integrated into scripts (see `GENERATION_FAILURE_20260120.md`)
2. **Validation Disabled:** `validation_enabled: false` in most broadcasts
3. **Content Repetition:** Gossip segments show high similarity
4. **Test Fixture Imports:** Some old tests reference deprecated conftest paths
5. **Module Import Errors:** Two test files have fixture import issues

---

## 📋 Next Steps

### High Priority
1. Enable validation system by default
2. Fix story integration in broadcast generation
3. Add diversity checks for gossip content
4. Resolve test fixture import errors
5. Create Appalachia-specific story library

### Medium Priority
1. Add environment variable templates (`.env.example`)
2. Create Docker Compose for services
3. Implement CLI improvements for `broadcast.py`
4. Add pre-commit hooks
5. Enhance mobile review app UX

### Low Priority
1. Archive old world state backups (compress)
2. Create setup script for new developers
3. Add contribution guidelines
4. Implement automated documentation generation
5. Create VS Code debugging configurations

---

**Document Version:** 1.0  
**Generated:** 2026-01-20  
**Maintainer:** GitHub Copilot + dogheadhunter
