#include <Arduino.h>
#include "Audio.h"
#include "FS.h"
#include "LittleFS.h"

// I2S Connections
#define I2S_DOUT 22
#define I2S_BCLK 26
#define I2S_LRC  25

Audio audio;
int currentVolume = 10;

// --- DEBUG CALLBACKS ---
void audio_info(const char *info){
    Serial.print("info        "); Serial.println(info);
}
void audio_bitrate(const char *info){
    Serial.print("bitrate     "); Serial.println(info);
}
// -----------------------

void setup() {
  Serial.begin(115200);
  delay(1000);

  // 1. Initialize Internal File System
  // true = format if failed (cleans up corruption)
  if (!LittleFS.begin(true)) {
    Serial.println("An Error has occurred while mounting LittleFS");
    return;
  }
  Serial.println("LittleFS mounted successfully.");

  // Check if file exists
  if(LittleFS.exists("/Atom_Bomb_Baby.mp3")){
    Serial.println("File found!");
  } else {
    Serial.println("File NOT found! Did you run 'Upload Filesystem Image'?");
    // List all files to be helpful
    File root = LittleFS.open("/");
    File file = root.openNextFile();
    while(file){
        Serial.print("FILE: ");
        Serial.println(file.name());
        file = root.openNextFile();
    }
  }

  // 2. Setup Audio
  audio.setPinout(I2S_BCLK, I2S_LRC, I2S_DOUT);
  audio.setVolume(currentVolume);

  Serial.println("\n--- Internal Flash Player Ready ---");
  Serial.println("Press 'p' to play.");
}

void loop() {
  audio.loop();

  if (Serial.available()) {
    char cmd = Serial.read();
    // Clear buffer
    while(Serial.available() && (Serial.peek() == '\n' || Serial.peek() == '\r')) Serial.read(); 

    switch (cmd) {
      case 'p':
        Serial.println("Playing from Internal Flash...");
        audio.connecttoFS(LittleFS, "/Atom_Bomb_Baby.mp3");
        break;
      case 's':
        audio.stopSong();
        break;
      case '+':
      case '=':
        if (currentVolume < 21) currentVolume++;
        audio.setVolume(currentVolume);
        Serial.printf("Volume Up: %d\n", currentVolume);
        break;
      case '-':
      case '_':
        if (currentVolume > 0) currentVolume--;
        audio.setVolume(currentVolume);
        Serial.printf("Volume Down: %d\n", currentVolume);
        break;
    }
  }
}
