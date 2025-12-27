# Play MP3 from SD Card

This test plays an MP3 file from the SD card using the MAX98357A I2S amplifier.

## Wiring

### MicroSD Module (Standard VSPI)
| MicroSD Module | ESP32 |
|---|---|
| VCC | 3.3V / 5V |
| GND | GND |
| CS | GPIO 5 |
| MOSI | GPIO 23 |
| CLK | GPIO 18 |
| MISO | GPIO 19 |

### MAX98357A (I2S Amplifier)
| MAX98357A | ESP32 |
|---|---|
| VIN | 3.3V / 5V |
| GND | GND |
| DIN | GPIO 22 |
| BCLK | GPIO 26 |
| LRC | GPIO 25 |
| GAIN | GND (Optional) |

## Usage
1. Place an MP3 file named `music.mp3` or `song.mp3` on the root of the SD card.
2. If you have a different filename, the code will try to auto-detect the first `.mp3` file it finds.
3. Upload the code and open Serial Monitor.
4. Send `+` or `-` in the Serial Monitor to adjust volume.
