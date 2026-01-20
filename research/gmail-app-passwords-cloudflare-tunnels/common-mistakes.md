# Common Mistakes & Pitfalls

**Topic**: Gmail App Passwords + PowerShell Profile + Cloudflare Tunnels

## Critical Mistakes to Avoid

### 1. ❌ Storing Credentials in Version Control

**The Mistake**:
```powershell
# PowerShell profile committed to git
$env:EMAIL_SENDER = "jtleyba2018@gmail.com"
$env:EMAIL_PASSWORD = "haqshjhcoazowlth"  # NOW IN GIT HISTORY FOREVER
```

**Why It's Bad**:
- Passwords remain in git history even after deletion
- Public repos expose credentials to the world
- Private repos still show to all contributors
- GitHub/GitLab scan for exposed secrets

**Real-World Impact**:
- Accounts get compromised within hours of pushing
- Automated bots scan for credentials
- Your email becomes a spam relay
- Account could be locked by Google

**How to Fix**:
```powershell
# Add to .gitignore
echo "*_profile.ps1" >> .gitignore
echo ".secrets/" >> .gitignore

# Remove from git history (if already committed)
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch Microsoft.PowerShell_profile.ps1" \
  --prune-empty --tag-name-filter cat -- --all

# Force push (destroys history)
git push origin --force --all
```

**Prevention**:
- Never store credentials in files tracked by git
- Use `.gitignore` from day one
- Use pre-commit hooks to detect secrets
- Use tools like `git-secrets` or `gitleaks`

---

### 2. ❌ Leaving Tunnels Running Indefinitely

**The Mistake**:
```powershell
# Start tunnel script
.\start_tunnel.bat
# User forgets about it, leaves it running for days/weeks
```

**Why It's Bad**:
- Public URL active 24/7
- Increases attack window
- Wastes resources
- URL could be discovered by scanners

**Real-World Scenario**:
1. You start tunnel Friday afternoon
2. Email yourself the URL
3. Weekend happens
4. Monday morning: Automated scanner found your URL
5. Your backend has been probed for vulnerabilities
6. If any SQL injection bugs exist, they're exploited

**How to Fix**:
```powershell
# Add auto-shutdown after timeout
$timeout = New-TimeSpan -Minutes 30

$timer = [System.Diagnostics.Stopwatch]::StartNew()
while (-not $tunnelProcess.HasExited) {
    if ($timer.Elapsed -gt $timeout) {
        Write-Host "⏰ Tunnel timeout reached. Shutting down..." -ForegroundColor Yellow
        break
    }
    Start-Sleep -Seconds 1
}
```

**Best Practice**:
- Set maximum tunnel lifetime (30 min, 1 hour max)
- Use scheduled tasks to auto-kill processes
- Add prominent timer display in console
- Send shutdown warning email

---

### 3. ❌ No Backend Authentication

**The Mistake**:
```python
# FastAPI backend with no auth
@app.get("/api/scripts")
async def get_scripts():
    return database.get_all_scripts()  # Anyone can access!

@app.post("/api/scripts/{id}/approve")
async def approve_script(id: int):
    database.approve_script(id)  # Anyone can approve!
```

**Why It's Bad**:
- **Public tunnel + No auth = Public API**
- Anyone with URL can read, modify, delete data
- No audit trail of who did what
- No rate limiting = easy to DDoS

**Real-World Attack**:
```bash
# Attacker finds your tunnel URL
curl https://random-words.trycloudflare.com/api/scripts
# Gets all your scripts

curl -X POST https://random-words.trycloudflare.com/api/scripts/1/approve
# Approves random script

# Automated attack
for i in {1..1000}; do
  curl -X POST https://random-words.trycloudflare.com/api/scripts/$i/approve
done
```

**How to Fix**:
```python
from fastapi import Header, HTTPException, Depends
import secrets

# Generate secure API key
API_KEY = secrets.token_urlsafe(32)  # Store this securely!

async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

@app.get("/api/scripts", dependencies=[Depends(verify_api_key)])
async def get_scripts():
    return database.get_all_scripts()
```

**Additional Protections**:
- Add rate limiting (slowapi, fastapi-limiter)
- Log all requests with IP addresses
- Add CORS restrictions
- Implement request signing
- Add IP whitelist

---

### 4. ❌ Sharing Tunnel URLs Insecurely

