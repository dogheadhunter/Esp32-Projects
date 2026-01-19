# Music Identification System - Quick Start Guide

This guide will help you get started with the music identification system in just a few minutes.

## Prerequisites

1. **Python 3.10+** installed
2. **Project dependencies** installed:
   ```bash
   pip install pyacoustid mutagen pydantic pydantic-settings requests
   ```
3. **AcoustID API Key** (free from https://acoustid.org/new-application)

## Step-by-Step Setup

### 1. Get Your API Key

1. Visit https://acoustid.org/new-application
2. Fill out the form:
   - Application name: `My Music Identifier` (or any name)
   - Application version: `1.0`
   - Contact email: your email
3. Submit and copy your API key

### 2. Set the API Key

**Option A - Environment Variable (Recommended)**

Windows:
```cmd
set ACOUSTID_API_KEY=your-api-key-here
```

Linux/Mac:
```bash
export ACOUSTID_API_KEY=your-api-key-here
```

**Option B - .env File**

Create `.env` file in the project root:
```
ACOUSTID_API_KEY=your-api-key-here
```

**Option C - Command Line**

Pass it directly when running:
```bash
python tools/music_identifier/identify_music.py --api-key your-api-key-here
```

### 3. Add Music Files

Place your MP3 files in the `music/input/` directory:

```
music/
├── input/
│   ├── unknown_song_1.mp3
│   ├── unknown_song_2.mp3
│   └── track03.mp3
├── identified/     (empty - will be populated)
└── unidentified/   (empty - will be populated)
```

### 4. Run the Identifier

**Option A - Using Python**

```bash
cd /path/to/Esp32-Projects
python tools/music_identifier/identify_music.py
```

**Option B - Using Batch Script (Windows)**

```cmd
cd C:\path\to\Esp32-Projects
scripts\identify_music.bat
```

### 5. Check Results

After processing, your files will be organized:

```
music/
├── input/          (now empty)
├── identified/     
│   ├── Queen - Bohemian Rhapsody.mp3   (identified and tagged)
│   └── The Beatles - Hey Jude.mp3      (identified and tagged)
└── unidentified/
    └── unknown_track.mp3               (couldn't be identified)
```

## Usage Examples

### Basic Usage

```bash
# Process all MP3s in music/input/
python tools/music_identifier/identify_music.py
```

### Dry Run (Preview Only)

```bash
# See what would happen without making changes
python tools/music_identifier/identify_music.py --dry-run
```

### Verbose Output

```bash
# Show detailed debug information
python tools/music_identifier/identify_music.py --verbose
```

### Skip Already Tagged Files

```bash
# Skip files that already have artist and title tags
python tools/music_identifier/identify_music.py --skip-tagged
```

### Custom Directories

```bash
# Use custom input/output directories
python tools/music_identifier/identify_music.py \
  --input /path/to/input \
  --identified /path/to/identified \
  --unidentified /path/to/unidentified
```

## What Gets Updated?

When a song is identified, the following ID3 tags are updated:

- **Title**: Song title
- **Artist**: Artist name
- **Album**: Album name
- **Date**: Release year
- **Track Number**: Track position (if available)
- **Genre**: Music genre (if available)

## Troubleshooting

### "fpcalc not found"

Install chromaprint fingerprinter:

**Ubuntu/Debian:**
```bash
sudo apt-get install libchromaprint-tools
```

**macOS:**
```bash
brew install chromaprint
```

**Windows:**
Download from https://acoustid.org/chromaprint and add to PATH

### "API key not configured"

Make sure you've set the `ACOUSTID_API_KEY` environment variable or passed `--api-key`

### "Rate limit exceeded"

The free AcoustID API has a limit of 3 requests/second. The tool automatically handles this, but if you have issues:

1. Make sure you're using a registered API key (not anonymous)
2. Try processing files in smaller batches
3. Add delays between runs if processing many files

### Low Identification Rate

Some files might not be identified because:

- **Poor audio quality**: The fingerprint can't be generated accurately
- **Obscure songs**: Not in the MusicBrainz database
- **Live recordings**: Different from studio versions
- **Remixes/covers**: May not match the original

For unidentified files, you can:

1. Try manual tagging with software like Mp3tag or MusicBrainz Picard
2. Re-encode the file to improve quality
3. Check if the file is corrupt

## Best Practices

1. **Start with a dry run** to preview changes:
   ```bash
   python tools/music_identifier/identify_music.py --dry-run
   ```

2. **Process in batches** of 20-50 files at a time for easier management

3. **Keep backups** of your original files before processing

4. **Review unidentified files** manually to see if you can add tags yourself

5. **Use good quality files** - higher bitrate files are easier to identify

## Advanced Configuration

You can customize behavior by modifying `tools/music_identifier/config.py`:

- `min_confidence`: Minimum confidence threshold (default: 0.5)
- `rate_limit`: Requests per second (default: 2.5, max 3 for free tier)
- `max_retries`: Number of retry attempts (default: 3)
- `fingerprint_duration`: Seconds to fingerprint (default: 120)

## Need Help?

- Check the full documentation: `tools/music_identifier/README.md`
- Run tests to verify setup: `pytest tools/music_identifier/tests/`
- Review the API documentation: https://acoustid.org/webservice

## Credits

This system uses:

- **AcoustID**: Audio fingerprinting service
- **MusicBrainz**: Music metadata database
- **Chromaprint**: Audio fingerprint library
- **Mutagen**: Python library for audio metadata
