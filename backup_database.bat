@echo off
REM Wrapper for PowerShell backup script

powershell -ExecutionPolicy Bypass -File "%~dp0backup_database.ps1"
