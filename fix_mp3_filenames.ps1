param (
    [Parameter(Mandatory=$true)]
    [Alias("TargetDirectory")]
    [string]$Path
)

# Check if directory exists
if (-not (Test-Path -Path $Path)) {
    Write-Host "Error: Directory '$Path' not found." -ForegroundColor Red
    exit
}

Write-Host "Scanning '$Path' for MP3 files..." -ForegroundColor Cyan

$files = Get-ChildItem -Path $Path -Filter "*.mp3" -Recurse
$count = 0

foreach ($file in $files) {
    $originalName = $file.Name
    $newName = $originalName

    # 1. Replace smart quotes and other common issues using unicode escapes for safety
    # Left/Right Single Quotes, Grave Accent, Acute Accent -> '
    $newName = $newName -replace "[\u2018\u2019\u0060\u00B4]", "'"
    # Left/Right Double Quotes -> "
    $newName = $newName -replace "[\u201C\u201D]", '"'
    # En-dash, Em-dash -> -
    $newName = $newName -replace "[\u2013\u2014]", "-"

    # 2. Remove accents (Normalization)
    $normalized = $newName.Normalize([System.Text.NormalizationForm]::FormD)
    $sb = [System.Text.StringBuilder]::new()
    foreach ($c in $normalized.ToCharArray()) {
        $cat = [System.Globalization.CharUnicodeInfo]::GetUnicodeCategory($c)
        if ($cat -ne [System.Globalization.UnicodeCategory]::NonSpacingMark) {
            [void]$sb.Append($c)
        }
    }
    $newName = $sb.ToString().Normalize([System.Text.NormalizationForm]::FormC)

    # 3. Strip non-ASCII characters (keep only basic safe chars)
    # Allowed: A-Z, a-z, 0-9, space, dot, hyphen, underscore, parenthesis, single quote
    $newName = $newName -replace '[^a-zA-Z0-9 ._()''-]', ''
    
    # 4. Trim whitespace
    $newName = $newName.Trim()

    # Rename if changed
    if ($originalName -cne $newName) {
        try {
            $newPath = Join-Path -Path $file.DirectoryName -ChildPath $newName
            
            if (Test-Path -Path $newPath) {
                Write-Host "Skipping: '$originalName' -> '$newName' (Target exists)" -ForegroundColor Yellow
            }
            else {
                Rename-Item -LiteralPath $file.FullName -NewName $newName -ErrorAction Stop
                Write-Host "Renamed: '$originalName' -> '$newName'" -ForegroundColor Green
                $count++
            }
        }
        catch {
            Write-Host "Failed to rename '$originalName': $_" -ForegroundColor Red
        }
    }
}

Write-Host "Done! Renamed $count files." -ForegroundColor Cyan
Write-Host "Note: If you still see INVALID_FRAMEHEADER errors, run 'mp3val' on the files." -ForegroundColor Yellow
