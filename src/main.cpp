#include <Arduino.h>
#include "FS.h"
#include "SD.h"
#include "SPI.h"
#include "AudioFileSourceSD.h"
#include "AudioGeneratorMP3.h"
#include "AudioOutputI2S.h"
#include <vector>
#include "tests/test_runner.h"

// --- CONFIGURATION ---
// Uncomment the line below to run diagnostics instead of the normal player
// #define TEST_MODE 

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
bool shuffleMode = false; // Default to Sequential (PC handles shuffle)
std::vector<int> shuffleOrder; // Stores the shuffled indices
int shufflePosition = 0; // Where we are in the shuffle list

// Volume
int targetVolume = -1; // The volume the user WANTS (from pot)
float currentOutputGain = 0.0; // The actual volume we are outputting
unsigned long lastVolCheck = 0;

// Watchdog
unsigned long lastAudioLoop = 0;

// SD Check
unsigned long lastSDCheck = 0;

// Logging
bool lastPrintWasStatus = false;

void cleanSerialLine() {
    if (lastPrintWasStatus) {
        Serial.println();
        lastPrintWasStatus = false;
    }
}

// Helper to list files with Buffered Writing for Speed
void scanDirectory() {
    cleanSerialLine();
    Serial.println("Scanning SD card (Optimized)...");
    SD.remove("/playlist.m3u");
    File playlistFile = SD.open("/playlist.m3u", FILE_WRITE);
    if (!playlistFile) return;

    // Directories to scan
    const char* dirs[] = { "/", "/music" };
    
    totalSongs = 0;
    String writeBuffer = "";
    writeBuffer.reserve(512); // Pre-allocate memory

    for (int i = 0; i < 2; i++) {
        File root = SD.open(dirs[i]);
        if (!root) continue;

        File entry;
        while (entry = root.openNextFile()) {
            String name = String(entry.name());
            if (!name.startsWith(".") && !entry.isDirectory() && name.endsWith(".mp3")) {
                // Construct full path
                String fullPath = String(dirs[i]);
                if (fullPath == "/") fullPath = ""; // Avoid double slash
                fullPath += "/" + name;

                // Add to buffer
                writeBuffer += fullPath + "\n";
                totalSongs++;

                if (totalSongs % 10 == 0) Serial.print(".");

                // Flush buffer if it gets large
                if (writeBuffer.length() > 500) {
                    playlistFile.print(writeBuffer);
                    writeBuffer = "";
                }
            }
            entry.close();
        }
        root.close();
    }
    
    // Flush remaining buffer
    if (writeBuffer.length() > 0) {
        playlistFile.print(writeBuffer);
    }

    playlistFile.close();
    Serial.printf("Done. Found %d songs.\n", totalSongs);
}

// Fisher-Yates Shuffle Generator
void generateShuffleOrder() {
    Serial.println("Generating new shuffle order...");
    shuffleOrder.clear();
    for (int i = 0; i < totalSongs; i++) {
        shuffleOrder.push_back(i);
    }
    
    // Fisher-Yates Algorithm
    for (int i = totalSongs - 1; i > 0; i--) {
        int j = random(0, i + 1);
        int temp = shuffleOrder[i];
        shuffleOrder[i] = shuffleOrder[j];
        shuffleOrder[j] = temp;
    }
    shufflePosition = 0;
    Serial.println("Shuffle complete.");
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
        // If we haven't generated a shuffle list yet, or we finished it
        if (shuffleOrder.empty() || shufflePosition >= totalSongs) {
            generateShuffleOrder();
        }
        nextIndex = shuffleOrder[shufflePosition];
        shufflePosition++;
    } else {
        nextIndex = (currentSongIndex + 1) % totalSongs;
    }
    
    playSongAtIndex(nextIndex);
}

// --- TEST SUITE IMPLEMENTATION ---
#ifdef TEST_MODE

void setup() {
    Serial.begin(115200);
    delay(2000);
    Serial.println("=== DIAGNOSTIC MODE (ROUND 3) ===");
    
    // Init Hardware
    pinMode(I2S_BCLK, OUTPUT); digitalWrite(I2S_BCLK, LOW);
    pinMode(I2S_LRC, OUTPUT); digitalWrite(I2S_LRC, LOW);
    pinMode(I2S_DOUT, OUTPUT); digitalWrite(I2S_DOUT, LOW);
    
    if (!SD.begin(SD_CS, SPI, 20000000)) {
        Serial.println("SD Fail - Cannot run tests"); return;
    }

    // Init Audio Objects for Testing
    out = new AudioOutputI2S();
    out->SetPinout(I2S_BCLK, I2S_LRC, I2S_DOUT);
    mp3 = new AudioGeneratorMP3();
    
    // Run All Tests from Suite
    runAllTests();
}

