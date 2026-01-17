@echo off
echo ================================================================================
echo Starting Wiki Ingestion (Fresh Mode - Clears Database First)
echo ================================================================================
echo.
echo WARNING: This will delete the existing ChromaDB collection!
echo Starting in 3 seconds...
echo.

echo Configuring power settings to prevent sleep...
powercfg /change standby-timeout-ac 0
powercfg /change monitor-timeout-ac 0
echo   - Sleep: DISABLED
echo   - Monitor: Will not turn off
echo.

python tools\wiki_to_chromadb\process_wiki.py lore\fallout_wiki_complete.xml --clear-database --no-progress

echo.
echo ================================================================================
echo Ingestion Complete
echo ================================================================================
echo.
echo Restoring power settings...
powercfg /change standby-timeout-ac 30
powercfg /change monitor-timeout-ac 10
echo   - Sleep: 30 minutes
echo   - Monitor: 10 minutes
