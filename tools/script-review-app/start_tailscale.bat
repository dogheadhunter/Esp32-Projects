@echo off
REM Script Review App - Tailscale Startup (Windows)
REM This script starts the FastAPI server and configures Tailscale for remote access

echo ========================================
echo Script Review App - Tailscale Mode
echo ========================================
echo.

REM Check if Tailscale is installed
where tailscale >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Tailscale is not installed!
    echo.
    echo Please install Tailscale from:
    echo https://tailscale.com/download/windows
    echo.
    echo Or use: winget install tailscale.tailscale
    echo.
    pause
    exit /b 1
)

REM Check if Tailscale is running
tailscale status >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] Tailscale is not running!
    echo Please start Tailscale and connect to your network.
    echo.
    pause
    exit /b 1
)

echo [OK] Tailscale is running
echo.

REM Start the FastAPI server in a new window
echo [INFO] Starting FastAPI server...
start "Script Review API" cmd /k "cd /d %~dp0 && python -m backend.main"

REM Wait for server to start
echo [INFO] Waiting for server to start...
timeout /t 5 /nobreak >nul

REM Check if server is running
powershell -Command "try { $response = Invoke-WebRequest -Uri 'http://localhost:8000/health' -TimeoutSec 2; exit 0 } catch { exit 1 }" >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] Server may not have started properly
    echo Check the server window for errors
    echo.
    pause
    exit /b 1
)

echo [OK] Server is running
echo.

REM Configure Tailscale serve for HTTPS
echo [INFO] Configuring Tailscale HTTPS...
tailscale serve https / http://localhost:8000

REM Get Tailscale URL
echo.
echo ========================================
echo Script Review App is READY!
echo ========================================
echo.

REM Display the Tailscale URL
for /f "tokens=2" %%a in ('tailscale status ^| findstr /C:"%COMPUTERNAME%"') do (
    set TAILSCALE_URL=%%a
)

if defined TAILSCALE_URL (
    echo Access your app from any device with Tailscale:
    echo.
    echo   https://%TAILSCALE_URL%
    echo.
    echo Copy this URL to your phone's browser!
) else (
    echo Run 'tailscale status' to find your URL
    echo It will look like: https://YOUR-PC.TAILNET.ts.net
)

echo.
echo [INFO] Mobile Access:
echo   1. Install Tailscale on your phone
echo   2. Sign in with the same account
echo   3. Connect to your Tailscale network
echo   4. Open the URL above
echo.
echo Press Ctrl+C in the server window to stop
echo.
pause
