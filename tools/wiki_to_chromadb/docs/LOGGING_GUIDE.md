# Wiki Ingestion Logging Guide

## Overview

The wiki ingestion pipeline now includes comprehensive file logging that captures the entire processing history, making it easy to review what happened even after terminal output has scrolled away.

## Features

✅ **Automatic timestamped log files** - `ingestion_20260114_232620.log`  
✅ **Detailed progress tracking** - Every page, chunk, and batch logged  
✅ **Error tracking with stack traces** - Full details for debugging  
✅ **Summary statistics** - Pages processed, chunks created, timing info  
✅ **Configurable log levels** - DEBUG, INFO, WARNING, ERROR  

## Usage

### Basic Usage (Auto-generated filename)

```bash
python tools/wiki_to_chromadb/process_wiki.py lore/fallout_wiki_complete.xml
```

Creates: `ingestion_YYYYMMDD_HHMMSS.log` (e.g., `ingestion_20260114_232620.log`)

### Custom Log File

```bash
python tools/wiki_to_chromadb/process_wiki.py lore/fallout_wiki_complete.xml \
  --log-file my_custom_log.log
```

### Debug Level Logging

```bash
python tools/wiki_to_chromadb/process_wiki.py lore/fallout_wiki_complete.xml \
  --log-level DEBUG
```

Log levels:
- **DEBUG**: Very detailed, includes every operation
- **INFO**: Normal operation (default)
- **WARNING**: Only warnings and errors
- **ERROR**: Only errors

### Full Example

```bash
python tools/wiki_to_chromadb/process_wiki.py lore/fallout_wiki_complete.xml \
  --limit 1000 \
  --log-file wiki_ingestion_batch1.log \
  --log-level INFO
```

## Log File Contents

Each log entry includes:
- **Timestamp**: `2026-01-14 23:26:20`
- **Module**: `wiki_to_chromadb.chunker_v2`
- **Level**: `INFO`, `WARNING`, `ERROR`
- **Message**: Detailed operation description

### Example Log Output

```
2026-01-14 23:26:20 | wiki_to_chromadb.__main__ | INFO     | ============================================================
2026-01-14 23:26:20 | wiki_to_chromadb.__main__ | INFO     | Fallout Wiki Ingestion Process Started
2026-01-14 23:26:20 | wiki_to_chromadb.__main__ | INFO     | Log file: ingestion_20260114_232620.log
2026-01-14 23:26:20 | wiki_to_chromadb.__main__ | INFO     | Log level: INFO
2026-01-14 23:26:20 | wiki_to_chromadb.__main__ | INFO     | ============================================================
2026-01-14 23:26:20 | wiki_to_chromadb.__main__ | INFO     | XML Source: lore\fallout_wiki_complete.xml
2026-01-14 23:26:20 | wiki_to_chromadb.__main__ | INFO     | Starting page processing
2026-01-14 23:26:20 | wiki_to_chromadb.chunker_v2 | INFO     | Created 1 chunks from page '"Air Purifier" Project Delays'
2026-01-14 23:26:20 | wiki_to_chromadb.metadata_enrichment | INFO     | Enriching 1 chunks
2026-01-14 23:26:21 | wiki_to_chromadb.__main__ | INFO     | Ingesting batch of 100 chunks (total processed: 50 pages, 120 chunks)
2026-01-14 23:26:22 | wiki_to_chromadb.__main__ | INFO     | ============================================================
2026-01-14 23:26:22 | wiki_to_chromadb.__main__ | INFO     | Processing pipeline complete
2026-01-14 23:26:22 | wiki_to_chromadb.__main__ | INFO     | Pages processed: 3
2026-01-14 23:26:22 | wiki_to_chromadb.__main__ | INFO     | Chunks created: 7
2026-01-14 23:26:22 | wiki_to_chromadb.__main__ | INFO     | Processing rate: 84.1 pages/min
```

## What Gets Logged

### Startup Information
- XML source file path
- Output directory and collection name
- Configuration (chunk size, batch size, etc.)
- Log file location and level

### Per-Page Operations
- Page title and processing status
- Number of chunks created
- Metadata enrichment details
- Skip reasons (redirect, empty, etc.)

### Batch Operations
- Batch ingestion events
- Number of chunks per batch
- Running totals (pages, chunks)

### Summary Statistics
- Total pages processed/skipped/failed
- Total chunks created/ingested
- Elapsed time and processing rate
- ChromaDB collection stats

### Errors
- Detailed error messages
- Full stack traces (at ERROR level)
- Context about what was being processed

## Reviewing Logs

### View entire log file
```powershell
Get-Content ingestion_20260114_232620.log
```

### View last 100 lines
```powershell
Get-Content ingestion_20260114_232620.log | Select-Object -Last 100
```

### Search for errors
```powershell
Select-String -Path ingestion_*.log -Pattern "ERROR|FAIL"
```

### Get summary statistics
```powershell
Select-String -Path ingestion_20260114_232620.log -Pattern "Pages processed|Chunks created|Elapsed time"
```

### Find all log files
```powershell
Get-ChildItem -Filter "ingestion_*.log" | Sort-Object LastWriteTime -Descending
```

## Log File Location

Log files are created in the **current working directory** where you run the command.

If you run:
```bash
cd C:\esp32-project
python tools\wiki_to_chromadb\process_wiki.py lore\fallout_wiki_complete.xml
```

Log file will be: `C:\esp32-project\ingestion_YYYYMMDD_HHMMSS.log`

## Tips

1. **Keep logs organized**: Use meaningful names for production runs
   ```bash
   --log-file logs/wiki_full_ingestion_2026-01-14.log
   ```

2. **Use DEBUG for troubleshooting**: When something goes wrong
   ```bash
   --log-level DEBUG --limit 10
   ```

3. **Archive successful runs**: Keep logs for reference
   ```bash
   mv ingestion_*.log archive/
   ```

4. **Compare runs**: Diff logs to see what changed
   ```powershell
   Compare-Object (Get-Content log1.txt) (Get-Content log2.txt)
   ```

## Integration with Existing Tools

The log file complements the existing `processing_stats.json` file:
- **Log file**: Detailed step-by-step narrative
- **Stats JSON**: Structured data for programmatic analysis

Both are saved automatically and reference each other in their output.
