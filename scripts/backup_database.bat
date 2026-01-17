@echo off
REM Wrapper for PowerShell backup script
REM Navigate to project root for PowerShell script

powershell -ExecutionPolicy Bypass -File "%~dp0..\backup_database.ps1"
