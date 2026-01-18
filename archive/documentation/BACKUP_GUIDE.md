# ChromaDB Database Backup Guide

## Overview

The Fallout Wiki ChromaDB database contains **291,343 chunks** ingested from **77,212 pages** and took **17.5 hours** to create. Regular backups are essential to protect this valuable data.

**Database Size**: ~2GB  
**Backup Location**: `C:\esp32-backups\chromadb\`  
**Compression**: Zip format with optimal compression

## Quick Start

### Create a Backup (RECOMMENDED - Fast Method)

1. Double-click `backup_quick.bat`
2. Wait ~30 seconds for the copy to complete
3. Backup will be saved to: `C:\esp32-backups\chromadb_backup_YYYYMMDD_HHMMSS\`
4. No compression needed - direct file copy is fast and reliable

**OR use compression (slower but saves space):**

1. Double-click `backup_database.bat`
2. Wait for compression to complete (~2-3 minutes)
3. Backup will be saved with timestamp: `fallout_wiki_backup_YYYYMMDD_HHMMSS.zip`

### Restore from Backup

**From Quick Backup (folder copy):**
1. Delete the current `chroma_db` folder
2. Copy `C:\esp32-backups\chromadb_backup_YYYYMMDD_HHMMSS\` to `chroma_db`

**From Compressed Backup:**
1. Double-click `restore_database.bat`
2. Select the backup file from the list
3. Confirm the restoration (this will replace the current database)

## Backup Strategy Recommendations

### Frequency
- **After major changes**: Always backup before running `ingest_wiki_fresh.bat`
- **Weekly**: If actively developing/testing
- **Monthly**: For stable production use

### Retention
- Keep at least **3 most recent backups**
- Keep one backup per month for long-term retention
- Delete older backups when space is limited (each backup is ~500-800MB compressed)

### Additional Protection
For maximum safety, consider copying backups to:
- External USB drive
- Cloud storage (Google Drive, Dropbox, OneDrive)
- Network attached storage (NAS)
- Different computer on your network

## Manual Backup (Alternative Methods)

### Method 1: Quick Copy (Fastest - 30 seconds)
```powershell
$timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
robocopy chroma_db "C:\esp32-backups\chromadb_backup_$timestamp" /E /MT:8
```

### Method 2: Compressed Archive (Slower - saves space)
```powershell
# Compress the database
Compress-Archive -Path "chroma_db" -DestinationPath "backup_$(Get-Date -Format 'yyyyMMdd_HHmmss').zip"
s)

### From Folder Copy
```powershell
# Delete current database
Remove-Item "chroma_db" -Recurse -Force

# Copy backup
Copy-Item "C:\esp32-backups\chromadb_backup_YYYYMMDD_HHMMSS" -Destination "chroma_db" -Recurse
```

### From Compressed Archive# Copy to external location
Copy-Item "backup_*.zip" -Destination "D:\Backups\" -Force
```

## Manual Restore (Alternative Method)

```powershell
# Delete current database
Remove-Item "chroma_db" -Recurse -Force

# Extract backup
Expand-Archive -Path "backup_YYYYMMDD_HHMMSS.zip" -DestinationPath "."
```

## Verifying Backup Integrity

After creating a backup, you can verify it worked:

```batch
cd tools\wiki_to_chromadb
python test_ingestion_quality.py
```

This runs 7 comprehensive tests to ensure the database is functioning correctly.

## Troubleshooting

### Backup Takes Too Long
- The database is 2GB, compression takes 1-2 minutes (normal)
- Close other programs to free up CPU/disk resources
- Consider using faster compression: Edit `backup_database.bat` and change `Optimal` to `Fastest`

### Not Enough Disk Space
- Each compressed backup is ~500-800MB
- Check `C:\esp32-backups\chromadb\` and delete old backups
- Change `BACKUP_DIR` in the script to a different drive

### Restore Failed
- Ensure the backup file is not corrupted (try extracting manually)
- Check if chroma_db folder is locked by another process
- Close any Python scripts or ChromaDB connections before restoring

## Backup File Naming

Format: `fallout_wiki_backup_YYYYMMDD_HHMMSS.zip`

Example: `fallout_wiki_backup_20260116_143052.zip`
- Created on: January 16, 2026
- Time: 2:30:52 PM

## Integration with Development Workflow

### Before Major Changes
```batch
REM 1. Create backup
backup_database.bat

REM 2. Make changes
ingest_wiki_fresh.bat

REM 3. Test changes
cd tools\wiki_to_chromadb
python test_ingestion_quality.py

REM 4. If something went wrong, restore
restore_database.bat
```

## Automated Scheduled Backups (Optional)

To schedule automatic backups using Windows Task Scheduler:

1. Open Task Scheduler
2. Create Basic Task
3.Method | Time | Size | Backups | Total Space |
|--------|------|------|---------|-------------|
| Quick Copy | 30 sec | ~2000 MB | 3 | ~6 GB |
| Compressed | 2-3 min | ~600 MB | 3 | ~1.8 GB |
| Quick Copy | 30 sec | ~2000 MB | 5 | ~10 GB |
| Compressed | 2-3 min | ~600 MB | 5 | ~3 GB |

**Recommendation**: Use Quick Copy for frequent backups, Compressed for long-term storage.

The script will create timestamped backups automatically.

## Storage Estimates

| Backups | Compressed Size | Uncompressed Size |
|---------|----------------|-------------------|
| 1 backup | ~600 MB | ~2000 MB |
| 3 backups | ~1.8 GB | ~6000 MB |
| 5 backups | ~3.0 GB | ~10000 MB |

## Emergency Recovery

If both your database AND backups are lost, you can regenerate:

1. Run `ingest_wiki.bat` (takes ~17.5 hours)
2. The pipeline will recreate the entire database from the XML source
3. All 291,343 chunks will be re-ingested with metadata

**Source file**: `lore/fallout_wiki_complete.xml` (always keep this safe!)