**The Mistake**:
```
# In Slack public channel
"Hey team, check out the review app: https://random.trycloudflare.com"

# In Twitter
"Just deployed my app! https://random.trycloudflare.com"

# In GitHub Issue
"Demo available at: https://random.trycloudflare.com"
```

**Why It's Bad**:
- URLs are indexed by search engines
- Public channels have unlimited audience
- URLs remain in message history forever
- Screenshots/archives preserve the URL

**Real-World Scenario**:
1. You share URL in company Slack
2. Guest user screenshots it
3. Leaves company, joins competitor
4. Tunnel still running
5. Competitor accesses your internal tool

**How to Fix**:
- **Only share via direct message**
- **Never post in public channels**
- **Use expiring links (URL + time-based token)**
- **Revoke access after sharing**

```python
# Better: Time-limited access tokens
import time
import hashlib

def generate_access_token(duration_minutes=30):
    expiry = int(time.time()) + (duration_minutes * 60)
    token = hashlib.sha256(f"{API_KEY}{expiry}".encode()).hexdigest()
    return f"{token}:{expiry}"

def verify_token(token: str):
    try:
        hash_part, expiry_str = token.split(":")
        expiry = int(expiry_str)
        if time.time() > expiry:
            raise HTTPException(status_code=401, detail="Token expired")
        expected = hashlib.sha256(f"{API_KEY}{expiry}".encode()).hexdigest()
        if hash_part != expected:
            raise HTTPException(status_code=401, detail="Invalid token")
    except:
        raise HTTPException(status_code=401, detail="Malformed token")
```

---

### 5. ❌ Exposing Sensitive Data via API

**The Mistake**:
```python
@app.get("/api/scripts/{id}")
async def get_script(id: int):
    script = database.get_script(id)
    return script  # Returns EVERYTHING including secrets!

# Response contains:
{
  "id": 1,
  "content": "...",
  "author_email": "john@company.com",
  "api_keys": {"openai": "sk-..."},  # ⚠️ EXPOSED
  "database_password": "...",        # ⚠️ EXPOSED
  "internal_notes": "..."            # ⚠️ EXPOSED
}
```

**Why It's Bad**:
- Leaks internal information
- Exposes other credentials
- Reveals system architecture
- Provides attack vectors

**How to Fix**:
```python
from pydantic import BaseModel

class ScriptResponse(BaseModel):
    id: int
    title: str
    content: str
    status: str
    # Explicitly exclude sensitive fields
    
    class Config:
        fields = {
            'api_keys': {'exclude': True},
            'author_email': {'exclude': True},
            'database_password': {'exclude': True}
        }

@app.get("/api/scripts/{id}", response_model=ScriptResponse)
async def get_script(id: int):
    script = database.get_script(id)
    return ScriptResponse(**script)
```

---

### 6. ❌ Using Same App Password Everywhere

**The Mistake**:
```powershell
# Using same app password for:
# - Email automation
# - IMAP sync
# - Backup scripts
# - CI/CD pipelines
# - Multiple projects
```

**Why It's Bad**:
- One compromise affects everything
- Can't revoke one without breaking all
- No way to audit which service is used
- Violates principle of least privilege

**How to Fix**:
```powershell
# Create separate app passwords:
# 1. Gmail → App Passwords → "Tunnel Email Automation"
# 2. Gmail → App Passwords → "Backup Scripts"
# 3. Gmail → App Passwords → "CI/CD Pipeline"

# Label them clearly so you know what to revoke
```

**Best Practice**:
- One app password per purpose
- Document what each password is for
- Revoke unused passwords monthly
- Rotate passwords quarterly

---

### 7. ❌ Ignoring Error Handling

**The Mistake**:
```python
# send_email.py
import smtplib

# No error handling
server = smtplib.SMTP("smtp.gmail.com", 587)
server.starttls()
server.login(sender, password)  # Fails silently if wrong
server.send_message(msg)        # Fails silently if rejected
server.quit()
```

**Why It's Bad**:
- Silent failures = you don't know email wasn't sent
- You assume tunnel URL was received
- Try to access URL that was never delivered
- Waste time debugging

**Real-World Scenario**:
1. Gmail app password expires/revoked
2. Email sending fails silently
3. You never receive tunnel URL
4. You wait for email that never comes
5. Tunnel times out while waiting

