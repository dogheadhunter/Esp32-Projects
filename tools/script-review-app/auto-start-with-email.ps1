# Script Review App Auto-Starter with Email Notification
# This script starts both the FastAPI app and Cloudflare Quick Tunnel,
# then emails you the URL and API key

# Email configuration
$EmailTo = "dogheadhunter@proton.me"
$EmailFrom = "falloutscripts@gmail.com"  # Change this to your Gmail
$EmailSubject = "Fallout Script Review - New Access URL"

# API Key from .env file
$ApiKey = "FalloutScripts2026!"

# Start FastAPI app in background
Write-Host "Starting FastAPI app..." -ForegroundColor Green
$FastAPIPath = "C:\esp32-project\tools\script-review-app"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$FastAPIPath'; .\start.bat" -WindowStyle Minimized

# Wait for FastAPI to start
Start-Sleep -Seconds 5

# Start Cloudflared tunnel and capture output
Write-Host "Starting Cloudflare Tunnel..." -ForegroundColor Green
$CloudflaredPath = "C:\esp32-project\tools\cloudflared"
$TunnelLogPath = "$CloudflaredPath\tunnel-url.txt"

# Start cloudflared and redirect output to file
$CloudflaredProcess = Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$CloudflaredPath'; .\cloudflared.exe tunnel --url http://localhost:8000 2>&1 | Tee-Object -FilePath '$TunnelLogPath'" -WindowStyle Minimized -PassThru

# Wait for tunnel to initialize and get URL
Write-Host "Waiting for tunnel URL..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Read the log file and extract the URL
$TunnelUrl = ""
$MaxAttempts = 30
$Attempt = 0

while ($Attempt -lt $MaxAttempts -and $TunnelUrl -eq "") {
    if (Test-Path $TunnelLogPath) {
        $LogContent = Get-Content $TunnelLogPath -Raw
        if ($LogContent -match "https://[a-z0-9-]+\.trycloudflare\.com") {
            $TunnelUrl = $Matches[0]
            break
        }
    }
    Start-Sleep -Seconds 2
    $Attempt++
}

if ($TunnelUrl -eq "") {
    Write-Host "ERROR: Could not extract tunnel URL. Check the log file at: $TunnelLogPath" -ForegroundColor Red
    exit 1
}

Write-Host "`nTunnel URL: $TunnelUrl" -ForegroundColor Cyan
Write-Host "API Key: $ApiKey" -ForegroundColor Cyan

# Prepare email body
$EmailBody = @"
Your Fallout Script Review app is now accessible!

🌐 Access URL:
$TunnelUrl

🔑 API Key:
$ApiKey

📝 Instructions:
1. Open the URL above in your browser
2. Enter the API key when prompted
3. Review and approve/reject DJ scripts

⚠️ Note: This URL is temporary and will change if you restart your PC or the tunnel.

---
Auto-generated on $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
"@

# Try to send email using Gmail SMTP
# NOTE: You need to set up an App Password in your Gmail account
# Go to: https://myaccount.google.com/apppasswords
Write-Host "`nAttempting to send email..." -ForegroundColor Green

try {
    # Prompt for Gmail app password (one-time setup)
    $GmailPassword = Read-Host "Enter your Gmail App Password (or press Enter to skip email)" -AsSecureString
    
    if ($GmailPassword.Length -gt 0) {
        $Credential = New-Object System.Management.Automation.PSCredential($EmailFrom, $GmailPassword)
        
        Send-MailMessage `
            -From $EmailFrom `
            -To $EmailTo `
            -Subject $EmailSubject `
            -Body $EmailBody `
            -SmtpServer "smtp.gmail.com" `
            -Port 587 `
            -UseSsl `
            -Credential $Credential
        
        Write-Host "✅ Email sent successfully to $EmailTo" -ForegroundColor Green
    } else {
        Write-Host "⚠️ Email skipped. Your access details are displayed above." -ForegroundColor Yellow
        
        # Save to a text file instead
        $DetailsFile = "$env:USERPROFILE\Desktop\FalloutScriptReview_AccessInfo.txt"
        $EmailBody | Out-File -FilePath $DetailsFile -Encoding UTF8
        Write-Host "💾 Access details saved to: $DetailsFile" -ForegroundColor Cyan
    }
} catch {
    Write-Host "❌ Failed to send email: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "💾 Saving access details to desktop instead..." -ForegroundColor Yellow
    
    $DetailsFile = "$env:USERPROFILE\Desktop\FalloutScriptReview_AccessInfo.txt"
    $EmailBody | Out-File -FilePath $DetailsFile -Encoding UTF8
    Write-Host "💾 Access details saved to: $DetailsFile" -ForegroundColor Cyan
}

Write-Host "`n✨ Setup complete! Both services are running." -ForegroundColor Green
Write-Host "Press any key to exit this window (services will continue running)..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
