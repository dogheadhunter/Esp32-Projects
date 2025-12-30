# ESP32 iPod Shuffle Clone

A high-fidelity audio player and Bluetooth receiver based on the ESP32, featuring SD card playback, WiFi time synchronization, and a dedicated Shuffle/Mode button.

## Features

*   **Dual Mode Operation**:
    *   **SD Card Player**: Plays MP3 files from an SD card.
    *   **Bluetooth Receiver**: Streams audio from your phone (YouTube Music, Spotify, etc.).
*   **Smart Shuffle**: Random playback without repeating the same song back-to-back.
*   **WiFi Time Sync**: Connects to WiFi on boot to fetch accurate time (NTP), then disconnects to save power.
*   **Resume Playback**: Remembers the last volume setting.
*   **Robust Stability**: Uses a "Reboot-to-Switch" strategy to ensure maximum RAM availability for both modes.

## Hardware Setup

*   **Board**: ESP32 Dev Module (ESP-WROOM-32)
*   **Audio**: MAX98357A I2S Amplifier
*   **Storage**: MicroSD Card Module (VSPI)
*   **Controls**:
    *   Play/Pause (GPIO 27)
    *   Next (GPIO 14)
    *   Prev (GPIO 13)
    *   Shuffle/Mode (GPIO 32)
    *   Volume Potentiometer (GPIO 39)

### Pinout

| Component | ESP32 Pin |
| :--- | :--- |
| **I2S Amp** | |
| BCLK | GPIO 26 |
| LRC | GPIO 25 |
| DOUT | GPIO 22 |
| **SD Card** | |
| CS | GPIO 5 |
| MOSI | GPIO 23 |
| MISO | GPIO 19 |
| SCK | GPIO 18 |
| **Buttons** | |
| Play/Pause | GPIO 27 |
| Next | GPIO 14 |
| Prev | GPIO 13 |
| Shuffle | GPIO 32 |
| **Misc** | |
| Volume Pot | GPIO 39 |
| LED | GPIO 2 |

## Controls

| Button | Action | Description |
| :--- | :--- | :--- |
| **Play/Pause** | Short Press | Toggle Play/Pause |
| **Play/Pause** | Long Press | Power Off / On |
| **Next** | Short Press | Next Song |
| **Prev** | Short Press | Previous Song (or restart current) |
| **Shuffle** | Short Press | Toggle Shuffle Mode (SD Card only) |
| **Shuffle** | **Long Press (2s)** | **Switch Mode (SD <-> Bluetooth)** |

## How to Use

1.  **Power On**: The device will boot into the last used mode (SD or Bluetooth).
2.  **SD Mode**:
    *   Connects to WiFi briefly to set the clock.
    *   Scans SD card for MP3s (creates a cache file `playlist.m3u` for speed).
    *   Starts playing.
3.  **Bluetooth Mode**:
    *   Device name: `ESP32-iPod`
    *   Connect your phone and play music.
    *   LED blinks fast to indicate Bluetooth mode.
4.  **Switching Modes**:
    *   Hold the **Shuffle Button** for 2 seconds.
    *   The device will save the new mode preference and **reboot** to ensure a clean start.

## Troubleshooting

*   **"i2s_driver_install failed" in Bluetooth Mode**: This is a known warning in the logs but does not affect functionality. If you hear music, it works!
*   **Songs cutting off**: Ensure your SD card is formatted correctly (FAT32) and the files are not corrupted. The player uses a 48KB buffer for stability.
*   **WiFi fails**: The device will wait 10 seconds for WiFi. If it fails, it skips time sync and plays music anyway.

## Firmware Updates

To update the code:
1.  Connect via USB.
2.  Run `pio run -t uploadAndMonitor`.
