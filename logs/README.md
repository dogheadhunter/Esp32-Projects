# Logs Directory

Centralized logging for all test runs, script executions, and ingestion operations.

## Structure

```
logs/
├── archive/                    # Organized historical logs
│   └── YYYY/                  # Year
│       └── MM/                # Month
│           └── DD/            # Day
│               ├── session_*.log      # Full output
│               ├── session_*.json     # Metadata
│               └── session_*.llm.md   # LLM summary
├── ingestion/                 # Wiki ingestion logs
├── Copilot_Chat_Logs/         # Copilot session logs
├── error_report.txt           # Error summaries
└── *.log                      # Current session logs (auto-organized nightly)
```

## Log Formats

### Test Session Logs (3 formats)

All test runs create 3 log files with the same timestamp:

1. **`.log`** - Human-readable complete output
   - Full pytest output with all test names, results, tracebacks
   - Coverage tables and warnings
   - Typical size: 50-300 KB
   - Best for: Debugging failures, reviewing test details

2. **`.json`** - Structured metadata
   - Session start/end times, duration
   - Command executed, exit code
   - Event log with timestamps
   - Typical size: <1 KB
   - Best for: Programmatic analysis, CI/CD integration

3. **`.llm.md`** - LLM-optimized markdown
   - Concise summary with key events
   - Event timeline and statistics
   - 99%+ smaller than .log while preserving context
   - Typical size: <1 KB
   - Best for: AI assistant context, quick review

### Example

```
session_20260120_122847_all.log      # 261 KB - Full output
session_20260120_122847_all.json     # 0.77 KB - Metadata
session_20260120_122847_all.llm.md   # 0.71 KB - Summary
```

## Log Management

### Automatic Organization

New logs from `run_tests.py` are automatically saved to date-organized folders:
```
logs/archive/2026/01/20/session_*.{log,json,llm.md}
```

### Manual Organization

Organize loose logs in the root:
```bash
python tools/utilities/log_manager.py
```

### View Inventory

Check current log storage:
```bash
python tools/utilities/log_manager.py --inventory-only
```

Output:
```json
{
  "total_files": 27,
  "total_size_mb": 0.37,
  "by_type": {
    ".json": 9,
    ".llm.md": 9,
    ".log": 9
  },
  "by_date": {
    "2026-01-20": 27
  }
}
```

### Dry Run (Preview Changes)

See what would be done without making changes:
```bash
python tools/utilities/log_manager.py --dry-run
```

### Maintenance Operations

The log manager performs 3 operations:

1. **Organize** - Move logs to `archive/YYYY/MM/DD/` folders
2. **Compress** - Gzip `.log` files older than 7 days (saves ~80% space)
3. **Cleanup** - Delete logs older than 30 days

### Custom Retention

```bash
# Keep logs for 90 days, compress after 14 days
python tools/utilities/log_manager.py --retention-days 90 --compress-after 14
```

## Log Rotation Schedule

**Recommended cron/scheduled task:**

```bash
# Daily at 2 AM - organize and compress logs
0 2 * * * cd /path/to/esp32-project && python tools/utilities/log_manager.py
```

**Windows Task Scheduler:**

```powershell
$action = New-ScheduledTaskAction -Execute "python" -Argument "tools\utilities\log_manager.py" -WorkingDirectory "C:\esp32-project"
$trigger = New-ScheduledTaskTrigger -Daily -At 2am
Register-ScheduledTask -Action $action -Trigger $trigger -TaskName "ESP32-LogMaintenance"
```

## Finding Logs

### Recent Test Runs
```bash
# View today's logs
ls logs/archive/$(date +%Y/%m/%d)/

# Last 5 test runs
ls -lt logs/archive/*/*/*/*.log | head -5
```

### Search by Type
```bash
# All "all" test runs
find logs/archive -name "session_*_all.log"

# All logging tests
find logs/archive -name "session_*_logging.*"
```

### Extract Data from JSON
```bash
# Get all test durations
jq '.duration_seconds' logs/archive/*/*/*/*.json

# Failed tests only
jq 'select(.events[].data.status == "failed")' logs/archive/*/*/*/*.json
```

## Disk Space Management

### Current Usage
```bash
du -sh logs/
du -sh logs/archive/
```

### Space Savings

Compression reduces `.log` file sizes by ~80%:
- Before: 261 KB `.log` file
- After: ~52 KB `.log.gz` file
- `.json` and `.llm.md` files stay uncompressed (already small)

### Emergency Cleanup

If logs are using too much space:

```bash
# Delete all logs older than 14 days
python tools/utilities/log_manager.py --retention-days 14

# Compress immediately instead of waiting 7 days
python tools/utilities/log_manager.py --compress-after 0
```

## Troubleshooting

### "Logs not being organized"

Check that filenames match the pattern: `session_YYYYMMDD_HHMMSS_type.ext`

### "Compression failing"

Ensure you have gzip support:
```python
import gzip  # Should not raise ImportError
```

### "Can't find recent logs"

Check both locations:
```bash
ls logs/session_*           # Current (not yet organized)
ls logs/archive/$(date +%Y/%m/%d)/  # Today's organized logs
```

## Best Practices

1. **Run log manager weekly** - Keeps logs organized and compressed
2. **Check inventory monthly** - Monitor disk usage trends
3. **Adjust retention** - Based on your disk space and compliance needs
4. **Keep .json small** - Only high-level events, not full output
5. **Archive before major changes** - Copy critical logs before cleanup

## Integration

### CI/CD

Upload structured logs as artifacts:
```yaml
- name: Run tests
  run: python run_tests.py all

- uses: actions/upload-artifact@v3
  with:
    name: test-logs
    path: logs/archive/**/*.json
```

### Monitoring

Parse JSON logs for metrics:
```python
import json
from pathlib import Path

for log in Path("logs/archive").rglob("*.json"):
    data = json.loads(log.read_text())
    if data.get("duration_seconds", 0) > 300:
        print(f"Slow test run: {log.name} took {data['duration_seconds']}s")
```
