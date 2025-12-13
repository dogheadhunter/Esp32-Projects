# ESP32 Development Workspace

This workspace is set up for your Inland ESP32 (ESP-WROOM-32) board.

## Prerequisites

1.  **VS Code Extension**: You need to install the **PlatformIO IDE** extension.
2.  **Drivers**: Ensure you have the drivers for the **CP2102** USB-to-Serial chip installed.
    *   Windows usually installs this automatically.
    *   If not, download "CP210x VCP Windows" drivers from Silicon Labs.

## Getting Started (USB)

1.  Connect your ESP32 to the computer via USB.
2.  Open `src/main.cpp` and update `YOUR_WIFI_SSID` and `YOUR_WIFI_PASSWORD` if you want to prepare for OTA immediately.
3.  Click the **PlatformIO Alien Icon** on the left sidebar.
4.  Under **Project Tasks**, click **Upload**.
5.  To see the output, click **Monitor**.

## Switching to OTA (Over-The-Air) Updates

Once you have successfully uploaded the code via USB and the device is connected to WiFi:

1.  Check the Serial Monitor output to find the **IP Address** of your ESP32.
2.  Open `platformio.ini`.
3.  Uncomment the OTA configuration lines:
    ```ini
    upload_protocol = espota
    upload_port = 192.168.1.X  ; <--- Put your ESP32's IP here
    ```
4.  Save the file.
5.  Now, when you click **Upload**, PlatformIO will try to upload wirelessly!

## Hardware Details
*   **Module**: ESP-WROOM-32
*   **USB Chip**: CP2102-GMR
*   **Built-in LED**: GPIO 2
