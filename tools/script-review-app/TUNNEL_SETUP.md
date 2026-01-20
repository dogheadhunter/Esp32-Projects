# Cloudflare Tunnel Setup

This folder contains scripts to start the Script Review App with a temporary Cloudflare tunnel and email you the URL.

## Quick Start

### Option 1: Batch File (Double-Click)
1. Double-click `start_tunnel.bat`
2. The URL will be displayed in the console and copied to clipboard
3. (Optional) Configure email to receive the URL via email

### Option 2: PowerShell Script
```powershell
.\start_tunnel.ps1
```

## Email Notification Setup (Optional)

**The script works perfectly without email!** The URL is always displayed and copied to clipboard.

If you want email notifications, here are your options:

### Option 1: ProtonMail

**For Paid ProtonMail Plans (with SMTP access):**
```powershell
$env:EMAIL_SENDER = "your-email@proton.me"
$env:EMAIL_PASSWORD = "your-protonmail-password"
$env:SMTP_SERVER = "smtp.proton.me"
$env:SMTP_PORT = "587"
```

**For Free/Paid ProtonMail (using ProtonMail Bridge):**
1. Download and install [ProtonMail Bridge](https://proton.me/mail/bridge)
2. Log in to Bridge and get the SMTP password (different from your ProtonMail password)
3. Set environment variables:
```powershell
$env:EMAIL_SENDER = "your-email@proton.me"
$env:EMAIL_PASSWORD = "bridge-generated-password"  # From ProtonMail Bridge
$env:SMTP_SERVER = "127.0.0.1"
$env:SMTP_PORT = "1025"
```

### Option 2: Outlook/Hotmail (Easiest - No App Password)
No app passwords needed! Just use your regular password:

```powershell
$env:EMAIL_SENDER = "your-email@outlook.com"  # or @hotmail.com
$env:EMAIL_PASSWORD = "your-regular-password"
$env:SMTP_SERVER = "smtp-mail.outlook.com"
$env:SMTP_PORT = "587"
```

### Option 3: Gmail (Requires App Password)
1. Enable 2-Factor Authentication on your Google account
2. Generate an app-specific password:
   - Go to https://myaccount.google.com/apppasswords
   - Create a new app password
3. Set environment variables:
   ```powershell
   $env:EMAIL_SENDER = "your-email@gmail.com"
   $env:EMAIL_PASSWORD = "your-16-char-app-password"
   # Gmail is the default, no need to set SMTP_SERVER
   ```

### Option 3: Other Email Providers
```powershell
$env:EMAIL_SENDER = "your-email@example.com"
$env:EMAIL_PASSWORD = "your-password"
$env:SMTP_SERVER = "smtp.example.com"
$env:SMTP_PORT = "587"
```

### To Persist Email Settings (Optional):
To avoid setting variables each time, add them to your PowerShell profile:

```powershell
# Edit your profile
notepad $PROFILE

# Add these lines (example for ProtonMail with Bridge):
$env:EMAIL_SENDER = "dogheadhunter@proton.me"
$env:EMAIL_PASSWORD = "your-bridge-password"
$env:SMTP_SERVER = "127.0.0.1"
$env:SMTP_PORT = "1025"
```

## What the Script Does

1. ✅ Checks if cloudflared is installed
2. ✅ Starts the FastAPI backend server (main.py)
3. ✅ Creates a temporary Cloudflare tunnel
4. ✅ Extracts and displays the tunnel URL
5. ✅ Copies the URL to your clipboard
6. ✅ Sends an email with the URL (if configured)
7. ✅ Keeps running until you press Ctrl+C
8. ✅ Cleans up processes on exit

## Requirements

- ✅ cloudflared (already installed on your system)
- ✅ Python 3.8+ (already installed)
- ✅ FastAPI backend dependencies (already installed)
- ⚠️ Email credentials (optional, for email notifications)

## Troubleshooting

### "cloudflared not found"
Install cloudflared:
```powershell
winget install Cloudflare.cloudflared
```
Or download from: https://github.com/cloudflare/cloudflared/releases

### Backend fails to start
Check backend logs in the console output. Common issues:
- Port 8000 already in use
- Missing Python dependencies: `pip install -r requirements.txt`

### Email not sending
- Verify EMAIL_SENDER and EMAIL_PASSWORD are set correctly
- **For ProtonMail Free/Paid:** Install ProtonMail Bridge and use the Bridge password
- **For ProtonMail Paid:** Verify SMTP is enabled in your plan settings
- For Gmail, ensure you're using an app-specific password (not your regular password)
- Check firewall/antivirus isn't blocking SMTP connections
- Test SMTP settings: `Test-NetConnection -ComputerName smtp.proton.me -Port 587`

### Tunnel URL not detected
The script waits up to 30 seconds for the tunnel URL. If it fails:
- Check your internet connection
- Try running cloudflared manually: `cloudflared tunnel --url http://localhost:8000`
- Check the logs in `%TEMP%\cloudflared_output.txt` and `%TEMP%\cloudflared_error.txt`

## Manual Testing

Test email sending separately:
```powershell
python send_email.py "https://test-url.trycloudflare.com"
```

Test cloudflared separately:
```powershell
cloudflared tunnel --url http://localhost:8000
```

## Security Notes

- ⚠️ The tunnel URL is publicly accessible (anyone with the URL can access your app)
- ⚠️ Tunnel URLs are temporary and change each time you restart
- ⚠️ Don't share your tunnel URL publicly if your app contains sensitive data
- ✅ Email passwords are stored in environment variables (not in code)
- ✅ Use app-specific passwords (never your main email password)
