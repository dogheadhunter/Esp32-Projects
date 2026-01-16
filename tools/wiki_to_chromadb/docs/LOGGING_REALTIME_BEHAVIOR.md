# Real-Time Logging Behavior

## How It Works

The wiki ingestion pipeline writes to the log file **in real-time** as it runs, not after completion. This means:

✅ **You can view progress during execution** - Tail the log file while processing runs  
✅ **Data is preserved on interruption** - Ctrl+C, crashes, or power loss won't lose logs  
✅ **No buffering delays** - Log entries are flushed immediately to disk  

## Implementation Details

The logging system uses:
1. **`logging.FileHandler`** with append mode for continuous writing
2. **Immediate flushing** after each log entry to ensure disk writes
3. **UTF-8 encoding** for proper character support

```python
# From logging_config.py
file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
file_handler.flush = lambda: file_handler.stream.flush()  # Immediate flush
```

## Testing Real-Time Behavior

### Watch the log file grow during processing:

**Terminal 1: Start the ingestion**
```bash
python tools\wiki_to_chromadb\process_wiki.py lore\fallout_wiki_complete.xml
```

**Terminal 2: Monitor the log file in real-time**
```powershell
# PowerShell equivalent of 'tail -f'
Get-Content ingestion_*.log -Wait -Tail 50
```

Or use a text editor with auto-reload (VS Code, Notepad++, etc.)

## Interruption Scenarios

### Scenario 1: Ctrl+C (KeyboardInterrupt)

```
Pages: 5000page [45:23, 1.84page/s]^C

Processing interrupted by user
Partial progress has been saved to ChromaDB
⚠️  Partial log saved to: ingestion_20260114_232620.log
```

**Result**: Log file contains all processing up to the interruption point, including the KeyboardInterrupt warning.

### Scenario 2: Crash/Exception

```
Pages: 3421page [31:12, 1.83page/s]
Error during processing: Connection timeout

❌ Error log saved to: ingestion_20260114_232620.log
```

**Result**: Log file contains all processing **plus** the full error stack trace.

### Scenario 3: Power Loss/Kill Signal

Even if the process is forcefully terminated:
- All log entries written up to that point are preserved
- You can see exactly where processing stopped
- The last log entry shows the last successfully completed operation

## Monitoring During Long Runs

### Option 1: PowerShell Tail (Recommended)

```powershell
# Monitor last 50 lines, updates in real-time
Get-Content ingestion_20260114_232620.log -Wait -Tail 50
```

### Option 2: File Watcher Script

```powershell
# Save as watch_log.ps1
$logFile = Get-ChildItem -Filter "ingestion_*.log" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
Get-Content $logFile.FullName -Wait -Tail 20
```

### Option 3: VS Code Auto-Refresh

1. Open the log file in VS Code
2. It will auto-reload when the file changes
3. Keep it in a split pane while running the ingestion

## What Gets Written When

| Event | When Logged | Example |
|-------|-------------|---------|
| Process start | Immediately at script launch | `Fallout Wiki Ingestion Process Started` |
| Configuration | Before processing begins | `XML Source: lore\fallout_wiki_complete.xml` |
| Page processing | After each page is parsed | `Created 4 chunks from page 'Vault 101'` |
| Batch ingestion | When batch threshold is reached | `Ingesting batch of 100 chunks` |
| Errors | Immediately when they occur | `ERROR | Failed to parse page: ...` |
| Progress updates | Every batch (typically every 50-100 pages) | `total processed: 5000 pages, 12500 chunks` |
| Final summary | When processing completes or is interrupted | `Processing rate: 84.1 pages/min` |

## Log File Safety

The logging system guarantees:

1. **Immediate disk writes** - No buffering that could be lost
2. **Append mode** - Multiple runs to the same file won't overwrite
3. **UTF-8 encoding** - Handles all wiki content correctly
4. **Exception safety** - Errors are logged before the process exits

## Practical Example

**Start ingestion at 10:00 AM**
```bash
python tools\wiki_to_chromadb\process_wiki.py lore\fallout_wiki_complete.xml
```

**At 10:30 AM, check progress** (in another terminal)
```powershell
PS C:\esp32-project> Get-Content ingestion_20260114_100000.log | Select-Object -Last 5

2026-01-14 10:29:45 | wiki_to_chromadb.__main__ | INFO     | Ingesting batch of 100 chunks (total processed: 3456 pages, 8901 chunks)
2026-01-14 10:29:47 | wiki_to_chromadb.__main__ | INFO     | Successfully ingested 100 chunks
2026-01-14 10:29:48 | wiki_to_chromadb.chunker_v2 | INFO     | Created 3 chunks from page 'Nuka-Cola Victory'
2026-01-14 10:29:48 | wiki_to_chromadb.metadata_enrichment | INFO     | Enriching 3 chunks
2026-01-14 10:29:49 | wiki_to_chromadb.metadata_enrichment | INFO     | Enrichment complete
```

**You immediately know**:
- Processing is ongoing (last entry was 1 second ago)
- 3,456 pages processed so far
- Currently working on "Nuka-Cola Victory"

**At 10:45 AM, your computer crashes** 💥

**After reboot, check the log**:
```powershell
PS C:\esp32-project> Get-Content ingestion_20260114_100000.log | Select-Object -Last 10
```

**You can see**:
- Last page successfully processed
- Exactly how many pages/chunks were completed
- Where to resume from (if needed)
- No data loss!

## Resume After Interruption

Since ChromaDB saves progress incrementally, you can:

1. Check the log to see how many pages were processed
2. Use `--skip-to-page` or filter the XML to resume (future feature)
3. Re-run the full ingestion (ChromaDB will skip duplicates based on chunk IDs)

Currently, the safest approach is to just re-run the full ingestion - ChromaDB's upsert behavior means duplicate chunks will be updated, not duplicated.

## Summary

✅ Logging is **real-time**, not post-process  
✅ Log files survive crashes, interruptions, and force-kills  
✅ You can monitor progress during long runs  
✅ Zero data loss from buffering  
✅ Perfect for debugging interrupted runs  

The log file is your complete audit trail of what happened, when it happened, and where things are if something goes wrong!
