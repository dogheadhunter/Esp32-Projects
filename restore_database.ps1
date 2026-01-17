# ChromaDB Database Restore Script
# Restores database from a backup zip file

Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "  ChromaDB Database Restore Utility" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""

# Configuration
$backupDir = "C:\esp32-backups\chromadb"
$targetDir = "chroma_db"

# Check if backup directory exists
if (-not (Test-Path $backupDir)) {
    Write-Host "[ERROR] Backup directory not found: $backupDir" -ForegroundColor Red
    Write-Host "Please run backup_database.ps1 first to create a backup." -ForegroundColor Red
    pause
    exit 1
}

# List available backups
$backups = Get-ChildItem $backupDir -Filter "*.zip" | Sort-Object LastWriteTime -Descending

if ($backups.Count -eq 0) {
    Write-Host "[ERROR] No backup files found in $backupDir" -ForegroundColor Red
    pause
    exit 1
}

Write-Host "Available backups:" -ForegroundColor Cyan
Write-Host ""
for ($i = 0; $i -lt $backups.Count; $i++) {
    $sizeMB = [math]::Round($backups[$i].Length / 1MB, 2)
    Write-Host "  [$($i+1)] $($backups[$i].Name)" -ForegroundColor White
    Write-Host "      Size: $sizeMB MB | Date: $($backups[$i].LastWriteTime)" -ForegroundColor Gray
}

Write-Host ""
Write-Host "Enter the number of the backup to restore (or 'q' to quit):" -ForegroundColor Yellow
$selection = Read-Host "Selection"

if ($selection -eq 'q') {
    Write-Host "Restore cancelled." -ForegroundColor Yellow
    exit 0
}

$index = [int]$selection - 1
if ($index -lt 0 -or $index -ge $backups.Count) {
    Write-Host "[ERROR] Invalid selection" -ForegroundColor Red
    pause
    exit 1
}

$selectedBackup = $backups[$index]

Write-Host ""
Write-Host "WARNING: This will delete the current chroma_db folder and replace it" -ForegroundColor Red
Write-Host "with the backup from: $($selectedBackup.Name)" -ForegroundColor Red
Write-Host ""
$confirm = Read-Host "Are you sure you want to continue? (type 'yes' to confirm)"

if ($confirm -ne 'yes') {
    Write-Host "Restore cancelled." -ForegroundColor Yellow
    exit 0
}

Write-Host ""
Write-Host "Deleting current database..." -ForegroundColor Yellow

if (Test-Path $targetDir) {
    try {
        Remove-Item $targetDir -Recurse -Force
        Write-Host "  [OK] Current database deleted" -ForegroundColor Green
    } catch {
        Write-Host "[ERROR] Failed to delete current database: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host "Make sure no programs are using the database." -ForegroundColor Red
        pause
        exit 1
    }
}

Write-Host "Extracting backup..." -ForegroundColor Yellow

try {
    Expand-Archive -Path $selectedBackup.FullName -DestinationPath "." -Force
    
    if (Test-Path $targetDir) {
        Write-Host ""
        Write-Host "[SUCCESS] Database restored successfully!" -ForegroundColor Green
        Write-Host "Restored from: $($selectedBackup.Name)" -ForegroundColor Green
        
        # Verify
        $chunkCount = (Get-ChildItem $targetDir -Recurse -File).Count
        Write-Host "Files restored: $chunkCount" -ForegroundColor Green
    } else {
        Write-Host "[ERROR] Restore completed but database folder not found" -ForegroundColor Red
    }
} catch {
    Write-Host ""
    Write-Host "[ERROR] Restore failed: $($_.Exception.Message)" -ForegroundColor Red
    pause
    exit 1
}

Write-Host ""
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""
pause
