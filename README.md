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

## Troubleshooting

*   **Buzzing on Startup**: Fixed in v1.1 by initializing I2S pins low before starting the SD card.
*   **Volume Jitter**: Fixed in v1.2 using 16-sample averaging and 2% hysteresis.
