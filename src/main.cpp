#include <Arduino.h>
#include "FS.h"
#include "SD.h"
#include "SPI.h"
#include "AudioFileSourceSD.h"
#include "AudioGeneratorMP3.h"
#include "AudioOutputI2S.h"
#include <vector>

// SD Card Pins (Standard VSPI)
#define SD_CS          5
#define SD_MOSI        23
#define SD_MISO        19
#define SD_SCK         18

// I2S Audio Pins (MAX98357A)
#define I2S_DOUT       22
#define I2S_BCLK       26
#define I2S_LRC        25

// Potentiometer Pin (Sensor VN = GPIO 39)
#define POT_PIN        39

// LED Indicator
#define LED_PIN        2

AudioGeneratorMP3 *mp3;
AudioFileSourceSD *file;
AudioOutputI2S *out;

// Playlist
int totalSongs = 0;
int currentSongIndex = -1;
bool shuffleMode = false; 

// Volume
int lastVolume = -1;
unsigned long lastVolCheck = 0;

// Logging
bool lastPrintWasStatus = false;

void cleanSerialLine() {
    if (lastPrintWasStatus) {
        Serial.println();
        lastPrintWasStatus = false;
    }
}

// Helper to list files
void scanDirectory() {
    cleanSerialLine();
    Serial.println("Scanning SD card for MP3 files...");
    SD.remove("/playlist.m3u");
    File playlistFile = SD.open("/playlist.m3u", FILE_WRITE);
    if (!playlistFile) return;

    File root = SD.open("/");
    if (!root) { playlistFile.close(); return; }
    
    totalSongs = 0;
    File entry;
    while (entry = root.openNextFile()) {
        String name = String(entry.name());
        if (!name.startsWith(".") && !entry.isDirectory() && name.endsWith(".mp3")) {
            if (!name.startsWith("/")) name = "/" + name;
            playlistFile.println(name);
            totalSongs++;
            if (totalSongs % 10 == 0) Serial.print(".");
        }
        entry.close();
    }
    root.close();
    playlistFile.close();
    Serial.println();
    Serial.printf("Found %d songs.\n", totalSongs);
}

// Verify playlist integrity using Reservoir Sampling
int checkPlaylist() {
    if (!SD.exists("/playlist.m3u")) return -1;
    File f = SD.open("/playlist.m3u");
    if (!f) return -1;

    String candidates[10];
    int count = 0;

    // Reservoir Sampling: Pick 10 random lines in one pass
    while (f.available()) {
        String line = f.readStringUntil('\n');
        line.trim();
        if (line.length() > 0) {
            if (count < 10) {
                candidates[count] = line;
            } else {
                int j = random(0, count + 1);
                if (j < 10) {
                    candidates[j] = line;
                }
            }
            count++;
        }
    }
    f.close();

    if (count == 0) return -1;

    // Verify the selected candidates exist
    int checks = (count < 10) ? count : 10;
    Serial.printf("Verifying playlist (%d songs)... checking %d random entries.\n", count, checks);
    
    for (int i = 0; i < checks; i++) {
        if (!SD.exists(candidates[i])) {
            Serial.printf("Validation failed. Missing: %s\n", candidates[i].c_str());
            return -1;
        }
    }
    
    Serial.println("Playlist valid.");
    return count;
}

String getSongPath(int index) {
    if (index < 0 || index >= totalSongs) return "";
    File f = SD.open("/playlist.m3u");
    if (!f) return "";
    int current = 0;
    String path = "";
    while (f.available()) {
        String line = f.readStringUntil('\n');
        line.trim();
        if (line.length() > 0) {
            if (current == index) { path = line; break; }
            current++;
        }
    }
    f.close();
    return path;
}

void playSongAtIndex(int index) {
    if (index < 0 || index >= totalSongs) return;
    currentSongIndex = index;
    String path = getSongPath(index);
    
    cleanSerialLine();
    Serial.printf("Playing [%d/%d]: %s\n", index + 1, totalSongs, path.c_str());
    
    if (mp3->isRunning()) mp3->stop();
    if (file) delete file;
    file = new AudioFileSourceSD(path.c_str());
    mp3->begin(file, out);
}

