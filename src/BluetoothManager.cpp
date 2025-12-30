#include "BluetoothManager.h"

// Define I2S Pins (Must match main.cpp)
#define I2S_DOUT       22
#define I2S_BCLK       26
#define I2S_LRC        25

BluetoothManager btManager;

void BluetoothManager::setup() {
    // Configure I2S pins for the A2DP Sink
    i2s_pin_config_t my_pin_config = {
        .bck_io_num = I2S_BCLK,
        .ws_io_num = I2S_LRC,
        .data_out_num = I2S_DOUT,
        .data_in_num = I2S_PIN_NO_CHANGE
    };
    a2dp_sink.set_pin_config(my_pin_config);
}

void BluetoothManager::start(const char* deviceName) {
    Serial.printf("Starting Bluetooth Sink: %s\n", deviceName);
    a2dp_sink.start(deviceName);
}

void BluetoothManager::stop() {
    Serial.println("Stopping Bluetooth Sink...");
    a2dp_sink.end();
}

bool BluetoothManager::isConnected() {
    return a2dp_sink.is_connected();
}

void BluetoothManager::loop() {
    // The library handles audio in background tasks, 
    // but we can add status checks here if needed.
}
