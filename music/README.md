# Music Identification System

This directory contains the music identification and organization system for the ESP32 AI Radio project.

## Directory Structure

- **`input/`** - Drop MP3 files here for identification
- **`identified/`** - Successfully identified and tagged songs are moved here
- **`unidentified/`** - Songs that couldn't be identified are moved here

## Quick Start

1. Place your MP3 files in the `input/` directory
2. Run the identification script:
   ```bash
   python tools/music_identifier/identify_music.py
   ```
3. Check the `identified/` and `unidentified/` folders for results

## How It Works

The system uses the AcoustID audio fingerprinting service and MusicBrainz database to:
1. Generate an acoustic fingerprint of each MP3 file
2. Query the AcoustID/MusicBrainz API to identify the song
3. Update the MP3's ID3 tags with correct metadata (title, artist, album, etc.)
4. Move the file to the appropriate output folder

## Requirements

- AcoustID API key (free from https://acoustid.org/new-application)
- See `tools/music_identifier/README.md` for setup instructions
