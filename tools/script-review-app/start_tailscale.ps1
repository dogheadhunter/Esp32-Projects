#!/usr/bin/env pwsh
# Script Review App - Tailscale Startup (PowerShell)
# This script starts the FastAPI server and configures Tailscale for remote access

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Script Review App - Tailscale Mode" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Tailscale is installed
if (!(Get-Command tailscale -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] Tailscale is not installed!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install Tailscale from:" -ForegroundColor Yellow
    Write-Host "https://tailscale.com/download/windows"
    Write-Host ""
    Write-Host "Or use: winget install tailscale.tailscale" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if Tailscale is running
try {
    $status = tailscale status 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Tailscale not connected"
    }
    Write-Host "[OK] Tailscale is running" -ForegroundColor Green
    Write-Host ""
} catch {
    Write-Host "[WARNING] Tailscale is not running!" -ForegroundColor Yellow
    Write-Host "Please start Tailscale and connect to your network." -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# Start the FastAPI server in background
Write-Host "[INFO] Starting FastAPI server..." -ForegroundColor Cyan
$serverJob = Start-Job -ScriptBlock {
    Set-Location $using:PSScriptRoot
    python -m backend.main
} -Name "ScriptReviewServer"

# Wait for server to start
Write-Host "[INFO] Waiting for server to start..." -ForegroundColor Cyan
Start-Sleep -Seconds 5

# Check if server is running
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 2 -ErrorAction Stop
    Write-Host "[OK] Server is running" -ForegroundColor Green
    Write-Host ""
} catch {
    Write-Host "[WARNING] Server may not have started properly" -ForegroundColor Yellow
    Write-Host "Check job output for errors: Receive-Job $($serverJob.Id)" -ForegroundColor Yellow
    Write-Host ""
}

# Configure Tailscale serve for HTTPS
Write-Host "[INFO] Configuring Tailscale HTTPS..." -ForegroundColor Cyan
tailscale serve https / http://localhost:8000

# Get Tailscale URL
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Script Review App is READY!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Extract Tailscale hostname
$statusOutput = tailscale status | Select-String -Pattern "$env:COMPUTERNAME" | Select-Object -First 1
if ($statusOutput) {
    $tailscaleUrl = ($statusOutput -split '\s+')[1]
    Write-Host "Access your app from any device with Tailscale:" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  https://$tailscaleUrl" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Copy this URL to your phone's browser!" -ForegroundColor White
    
    # Copy to clipboard if available
    try {
        "https://$tailscaleUrl" | Set-Clipboard
        Write-Host "[OK] URL copied to clipboard!" -ForegroundColor Green
    } catch {
        # Clipboard not available, skip
    }
} else {
    Write-Host "Run 'tailscale status' to find your URL" -ForegroundColor Yellow
    Write-Host "It will look like: https://YOUR-PC.TAILNET.ts.net" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "[INFO] Mobile Access:" -ForegroundColor Cyan
Write-Host "  1. Install Tailscale on your phone" -ForegroundColor White
Write-Host "  2. Sign in with the same account" -ForegroundColor White
Write-Host "  3. Connect to your Tailscale network" -ForegroundColor White
Write-Host "  4. Open the URL above" -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Gray
Write-Host ""

# Wait for user to stop (Ctrl+C)
try {
    while ($true) {
        Start-Sleep -Seconds 1
        
        # Check if job is still running
        if ($serverJob.State -ne "Running") {
            Write-Host ""
            Write-Host "[WARNING] Server job stopped unexpectedly" -ForegroundColor Yellow
            Receive-Job $serverJob
            break
        }
    }
} finally {
    # Cleanup
    Write-Host ""
    Write-Host "[INFO] Stopping server..." -ForegroundColor Cyan
    Stop-Job $serverJob -ErrorAction SilentlyContinue
    Remove-Job $serverJob -ErrorAction SilentlyContinue
    
    Write-Host "[INFO] Resetting Tailscale serve..." -ForegroundColor Cyan
    tailscale serve reset
    
    Write-Host "[OK] Cleanup complete" -ForegroundColor Green
}
