# Music Identifier Tool

A robust music identification and tagging system using AcoustID fingerprinting and MusicBrainz metadata.

## Features

- **Automatic Music Identification**: Uses acoustic fingerprinting to identify songs
- **Metadata Tagging**: Updates MP3 ID3 tags with correct artist, title, album, year, etc.
- **Smart Organization**: Automatically organizes files into identified/unidentified folders
- **Batch Processing**: Handles multiple files at once with progress tracking
- **Fingerprint Caching**: Caches fingerprints locally to avoid re-processing files
- **Progress Bar**: Real-time progress with ETA (requires tqdm)
- **Batch Statistics**: Comprehensive reports on processing results
- **Robust Error Handling**: Gracefully handles API failures and edge cases
- **Comprehensive Testing**: Full pytest test suite (84 tests)

## Setup

### 1. Install Dependencies

Dependencies are automatically installed with the project:

```bash
pip install -e .[dev]
```

### 2. Get AcoustID API Key

1. Visit https://acoustid.org/new-application
2. Register your application (free)
3. Copy your API key

### 3. Configure API Key

Create a `.env` file in the project root or set environment variable:

```bash
export ACOUSTID_API_KEY="your-api-key-here"
```

Or create `/home/runner/work/Esp32-Projects/Esp32-Projects/.env`:
```
ACOUSTID_API_KEY=your-api-key-here
```

## Usage

### Command Line

```bash
# Identify all MP3s in the music/input/ folder (with progress bar)
python tools/music_identifier/identify_music.py

# With custom paths
python tools/music_identifier/identify_music.py --input /path/to/input --identified /path/to/identified --unidentified /path/to/unidentified

# Dry run (don't move files)
python tools/music_identifier/identify_music.py --dry-run

# Verbose output (shows detailed logs, disables progress bar)
python tools/music_identifier/identify_music.py --verbose

# Disable fingerprint caching (slower but uses less disk)
python tools/music_identifier/identify_music.py --no-cache

# Disable progress bar
python tools/music_identifier/identify_music.py --no-progress
```

### Python API

```python
from tools.music_identifier.identifier import MusicIdentifier

# Initialize
identifier = MusicIdentifier(api_key="your-api-key")

# Identify a single file
result = identifier.identify_file("/path/to/song.mp3")

if result.identified:
    print(f"Found: {result.title} by {result.artist}")
else:
    print(f"Could not identify: {result.error}")
```

## How It Works

1. **Fingerprinting**: Uses `fpcalc` (from Chromaprint) to generate acoustic fingerprints
2. **Cache Check**: Checks local cache to avoid re-processing (enabled by default)
3. **API Lookup**: Sends fingerprint to AcoustID API for matching
4. **Metadata Retrieval**: Gets detailed metadata from MusicBrainz
5. **Tag Update**: Updates MP3 ID3 tags using mutagen library
6. **File Organization**: Moves files to appropriate folders
7. **Statistics Tracking**: Tracks success rates, confidence scores, and processing speed

## Performance Features

### Fingerprint Caching

Fingerprints are cached locally in `music/.cache/fingerprints.json` to:
- Avoid re-processing unchanged files
- Speed up subsequent runs
- Reduce API calls

Cache uses MD5 file hashing to detect file changes. Disable with `--no-cache` flag.

### Progress Bar

Real-time progress tracking with:
- Current file being processed
- Files per minute processing speed
- Time remaining estimate (ETA)
- Running counts of identified/unidentified files

Automatically disabled in verbose mode. Disable manually with `--no-progress`.

### Batch Statistics

Detailed end-of-run report including:
- Success rate percentage
- Average confidence score
- Processing speed (files/minute)
- Cache hit rate
- List of unidentified files
- Quality metrics (confidence range)

## API Considerations

The AcoustID API has rate limits:
- **Free tier**: 3 requests per second
- **Registered app**: Better rate limits with API key

The implementation includes:
- Automatic rate limiting and retry logic
- Exponential backoff on failures
- Caching to avoid repeated API calls
- Graceful degradation if API is unavailable

## Testing

```bash
# Run all tests
pytest tools/music_identifier/tests/

# Run with coverage
pytest tools/music_identifier/tests/ --cov=tools/music_identifier --cov-report=term-missing

# Run specific test file
pytest tools/music_identifier/tests/test_identifier.py
```

## Troubleshooting

### "fpcalc not found"
Install chromaprint:
```bash
# Ubuntu/Debian
sudo apt-get install libchromaprint-tools

# macOS
brew install chromaprint

# Windows
# Download from https://acoustid.org/chromaprint
```

### "API key not configured"
Set the `ACOUSTID_API_KEY` environment variable or create a `.env` file.

### "Rate limit exceeded"
The tool automatically handles rate limiting. If you hit limits frequently, consider:
- Adding delays between batches
- Using the registered API key (not anonymous)
- Processing files in smaller batches

## Architecture

```
tools/music_identifier/
├── __init__.py           # Package init
├── identifier.py         # Core identification logic
├── metadata_tagger.py    # ID3 tag management
├── file_organizer.py     # File movement and organization
├── config.py             # Configuration management
├── identify_music.py     # CLI entry point
└── tests/
    ├── __init__.py
    ├── conftest.py       # Pytest fixtures
    ├── test_identifier.py
    ├── test_metadata_tagger.py
    ├── test_file_organizer.py
    └── test_integration.py
```
