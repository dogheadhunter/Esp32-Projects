# Basic MP3 Player (No Wireless)

A simplified, high-stability version of the ESP32 audio player. This version removes all WiFi, Bluetooth, and button logic to create a "turn on and play" device that is extremely robust and fast to boot.

## Features

*   **Instant Play**: Starts playing music immediately upon power-up.
*   **Smart Playlist**: Automatically scans the SD card for MP3s.
*   **Integrity Check**: Verifies the playlist on every boot. If you change the SD card content, it automatically rescans.
*   **No-Flicker Volume**: Advanced smoothing and hysteresis logic for the volume knob.
*   **Debug Logging**: Detailed serial output for monitoring playback status.

## Hardware Setup

*   **Board**: ESP32 Dev Module (ESP-WROOM-32)
*   **Audio**: MAX98357A I2S 3W Class D Amplifier
*   **Speaker**: DWEII 4 Ohm 3 Watt Speaker
*   **Storage**: WWZMDiB 6 pcs Micro SD TF Card Reader
*   **Controls**: 10k Potentiometer

### Pinout

| Component | ESP32 Pin | Description |
| :--- | :--- | :--- |
| **MAX98357A** | | **I2S Audio Amp** |
| BCLK | GPIO 26 | Bit Clock |
| LRC | GPIO 25 | Left/Right Clock |
| DIN | GPIO 22 | Data In |
| GND | GND | Ground |
| VIN | 5V / VIN | Power |
| **SD Card** | | **VSPI Bus** |
| CS | GPIO 5 | Chip Select |
| MOSI | GPIO 23 | Data In |
| MISO | GPIO 19 | Data Out |
| SCK | GPIO 18 | Clock |
| VCC | 5V | Power |
| GND | GND | Ground |
| **Controls** | | |
| Potentiometer | GPIO 39 | Volume Control (VN) |
| **Misc** | | |
| LED | GPIO 2 | Status Indicator |

## How to Use

1.  **Power On**: The device boots up.
2.  **Auto-Check**: It checks 10 random songs from its playlist.
    *   If they exist, it starts playing immediately.
    *   If they are missing (new card inserted), it rescans the card and creates a new playlist.
3.  **Playback**: It plays songs sequentially or randomly (depending on code setting).
4.  **Volume**: Turn the knob to adjust volume.

## Python Tools & Radio Station Workflow

This project includes a suite of Python tools to turn your MP3 collection into a "Fake Radio Station" with automated DJ intros, voiceovers, and scheduling.

### 1. Setup
```bash
cd tools
pip install -r requirements.txt
```

### 2. Workflow
1.  **Extract Metadata**: Scan your MP3 folder to create a CSV library.
    ```bash
    python tools/extract_metadata.py "C:\Path\To\MP3s"
    ```
2.  **Enrich Metadata**: Fetch release dates and genres from MusicBrainz.
    ```bash
    python tools/enrich_metadata.py my_music.csv
    ```
3.  **Clean Metadata**: Remove junk text (e.g., "Remastered 2009") for better TTS.
    ```bash
    python tools/clean_metadata.py music_library_enriched.csv
    ```
4.  **Generate Show**: Create a ready-to-play SD card folder with normalized audio and DJ intros.
    ```bash
    # Use Microsoft Edge Neural Voices (High Quality, Free)
    python tools/prepare_sd_card.py music_library_clean.csv --shuffle --engine edge --voice guy
    ```

### 3. Advanced: Custom Voice (Concatenative Synthesis)
You can record your own voice to announce songs!
1.  Record clips in `my_voice_assets/` (Templates, Artists, Titles).
2.  Run the show builder:
    ```bash
    python tools/build_radio_show.py
    ```

## Future Plans
*   **60-Minute Show Generation**: Create hour-long blocks with Station IDs, Ad breaks, and Time checks.
*   **Concatenative Synthesis**: Full implementation of the "Stitching" script to mix user voice with music.


## Audio Preparation (Volume Normalization)

To ensure all songs play at the same volume, you should normalize them before copying them to the SD card.

### Option 1: The Easy Way (MP3Gain)
1. Download **MP3Gain** (Windows) or a similar tool.
2. Load your MP3 folder.
3. Set "Target Volume" to **89.0 dB**.
4. Click "Track Gain".
5. Copy the files to your SD card.

### Option 2: The Coder Way (Python Script)
We have included a script in `tools/normalize_volume.py`.

1. Install Python and FFMPEG.
2. Install dependencies: `pip install -r tools/requirements.txt`
3. Run the script:
   ```bash
   python tools/normalize_volume.py "C:\Path\To\Your\Music" --target -14.0
   ```

## Troubleshooting

*   **Buzzing on Startup**: Fixed in v1.1 by initializing I2S pins low before starting the SD card.
*   **Volume Jitter**: Fixed in v1.2 using 16-sample averaging and 2% hysteresis.
