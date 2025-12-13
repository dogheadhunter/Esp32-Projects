# External LED Blink Test

## Overview
This test verifies that the ESP32 can drive an external LED using a digital output pin. This was necessary because the Inland ESP32 Core Board does not have a user-programmable onboard LED on the standard GPIO 2.

## Hardware Setup
*   **Board**: Inland ESP32 Core Board (ESP-WROOM-32)
*   **Component**: Standard LED (Any color)
*   **Resistor**: Recommended 220Ω or 330Ω in series with the LED (though for short tests, direct connection might work, it's safer with a resistor).

### Wiring
1.  **Anode (+)**: The longer leg of the LED. Connect this to **GPIO 32**.
2.  **Cathode (-)**: The shorter leg of the LED. Connect this to a **GND** pin on the ESP32 board.

**Note**: We used **GPIO 32** because GPIO 34, 35, 36, and 39 are *Input Only* pins and cannot drive an LED.

## Code Description
The code configures GPIO 32 as an output and toggles it HIGH/LOW every 1000ms (1 second) using a non-blocking `millis()` timer.

## How to Run
1.  Copy the contents of `main.cpp` in this folder to `src/main.cpp` in the project root.
2.  Build and Upload using PlatformIO.