**How to Fix**:
```python
import smtplib
import logging

try:
    server = smtplib.SMTP("smtp.gmail.com", 587, timeout=10)
    server.starttls()
    server.login(sender, password)
    server.send_message(msg)
    server.quit()
    logging.info("✅ Email sent successfully")
    return True
except smtplib.SMTPAuthenticationError:
    logging.error("❌ Email authentication failed - check app password")
    print("CRITICAL: Email login failed. Check your app password.")
    return False
except smtplib.SMTPException as e:
    logging.error(f"❌ Email sending failed: {e}")
    print(f"Warning: Could not send email: {e}")
    return False
except Exception as e:
    logging.error(f"❌ Unexpected error: {e}")
    print(f"Error: {e}")
    return False
```

---

### 8. ❌ No Logging or Monitoring

**The Mistake**:
```powershell
# Start tunnel
cloudflared tunnel --url http://localhost:8000
# No logs, no monitoring, no alerting
```

**Why It's Bad**:
- Can't detect unauthorized access
- Can't diagnose issues
- Can't prove who accessed what
- No security audit trail

**How to Fix**:
```powershell
# PowerShell script logging
Start-Transcript -Path "$HOME\tunnel_logs\session_$(Get-Date -Format 'yyyyMMdd_HHmmss').txt"

# Backend logging
import logging
logging.basicConfig(
    filename='tunnel_access.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    logging.info(f"Request: {request.method} {request.url.path} from {request.client.host}")
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    logging.info(f"Response: {response.status_code} in {duration:.2f}s")
    
    return response
```

---

### 9. ❌ Forgetting to Clear Clipboard

**The Mistake**:
```powershell
# Script copies URL to clipboard
Set-Clipboard -Value $tunnelUrl
# User never clears it
# Hours later, pastes in public chat by accident
```

**Why It's Bad**:
- URL remains in clipboard indefinitely
- Easy to paste accidentally
- Clipboard managers store history
- Syncs to other devices (iCloud, Windows sync)

**How to Fix**:
```powershell
# After user has time to use URL, clear clipboard
Set-Clipboard -Value $tunnelUrl
Write-Host "✅ URL copied to clipboard! (Will auto-clear in 60 seconds)"

Start-Sleep -Seconds 60

if ((Get-Clipboard) -eq $tunnelUrl) {
    Set-Clipboard -Value ""
    Write-Host "🔒 Clipboard cleared for security"
}
```

---

### 10. ❌ Running on Untrusted Networks

**The Mistake**:
```
# Running tunnel script on:
- Coffee shop WiFi
- Airport WiFi
- Hotel WiFi
- Public library
```

**Why It's Bad**:
- Traffic could be monitored
- Man-in-the-middle attacks
- Malicious network actors
- DNS hijacking

**How to Fix**:
- Only run on trusted networks (home, office)
- Use VPN before starting tunnel
- Enable Windows Firewall
- Use HTTPS for all communications

---

## Checklist: Before Running Your Tunnel

- [ ] Backend has authentication (API key, OAuth, etc.)
- [ ] Rate limiting is enabled
- [ ] Request logging is configured
- [ ] Sensitive data is not exposed via API
- [ ] Error handling is implemented
- [ ] Tunnel will auto-stop after timeout
- [ ] Email credentials are stored securely (not in plain text)
- [ ] URL will not be shared publicly
- [ ] You're on a trusted network
- [ ] Firewall is enabled
- [ ] You know how to quickly stop the tunnel (Ctrl+C)

## Red Flags: When to Stop Immediately

Stop your tunnel if you notice:
- ⛔ Unexpected traffic in logs
- ⛔ Failed authentication attempts
- ⛔ Unusual patterns (scanning, probing)
- ⛔ High request volume from single IP
- ⛔ Database errors or timeouts
- ⛔ Someone else mentions your URL
- ⛔ Email was forwarded to wrong person

## Recovery: If Your Credentials Are Compromised

If your Gmail app password is exposed:

1. **Immediate**: Revoke app password
   - Go to https://myaccount.google.com/apppasswords
   - Delete compromised password

2. **Check for damage**:
   - Review Gmail sent folder for spam
   - Check login activity
   - Enable alerts for suspicious activity

3. **Create new app password**:
   - Generate new password
   - Update scripts/credentials
   - Test before deploying

4. **Monitor**:
   - Watch for unusual activity
   - Check spam reports
   - Review account security regularly
