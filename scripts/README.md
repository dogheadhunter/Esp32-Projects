# Scripts Directory

Utility batch scripts for ESP32 AI Radio project operations.

## Available Scripts

### Database Management
- **backup_database.bat** - Backup ChromaDB to compressed archive
- **backup_quick.bat** - Quick backup without compression
- **restore_database.bat** - Restore ChromaDB from backup archive

### Wiki Processing
- **ingest_wiki.bat** - Ingest Fallout Wiki XML into ChromaDB (update mode)
- **ingest_wiki_fresh.bat** - Fresh ingestion (clears existing data)

### Testing
- **run_tests.bat** - Run all test suites (wiki_to_chromadb + script-generator)

### Utilities
- **analyze_log.bat** - Analyze ingestion logs for errors

## Usage

All scripts can be executed from any location:

```batch
# From project root
.\scripts\run_tests.bat

# From scripts directory
cd scripts
.\run_tests.bat

# From any other location
C:\esp32-project\scripts\run_tests.bat
```

Scripts automatically navigate to the project root before executing commands, ensuring paths resolve correctly.

## Path Resolution

All scripts use `cd /d "%~dp0.."` to navigate to the project root, making them portable and location-independent.
