@echo off
REM Wrapper for PowerShell restore script

powershell -ExecutionPolicy Bypass -File "%~dp0restore_database.ps1"
