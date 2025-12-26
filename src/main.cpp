// ESP32 SD I2S Music Player - PlatformIO-ready
#include <Arduino.h>
#include <SPI.h>
#include "Audio.h"
#include "SD.h"
#include "FS.h"

// microSD Card Reader connections
#define SD_CS    5
#define SPI_MOSI 23
#define SPI_MISO 19  // CHANGED BACK: Standard Hardware MISO
#define SPI_SCK  18  // CHANGED BACK: Standard Hardware SCK

// I2S Connections
#define I2S_DOUT 22
#define I2S_BCLK 26
#define I2S_LRC  25

Audio audio;
int currentVolume = 10; // Start at volume 10 (0-21)

void setup() {
  Serial.begin(115200);
  delay(1000); // Give the card a moment to power up

  // 1. Setup SD Card
  pinMode(SD_CS, OUTPUT);
  digitalWrite(SD_CS, HIGH); // Ensure CS is high (inactive) before starting

  // Initialize SPI with explicit pins
  SPI.begin(SPI_SCK, SPI_MISO, SPI_MOSI, SD_CS);

  // Start SD with:
  // - Specific CS pin
  // - The SPI instance we just configured
  // - 4MHz frequency (safer for long wires/breadboards)
  if (!SD.begin(SD_CS, SPI, 4000000)) {
    Serial.println("Error accessing microSD card!");
    Serial.println("1. Check MISO (19) and MOSI (23) are not swapped.");
    Serial.println("2. Check CS (5) connection.");
    while (true) delay(1000);
  }
  Serial.println("SD initialized successfully.");

  // 2. Setup Audio
  audio.setPinout(I2S_BCLK, I2S_LRC, I2S_DOUT);
  audio.setVolume(currentVolume);

  // 3. Print Instructions
  Serial.println("\n--- Audio Player Ready ---");
  Serial.println("Enter command:");
  Serial.println(" 'p' = Play / Restart Song");
  Serial.println(" 's' = Stop");
  Serial.println(" ' ' (Space) = Pause / Resume");
  Serial.println(" '+' = Volume Up");
  Serial.println(" '-' = Volume Down");
}

void loop() {
  // 1. Keep audio running (MUST be called frequently)
  audio.loop();

  // 2. Check for Serial Commands
  if (Serial.available()) {
    char cmd = Serial.read();
    
    // Clear any extra newline characters from the buffer
    while(Serial.available() && (Serial.peek() == '\n' || Serial.peek() == '\r')) {
        Serial.read(); 
    }

    switch (cmd) {
      case 'p':
        Serial.println("Command: Play");
        audio.connecttoFS(SD, "/Atom_Bomb_Baby.mp3");
        break;
      
      case 's':
        Serial.println("Command: Stop");
        audio.stopSong();
        break;

      case ' ': // Spacebar
        Serial.println("Command: Pause/Resume");
        audio.pauseResume();
        break;

      case '+':
        if (currentVolume < 21) currentVolume++;
        audio.setVolume(currentVolume);
        Serial.printf("Volume: %d\n", currentVolume);
        break;

      case '-':
        if (currentVolume > 0) currentVolume--;
        audio.setVolume(currentVolume);
        Serial.printf("Volume: %d\n", currentVolume);
        break;
    }
  }
}

// Optional: Library status callbacks (helps debugging)
void audio_info(const char *info){
    Serial.print("info        "); Serial.println(info);
}
void audio_eof_mp3(const char *info){  //end of file
    Serial.print("eof_mp3     "); Serial.println(info);
}