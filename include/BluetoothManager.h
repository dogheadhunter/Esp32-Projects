#ifndef BLUETOOTH_MANAGER_H
#define BLUETOOTH_MANAGER_H

#include <Arduino.h>
#include "BluetoothA2DPSink.h"

class BluetoothManager {
public:
    void setup();
    void start(const char* deviceName);
    void stop();
    bool isConnected();
    
    // Call this in the main loop if needed (though A2DP is mostly callback based)
    void loop();

private:
    BluetoothA2DPSink a2dp_sink;
};

extern BluetoothManager btManager;

#endif
