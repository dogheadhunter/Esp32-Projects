@echo off
REM Music Identification Batch Script
REM Identifies MP3 files in the music/input directory

cd /d %~dp0..

echo.
echo ====================================
echo Music Identifier
echo ====================================
echo.
echo This script will identify all MP3 files in the music/input/ folder
echo.

REM Check if API key is set
if "%ACOUSTID_API_KEY%"=="" (
    echo ERROR: ACOUSTID_API_KEY environment variable not set!
    echo.
    echo Please set your AcoustID API key:
    echo   1. Get a free key from https://acoustid.org/new-application
    echo   2. Set environment variable:
    echo      set ACOUSTID_API_KEY=your-api-key-here
    echo.
    pause
    exit /b 1
)

REM Count MP3 files
set count=0
for %%f in (music\input\*.mp3) do set /a count+=1

if %count%==0 (
    echo No MP3 files found in music/input/
    echo.
    echo Place MP3 files in the music/input/ folder and run this script again.
    echo.
    pause
    exit /b 0
)

echo Found %count% MP3 file(s) to process
echo.

REM Ask for confirmation
set /p confirm="Proceed with identification? (y/n): "
if /i not "%confirm%"=="y" (
    echo Cancelled by user.
    pause
    exit /b 0
)

echo.
echo Starting identification...
echo.

REM Run the identifier
python tools\music_identifier\identify_music.py

echo.
echo ====================================
echo Identification complete!
echo ====================================
echo.
echo Check the results:
echo   - Identified songs: music\identified\
echo   - Unidentified songs: music\unidentified\
echo.

pause
