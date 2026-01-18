# Script Review App Auto-Starter with Automatic Email
# Starts FastAPI app and Cloudflare Tunnel, then emails you the URL

# Email configuration
$EmailTo = "dogheadhunter@proton.me"
$EmailFrom = "jtleyba2018@gmail.com"
$EmailSubject = "Fallout Script Review - New Access URL"
$AppPassword = "qpeqilqxbvqfjrke"
$ApiKey = "FalloutScripts2026!"

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

# Extract URL from log
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

if ($TunnelUrl -eq "") {
    Write-Host "ERROR: Could not extract tunnel URL" -ForegroundColor Red
    exit 1
}

Write-Host "`nTunnel URL: $TunnelUrl" -ForegroundColor Cyan
Write-Host "API Key: $ApiKey" -ForegroundColor Cyan

# Save to desktop (backup)
$DetailsFile = "$env:USERPROFILE\Desktop\FalloutScriptReview_URL.txt"
$TextContent = @"
FALLOUT DJ SCRIPT REVIEW APP

Access URL:
$TunnelUrl

API Key:
$ApiKey

Generated: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

Note: This URL changes each time you restart your PC.
"@

$TextContent | Out-File -FilePath $DetailsFile -Encoding UTF8
Write-Host "Saved to desktop: $DetailsFile" -ForegroundColor Green

# Prepare email
$EmailBody = @"
Your Fallout Script Review app is now accessible!

Access URL:
$TunnelUrl

API Key:
$ApiKey

Instructions:
1. Open the URL above in your browser
2. Enter the API key when prompted
3. Review and approve/reject DJ scripts

Note: This URL is temporary and will change if you restart your PC or the tunnel.

---
Auto-generated on $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
"@

# Send email using .NET SmtpClient with explicit TLS
Write-Host "`nSending email to $EmailTo..." -ForegroundColor Green

try {
    # Force TLS 1.2
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.SecurityProtocolType]::Tls12
    
    $SmtpClient = New-Object System.Net.Mail.SmtpClient("smtp.gmail.com", 587)
    $SmtpClient.EnableSsl = $true
    $SmtpClient.UseDefaultCredentials = $false
    $SmtpClient.Credentials = New-Object System.Net.NetworkCredential($EmailFrom, $AppPassword)
    $SmtpClient.DeliveryMethod = [System.Net.Mail.SmtpDeliveryMethod]::Network
    
    $MailMessage = New-Object System.Net.Mail.MailMessage
    $MailMessage.From = New-Object System.Net.Mail.MailAddress($EmailFrom)
    $MailMessage.To.Add($EmailTo)
    $MailMessage.Subject = $EmailSubject
    $MailMessage.Body = $EmailBody
    $MailMessage.IsBodyHtml = $false
    
    $SmtpClient.Send($MailMessage)
    
    Write-Host "Email sent successfully!" -ForegroundColor Green
    $SmtpClient.Dispose()
    $MailMessage.Dispose()
} catch {
    Write-Host "Failed to send email: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Access details saved to desktop instead." -ForegroundColor Yellow
}

Write-Host "`nSetup complete! Both services are running." -ForegroundColor Green
