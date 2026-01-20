# ESP32 AI Radio - Complete Scripts Reference

**Last Updated**: January 2026  
**Purpose**: Comprehensive catalog of all scripts, batch files, and Python modules in the ESP32 AI Radio project.

This document provides a complete reference for every executable script in the codebase, organized by category for easy navigation when refactoring or maintaining the project.

---

## Table of Contents

1. [Root-Level Python Scripts](#root-level-python-scripts)
2. [Batch Scripts (scripts/)](#batch-scripts)
3. [Script Generator (tools/script-generator/)](#script-generator-toolsscript-generator)
4. [Wiki to ChromaDB Pipeline (tools/wiki_to_chromadb/)](#wiki-to-chromadb-pipeline-toolswiki_to_chromadb)
5. [Script Review App (tools/script-review-app/)](#script-review-app-toolsscript-review-app)
6. [Shared Configuration (tools/shared/)](#shared-configuration-toolsshared)
7. [Archive and Utilities](#archive-and-utilities)
8. [Firmware](#firmware)
9. [Test Scripts](#test-scripts)

---

## Root-Level Python Scripts

These are the primary user-facing scripts in the project root directory.

### `broadcast.py`
**Purpose**: Main CLI tool for generating radio broadcasts  
**Type**: User-facing CLI application  
**Dependencies**: 
- `tools/script-generator/broadcast_engine.py`
- Ollama LLM service running
- ChromaDB populated with wiki data

**Usage**:
```bash
# Generate 7 days of content for Julie
python broadcast.py --dj Julie --days 7 --enable-stories

# Generate 24 hours for Mr. New Vegas with validation
python broadcast.py --dj "Mr. New Vegas" --hours 24 --validation-mode hybrid

# Generate with custom segments per hour
python broadcast.py --dj Travis --days 2 --segments-per-hour 3
```

**What it does**:
- Provides full control over DJ personalities, story system, validation modes
- Generates Fallout-themed radio broadcasts with temporal/spatial consistency
- Supports DJ shortcuts: 'julie', 'vegas', 'travis', 'travis-confident', 'threedog', '3dog'
- Outputs scripts to configured output directory

---

### `generate_julie.py`
**Purpose**: Quick script generator for Julie personality  
**Type**: Convenience wrapper  
**Dependencies**: 
- `tools/script-generator/broadcast_engine.py`

**What it does**:
- Generates 8 hours of content (2 segments per hour = 16 scripts) for Julie
- Outputs to `output/scripts/pending_review/Julie/`
- Pre-configured with validation enabled
- Filename format: `2026-01-17_HHMMSS_Julie_Segment-Type.txt`

**Usage**:
```bash
python generate_julie.py
```

---

### `generate_mr_new_vegas.py`
**Purpose**: Quick script generator for Mr. New Vegas personality  
**Type**: Convenience wrapper  
**Dependencies**: 
- `tools/script-generator/broadcast_engine.py`

**What it does**:
- Generates 8 hours of content (2 segments per hour = 16 scripts) for Mr. New Vegas
- Outputs to `output/scripts/pending_review/Mr. New Vegas/`
- Pre-configured with validation enabled
- Uses Mojave Wasteland temporal/spatial context (2281)

**Usage**:
```bash
python generate_mr_new_vegas.py
```

---

### `generate_travis.py`
**Purpose**: Quick script generator for Travis Miles (Nervous) personality  
**Type**: Convenience wrapper  
**Dependencies**: 
- `tools/script-generator/broadcast_engine.py`

**What it does**:
- Generates 8 hours of content for Travis Miles Nervous variant
- Outputs to `output/scripts/pending_review/Travis Miles (Nervous)/`
- Uses Commonwealth temporal/spatial context (2287)
- Pre-configured with validation enabled

**Usage**:
```bash
python generate_travis.py
```

---

### `generate_performance_test_scripts.py`
**Purpose**: Generate bulk test scripts for performance testing  
**Type**: Development/testing utility  
**Dependencies**: 
- `tools/script-generator/broadcast_engine.py`

**What it does**:
- Generates 100+ test scripts by duplicating category samples
- Creates one template per category: weather, news, music, gossip, general, story
- Duplicates templates to create volume for performance testing
- Outputs to `output/scripts/pending_review/Julie/perf_test_*.txt`
- Runs with validation disabled for speed

**Usage**:
```bash
python generate_performance_test_scripts.py
```

---

### `reset_world_state.py`
**Purpose**: Archive current state and reset for fresh broadcast season  
**Type**: Maintenance utility  
**Dependencies**: None (file system operations only)

**What it does**:
- Creates timestamped archives in `archive/world_state_YYYYMMDD_HHMMSS/`
- Archives broadcast data, world state, generated content
- Perfect for:
  - Starting a new broadcast "season"
  - Testing story progression from scratch
  - Cleaning up after experimentation
- Moves files from output directories to archive

**Usage**:
```bash
python reset_world_state.py
```

---

### `test_integration.py`
**Purpose**: Quick integration test for ChromaDB and Ollama connections  
**Type**: Development utility  
**Dependencies**: 
- `tools/wiki_to_chromadb/chromadb_ingest.py`
- `tools/script-generator/ollama_client.py`
- ChromaDB running
- Ollama running

**What it does**:
- Tests ChromaDB connection and verifies database has data
- Tests Ollama LLM connection and model availability
- Reports collection stats (total chunks, collection name)
- Returns success/failure status for each component

**Usage**:
```bash
python test_integration.py
```

---

## Batch Scripts

Located in `scripts/` directory - portable batch scripts for common operations.

### `run_tests.bat`
**Purpose**: Run all test suites in the project  
**Type**: Test runner  
**Dependencies**: 
- pytest installed
- All project dependencies

**What it does**:
1. Runs Wiki Ingestion Pipeline tests (`tools/wiki_to_chromadb/`)
2. Runs Script Generator tests (`tools/script-generator/`)
3. Reports success/failure for each suite
4. Exits with error code if any tests fail

**Usage**:
```cmd
.\scripts\run_tests.bat
```

---

### `ingest_wiki.bat`
**Purpose**: Ingest Fallout Wiki XML into ChromaDB (update mode)  
**Type**: Data pipeline  
**Dependencies**: 
- `tools/wiki_to_chromadb/process_wiki.py`
- `lore/fallout_wiki_complete.xml`

**What it does**:
- Configures Windows power settings to prevent sleep during ingestion
- Runs wiki processing pipeline (2-3 hours)
- Preserves existing ChromaDB data (update mode, not fresh)
- Restores power settings after completion
- Uses `--no-progress` flag for cleaner output

**Usage**:
```cmd
.\scripts\ingest_wiki.bat
```

**Note**: Takes 2-3 hours to complete. Ingests ~40K+ articles into ChromaDB.

---

### `ingest_wiki_fresh.bat`
**Purpose**: Fresh ingestion of Fallout Wiki (deletes existing ChromaDB)  
**Type**: Data pipeline  
**Dependencies**: 
- `tools/wiki_to_chromadb/process_wiki.py`
- `lore/fallout_wiki_complete.xml`

**What it does**:
- Same as `ingest_wiki.bat` but starts fresh
- Deletes existing ChromaDB collection
- Full re-ingestion from scratch
- Useful for testing pipeline changes or database corruption recovery

**Usage**:
```cmd
.\scripts\ingest_wiki_fresh.bat
```

---

### `backup_database.bat`
**Purpose**: Wrapper for PowerShell backup script  
**Type**: Maintenance utility  
**Dependencies**: 
- PowerShell execution policy allows scripts
- `backup_database.ps1` in project root

**What it does**:
- Calls PowerShell backup script with bypass execution policy
- Creates backup of ChromaDB database
- Timestamped backup archives

**Usage**:
```cmd
.\scripts\backup_database.bat
```

---

### `backup_quick.bat`
**Purpose**: Quick backup of essential files  
**Type**: Maintenance utility  
**Dependencies**: None (file copy operations)

**What it does**:
- Quick backup of critical project files
- Faster than full database backup
- Copies configuration and state files to backup location

**Usage**:
```cmd
.\scripts\backup_quick.bat
```

---

### `restore_database.bat`
**Purpose**: Restore ChromaDB from backup  
**Type**: Maintenance utility  
**Dependencies**: 
- Backup files exist
- PowerShell restore script

**What it does**:
- Restores ChromaDB database from timestamped backup
- Prompts for backup selection
- Replaces current database with backup

**Usage**:
```cmd
.\scripts\restore_database.bat
```

---

### `analyze_log.bat`
**Purpose**: Analyze latest wiki ingestion log  
**Type**: Development utility  
**Dependencies**: 
- `tools/wiki_to_chromadb/analyze_log.py`

**What it does**:
- Analyzes ingestion log files for errors and statistics
- Reports processing metrics
- Passes command-line arguments to Python analyzer

**Usage**:
```cmd
.\scripts\analyze_log.bat [arguments]
```

---

## Script Generator (tools/script-generator/)

RAG-powered radio script generation system. **75 Python files total**.

### Core Engine Files

#### `broadcast_engine.py`
**Purpose**: Main broadcast generation orchestration engine  
**Type**: Core library  
**Size**: ~46KB

**What it does**:
- Orchestrates entire broadcast generation process
- Manages DJ personalities and session state
- Coordinates RAG queries, LLM generation, validation
- Handles temporal/spatial consistency
- Manages broadcast scheduling and segment sequencing
- Integrates story system with broadcast flow
- Provides validation modes: strict, permissive, hybrid, disabled

**Key Classes**:
- `BroadcastEngine`: Main orchestration class
- Methods: `start_broadcast()`, `generate_broadcast_sequence()`, `end_broadcast()`

---

#### `generator.py`
**Purpose**: Core RAG-powered script generation  
**Type**: Core library  
**Size**: ~41KB

**What it does**:
- Interfaces with ChromaDB for lore retrieval
- Uses Ollama LLM for text generation
- Implements Jinja2 template rendering
- Handles 5 script types: weather, news, music, gossip, general
- Manages DJ personality injection
- Provides model unloading for VRAM management

**Key Classes**:
- `ScriptGenerator`: Main generation class
- Methods: `generate_script()`, `save_script()`, `unload_model()`

---

#### `ollama_client.py`
**Purpose**: Ollama LLM API client wrapper  
**Type**: External service client  
**Size**: ~7KB

**What it does**:
- Handles HTTP communication with Ollama service
- Manages streaming and non-streaming responses
- Implements retry logic and error handling
- Provides model loading/unloading
- Supports multiple models with fallback

**Key Functions**:
- `generate_text()`: Main generation function
- `stream_generate()`: Streaming generation
- `is_model_loaded()`: Check model status

---

### Validation System

#### `llm_validator.py`
**Purpose**: Intelligent LLM-powered script validation  
**Type**: Validation library  
**Size**: ~23KB

**What it does**:
- Hybrid LLM + rule-based validation
- Checks lore accuracy, character consistency, tone
- Validates temporal/spatial references
- Detects anachronisms and out-of-character dialogue
- Provides detailed validation reports with suggestions
- Three validation modes: strict, permissive, hybrid

**Key Classes**:
- `LLMValidator`: Main validation class
- Methods: `validate_script()`, `get_validation_report()`

---

#### `consistency_validator.py`
**Purpose**: Rule-based consistency validation  
**Type**: Validation library  
**Size**: ~12KB

**What it does**:
- Fast rule-based validation checks
- Validates DJ personality consistency
- Checks script structure and formatting
- Validates metadata completeness
- Used in conjunction with LLM validator

**Key Classes**:
- `ConsistencyValidator`: Main validation class

---

#### `phase6_validation.py`
**Purpose**: Phase 6 comprehensive validation suite  
**Type**: Validation library  
**Size**: ~30KB

**What it does**:
- Advanced validation for Phase 6 features
- Multi-dimensional validation: lore, character, temporal, spatial
- Comprehensive reporting system
- Integration testing support

---

### DJ Personality System

#### `personality_loader.py`
**Purpose**: Load and parse DJ character profiles  
**Type**: Data loader  
**Size**: ~5KB

**What it does**:
- Loads character cards from `dj_personalities/`
- Parses JSON character configuration
- Reads markdown personality profiles
- Validates personality data structure
- Provides personality data to generation system

**Key Functions**:
- `load_personality()`: Load DJ profile
- `get_available_personalities()`: List all DJs

---

#### `dj_knowledge_profiles.py`
**Purpose**: DJ-specific knowledge filtering and context  
**Type**: Knowledge management  
**Size**: ~24KB

**What it does**:
- Implements temporal/spatial filtering for DJ knowledge
- Manages what each DJ "knows" based on their time/location
- Filters ChromaDB queries by era and region
- Provides DJ-specific context augmentation
- Prevents anachronisms in generated content

**Key Classes**:
- `DJKnowledgeProfile`: Knowledge filter class
- Temporal ranges, spatial boundaries per DJ

---

### Broadcasting and Scheduling

#### `broadcast_scheduler.py`
**Purpose**: Schedule broadcast segments over time  
**Type**: Scheduling utility  
**Size**: ~4KB

**What it does**:
- Schedules segment generation over hours/days
- Manages segment timing and sequencing
- Coordinates multi-segment broadcasts
- Ensures proper pacing and variety

**Key Classes**:
- `BroadcastScheduler`: Scheduling class

---

#### `broadcast_freshness.py`
**Purpose**: Prevent content repetition across broadcasts  
**Type**: Content management  
**Size**: ~14KB

**What it does**:
- Tracks previously used lore chunks
- Prevents repeating the same facts too frequently
- Manages "freshness" scoring for content
- Ensures variety across multiple broadcast sessions
- Configurable repeat windows

**Key Classes**:
- `BroadcastFreshness`: Freshness tracking class

---

#### `session_memory.py`
**Purpose**: Maintain broadcast session state and memory  
**Type**: State management

**What it does**:
- Tracks what was said in current broadcast session
- Prevents immediate repetition within session
- Manages short-term memory for continuity
- Saves and loads session state

---

### Weather and World State

#### `weather_simulator.py`
**Purpose**: Generate realistic weather patterns for broadcasts  
**Type**: Simulation system

**What it does**:
- Simulates Fallout-appropriate weather (radiation storms, etc.)
- Generates daily weather forecasts
- Maintains weather continuity across broadcasts
- Provides weather data for script generation

**Key Classes**:
- `WeatherSimulator`: Weather generation class

---

#### `world_state.py`
**Purpose**: Manage global world state across broadcasts  
**Type**: State management

**What it does**:
- Tracks global events and changes
- Manages persistent world state
- Coordinates state between broadcasts
- Saves/loads world state from JSON

---

#### `query_weather_history.py`
**Purpose**: Query historical weather data  
**Type**: Utility script  
**Executable**: Yes

**What it does**:
- Queries past weather records from world state
- Provides historical weather context
- Used for generating weather reports with continuity

**Usage**:
```bash
python tools/script-generator/query_weather_history.py
```

---

#### `regenerate_weather_calendar.py`
**Purpose**: Regenerate weather calendar for new time period  
**Type**: Utility script  
**Executable**: Yes

**What it does**:
- Creates new weather calendar from scratch
- Useful for resetting weather state
- Generates realistic weather patterns

**Usage**:
```bash
python tools/script-generator/regenerate_weather_calendar.py
```

---

#### `regional_climate.py`
**Purpose**: Define climate patterns for different Fallout regions  
**Type**: Configuration/data

**What it does**:
- Defines regional climate characteristics
- Provides climate data for different wastelands
- Used by weather simulator for region-appropriate weather

---

#### `set_weather.py`
**Purpose**: Manually set weather for testing  
**Type**: Development utility

**What it does**:
- Override weather system with manual settings
- Useful for testing specific weather scenarios
- Bypasses weather simulation

---

### Story System

Located in `tools/script-generator/story_system/`

**Purpose**: Multi-temporal story arc management for broadcasts

**Key Files**:
- Story arc management and progression
- Character development tracking
- Plot thread coordination
- Story-to-broadcast integration

---

### Templates

Located in `tools/script-generator/templates/`

**Purpose**: Jinja2 templates for different script types

**Templates**:
- `weather.jinja2` - Weather report format
- `news.jinja2` - News broadcast format
- `music.jinja2` - Music introduction format
- `gossip.jinja2` - Wasteland gossip format
- `general.jinja2` - General commentary format
- Story-related templates

---

### Content Types

Located in `tools/script-generator/content_types/`

**Purpose**: Define content type schemas and validation

---

### Test Files

Located in `tools/script-generator/tests/`

**Key Test Files**:
- `test_broadcast_llm_validation.py` - Tests for LLM validation
- `test_dj_knowledge_system.py` - Tests for DJ knowledge filtering
- `test_llm_validator_standalone.py` - Standalone validator tests
- Additional unit and integration tests

---

### Examples and Demos

#### `demo_llm_validation_integration.py`
**Purpose**: Demonstrate LLM validation system  
**Type**: Example/demo script

**What it does**:
- Shows how to use LLM validation
- Provides example validation scenarios
- Demonstrates validation modes
- Good starting point for understanding validation system

**Usage**:
```bash
python tools/script-generator/demo_llm_validation_integration.py
```

---

### Query Helpers

#### `query_helpers.py`
**Purpose**: Helper functions for ChromaDB queries  
**Type**: Utility library  
**Size**: ~6KB

**What it does**:
- Provides reusable query patterns
- Simplifies common ChromaDB operations
- Handles query formatting and filtering
- Used throughout script generation system

---

## Wiki to ChromaDB Pipeline (tools/wiki_to_chromadb/)

Complete pipeline for converting Fallout Wiki XML to ChromaDB embeddings. **49 Python files total**.

### Core Pipeline Files

#### `process_wiki.py`
**Purpose**: Main entry point for wiki processing pipeline  
**Type**: Main executable  
**Size**: ~17KB

**What it does**:
- Orchestrates entire wiki → ChromaDB pipeline
- Streaming XML processing for memory efficiency
- Wikitext cleaning and conversion
- Semantic chunking (500-800 tokens with 100-token overlap)
- Metadata enrichment (temporal/spatial/content-type classification)
- ChromaDB ingestion with embeddings
- Progress tracking and logging

**Usage**:
```bash
python tools/wiki_to_chromadb/process_wiki.py lore/fallout_wiki_complete.xml
python tools/wiki_to_chromadb/process_wiki.py lore/fallout_wiki_complete.xml --no-progress
```

**Key Features**:
- Update mode (preserves existing data)
- Fresh mode (deletes existing collection)
- Progress bars or quiet mode
- Comprehensive error logging

---

#### `chromadb_ingest.py`
**Purpose**: ChromaDB client and ingestion logic  
**Type**: Core library  
**Size**: ~15KB

**What it does**:
- Interfaces with ChromaDB database
- Manages collection creation and updates
- Handles embeddings and metadata
- Provides query interface
- Batch insertion for performance
- Collection statistics and health checks

**Key Classes**:
- `ChromaDBIngestor`: Main database interface
- Methods: `ingest_chunks()`, `query()`, `get_collection_stats()`

---

### Parsing and Extraction

#### `wiki_parser.py`
**Purpose**: MediaWiki XML parsing (legacy)  
**Type**: Parser library  
**Size**: ~Various

**What it does**:
- Parses MediaWiki XML dump format
- Extracts article content
- Handles XML namespaces
- Streaming parsing for large files

**Status**: Still in use, but see `wiki_parser_v2.py` for enhanced version

---

#### `wiki_parser_v2.py`
**Purpose**: Enhanced MediaWiki XML parser  
**Type**: Parser library  
**Size**: ~Various

**What it does**:
- Improved version of wiki_parser.py
- Better error handling
- Enhanced metadata extraction
- Preserves native MediaWiki structure
- Extracts categories, infoboxes, templates, wikilinks

---

#### `extractors.py`
**Purpose**: Extract specific elements from wikitext  
**Type**: Extraction library  
**Size**: ~11KB

**What it does**:
- Extract categories from wikitext
- Extract infoboxes
- Extract templates ({{Game}}, {{Quote}}, etc.)
- Extract wikilinks [[Link|Display]]
- Parse complex MediaWiki markup

**Key Functions**:
- `extract_categories()`
- `extract_infoboxes()`
- `extract_templates()`
- `extract_links()`

---

#### `template_parser.py`
**Purpose**: Parse MediaWiki template syntax  
**Type**: Parser library

**What it does**:
- Parses {{template}} syntax
- Handles nested templates
- Extracts template parameters
- Resolves template references

---

### Chunking

#### `chunker.py`
**Purpose**: Semantic chunking for wiki articles (legacy)  
**Type**: Text processing library  
**Size**: ~16KB  
**Status**: ⚠️ Deprecated - shows warning on import

**What it does**:
- Section-based chunking
- 500-800 token chunks with 100-token overlap
- Preserves section context
- Smart boundary detection

**Migration**: Use `chunker_v2.py` instead

---

#### `chunker_v2.py`
**Purpose**: Enhanced semantic chunking (recommended)  
**Type**: Text processing library  
**Size**: ~12KB

**What it does**:
- Improved version of chunker.py
- Type-safe with Pydantic models
- Better section handling
- Preserves hierarchical structure
- Configurable chunk sizes and overlap

**Key Classes**:
- `ChunkerV2`: Main chunking class
- Pydantic models for type safety

---

### Metadata Enrichment

#### `metadata_enrichment.py`
**Purpose**: Automatic metadata classification (current)  
**Type**: Enrichment library  
**Size**: ~20KB

**What it does**:
- Temporal classification (which era does content belong to?)
- Spatial classification (which region/location?)
- Content-type classification (character, location, faction, etc.)
- DJ relevance scoring
- Uses regex patterns and keyword matching

**Key Classes**:
- `MetadataEnricher`: Main enrichment class
- Methods: `enrich_chunk()`, `classify_temporal()`, `classify_spatial()`

---

#### `metadata_enrichment_v2.py`
**Purpose**: Enhanced metadata enrichment with Pydantic  
**Type**: Enrichment library  
**Size**: ~23KB

**What it does**:
- Type-safe metadata enrichment
- Improved classification accuracy
- Better handling of edge cases
- Pydantic validation of metadata
- Preserves native MediaWiki structure in metadata

---

#### `re_enrich_database.py`
**Purpose**: Re-run metadata enrichment on existing database  
**Type**: Utility script  
**Size**: ~7KB

**What it does**:
- Updates metadata for chunks already in ChromaDB
- Useful after enrichment logic improvements
- Batch processing of existing data
- Preserves original chunks, updates metadata only

**Usage**:
```bash
python tools/wiki_to_chromadb/re_enrich_database.py
```

---

#### `re_enrich_phase6.py`
**Purpose**: Phase 6 metadata re-enrichment  
**Type**: Utility script  
**Size**: ~20KB

**What it does**:
- Specifically for Phase 6 metadata updates
- Enhanced structural metadata preservation
- Updates to include native categories, infoboxes, templates
- Batch processing with progress tracking

**Usage**:
```bash
python tools/wiki_to_chromadb/re_enrich_phase6.py
```

---

### Configuration and Models

#### `config.py`
**Purpose**: Configuration for wiki processing pipeline  
**Type**: Configuration file  
**Size**: ~5KB

**What it does**:
- Defines processing parameters
- Chunk sizes, overlap amounts
- Database settings
- Environment variable loading
- Processing options

**Key Settings**:
- `CHUNK_SIZE`: Target chunk size in tokens
- `CHUNK_OVERLAP`: Overlap between chunks
- `BATCH_SIZE`: ChromaDB batch insertion size

---

#### `constants.py`
**Purpose**: Constants and lookup tables  
**Type**: Constants file  
**Size**: ~19KB

**What it does**:
- Temporal classification patterns
- Spatial classification patterns
- Content-type keywords
- DJ knowledge filters
- Regular expressions for classification

---

#### `models.py`
**Purpose**: Pydantic data models for type safety  
**Type**: Data models  
**Size**: ~10KB

**What it does**:
- Defines data structures for chunks
- Metadata schemas
- Validation rules
- Type hints for all data
- Used by v2 modules for type safety

**Key Models**:
- `WikiChunk`: Chunk data model
- `ChunkMetadata`: Metadata model
- Validation methods

---

### Logging and Debugging

#### `logging_config.py`
**Purpose**: Structured logging configuration  
**Type**: Logging configuration  
**Size**: ~3KB

**What it does**:
- Configures Python logging
- Sets log levels and formats
- File and console handlers
- Structured logging for pipeline
- Log rotation settings

---

#### `analyze_log.py`
**Purpose**: Analyze processing logs for insights  
**Type**: Analysis utility  
**Size**: ~12KB

**What it does**:
- Parses pipeline log files
- Generates statistics reports
- Identifies errors and warnings
- Performance metrics
- Success/failure counts

**Usage**:
```bash
python tools/wiki_to_chromadb/analyze_log.py [log_file]
.\scripts\analyze_log.bat
```

---

#### `debug_sections.py`
**Purpose**: Debug section parsing issues  
**Type**: Debug utility  
**Size**: ~3KB

**What it does**:
- Analyzes section extraction
- Shows section hierarchy
- Identifies parsing problems
- Useful for troubleshooting

**Usage**:
```bash
python tools/wiki_to_chromadb/debug_sections.py
```

---

#### `debug_missing_sections.py`
**Purpose**: Find articles with missing sections  
**Type**: Debug utility  
**Size**: ~3KB

**What it does**:
- Identifies articles without sections
- Checks section extraction completeness
- Reports parsing failures
- Quality assurance tool

**Usage**:
```bash
python tools/wiki_to_chromadb/debug_missing_sections.py
```

---

### Testing and Verification

#### `test_database.py`
**Purpose**: Test ChromaDB connection and data  
**Type**: Test utility

**What it does**:
- Verifies ChromaDB connection
- Tests query functionality
- Checks data integrity
- Validates embeddings

**Usage**:
```bash
python tools/wiki_to_chromadb/test_database.py
```

---

#### `verify_database.py`
**Purpose**: Comprehensive database verification  
**Type**: Verification utility

**What it does**:
- Checks database health
- Validates all chunks
- Verifies metadata completeness
- Generates verification report

**Usage**:
```bash
python tools/wiki_to_chromadb/verify_database.py
```

---

#### `verify_fixes.py`
**Purpose**: Verify specific bug fixes  
**Type**: Verification utility

**What it does**:
- Tests specific fixes after bugs
- Validates edge cases
- Regression testing
- Quality assurance

**Usage**:
```bash
python tools/wiki_to_chromadb/verify_fixes.py
```

---

#### `test_ingestion_quality.py`
**Purpose**: Test ingestion quality metrics  
**Type**: Test utility

**What it does**:
- Measures ingestion accuracy
- Checks chunk quality
- Validates metadata correctness
- Performance benchmarks

---

#### `test_new_patterns.py`
**Purpose**: Test new classification patterns  
**Type**: Test utility

**What it does**:
- Tests new regex patterns
- Validates classification changes
- Before deploying pattern updates
- Pattern accuracy testing

---

#### `test_section_fix.py`
**Purpose**: Test section parsing fixes  
**Type**: Test utility

**What it does**:
- Validates section parsing improvements
- Tests edge cases in section extraction
- Regression testing for section bugs

---

### Performance and Benchmarking

#### `benchmark.py`
**Purpose**: Performance benchmarking for pipeline  
**Type**: Benchmark utility  
**Size**: ~16KB

**What it does**:
- Measures processing speed
- Times different pipeline stages
- Generates performance reports
- Compares different approaches
- Saves results to `benchmark_results.json`

**Usage**:
```bash
python tools/wiki_to_chromadb/benchmark.py
```

---

#### `analyze_dump_stats.py`
**Purpose**: Analyze wiki dump statistics  
**Type**: Analysis utility  
**Size**: ~6KB

**What it does**:
- Analyzes XML dump structure
- Counts articles, categories, templates
- Reports size statistics
- Useful for understanding data before processing

**Usage**:
```bash
python tools/wiki_to_chromadb/analyze_dump_stats.py lore/fallout_wiki_complete.xml
```

---

### Phase 6 Metadata System

#### `phase6_metadata_audit.py`
**Purpose**: Audit Phase 6 structural metadata  
**Type**: Audit utility  
**Size**: ~28KB

**What it does**:
- Audits native structure preservation
- Checks categories, infoboxes, templates, wikilinks
- Generates compliance reports
- Identifies missing metadata
- Quality assurance for Phase 6 features

**Usage**:
```bash
python tools/wiki_to_chromadb/phase6_metadata_audit.py
```

---

### Tests Directory

Located in `tools/wiki_to_chromadb/tests/`

**Purpose**: Pytest test suite for wiki pipeline

**Coverage**: 87 passing tests, ~40% code coverage

**Key Test Areas**:
- XML parsing
- Chunk creation
- Metadata enrichment
- ChromaDB integration
- Edge cases and error handling

**Usage**:
```bash
cd tools/wiki_to_chromadb
python -m pytest -v
```

---

## Script Review App (tools/script-review-app/)

Mobile-first Progressive Web App for reviewing AI-generated DJ scripts.

### Backend (FastAPI)

#### `run_server.py`
**Purpose**: Start the FastAPI backend server  
**Type**: Server launcher

**What it does**:
- Starts FastAPI server on localhost
- Serves REST API for script management
- Provides authentication endpoints
- Handles file operations for scripts

**Usage**:
```bash
cd tools/script-review-app
python run_server.py
```

---

#### `backend/main.py`
**Purpose**: FastAPI application and routes  
**Type**: API application

**What it does**:
- Defines API endpoints
- Handles script CRUD operations
- Authentication middleware
- CORS configuration
- Request validation

**Key Endpoints**:
- `GET /api/scripts/pending` - Get pending scripts
- `POST /api/scripts/{id}/approve` - Approve script
- `POST /api/scripts/{id}/reject` - Reject script
- `GET /api/stats` - Get statistics

---

#### `backend/storage.py`
**Purpose**: File-based storage for scripts and metadata  
**Type**: Storage layer

**What it does**:
- Manages script file organization
- Handles metadata JSON files
- Moves scripts between folders (pending/approved/rejected)
- Tracks review history
- Generates filenames and paths

**Key Classes**:
- `StorageManager`: File operations manager

---

#### `backend/auth.py`
**Purpose**: Token-based authentication  
**Type**: Authentication module

**What it does**:
- Validates bearer tokens
- Environment variable configuration
- Simple token auth for API
- Protects endpoints

---

#### `backend/config.py`
**Purpose**: Backend configuration  
**Type**: Configuration

**What it does**:
- Loads environment variables
- Configures paths
- Server settings
- CORS origins

---

#### `backend/models.py`
**Purpose**: Pydantic models for API  
**Type**: Data models

**What it does**:
- Script data models
- Review metadata models
- Request/response schemas
- Validation rules

---

#### `backend/dj_profiles.py`
**Purpose**: DJ personality profiles for UI  
**Type**: Configuration

**What it does**:
- Defines DJ profile data
- Character descriptions
- Profile images
- Used by frontend for display

---

### Frontend

Located in `tools/script-review-app/frontend/`

**Purpose**: Mobile-first PWA for script review

**Technologies**:
- Vanilla JavaScript (no framework)
- Tailwind CSS for styling
- Service Worker for offline support
- Touch gesture detection

**Key Features**:
- Tinder-like swipe interface
- Swipe right to approve, left to reject
- Statistics dashboard
- Responsive design
- Keyboard shortcuts

---

### Utilities and Tests

#### `generate_icons.py`
**Purpose**: Generate PWA icons and assets  
**Type**: Asset generator

**What it does**:
- Generates app icons in multiple sizes
- Creates splash screens
- PWA manifest icons
- iOS app icons

**Usage**:
```bash
python tools/script-review-app/generate_icons.py
```

---

#### `generate_test_scripts.py`
**Purpose**: Generate test scripts for review app  
**Type**: Test data generator

**What it does**:
- Creates sample scripts for testing
- Populates pending_review folder
- Different DJ personalities
- Various script types
- Useful for UI testing

**Usage**:
```bash
python tools/script-review-app/generate_test_scripts.py
```

---

#### `send_email.py`
**Purpose**: Email notification system  
**Type**: Notification utility

**What it does**:
- Sends email notifications
- Review status updates
- Daily summary emails
- Configurable SMTP settings

**Usage**:
```bash
python tools/script-review-app/send_email.py
```

---

#### `tests/`
**Purpose**: Test suite for review app

**Key Files**:
- `test_playwright.py` - Browser automation tests
- `conftest.py` - Pytest configuration
- `ui/capture_screenshots.py` - Screenshot testing
- `ui/create_mock_scripts.py` - Mock data for tests

---

### Startup Scripts

#### `start.bat` / `start.sh`
**Purpose**: Quick start script for development  
**Type**: Launcher

**What it does**:
- Starts backend server
- Opens browser to app
- Development mode startup

**Usage**:
```cmd
.\tools\script-review-app\start.bat
```

---

#### `auto-start-simple.ps1`
**Purpose**: Simple PowerShell auto-start  
**Type**: PowerShell launcher

**What it does**:
- Starts server in background
- Opens browser automatically
- Windows-specific launcher

---

#### `auto-start-with-email.ps1`
**Purpose**: Auto-start with email notifications  
**Type**: PowerShell launcher

**What it does**:
- Starts server with email enabled
- Configures SMTP settings
- Sends notification emails

---

## Shared Configuration (tools/shared/)

Centralized configuration for all Python tools.

### `project_config.py`
**Purpose**: Shared project configuration and paths  
**Type**: Configuration module  
**Size**: ~3KB

**What it does**:
- Defines PROJECT_ROOT for all tools
- LLM configuration (model names, Ollama URL)
- Database paths (CHROMA_DB_PATH)
- Content source paths (LORE_PATH)
- Output paths (SCRIPTS_OUTPUT_DIR, AUDIO_OUTPUT_DIR)
- Personality paths (PERSONALITIES_DIR)
- Creates output directories if missing

**Key Constants**:
- `PROJECT_ROOT`: Absolute path to project root
- `LLM_MODEL`: "fluffy/l3-8b-stheno-v3.2"
- `LLM_BACKUP_MODEL`: "dolphin-llama3"
- `OLLAMA_URL`: "http://localhost:11434/api/generate"
- `CHROMA_DB_PATH`: Path to ChromaDB storage
- `LORE_PATH`: Path to wiki XML
- `OUTPUT_PATH`: Output directory
- `PERSONALITIES_DIR`: DJ personality directory

**Usage**:
```python
from tools.shared.project_config import PROJECT_ROOT, CHROMA_DB_PATH
```

---

## Archive and Utilities

Historical and archived components.

### Archive Organization

Located in `archive/` directory. See `archive/INDEX.md` for complete catalog.

**Key Archive Folders**:

#### `archive/pipeline_reset_20260112/`
**Purpose**: Preserved TTS pipeline development history  
**Contents**:
- Old TTS generation scripts
- Custom pipeline code
- Validation iteration data
- Historical reference (do not delete)

---

#### `archive/lore-scraper/`
**Purpose**: Early wiki scraping tools  
**Contents**: 
- Superseded by `tools/wiki_to_chromadb/`
- Python scraping scripts
- Early data extraction attempts

---

#### `archive/story-generation/`
**Purpose**: Early story generation experiments  
**Contents**:
- Narrative generation prototypes
- Replaced by `tools/script-generator/`

---

#### `archive/xtts-research/`
**Purpose**: XTTS fine-tuning research  
**Contents**:
- XTTS v2 research documents
- Fine-tuning guides
- Preserved for future TTS projects

---

#### `archive/backups/`
**Purpose**: One-off files and manual backups  
**Contents**:
- `wiki_xml_backup/` - Duplicate wiki XML (safe to delete)
- `test_normalize.py` - Audio normalization tests

---

### Archive Utilities

#### `archive/utilities/`
**Purpose**: Archived utility scripts  
**Contents**: Various one-off utilities no longer in active use

---

#### `archive/test_scripts/`
**Purpose**: Old test scripts  
**Contents**: Historical test scripts superseded by current test suites

---

#### `archive/documentation/`
**Purpose**: Old documentation  
**Contents**: Superseded documentation versions

---

## Firmware

ESP32 C++ firmware for audio playback.

### `firmware/main.cpp`
**Purpose**: ESP32 firmware for MP3 playback  
**Type**: C++ firmware  
**Platform**: PlatformIO + ESP32 + Arduino

**What it does**:
- MP3 audio playback from SD card
- I2S audio output to MAX98357A amplifier
- SD card file management (VSPI bus)
- Volume control via potentiometer
- Status LED indication
- WiFi connectivity (optional)

**Hardware**:
- Board: ESP32 Dev Module (ESP-WROOM-32)
- Audio: MAX98357A I2S 3W Class D Amplifier
- Speaker: DWEII 4 Ohm 3 Watt
- Storage: Micro SD Card

**Pinout**:
- I2S BCLK: GPIO 26
- I2S LRC: GPIO 25
- I2S DIN: GPIO 22
- SD CS: GPIO 5
- SD MOSI: GPIO 23
- SD MISO: GPIO 19
- SD SCK: GPIO 18
- Volume: GPIO 39 (ADC)
- LED: GPIO 2

**Building**:
```bash
pio run -t upload
```

---

### `platformio.ini`
**Purpose**: PlatformIO build configuration  
**Type**: Configuration file

**What it does**:
- Defines ESP32 platform and board
- Lists library dependencies
- Build flags and settings
- Upload configuration

**Key Dependencies**:
- `ESP8266Audio` - Audio playback library
- Arduino framework

---

## Test Scripts

Various test and verification scripts.

### `test_phase8_performance.ps1`
**Purpose**: Phase 8 performance testing  
**Type**: PowerShell test script

**What it does**:
- Performance benchmarks for Phase 8 features
- Measures generation speed
- Resource usage tracking
- Generates performance reports

**Usage**:
```powershell
.\test_phase8_performance.ps1
```

---

### Test Directories

#### `tests/`
**Purpose**: Repository-level tests  
**Contents**: High-level integration tests

#### `tests/ui/`
**Purpose**: UI testing (script-review-app)  
**Contents**: Playwright browser tests, screenshots

---

## Documentation Files

Comprehensive project documentation.

### Root Documentation

#### `README.md`
**Purpose**: Main project documentation  
**Contents**: 
- Project overview
- Quick start guide
- Architecture overview
- Hardware setup
- Installation instructions

---

### `docs/` Directory

Comprehensive technical documentation.

#### `docs/ARCHITECTURE.md`
**Purpose**: System architecture documentation  
**Contents**: 
- Component architecture
- Data flow diagrams
- System design decisions
- Integration points

---

#### `docs/DJ_KNOWLEDGE_SYSTEM.md`
**Purpose**: DJ knowledge filtering documentation  
**Contents**: 
- Temporal/spatial filtering
- DJ knowledge profiles
- Lore consistency rules

---

#### `docs/SYSTEM_SPECS.md`
**Purpose**: System specifications  
**Contents**: 
- Hardware requirements
- Software requirements
- Performance specs

---

#### `docs/INLAND_ESP32_SPECS.md`
**Purpose**: Specific ESP32 hardware specs  
**Contents**: 
- Board specifications
- Pin configurations
- Hardware limitations

---

#### `docs/LOCAL_TESTING_PLAN.md`
**Purpose**: Local testing procedures  
**Contents**: 
- Test plans
- Validation procedures
- Quality assurance steps

---

#### `docs/PHASE7_COMPLETE.md`
**Purpose**: Phase 7 completion report  
**Contents**: Multi-temporal story system completion

---

#### `docs/PHASE7_MULTI_TEMPORAL_STORY_SYSTEM.md`
**Purpose**: Phase 7 feature documentation  
**Contents**: 
- Multi-temporal story arcs
- Cross-era story coordination
- Implementation details

---

## Additional Tools

### Ollama Setup

Located in `tools/ollama_setup/`

#### `test_connection.py`
**Purpose**: Test Ollama service connection  
**Type**: Utility script

**What it does**:
- Tests connection to Ollama
- Verifies model availability
- Checks service health
- Reports connection status

**Usage**:
```bash
python tools/ollama_setup/test_connection.py
```

---

### Cloudflared

Located in `tools/cloudflared/`

**Purpose**: Cloudflare Tunnel setup for remote access  
**Contents**: Configuration for exposing local services

---

## Data Directories

### `data/`
**Purpose**: Runtime data storage  
**Contents**: 
- Generated data
- Temporary files
- Runtime state

---

### `dj_personalities/`
**Purpose**: DJ character definitions  
**Structure**:
```
dj_personalities/
├── Julie (2102, Appalachia)/
│   ├── character_card.json
│   └── character_profile.md
├── Mr. New Vegas (2281, Mojave Wasteland)/
│   ├── character_card.json
│   └── character_profile.md
├── Travis Miles (Nervous) (2287, Commonwealth)/
│   ├── character_card.json
│   └── character_profile.md
└── Travis Miles (Confident) (2287, Commonwealth)/
    ├── character_card.json
    └── character_profile.md
```

**Files**:
- `character_card.json` - Structured personality data
- `character_profile.md` - Detailed character description

---

### `output/`
**Purpose**: Generated content output  
**Structure**:
```
output/
├── scripts/
│   ├── pending_review/  # Scripts awaiting review
│   ├── approved/        # Approved scripts
│   ├── rejected/        # Rejected scripts
│   └── metadata/        # Review logs
└── audio/               # Generated audio files (future)
```

---

### `lore/`
**Purpose**: Source lore data  
**Contents**: 
- `fallout_wiki_complete.xml` (140MB) - Complete Fallout Wiki dump

---

### `chroma_db/`
**Purpose**: ChromaDB vector database storage  
**Contents**: 
- Embeddings for ~356,601 wiki chunks
- Metadata and indices
- Created by wiki ingestion pipeline

---

## Configuration Files

### `pyproject.toml`
**Purpose**: Python package configuration  
**Type**: Package manifest

**What it does**:
- Defines package metadata
- Lists dependencies
- Build system configuration
- Development dependencies

**Key Dependencies**:
- chromadb
- jinja2
- fastapi
- pydantic
- pytest (dev)

---

### `.gitignore`
**Purpose**: Git ignore patterns  
**Contents**: 
- Python cache files
- ChromaDB directory
- Output files
- Archive directory
- Environment files

---

### Package Configuration

#### `esp32_ai_radio.egg-info/`
**Purpose**: Python package metadata  
**Type**: Auto-generated by pip install

---

## State Files

### `broadcast_state.json`
**Purpose**: Current broadcast state  
**Type**: JSON state file

**What it does**:
- Stores current broadcast session state
- Tracks generated content
- Maintains continuity between runs
- Used by broadcast engine

---

## Summary by Category

### User-Facing Scripts (7 files)
1. `broadcast.py` - Main CLI for broadcast generation
2. `generate_julie.py` - Quick Julie script generator
3. `generate_mr_new_vegas.py` - Quick Mr. New Vegas generator
4. `generate_travis.py` - Quick Travis generator
5. `generate_performance_test_scripts.py` - Performance test data
6. `reset_world_state.py` - Reset world state
7. `test_integration.py` - Integration test

### Batch Scripts (8 files)
1. `run_tests.bat` - Run all tests
2. `ingest_wiki.bat` - Wiki ingestion (update mode)
3. `ingest_wiki_fresh.bat` - Wiki ingestion (fresh)
4. `backup_database.bat` - Backup ChromaDB
5. `backup_quick.bat` - Quick backup
6. `restore_database.bat` - Restore ChromaDB
7. `analyze_log.bat` - Analyze logs
8. `scripts/README.md` - Batch scripts documentation

### Script Generator (75 files)
- Core: `broadcast_engine.py`, `generator.py`, `ollama_client.py`
- Validation: `llm_validator.py`, `consistency_validator.py`, `phase6_validation.py`
- Personality: `personality_loader.py`, `dj_knowledge_profiles.py`
- Broadcasting: `broadcast_scheduler.py`, `broadcast_freshness.py`, `session_memory.py`
- Weather: `weather_simulator.py`, `world_state.py`, `regional_climate.py`
- Templates: 5+ Jinja2 templates
- Tests: 10+ test files
- Utilities: Multiple helper scripts

### Wiki to ChromaDB (49 files)
- Main: `process_wiki.py`, `chromadb_ingest.py`
- Parsing: `wiki_parser.py`, `wiki_parser_v2.py`, `extractors.py`, `template_parser.py`
- Chunking: `chunker.py`, `chunker_v2.py`
- Enrichment: `metadata_enrichment.py`, `metadata_enrichment_v2.py`
- Configuration: `config.py`, `constants.py`, `models.py`
- Testing: `test_database.py`, `verify_database.py`, `benchmark.py`
- Analysis: `analyze_log.py`, `analyze_dump_stats.py`
- Debug: `debug_sections.py`, `debug_missing_sections.py`
- Phase 6: `phase6_metadata_audit.py`, `re_enrich_phase6.py`
- Tests: 87 test files in tests/ directory

### Script Review App (20+ files)
- Backend: `run_server.py`, `main.py`, `storage.py`, `auth.py`
- Frontend: HTML/CSS/JS PWA
- Utilities: `generate_icons.py`, `generate_test_scripts.py`, `send_email.py`
- Tests: Playwright tests, UI tests

### Firmware (2 files)
1. `firmware/main.cpp` - ESP32 C++ firmware
2. `platformio.ini` - Build configuration

### Configuration (5 files)
1. `tools/shared/project_config.py` - Centralized config
2. `pyproject.toml` - Package config
3. `.gitignore` - Git ignore
4. `platformio.ini` - Firmware build
5. Various `.env.template` files

### Documentation (20+ files)
- Root: `README.md`, `SCRIPTS_REFERENCE.md` (comprehensive reference)
- `docs/`: `ARCHITECTURE.md`, `DJ_KNOWLEDGE_SYSTEM.md`, `SYSTEM_SPECS.md`, etc.
- Tool-specific READMEs in each tool directory
- `archive/documentation/`: Historical phase completion reports, test results, and implementation plans

**Note**: Many phase completion reports and historical test results have been moved to `archive/documentation/` to reduce clutter. See `archive/INDEX.md` for details.

---

## Quick Reference by Task

### "I want to generate scripts"
→ Use `broadcast.py` or `generate_julie.py`/`generate_mr_new_vegas.py`/`generate_travis.py`

### "I need to set up the database"
→ Run `.\scripts\ingest_wiki.bat` (takes 2-3 hours)

### "I want to test if everything works"
→ Run `python test_integration.py` or `.\scripts\run_tests.bat`

### "I need to review scripts"
→ Start `tools/script-review-app/run_server.py` and open web UI

### "I want to understand the architecture"
→ Read `docs/ARCHITECTURE.md` and `README.md`

### "I need to debug wiki processing"
→ Use `tools/wiki_to_chromadb/debug_sections.py` and `analyze_log.py`

### "I want to reset everything"
→ Run `python reset_world_state.py`

### "I need to backup the database"
→ Run `.\scripts\backup_database.bat`

### "I'm looking for a specific tool"
→ Search this document by function or check the appropriate section

---

## Version History

**Current Version**: 1.0.0 (January 2026)

**Recent Changes**:
- Centralized configuration (`tools/shared/project_config.py`)
- Proper Python packaging with `pyproject.toml`
- Clean import paths (no sys.path hacks)
- Organized directory structure (firmware/, tools/, output/)
- Portable batch scripts
- Renamed `dj personality/` → `dj_personalities/`

---

## Notes for Refactoring

This reference document is designed to help understand the current state of the codebase before refactoring. Key observations:

1. **Duplication**: Multiple DJ generator scripts could be consolidated
2. **Testing**: Test coverage varies (40% for wiki pipeline, unknown for others)
3. **Documentation**: Well-documented but spread across many files
4. **Modularity**: Good separation of concerns (tools/, firmware/, output/)
5. **Type Safety**: V2 modules use Pydantic, V1 modules don't
6. **Configuration**: Centralized in `tools/shared/project_config.py`

**Recommended Next Steps**:
- Consolidate duplicate generator scripts
- Increase test coverage
- Complete migration to V2 modules
- Consider consolidating documentation
- Add integration tests for full pipeline

---

*End of Scripts Reference*
