# Simple Auto-Starter - Saves URL to Desktop
# This version saves the URL and API key to a text file on your desktop

$ApiKey = "555"

# Start FastAPI app
Write-Host "Starting FastAPI app..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd 'C:\esp32-project\tools\script-review-app'; .\start.bat" -WindowStyle Minimized

Start-Sleep -Seconds 5

# Start Cloudflared tunnel
Write-Host "Starting Cloudflare Tunnel..." -ForegroundColor Green
$TunnelLogPath = "C:\esp32-project\tools\cloudflared\tunnel-url.txt"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd 'C:\esp32-project\tools\cloudflared'; .\cloudflared.exe tunnel --url http://localhost:8000 2>&1 | Tee-Object -FilePath '$TunnelLogPath'" -WindowStyle Minimized

# Wait for tunnel URL
Write-Host "Waiting for tunnel URL..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Extract URL
$TunnelUrl = ""
$MaxAttempts = 30
for ($i = 0; $i -lt $MaxAttempts; $i++) {
    if (Test-Path $TunnelLogPath) {
        $LogContent = Get-Content $TunnelLogPath -Raw
        if ($LogContent -match "https://[a-z0-9-]+\.trycloudflare\.com") {
            $TunnelUrl = $Matches[0]
            break
        }
    }
    Start-Sleep -Seconds 2
}

# Save to desktop
$DetailsFile = "$env:USERPROFILE\Desktop\FalloutScriptReview_URL.txt"
$Content = @"
FALLOUT DJ SCRIPT REVIEW APP

Access URL:
$TunnelUrl

API Key:
$ApiKey

Generated: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

Note: This URL changes each time you restart your PC.
"@

$Content | Out-File -FilePath $DetailsFile -Encoding UTF8

Write-Host "`nServices started!" -ForegroundColor Green
Write-Host "Access details saved to: $DetailsFile" -ForegroundColor Cyan
Write-Host "`nURL: $TunnelUrl" -ForegroundColor Yellow
Write-Host "Key: $ApiKey" -ForegroundColor Yellow
