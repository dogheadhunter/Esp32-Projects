# Simple Copy-Based Backup for ChromaDB
# Faster than compression, copies database to backup location

Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "  ChromaDB Database Backup (Copy Method)" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$sourceDir = "chroma_db"
$backupBase = "C:\esp32-backups\chromadb_copies"
$backupDir = Join-Path $backupBase "backup_$timestamp"

# Check source
if (-not (Test-Path $sourceDir)) {
    Write-Host "[ERROR] Source database not found: $sourceDir" -ForegroundColor Red
    pause
    exit 1
}

# Create backup directory
Write-Host "Creating backup directory..." -ForegroundColor Yellow
New-Item -ItemType Directory -Path $backupDir -Force | Out-Null

# Get source size
$sourceSize = (Get-ChildItem $sourceDir -Recurse -File | Measure-Object -Property Length -Sum).Sum / 1MB
Write-Host "Database size: $([math]::Round($sourceSize, 2)) MB" -ForegroundColor White
Write-Host "Backup location: $backupDir" -ForegroundColor White
Write-Host ""
Write-Host "Copying files (this will take 30-60 seconds)..." -ForegroundColor Yellow

# Copy with progress
try {
    Copy-Item -Path $sourceDir -Destination $backupDir -Recurse -Force
    
    if (Test-Path $backupDir\chroma_db) {
        $backupSize = (Get-ChildItem "$backupDir\chroma_db" -Recurse -File | Measure-Object -Property Length -Sum).Sum / 1MB
        Write-Host ""
        Write-Host "[SUCCESS] Backup completed!" -ForegroundColor Green
        Write-Host "Backed up: $([math]::Round($backupSize, 2)) MB" -ForegroundColor Green
        Write-Host "Location: $backupDir\chroma_db" -ForegroundColor Green
        
        # List existing backups
        Write-Host ""
        Write-Host "Existing backups:" -ForegroundColor Cyan
        Get-ChildItem $backupBase -Directory | Sort-Object LastWriteTime -Descending | ForEach-Object {
            $sizeMB = [math]::Round(((Get-ChildItem $_.FullName -Recurse -File | Measure-Object -Property Length -Sum).Sum / 1MB), 2)
            Write-Host "  $($_.Name) - $sizeMB MB - $($_.LastWriteTime)" -ForegroundColor White
        }
        
        # Cleanup suggestion
        $backupCount = (Get-ChildItem $backupBase -Directory).Count
        if ($backupCount -gt 3) {
            Write-Host ""
            Write-Host "[TIP] You have $backupCount backups (~$([math]::Round($backupCount * $backupSize, 0)) MB total)" -ForegroundColor Yellow
            Write-Host "Consider deleting old backups to save space." -ForegroundColor Yellow
        }
    }
} catch {
    Write-Host ""
    Write-Host "[ERROR] Backup failed: $($_.Exception.Message)" -ForegroundColor Red
    pause
    exit 1
}

Write-Host ""
Write-Host "=" * 80 -ForegroundColor Cyan
pause
