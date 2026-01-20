# Tailscale Setup for Script Review App

Access your Script Review App from anywhere - phone, laptop, anywhere with internet - using Tailscale's secure private network.

## Why Tailscale Instead of Cloudflare?

| Feature | Tailscale | Cloudflare Tunnels |
|---------|-----------|-------------------|
| **URL Persistence** | Same URL every time | Random subdomain each start |
| **Security** | Private network only | Public internet exposure |
| **Speed** | Direct P2P when possible | Routed through Cloudflare |
| **Setup Complexity** | One-time setup | Works immediately |
| **Mobile Access** | Native app, works everywhere | Browser only |
| **Cost** | Free for personal use | Free |
| **Best For** | Personal, secure access | Quick temporary access |

**For personal use accessing from your phone anywhere: Tailscale is the clear winner.**

## Quick Start

### 1. Install Tailscale

**On your server/PC (where the app runs):**

#### Windows:
```powershell
# Download and install from
https://tailscale.com/download/windows
# Or use winget
winget install tailscale.tailscale
```

#### Linux:
```bash
curl -fsSL https://tailscale.com/install.sh | sh
```

#### macOS:
```bash
brew install tailscale
```

### 2. Sign Up & Connect

1. Start Tailscale and sign up (free personal account)
2. Authenticate with Google, Microsoft, or GitHub
3. Your machine is now on your private Tailscale network!

### 3. Enable Tailscale Serve (HTTPS)

This exposes your local app on your Tailscale network with automatic HTTPS:

```bash
# Start Tailscale serve on port 443 (HTTPS)
tailscale serve https / http://localhost:8000
```

This command:
- Maps `https://YOUR-MACHINE-NAME.TAILNET-NAME.ts.net/` → `http://localhost:8000`
- Provides automatic HTTPS certificates
- Only accessible on your private Tailscale network

### 4. Install Tailscale on Your Phone

1. Download Tailscale app:
   - **iOS**: https://apps.apple.com/app/tailscale/id1470499037
   - **Android**: https://play.google.com/store/apps/details?id=com.tailscale.ipn

2. Sign in with the same account
3. Connect to your Tailscale network

### 5. Access Your App

On your phone (or any device with Tailscale):
```
https://YOUR-MACHINE-NAME.TAILNET-NAME.ts.net
```

**To find your URL:**
```bash
tailscale status
# Look for your machine's hostname, it will be like:
# my-pc.tail12345.ts.net
```

## Automated Startup Scripts

### Windows: start_tailscale.bat

```batch
@echo off
echo Starting Script Review App with Tailscale...
echo.

REM Start the FastAPI server
start "Script Review API" cmd /k "cd %~dp0 && python -m backend.main"

REM Wait for server to start
echo Waiting for server to start...
timeout /t 5 /nobreak >nul

REM Configure Tailscale serve
echo Configuring Tailscale HTTPS...
tailscale serve https / http://localhost:8000

REM Get and display the URL
echo.
echo ========================================
echo Script Review App is now running!
echo ========================================
tailscale status | findstr /C:"."
echo.
echo Access from any device with Tailscale installed:
echo https://YOUR-MACHINE-NAME.TAILNET-NAME.ts.net
echo.
echo Press Ctrl+C to stop the server
pause
```

### Windows PowerShell: start_tailscale.ps1

```powershell
Write-Host "Starting Script Review App with Tailscale..." -ForegroundColor Cyan
Write-Host ""

# Start FastAPI server in background
$serverJob = Start-Job -ScriptBlock {
    Set-Location $using:PSScriptRoot
    python -m backend.main
}

Write-Host "Waiting for server to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Configure Tailscale serve
Write-Host "Configuring Tailscale HTTPS..." -ForegroundColor Yellow
tailscale serve https / http://localhost:8000

# Get Tailscale status
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Script Review App is running!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
tailscale status

Write-Host ""
Write-Host "Access from any device with Tailscale:" -ForegroundColor Cyan
Write-Host "https://YOUR-MACHINE-NAME.TAILNET-NAME.ts.net" -ForegroundColor Yellow
Write-Host ""
Write-Host "Press Ctrl+C to stop" -ForegroundColor Gray

# Wait for user to stop
try {
    while ($true) {
        Start-Sleep -Seconds 1
    }
} finally {
    Stop-Job $serverJob
    Remove-Job $serverJob
}
```

### Linux/macOS: start_tailscale.sh