void playNextSong() {
    if (totalSongs == 0) return;
    int nextIndex;
    if (shuffleMode) {
        nextIndex = random(0, totalSongs);
        if (totalSongs > 1 && nextIndex == currentSongIndex) nextIndex = (nextIndex + 1) % totalSongs;
    } else {
        nextIndex = (currentSongIndex + 1) % totalSongs;
    }
    playSongAtIndex(nextIndex);
}

void setup() {
    Serial.begin(115200);
    delay(1000);
    Serial.println("\n\n========================================");
    Serial.println("       ESP32 Simple Player (No WiFi)");
    Serial.println("========================================");
    
    // Anti-pop: Pull I2S pins low immediately
    pinMode(I2S_BCLK, OUTPUT); digitalWrite(I2S_BCLK, LOW);
    pinMode(I2S_LRC, OUTPUT); digitalWrite(I2S_LRC, LOW);
    pinMode(I2S_DOUT, OUTPUT); digitalWrite(I2S_DOUT, LOW);

    // SD Setup
    if (SD.begin(SD_CS, SPI, 20000000)) {
        Serial.println("SD Mounted");
        
        // Seed random for reservoir sampling check
        randomSeed(analogRead(POT_PIN) + millis());

        // Check if playlist matches current SD card content
        int validCount = checkPlaylist();
        if (validCount > 0) {
            totalSongs = validCount;
        } else {
            scanDirectory();
        }
        
        // I2S Setup - Initialize AFTER SD work to prevent buzzing
        out = new AudioOutputI2S();
        out->SetPinout(I2S_BCLK, I2S_LRC, I2S_DOUT);
        out->SetOutputModeMono(true);
        out->SetGain(0.0); // Start muted
        mp3 = new AudioGeneratorMP3();
        
        // Initial Volume
        long sum = 0;
        for (int i = 0; i < 10; i++) { sum += analogRead(POT_PIN); delay(2); }
        float startGain = map(sum / 10, 0, 4095, 0, 100) / 100.0;
        out->SetGain(startGain);
        lastVolume = startGain * 100;
        Serial.printf("Initial Volume: %d%%\n", lastVolume);
        
        randomSeed(analogRead(POT_PIN) + millis());
        playNextSong();
    } else {
        Serial.println("SD Mount Failed!");
    }
}

void loop() {
    if (mp3->isRunning()) {
        if (!mp3->loop()) {
            mp3->stop();
            cleanSerialLine();
            Serial.println("Song finished.");
            playNextSong();
        }
    }

    // Volume Control
    if (millis() - lastVolCheck > 50) { // Check more often (50ms) but filter heavily
        lastVolCheck = millis();
        
        long sum = 0;
        for (int i = 0; i < 16; i++) sum += analogRead(POT_PIN);
        int avgRaw = sum / 16;
        
        // Map to 0-100
        int newVol = map(avgRaw, 0, 4095, 0, 100);
        
        // Hysteresis: Only update if change is > 1% (prevents 50 <-> 51 flickering)
        // This effectively reduces resolution to 2% steps, which is stable.
        if (abs(newVol - lastVolume) > 1) {
            lastVolume = newVol;
            out->SetGain(lastVolume / 100.0);
            cleanSerialLine();
            Serial.printf("Volume Changed: %d%%\n", lastVolume);
        }
    }

    // Status Display
    static unsigned long lastStatusPrint = 0;
    if (mp3->isRunning() && millis() - lastStatusPrint > 1000) {
        lastStatusPrint = millis();
        Serial.printf("\r[PLAYING] %d/%d | Vol: %d%% | Heap: %d | Up: %lu s   ",
            currentSongIndex + 1,
            totalSongs,
            lastVolume,
            ESP.getFreeHeap(), 
            millis() / 1000);
        lastPrintWasStatus = true;
    }
}
