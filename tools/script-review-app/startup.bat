@echo off
REM Start Fallout Script Review
cd /d "%~dp0"
PowerShell.exe -ExecutionPolicy Bypass -File "auto-start-simple.ps1"
