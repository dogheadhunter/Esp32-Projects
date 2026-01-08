# Inland ESP32 Core Board (Black and Eco-friendly)

## Overview
The Inland ESP32 Core Board is a Mini development board based on the **ESP-WROOM-32** module. It breaks out most I/O ports to standard 2.54mm pitch headers, making it easy to connect peripherals. It features integrated WiFi + Bluetooth (BLE) and is designed for low-power applications.

## Technical Specifications
*   **Microcontroller**: ESP-WROOM-32 module
*   **USB to Serial Port Chip**: CP2102-GMR
*   **Operating Voltage**: DC 5V (via USB)
*   **Logic Voltage**: 3.3V
*   **Operating Current**: 80mA (average)
*   **Current Supply**: 500mA (Minimum)
*   **Operating Temperature Range**: -40℃ ~ +85℃
*   **WiFi Protocol**: 802.11 b/g/n/e/i (802.11n up to 150 Mbps)
*   **WiFi Frequency**: 2.4 GHz ~ 2.5 GHz
*   **Bluetooth**: v4.2 BR/EDR and BLE standards
*   **Dimensions**: 55mm * 26mm * 13mm
*   **Weight**: 9.3g

## Hardware Notes & Pinout Quirks

### Input-Only Pins
The following GPIO pins are **Input Only** (GPI). They cannot be used for `digitalWrite` or to drive LEDs/relays:
*   **GPIO 34**
*   **GPIO 35**
*   **GPIO 36** (SENSOR_VP)
*   **GPIO 39** (SENSOR_VN)

### Onboard LED
*   This specific board **does not** have a user-programmable onboard LED connected to the standard GPIO 2 (unlike some other ESP32 dev kits).
*   To test "Blink", you must connect an external LED to a valid output pin (e.g., GPIO 32).

### Boot/Upload Mode
If the board fails to upload with a "Write timeout" error, you may need to manually enter bootloader mode:
1.  Hold the **BOOT** button.
2.  Press and release the **EN** button.
3.  Release the **BOOT** button.

## PlatformIO Configuration
For successful programming via VS Code / PlatformIO, use the following settings in `platformio.ini`:

```ini
[env:esp32dev]
platform = espressif32
board = esp32dev
framework = arduino

; Serial Monitor Speed
monitor_speed = 115200

; Upload Settings
upload_speed = 115200          ; Lower speed helps with stability
upload_resetmethod = nodemcu   ; Helps with auto-reset into bootloader
monitor_rts = 0                ; Prevents serial monitor from holding reset
monitor_dtr = 0
```

## Drivers
*   **CP210x USB to UART Bridge VCP Drivers**: Required for the computer to recognize the board.
    *   [Download from Silicon Labs](https://www.silabs.com/developers/usb-to-uart-bridge-vcp-drivers)

## References
*   [Micro Center Community Article](https://community.microcenter.com/kb/articles/652-inland-esp32-core-board-black-and-eco-friendly)
