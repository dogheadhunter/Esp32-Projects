# PowerShell Credential Storage: Security Analysis

**Topic**: Storing EMAIL_SENDER and EMAIL_PASSWORD in PowerShell Profile Environment Variables

## Current Implementation

```powershell
# In PowerShell profile ($PROFILE)
$env:EMAIL_SENDER = "jtleyba2018@gmail.com"
$env:EMAIL_PASSWORD = "haqshjhcoazowlth"
```

## Security Analysis of Environment Variables

### ❌ Critical Security Vulnerabilities

#### 1. Plain Text Storage
**Location**: `$PROFILE` file (usually `C:\Users\<username>\Documents\WindowsPowerShell\Microsoft.PowerShell_profile.ps1`)

**Problems**:
- File is stored as plain text on disk
- Readable by any process running under your user account
- Backed up by OneDrive, cloud storage, backup software
- May be synced to other devices
- Visible in file history/shadow copies

**Risk**: High - Anyone with access to your user account can read your credentials

#### 2. Memory Exposure
**How `$env` works**:
- Environment variables are stored in process memory
- Accessible to child processes
- Visible to debugging tools
- Can be dumped from memory

**From Stack Overflow Research**:
> "$env is ONLY in ram. It left no pointers when PS closed... Even with a shared memory attack, that address space is only available to system32, etc and kernel mode drivers"

**However**:
- Attackers with admin access can dump process memory
- May be written to pagefile/swap on disk
- Visible in crash dumps
- Can be logged by security software

**Risk**: Medium - Requires elevated access but still exploitable

#### 3. Process Environment Visibility
**Who can see environment variables**:
- The current PowerShell process
- All child processes spawned
- Tools like Process Explorer, Process Monitor
- PowerShell transcripts (if enabled)
- Event logs (if configured to log environment)

**Attack Scenarios**:
```powershell
# Any process can read parent's environment
Get-ChildItem Env:EMAIL_PASSWORD

# Transcripts may log this
$env:EMAIL_PASSWORD  # Logged to transcript
```

#### 4. No Encryption
- Not encrypted at rest
- Not encrypted in memory
- Not tied to user or machine
- Can be copy-pasted to other systems

## Security Risk Comparison

| Storage Method | At Rest | In Memory | Cross-Machine | Admin Access Needed |
|---------------|---------|-----------|---------------|---------------------|
| **Environment Variables (Current)** | ❌ Plain text | ⚠️ Plain text | ✅ Portable | ❌ No |
| **PowerShell SecureString** | ✅ DPAPI encrypted | ⚠️ Plain text when used | ❌ Machine-specific | ❌ No |
| **Windows Credential Manager** | ✅ DPAPI encrypted | ⚠️ Plain text when accessed | ❌ User-specific | ❌ No |
| **Azure Key Vault** | ✅ Cloud encrypted | ⚠️ Plain text when accessed | ✅ Cloud-based | ✅ Yes (Azure auth) |
| **Hardware Security Module** | ✅ Hardware | ✅ Never leaves HSM | ✅ Cloud/local | ✅ Yes |

## Alternative Solutions

### Option 1: PowerShell SecureString (Recommended for Local Scripts)

**Implementation**:
```powershell
# One-time: Store credential
$cred = Get-Credential -Message "Enter Gmail credentials"
$cred.Password | ConvertFrom-SecureString | Set-Content "$HOME\.secrets\gmail-password.txt"
$cred.UserName | Set-Content "$HOME\.secrets\gmail-username.txt"

# In your scripts: Retrieve credential
$username = Get-Content "$HOME\.secrets\gmail-username.txt"
$securePassword = Get-Content "$HOME\.secrets\gmail-password.txt" | ConvertTo-SecureString
$cred = New-Object PSCredential($username, $securePassword)

# Use in send_email.py
$plainPassword = $cred.GetNetworkCredential().Password
```

