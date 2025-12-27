# SD Card Verification Test

This test verifies that the ESP32 can read and write to a MicroSD card using the SPI interface. It uses the exact code from the Random Nerd Tutorials guide.

## Wiring

| MicroSD Module | ESP32 |
|---|---|
| 3V3 | 3.3V |
| CS | GPIO 5 |
| MOSI | GPIO 23 |
| CLK | GPIO 18 |
| MISO | GPIO 19 |
| GND | GND |

## Description

The code initializes the SD card, lists directories, creates a directory, removes a directory, writes a file, appends to a file, reads a file, renames a file, deletes a file, and tests file I/O speed.

## Expected Output

Open the Serial Monitor at 115200 baud. You should see output indicating successful file operations.
