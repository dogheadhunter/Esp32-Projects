#include <Arduino.h>
#include "FS.h"
#include "SD.h"
#include "SPI.h"
#include "Audio.h"

// SD Card Pins (Standard VSPI)
#define SD_CS          5
#define SD_MOSI        23
#define SD_MISO        19
#define SD_SCK         18

// I2S Audio Pins (MAX98357A)
#define I2S_DOUT       22
#define I2S_BCLK       26
#define I2S_LRC        25

Audio audio;

// --- Helper Functions from SD Test ---

void listDir(fs::FS &fs, const char * dirname, uint8_t levels){
    Serial.printf("Listing directory: %s\n", dirname);

    File root = fs.open(dirname);
    if(!root){
        Serial.println("Failed to open directory");
        return;
    }
    if(!root.isDirectory()){
        Serial.println("Not a directory");
        return;
    }

    File file = root.openNextFile();
    while(file){
        if(file.isDirectory()){
            Serial.print("  DIR : ");
            Serial.println(file.name());
            if(levels){
                listDir(fs, file.name(), levels -1);
            }
        } else {
            Serial.print("  FILE: ");
            Serial.print(file.name());
            Serial.print("  SIZE: ");
            Serial.println(file.size());
        }
        file = root.openNextFile();
    }
}

void readFile(fs::FS &fs, const char * path){
  Serial.printf("Reading file: %s\n", path);

  File file = fs.open(path);
  if(!file){
    Serial.println("Failed to open file for reading");
    return;
  }

  Serial.print("Read from file: ");
  while(file.available()){
    Serial.write(file.read());
  }
  file.close();
}

void writeFile(fs::FS &fs, const char * path, const char * message){
  Serial.printf("Writing file: %s\n", path);

  File file = fs.open(path, FILE_WRITE);
  if(!file){
    Serial.println("Failed to open file for writing");
    return;
  }
  if(file.print(message)){
    Serial.println("File written");
  } else {
    Serial.println("Write failed");
  }
  file.close();
}

// -------------------------------------

void setup() {
    Serial.begin(115200);
    delay(1000); // Give power a moment to settle
    
    Serial.println("--- Starting SD Card & Audio Test ---");

    // 1. Initialize SD Card
    // Note: We use the default SPI bus, so we don't need to pass SPI instance if using default pins
    if(!SD.begin(SD_CS)){
        Serial.println("Card Mount Failed");
        Serial.println("Check the following:");
        Serial.println("1. Wiring: CS->5, MOSI->23, MISO->19, CLK->18");
        Serial.println("2. Power: Ensure SD module has 3.3V or 5V as required");
        Serial.println("3. Card: Ensure card is inserted and formatted FAT32");
        return;
    }
    
    Serial.println("SD Card mounted successfully.");
    
    // 2. Run Diagnostic Read/Write
    Serial.println("\n--- Running Read/Write Test ---");
    writeFile(SD, "/audio_test.txt", "Audio Test Write Successful!");
    readFile(SD, "/audio_test.txt");
    Serial.println("\n-------------------------------");

    // List files so user can see what's on the card
    listDir(SD, "/", 0);

    // 3. Initialize Audio
    audio.setPinout(I2S_BCLK, I2S_LRC, I2S_DOUT);
    audio.setVolume(15); // 0...21

    // 4. Play File
    // REPLACE "music.mp3" with the actual filename on your SD card!
    // The library supports .mp3, .aac, .wav, .flac
    if(SD.exists("/music.mp3")) {
        audio.connecttoFS(SD, "/music.mp3");
        Serial.println("Playing /music.mp3");
    } else if (SD.exists("/song.mp3")) {
        audio.connecttoFS(SD, "/song.mp3");
        Serial.println("Playing /song.mp3");
    } else {
        Serial.println("Could not find /music.mp3 or /song.mp3");
        
        // Try to find the first MP3 file
        File root = SD.open("/");
        File file = root.openNextFile();
        bool found = false;
        while(file){
            String fileName = String(file.name());
            if(!file.isDirectory() && fileName.endsWith(".mp3")){
                Serial.print("Found mp3: ");
                Serial.println(fileName);
                audio.connecttoFS(SD, fileName.c_str());
                found = true;
                break;
            }
            file = root.openNextFile();
        }
        if (!found) Serial.println("No MP3 files found on root.");
    }
}

void loop() {
    audio.loop();
    
    // Optional: Serial commands to control volume
    if(Serial.available()){
        String r = Serial.readStringUntil('\n');
        r.trim();
        if(r.length() > 0) {
            if(r == "+") {
                int vol = audio.getVolume();
                if(vol < 21) audio.setVolume(vol + 1);
                Serial.printf("Volume: %d\n", audio.getVolume());
            } else if(r == "-") {
                int vol = audio.getVolume();
                if(vol > 0) audio.setVolume(vol - 1);
                Serial.printf("Volume: %d\n", audio.getVolume());
            } else {
                Serial.println("Commands: '+' to increase volume, '-' to decrease.");
            }
        }
    }
}

// Optional: Audio status callbacks
void audio_info(const char *info){
    Serial.print("info        "); Serial.println(info);
}
void audio_eof_mp3(const char *info){  //end of file
    Serial.print("eof_mp3     "); Serial.println(info);
}
