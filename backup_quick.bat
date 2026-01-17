@echo off
REM Fast backup using robocopy (Windows built-in tool)

echo ============================================================================
echo   ChromaDB Database Quick Backup (Robocopy)
echo ============================================================================
echo.

REM Get timestamp
for /f "tokens=2 delims==." %%a in ('wmic os get localdatetime /value') do set dt=%%a
set TIMESTAMP=%dt:~0,8%_%dt:~8,6%

set SOURCE=chroma_db
set DEST=C:\esp32-backups\chromadb_backup_%TIMESTAMP%

echo Source: %SOURCE%
echo Destination: %DEST%
echo.
echo Starting fast backup with robocopy...
echo (This will take about 30 seconds)
echo.

robocopy "%SOURCE%" "%DEST%" /E /MT:8 /R:2 /W:5

if %ERRORLEVEL% LEQ 7 (
    echo.
    echo [SUCCESS] Backup completed!
    echo Location: %DEST%
    echo.
    echo To restore, copy this folder back to: chroma_db
) else (
    echo.
    echo [ERROR] Backup failed with error level %ERRORLEVEL%
)

echo.
echo ============================================================================
pause