```bash
#!/bin/bash

echo "Starting Script Review App with Tailscale..."
echo ""

# Start FastAPI server in background
cd "$(dirname "$0")"
python3 -m backend.main &
SERVER_PID=$!

# Wait for server to start
echo "Waiting for server to start..."
sleep 5

# Configure Tailscale serve
echo "Configuring Tailscale HTTPS..."
tailscale serve https / http://localhost:8000

# Display status
echo ""
echo "========================================"
echo "Script Review App is running!"
echo "========================================"
tailscale status

echo ""
echo "Access from any device with Tailscale:"
echo "https://$(hostname).$(tailscale status --json | jq -r '.Self.DNSName')"
echo ""
echo "Press Ctrl+C to stop"

# Cleanup on exit
trap "kill $SERVER_PID; tailscale serve reset; exit" INT TERM

# Wait for interrupt
wait
```

## Mobile Access Setup

### One-Time Setup on Phone

1. **Install Tailscale** (see links above)
2. **Sign in** with the same account as your PC
3. **Connect** - Turn on Tailscale
4. **Bookmark** your app URL in your phone's browser

### Daily Use

1. Open Tailscale app on phone
2. Ensure it's connected (green check mark)
3. Open your bookmarked URL
4. That's it! Works from anywhere with internet.

## Features with Tailscale

### ✅ Works From Anywhere
- Home WiFi
- Mobile data
- Coffee shop
- Different country
- As long as both devices have Tailscale connected

### ✅ Always the Same URL
- No more copying new URLs
- Bookmark it once
- Add to home screen (PWA)

### ✅ Automatic HTTPS
- Secure by default
- No certificate management
- Service workers work properly

### ✅ Private & Secure
- Not exposed to public internet
- Only accessible with Tailscale authentication
- End-to-end encrypted

## Troubleshooting

### Can't access the URL from phone

1. Check Tailscale is connected on both devices (green indicator)
2. Verify both devices show in `tailscale status` on PC
3. Ping your PC from phone: `ping YOUR-MACHINE-NAME.TAILNET-NAME.ts.net`
4. Check firewall isn't blocking port 8000

### "Certificate error" or "Not secure"

Make sure you're using `https://` not `http://`. Tailscale serve provides automatic HTTPS.

### Server not starting

```bash
# Check if port 8000 is already in use
netstat -ano | findstr :8000    # Windows
lsof -i :8000                   # Linux/macOS

# Kill any process using port 8000
taskkill /PID <pid> /F          # Windows
kill <pid>                      # Linux/macOS
```

### Tailscale serve not working

```bash
# Reset Tailscale serve configuration
tailscale serve reset

# Try again
tailscale serve https / http://localhost:8000

# Check Tailscale status
tailscale status
```

### Can't find your Tailscale URL

```bash
# On Windows/Linux/macOS
tailscale status

# Look for a line like:
# 100.x.x.x  my-machine  user@   -
#            my-machine.tail12345.ts.net

# Your URL is: https://my-machine.tail12345.ts.net
```

## Advanced: Custom Domain (Optional)

Tailscale supports MagicDNS with custom domains:

1. In Tailscale admin console: https://login.tailscale.com/admin/dns
2. Add a custom nameserver or use Tailscale's DNS
3. Set up a CNAME pointing to your Tailscale hostname

Example:
```
scripts.mydomain.com → my-pc.tail12345.ts.net
```

## Comparison to Cloudflare Tunnels

**When to use Tailscale:**
- ✅ Personal use
- ✅ Want consistent URL
- ✅ Need mobile access from anywhere
- ✅ Want maximum security
- ✅ Don't want to share URL with others

**When to use Cloudflare Tunnels:**
- Share with friends without Tailscale
- Temporary demo to someone
- Don't want to install software
- Need immediate access without setup

## Security Best Practices

1. **Keep Tailscale connected only when needed** on phone (saves battery)
2. **Use device authentication** in Tailscale admin console
3. **Enable key expiry** to automatically disconnect old devices
4. **Review connected devices** regularly in admin console
5. **Use API token authentication** in the app itself (already configured)

## Cost

**Tailscale Personal**: FREE
- Up to 100 devices
- Unlimited data
- All features included

Perfect for personal use accessing your script review app!

## Next Steps

1. Run `start_tailscale.bat` (Windows) or `./start_tailscale.sh` (Linux/macOS)
2. Install Tailscale on your phone
3. Bookmark the URL
4. Add to home screen for app-like experience
5. Review scripts from anywhere! 🎉