void loop() {
    // Do nothing in test mode
}

#else 

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
        
        // Soft Start: Set target, but keep actual gain at 0.0 initially
        targetVolume = startGain * 100;
        out->SetGain(0.0); 
        currentOutputGain = 0.0;
        
        Serial.printf("Initial Target Volume: %d%%\n", targetVolume);
        
        randomSeed(analogRead(POT_PIN) + millis());
        playNextSong();
    } else {
        Serial.println("SD Mount Failed!");
    }
}

void loop() {
    // 1. Watchdog & Audio Loop
    if (mp3->isRunning()) {
        if (!mp3->loop()) {
            mp3->stop();
            cleanSerialLine();
            Serial.println("Song finished.");
            playNextSong();
        } else {
            lastAudioLoop = millis(); // Update timestamp on success
        }
    } else {
        lastAudioLoop = millis(); // Reset watchdog when not running
    }

    // Watchdog Check (2 seconds timeout)
    if (mp3->isRunning() && (millis() - lastAudioLoop > 2000)) {
        cleanSerialLine();
        Serial.println("Error: Decoder stuck! Skipping song...");
        mp3->stop();
        playNextSong();
        lastAudioLoop = millis();
    }

    // 2. SD Card Removal Check - REMOVED (Too slow, causes audio stutter)
    // The decoder will naturally fail if the card is removed.
    /* 
    if (millis() - lastSDCheck > 1000) {
        lastSDCheck = millis();
        if (!SD.exists("/playlist.m3u")) {
             // ...
        }
    }
    */

    // 3. Volume Control (Input Smoothing)
    if (millis() - lastVolCheck > 50) { 
        lastVolCheck = millis();
        
        long sum = 0;
        // Reduced oversampling from 16 to 4 to prevent blocking (4 * ~1ms = 4ms)
        for (int i = 0; i < 4; i++) sum += analogRead(POT_PIN);
        int avgRaw = sum / 4;
        int newVol = map(avgRaw, 0, 4095, 0, 100);
        
        // Spike Protection: Limit sudden jumps > 10%
        if (targetVolume != -1) { // If initialized
            int diff = newVol - targetVolume;
            if (abs(diff) > 10) {
                // Clamp change to 2 steps
                newVol = targetVolume + (diff > 0 ? 2 : -2);
            }
        }

        // Hysteresis: Only update target if change is > 1%
        if (abs(newVol - targetVolume) > 1) {
            targetVolume = newVol;
            // We do NOT set out->SetGain here anymore. 
            // We let the Soft Start logic handle the actual change.
        }
    }

    // 4. Soft Start / Volume Ramping (Output Smoothing)
    // Smoothly move currentOutputGain towards targetVolume
    float targetGain = targetVolume / 100.0;
    if (abs(currentOutputGain - targetGain) > 0.005) {
        if (currentOutputGain < targetGain) currentOutputGain += 0.005;
        else currentOutputGain -= 0.005;
        
        out->SetGain(currentOutputGain);
        
        // Only print if significant change to avoid spam
        static int lastPrintedVol = -1;
        int currentVolInt = currentOutputGain * 100;
        if (abs(currentVolInt - lastPrintedVol) > 2) {
            cleanSerialLine();
            // Serial.printf("Volume: %d%%\n", currentVolInt); // Optional debug
            lastPrintedVol = currentVolInt;
        }
    }

    // Status Display
    static unsigned long lastStatusPrint = 0;
    if (mp3->isRunning() && millis() - lastStatusPrint > 1000) {
        lastStatusPrint = millis();
        Serial.printf("\r[PLAYING] %d/%d | Vol: %d%% | Heap: %d | Up: %lu s   ",
            currentSongIndex + 1,
            totalSongs,
            (int)(currentOutputGain * 100), // Show actual output volume
            ESP.getFreeHeap(), 
            millis() / 1000);
        lastPrintWasStatus = true;
    }
}

#endif
