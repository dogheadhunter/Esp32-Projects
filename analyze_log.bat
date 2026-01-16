@echo off
echo ================================================================================
echo Analyzing Latest Ingestion Log
echo ================================================================================
echo.

python tools\wiki_to_chromadb\analyze_log.py %*

echo.
