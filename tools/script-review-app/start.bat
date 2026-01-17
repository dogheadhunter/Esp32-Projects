@echo off
REM Startup script for Script Review App (Windows)

cd /d "%~dp0"

REM Check if .env exists
if not exist .env (
    echo Creating .env from template...
    copy .env.template .env
    echo Please edit .env and set SCRIPT_REVIEW_TOKEN before running again
    exit /b 1
)

REM Install dependencies if needed
python -c "import fastapi" >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt
)

REM Start the server
echo Starting Script Review App...
echo Access the app at: http://localhost:8000
echo Press Ctrl+C to stop
python -m backend.main
