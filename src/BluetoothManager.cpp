#include "BluetoothManager.h"

// Define I2S Pins (Must match main.cpp)
#define I2S_DOUT       22
#define I2S_BCLK       26
#define I2S_LRC        25

BluetoothManager btManager;

// ============================================
// BLUETOOTH CALLBACKS
// ============================================

void avrc_metadata_callback(uint8_t id, const uint8_t *text) {
  // id 0x1 = Title, 0x2 = Artist, 0x4 = Album, etc.
  const char* label = "Unknown";
  switch (id) {
      case ESP_AVRC_MD_ATTR_TITLE: label = "Title"; break;
      case ESP_AVRC_MD_ATTR_ARTIST: label = "Artist"; break;
      case ESP_AVRC_MD_ATTR_ALBUM: label = "Album"; break;
      case ESP_AVRC_MD_ATTR_GENRE: label = "Genre"; break;
  }
  Serial.printf("[BT Metadata] %s: %s\n", label, text);
}

void connection_state_changed(esp_a2d_connection_state_t state, void *ptr) {
  Serial.print("[BT Status] Connection: ");
  switch (state) {
      case ESP_A2D_CONNECTION_STATE_DISCONNECTED: Serial.println("Disconnected"); break;
      case ESP_A2D_CONNECTION_STATE_CONNECTING: Serial.println("Connecting..."); break;
      case ESP_A2D_CONNECTION_STATE_CONNECTED: Serial.println("Connected"); break;
      case ESP_A2D_CONNECTION_STATE_DISCONNECTING: Serial.println("Disconnecting..."); break;
      default: Serial.printf("Unknown (0x%x)\n", state); break;
  }
}

void audio_state_changed(esp_a2d_audio_state_t state, void *ptr) {
  Serial.print("[BT Status] Audio: ");
  switch (state) {
      case ESP_A2D_AUDIO_STATE_REMOTE_SUSPEND: Serial.println("Suspended"); break;
      case ESP_A2D_AUDIO_STATE_STOPPED: Serial.println("Stopped"); break;
      case ESP_A2D_AUDIO_STATE_STARTED: Serial.println("Playing"); break;
      default: Serial.printf("Unknown (0x%x)\n", state); break;
  }
}

void BluetoothManager::setup() {
    // Configure I2S pins for the A2DP Sink
    i2s_pin_config_t my_pin_config = {
        .bck_io_num = I2S_BCLK,
        .ws_io_num = I2S_LRC,
        .data_out_num = I2S_DOUT,
        .data_in_num = I2S_PIN_NO_CHANGE
    };
    a2dp_sink.set_pin_config(my_pin_config);
    
    // Force Mono Output (Mix L+R)
    a2dp_sink.set_mono_downmix(true);

    // Register Callbacks
    a2dp_sink.set_avrc_metadata_callback(avrc_metadata_callback);
    a2dp_sink.set_on_connection_state_changed(connection_state_changed);
    a2dp_sink.set_on_audio_state_changed(audio_state_changed);
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
