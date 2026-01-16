@echo off
echo ================================================================================
echo Running All Test Suites
echo ================================================================================
echo.

echo [1/2] Wiki Ingestion Pipeline Tests...
cd tools\wiki_to_chromadb
python -m pytest -v
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Wiki ingestion tests failed!
    cd ..\..
    pause
    exit /b 1
)
cd ..\..

echo.
echo [2/2] Script Generator Tests...
cd tools\script-generator
python -m pytest -v
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Script generator tests failed!
    cd ..\..
    pause
    exit /b 1
)
cd ..\..

echo.
echo ================================================================================
echo All Tests Passed!
echo ================================================================================