**Pros**:
- ✅ Encrypted using Windows DPAPI (Data Protection API)
- ✅ Can only be decrypted by same user on same machine
- ✅ Simple to implement
- ✅ No additional dependencies

**Cons**:
- ⚠️ Tied to specific machine/user (can't copy to another PC)
- ⚠️ Still in plain text briefly when converted back
- ⚠️ Requires recreating on different machines

**Security Level**: Medium-High

---

### Option 2: Windows Credential Manager (Best Balance)

**Implementation**:
```powershell
# One-time: Store credential
cmdkey /generic:GmailForTunnel /user:jtleyba2018@gmail.com /pass:haqshjhcoazowlth

# Or using PowerShell (requires CredentialManager module)
Install-Module -Name CredentialManager -Force
New-StoredCredential -Target "GmailForTunnel" -UserName "jtleyba2018@gmail.com" -Password "haqshjhcoazowlth" -Persist LocalMachine

# In your scripts: Retrieve
$cred = Get-StoredCredential -Target "GmailForTunnel"
$env:EMAIL_SENDER = $cred.UserName
$env:EMAIL_PASSWORD = $cred.GetNetworkCredential().Password
```

**Pros**:
- ✅ Built into Windows (no extra software)
- ✅ Encrypted using DPAPI
- ✅ GUI available (Control Panel → Credential Manager)
- ✅ Supports both generic and domain credentials
- ✅ Per-user or per-machine storage

**Cons**:
- ⚠️ Requires PowerShell module or cmdkey
- ⚠️ User-specific (doesn't roam to other machines)
- ⚠️ Can be accessed by admin users

**Security Level**: High

---

### Option 3: Microsoft SecretManagement Module (Enterprise-Grade)

**Implementation**:
```powershell
# One-time setup
Install-Module Microsoft.PowerShell.SecretManagement -Force
Install-Module SecretStore -Force

# Create a vault
Register-SecretVault -Name "LocalVault" -ModuleName SecretStore -DefaultVault

# Store secret (prompted for vault password)
Set-Secret -Name "GmailPassword" -Secret "haqshjhcoazowlth"

# In your scripts: Retrieve
$password = Get-Secret -Name "GmailPassword" -AsPlainText
$env:EMAIL_SENDER = "jtleyba2018@gmail.com"
$env:EMAIL_PASSWORD = $password
```

**Pros**:
- ✅ Microsoft's official secrets management solution
- ✅ Supports multiple vault backends (SecretStore, Azure Key Vault, etc.)
- ✅ Optional password protection
- ✅ Configurable timeout
- ✅ Cross-platform (Windows, Linux, macOS)

**Cons**:
- ⚠️ Requires module installation
- ⚠️ More complex setup
- ⚠️ May prompt for vault password

**Security Level**: Very High

---

### Option 4: Azure Key Vault (Production/Enterprise)

**Implementation**:
```powershell
# One-time setup
Install-Module Az.KeyVault
Connect-AzAccount

# Store secret in Azure Key Vault
$secretValue = ConvertTo-SecureString "haqshjhcoazowlth" -AsPlainText -Force
Set-AzKeyVaultSecret -VaultName "MyVault" -Name "GmailPassword" -SecretValue $secretValue

# In your scripts: Retrieve
$secret = Get-AzKeyVaultSecret -VaultName "MyVault" -Name "GmailPassword" -AsPlainText
$env:EMAIL_PASSWORD = $secret
```

**Pros**:
- ✅ Cloud-based (accessible from anywhere)
- ✅ HSM-backed option (FIPS 140-2 compliant)
- ✅ Full audit logging
- ✅ Automatic key rotation
- ✅ Fine-grained RBAC
- ✅ Integrates with Azure AD

**Cons**:
- ❌ Requires Azure subscription (costs money)
- ❌ More complex setup
- ❌ Overkill for personal projects
- ❌ Requires internet connection

**Security Level**: Enterprise

---

## Recommended Approach for Your Use Case

### Best Choice: Windows Credential Manager + SecureString

This provides a good balance of security and convenience:

```powershell
# Add to your PowerShell profile
function Get-TunnelEmailCredentials {
    $credPath = "$HOME\.tunnel-creds"
    
    # Check if credentials are cached
    if (Test-Path "$credPath\gmail-user.txt") {
        $username = Get-Content "$credPath\gmail-user.txt"
        $password = Get-Content "$credPath\gmail-pass.txt" | ConvertTo-SecureString
        return [PSCredential]::new($username, $password)
    }
    
    # Prompt for credentials and save
    Write-Host "First time setup: Enter Gmail credentials" -ForegroundColor Cyan
    $cred = Get-Credential -Message "Gmail for Tunnel Notifications"
    
    New-Item -ItemType Directory -Path $credPath -Force | Out-Null
    $cred.UserName | Set-Content "$credPath\gmail-user.txt"
    $cred.Password | ConvertFrom-SecureString | Set-Content "$credPath\gmail-pass.txt"
    
    return $cred
}

# Later in start_tunnel.ps1
$cred = Get-TunnelEmailCredentials
$env:EMAIL_SENDER = $cred.UserName
$env:EMAIL_PASSWORD = $cred.GetNetworkCredential().Password
```

**Why this works**:
1. Credentials encrypted using DPAPI
2. Only stored locally
3. First-time setup, then automatic
4. Easy to delete/reset (just delete the folder)
5. No cloud dependencies

## Common Mistakes to Avoid

### ❌ DON'T: Store in Profile Directly
```powershell
# BAD - Plain text in profile
$env:EMAIL_PASSWORD = "haqshjhcoazowlth"
```

### ❌ DON'T: Hard-code in Scripts
```powershell
# BAD - Committed to git
$password = "haqshjhcoazowlth"
```

### ❌ DON'T: Use Obfuscation as Security
```powershell
# BAD - Base64 is not encryption
$password = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String("aGFxc2pqaGNvYXpvd2x0aA=="))
```

### ❌ DON'T: Log Credentials
```powershell
# BAD - Logs contain password
Write-Verbose "Connecting with password: $env:EMAIL_PASSWORD"
```

### ✅ DO: Use Secure Patterns
```powershell
# GOOD - Encrypted storage
$cred = Get-StoredCredential -Target "TunnelGmail"

# GOOD - Minimal exposure
$password = $cred.GetNetworkCredential().Password
# Use password immediately, don't store
Send-Email -Password $password
Remove-Variable password
```

## Security Checklist

Before storing credentials, ask:

- [ ] Is the credential encrypted at rest?
- [ ] Is it tied to my user account/machine?
- [ ] Can I revoke it remotely if needed?
- [ ] Is there audit logging?
- [ ] Will it survive a git commit by accident?
- [ ] Can another user on this PC access it?
- [ ] What happens if my PC is stolen?
- [ ] Am I using the least privilege necessary?

## Memory Security Best Practices

Even with encrypted storage, credentials exist in memory when used:

```powershell
# Clear variables after use
$password = $cred.GetNetworkCredential().Password
# Use password...
Remove-Variable password -ErrorAction SilentlyContinue

# Don't keep in environment longer than needed
$env:EMAIL_PASSWORD = $password
# Run email script...
Remove-Item Env:\EMAIL_PASSWORD -ErrorAction SilentlyContinue
```

## References

- [PowerShell SecretManagement Module](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.secretmanagement/)
- [Stack Overflow: Is it safe to store passwords in $env](https://stackoverflow.com/questions/28504850/)
- [AdminDroid: Best Methods to Securely Store Passwords](https://blog.admindroid.com/best-methods-to-securely-store-passwords-for-automated-powershell-scripts/)
- [Microsoft: Data Protection API (DPAPI)](https://learn.microsoft.com/en-us/windows/win32/seccng/cng-dpapi)
