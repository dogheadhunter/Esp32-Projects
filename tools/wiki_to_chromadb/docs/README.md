# Documentation Index

Complete documentation for the Fallout Wiki → ChromaDB processing pipeline.

## Quick Links

- **[Main README](../README.md)** - Project overview and getting started
- **[Current Status](../STATUS.md)** - Development status and progress

---

## Documentation Sections

### 📘 Guides (Getting Started)

**Location**: [`docs/guides/`](guides/)

- **[QUICKSTART.md](guides/QUICKSTART.md)** - Quick start guide for using the pipeline
- **[SETUP.md](guides/SETUP.md)** - Installation and configuration instructions
- **[IMPLEMENTATION.md](guides/IMPLEMENTATION.md)** - Implementation details and architecture

### 🔄 Migration (Deprecation & Upgrade)

**Location**: [`docs/migration/`](migration/)

- **[MIGRATION_GUIDE.md](migration/MIGRATION_GUIDE.md)** - Step-by-step migration from old modules to refactored ones
- **[DEPRECATION_TIMELINE.md](migration/DEPRECATION_TIMELINE.md)** - Deprecation schedule and deadlines (March 2026)
- **[PHASE4_DEPRECATION.md](migration/PHASE4_DEPRECATION.md)** - Phase 4 deprecation implementation details

**Action Required**: Migrate from deprecated modules by **February 28, 2026**

### 🏗️ Implementation (Technical Details)

**Location**: [`docs/implementation/`](implementation/)

- **[IMPLEMENTATION_SUMMARY.md](implementation/IMPLEMENTATION_SUMMARY.md)** - Complete implementation summary
- **[STRUCTURAL_METADATA_COMPLETE.md](implementation/STRUCTURAL_METADATA_COMPLETE.md)** - Structural metadata preservation details
- **[QUICKSTART_STRUCTURAL_METADATA.md](implementation/QUICKSTART_STRUCTURAL_METADATA.md)** - Quick start for structural metadata features

### 🔧 Refactoring (Codebase Improvements)

**Location**: [`docs/refactoring/`](refactoring/)

- **[REFACTORING_GUIDE.md](refactoring/REFACTORING_GUIDE.md)** - Complete refactoring guide and architecture
- **[REFACTORING_SUMMARY.md](refactoring/REFACTORING_SUMMARY.md)** - Summary of refactoring efforts
- **[METADATA_ENRICHMENT_REFACTORING.md](refactoring/METADATA_ENRICHMENT_REFACTORING.md)** - Metadata enrichment module refactoring
- **[PROCESS_WIKI_REFACTORING.md](refactoring/PROCESS_WIKI_REFACTORING.md)** - Main pipeline refactoring details

### 📊 Phase Status (Development Progress)

**Location**: [`docs/phases/`](phases/)

- **[PHASE2_STATUS.md](phases/PHASE2_STATUS.md)** - Phase 2 completion status
- **[INTEGRATION_TESTS.md](phases/INTEGRATION_TESTS.md)** - Phase 3 integration testing (62 tests passing)
- **[TEST_RESULTS.md](phases/TEST_RESULTS.md)** - Test results and coverage
- **[FIXES_SUMMARY.md](phases/FIXES_SUMMARY.md)** - Bug fixes and improvements

---

## Development Phases

| Phase | Status | Documentation |
|-------|--------|---------------|
| **Phase 1** | ✅ Complete | Infrastructure modules (models, config, logging) |
| **Phase 2** | ✅ Complete | [PHASE2_STATUS.md](phases/PHASE2_STATUS.md) - Refactored enrichment & pipeline |
| **Phase 3** | ✅ Complete | [INTEGRATION_TESTS.md](phases/INTEGRATION_TESTS.md) - Integration testing |
| **Phase 4** | ✅ Complete | [PHASE4_DEPRECATION.md](migration/PHASE4_DEPRECATION.md) - Deprecation & migration |

---

## By Topic

### Getting Started
1. [QUICKSTART.md](guides/QUICKSTART.md) - Start here
2. [SETUP.md](guides/SETUP.md) - Installation
3. [Main README](../README.md) - Overview

### Understanding the Code
1. [REFACTORING_GUIDE.md](refactoring/REFACTORING_GUIDE.md) - Architecture overview
2. [IMPLEMENTATION.md](guides/IMPLEMENTATION.md) - Implementation details
3. [IMPLEMENTATION_SUMMARY.md](implementation/IMPLEMENTATION_SUMMARY.md) - Feature summary

### Upgrading from Old Code
1. [MIGRATION_GUIDE.md](migration/MIGRATION_GUIDE.md) - Migration steps
2. [DEPRECATION_TIMELINE.md](migration/DEPRECATION_TIMELINE.md) - Timeline and deadlines
3. [Main README](../README.md#deprecation-notice) - Deprecation notice

### Development Status
1. [Current Status](../STATUS.md) - Latest progress
2. [INTEGRATION_TESTS.md](phases/INTEGRATION_TESTS.md) - Test coverage
3. [TEST_RESULTS.md](phases/TEST_RESULTS.md) - Test results

---

## Recent Updates

- **January 14, 2026**: Phase 4 complete - Deprecation warnings added, migration guide published
- **January 2026**: Integration testing complete - 62/66 tests passing (94%)
- **January 2026**: Phase 2 complete - `process_wiki.py` and `metadata_enrichment.py` refactored
- **January 2026**: Structural metadata preservation implemented

---

## Contributing

When adding new documentation:
- Place guides in `docs/guides/`
- Place implementation details in `docs/implementation/`
- Place refactoring notes in `docs/refactoring/`
- Place phase updates in `docs/phases/`
- Update this index with links
