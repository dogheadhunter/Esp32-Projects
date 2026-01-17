# ChromaDB Database Backup Script
# Creates timestamped compressed backup of the Fallout Wiki database

Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "  ChromaDB Database Backup Utility" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""

# Configuration
$backupDir = "C:\esp32-backups\chromadb"
$sourceDir = "chroma_db"
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupFile = Join-Path $backupDir "fallout_wiki_backup_$timestamp.zip"

# Create backup directory if it doesn't exist
if (-not (Test-Path $backupDir)) {
    Write-Host "Creating backup directory: $backupDir" -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
}

# Check if source exists
if (-not (Test-Path $sourceDir)) {
    Write-Host "[ERROR] Source database not found: $sourceDir" -ForegroundColor Red
    Write-Host "Please run this script from the esp32-project directory" -ForegroundColor Red
    pause
    exit 1
}

# Get source size
$sourceSize = (Get-ChildItem $sourceDir -Recurse -File | Measure-Object -Property Length -Sum).Sum / 1MB
Write-Host "Database size: $([math]::Round($sourceSize, 2)) MB" -ForegroundColor White
Write-Host "Backup location: $backupFile" -ForegroundColor White
Write-Host ""
Write-Host "Starting backup (this may take 1-2 minutes)..." -ForegroundColor Yellow
Write-Host ""

# Create backup
try {
    Compress-Archive -Path $sourceDir -DestinationPath $backupFile -CompressionLevel Optimal -Force
    
    # Check if successful
    if (Test-Path $backupFile) {
        $backupSize = (Get-Item $backupFile).Length / 1MB
        Write-Host ""
        Write-Host "[SUCCESS] Backup completed successfully!" -ForegroundColor Green
        Write-Host "Backup saved to: $backupFile" -ForegroundColor Green
        Write-Host "Compressed size: $([math]::Round($backupSize, 2)) MB" -ForegroundColor Green
        Write-Host "Compression ratio: $([math]::Round(($backupSize/$sourceSize)*100, 1))%" -ForegroundColor Green
        
        # List existing backups
        Write-Host ""
        Write-Host "Existing backups in $backupDir :" -ForegroundColor Cyan
        Get-ChildItem $backupDir -Filter "*.zip" | Sort-Object LastWriteTime -Descending | ForEach-Object {
            $sizeMB = [math]::Round($_.Length / 1MB, 2)
            Write-Host "  $($_.Name) - $sizeMB MB - $($_.LastWriteTime)" -ForegroundColor White
        }
        
        # Cleanup suggestion
        $backupCount = (Get-ChildItem $backupDir -Filter "*.zip").Count
        if ($backupCount -gt 5) {
            Write-Host ""
            Write-Host "[TIP] You have $backupCount backups. Consider deleting old ones to save space." -ForegroundColor Yellow
        }
    }
} catch {
    Write-Host ""
    Write-Host "[ERROR] Backup failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host $_.Exception -ForegroundColor Red
    pause
    exit 1
}

Write-Host ""
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""
pause
