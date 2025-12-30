#include <Arduino.h>
#include "FS.h"
#include "SD.h"
#include "SPI.h"
// #include "Audio.h" // REMOVED: Old Library
#include "AudioFileSourceSD.h"
#include "AudioGeneratorMP3.h"
#include "AudioOutputI2S.h"
#include "AudioFileSourceID3.h" // Optional: For ID3 tags

#include <vector>
#include <algorithm> // For std::sort
#include <Preferences.h> // For saving mode across reboots
#include "WifiTime.h" // WiFi Time Module
#include "BluetoothManager.h" // Bluetooth Manager
#include <WiFiManager.h> // ADDED: Required for WiFiManager
#include <OneButton.h> // ADDED: For advanced button handling

Preferences prefs;
int bootMode = 0; // 0 = SD, 1 = Bluetooth

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

// Button Pins
#define BTN_PLAY_PAUSE 27
#define BTN_NEXT       14
#define BTN_PREV       13
#define BTN_SHUFFLE    32  // New Shuffle Button

// LED Indicator
#define LED_PIN        2

// Audio audio; // REMOVED
AudioGeneratorMP3 *mp3;
AudioFileSourceSD *file;
AudioOutputI2S *out;
AudioFileSourceID3 *id3;

OneButton btnOne(BTN_PLAY_PAUSE, true, true); // Active Low, Enable Internal Pullup
OneButton btnTwo(BTN_NEXT, true, true);       // Button 2: WiFi Reset
OneButton btnThree(BTN_PREV, true, true);     // Button 3: Mode Switch

// --- State Machine ---
enum PlayerState {
    STATE_NO_CARD,
    STATE_IDLE,
    STATE_PLAYING,
    STATE_PAUSED,
    STATE_OFF,
    STATE_BLUETOOTH
};
PlayerState currentState = STATE_NO_CARD;

// --- Playlist Management ---
int totalSongs = 0;
int currentSongIndex = -1;
bool shuffleMode = true; // Default to shuffle mode on startup

// --- Flags ---
bool shouldPlayNext = false;
bool cardMounted = false;

// --- Volume ---
int lastVolume = -1;
unsigned long lastVolCheck = 0;

// --- Button Debouncing ---
unsigned long lastDebounceTime = 0;
const unsigned long debounceDelay = 250;

// Play/Pause Long Press Detection
int lastPlayPauseState = HIGH;
unsigned long playPausePressStartTime = 0;
bool playPauseLongPressHandled = false;
const unsigned long longPressDuration = 1500; // 1.5 sec for power off

// Button States
int lastPrevState = HIGH;
int lastShuffleState = HIGH;
unsigned long shufflePressStartTime = 0;
bool shuffleLongPressHandled = false;

// --- SD Card Detection ---
unsigned long lastCardCheck = 0;
const unsigned long cardCheckInterval = 2000; // Check every 2 seconds

// --- LED Blinking ---
unsigned long lastLedBlink = 0;
bool ledState = false;

// --- Serial Monitor Formatting ---
bool lastPrintWasStatus = false;

// ============================================
// HELPER FUNCTIONS
// ============================================

void cleanSerialLine() {
    if (lastPrintWasStatus) {
        Serial.println(); // Move to next line if we were printing status
        lastPrintWasStatus = false;
    }
}

void blinkLED(int times, int delayMs) {
    for (int i = 0; i < times; i++) {
        digitalWrite(LED_PIN, HIGH);
        delay(delayMs);
        digitalWrite(LED_PIN, LOW);
        delay(delayMs);
    }
}

void setLED(bool on) {
    digitalWrite(LED_PIN, on ? HIGH : LOW);
}

// Load playlist from file (Just count lines)
bool loadPlaylistCache() {
    if (!SD.exists("/playlist.m3u")) return false;
    
    cleanSerialLine();
    Serial.println("Loading playlist from cache...");
    File f = SD.open("/playlist.m3u");
    if (!f) return false;

    totalSongs = 0;
    while (f.available()) {
        String line = f.readStringUntil('\n');
        line.trim();
        if (line.length() > 0) {
            totalSongs++;
        }
    }
    f.close();
    
    if (totalSongs > 0) {
        Serial.printf("Found %d songs in cache.\n", totalSongs);
        return true;
    }
    return false;
}

// Scan directory for MP3s and write to file
void scanDirectory() {
    cleanSerialLine();
    Serial.println("Scanning SD card for MP3 files...");
    
    // Delete old cache
    SD.remove("/playlist.m3u");
    File playlistFile = SD.open("/playlist.m3u", FILE_WRITE);
    if (!playlistFile) {
        Serial.println("Failed to create playlist file!");
        return;
    }

    File root = SD.open("/");
    if (!root) {
        Serial.println("Failed to open root directory!");
        playlistFile.close();
        return;
    }
    
    totalSongs = 0;
    File entry;
    while (entry = root.openNextFile()) {
        yield(); // Prevent watchdog timeout
        
        String name = String(entry.name());
        if (!name.startsWith(".")) {
            if (!entry.isDirectory() && name.endsWith(".mp3")) {
                if (!name.startsWith("/")) name = "/" + name;
                playlistFile.println(name);
                totalSongs++;
                if (totalSongs % 10 == 0) Serial.print(".");
            }
        }
        entry.close();
    }
    root.close();
    playlistFile.close();
    
    Serial.printf("\nScan complete. Found %d songs.\n", totalSongs);
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
            if (current == index) {
                path = line;
                break;
            }
            current++;
        }
    }
    f.close();
    return path;
}

void fadeOut() {
    float startVol = lastVolume / 100.0;
    for (float v = startVol; v >= 0; v -= 0.05) {
        out->SetGain(v);
        unsigned long start = millis();
        while (millis() - start < 15) {
            if (mp3->isRunning()) mp3->loop();
        }
    }
    out->SetGain(0);
}

void fadeIn(int targetVol) {
    float target = targetVol / 100.0;
    for (float v = 0; v <= target; v += 0.05) {
        out->SetGain(v);
        unsigned long start = millis();
        while (millis() - start < 20) {
            if (mp3->isRunning()) mp3->loop();
        }
    }
}

// ============================================
// CARD MANAGEMENT
// ============================================

bool mountSDCard() {
    // RESEARCH FIX: 
    // Try 20MHz. 10MHz might be too slow, causing buffer underruns if the card has high latency.
    // If this fails, we can try dropping to 10MHz or even 4MHz.
    if (SD.begin(SD_CS, SPI, 20000000)) {
        cleanSerialLine();
        Serial.println("SD Card mounted.");
        Serial.printf("SD Card Type: %d\n", SD.cardType());
        Serial.printf("SD Card Size: %llu MB\n", SD.cardSize() / (1024 * 1024));
        
        // Check if user wants to force rescan (holding SHUFFLE button)
        if (digitalRead(BTN_SHUFFLE) == LOW) {
            Serial.println("Force Rescan requested.");
            SD.remove("/playlist.m3u");
            blinkLED(5, 50);
        }

        // Try to load cache, otherwise scan
        if (!loadPlaylistCache()) {
            scanDirectory();
        }
        
        Serial.printf("Total Songs: %d\n", totalSongs);
        
        // Seed random
        randomSeed(analogRead(POT_PIN) + millis());
        
        cardMounted = true;
        return true;
    }
    return false;
}

void unmountSDCard() {
    if (mp3->isRunning()) mp3->stop();
    SD.end();
    cardMounted = false;
    currentState = STATE_NO_CARD;
    totalSongs = 0;
    currentSongIndex = -1;
    cleanSerialLine();
    Serial.println("SD Card unmounted.");
}

bool checkCardPresent() {
    // Simple check without opening a file to avoid interrupting playback
    return SD.totalBytes() > 0;
}

// ============================================
// PLAYBACK CONTROL
// ============================================

void playSongAtIndex(int index) {
    if (index < 0 || index >= totalSongs) return;
    
    currentSongIndex = index;
    String path = getSongPath(index);
    
    if (path == "") {
        Serial.println("Error: Could not retrieve song path.");
        return;
    }
    
    cleanSerialLine();
    Serial.printf("Playing [%d/%d]: %s\n", index + 1, totalSongs, path.c_str());
    
    if (mp3->isRunning()) mp3->stop();
    
    // Create new file source
    if (file) delete file;
    file = new AudioFileSourceSD(path.c_str());
    
    // Optional: ID3
    // if (id3) delete id3;
    // id3 = new AudioFileSourceID3(file);
    
    mp3->begin(file, out);
    
    // Re-apply volume to ensure it persists across tracks
    out->SetGain(lastVolume / 100.0);
    
    currentState = STATE_PLAYING;
}

void playNextSong() {
    if (totalSongs == 0) return;
    
    int nextIndex;
    if (shuffleMode) {
        // Pick random index
        nextIndex = random(0, totalSongs);
        // Avoid repeating same song if possible
        if (totalSongs > 1 && nextIndex == currentSongIndex) {
            nextIndex = (nextIndex + 1) % totalSongs;
        }
    } else {
        // Sequential
        nextIndex = (currentSongIndex + 1) % totalSongs;
    }
    
    playSongAtIndex(nextIndex);
}

void playPreviousSong() {
    if (totalSongs == 0) return;
    
    // If more than 3 seconds in, restart current song (Approximate check)
    // ESP8266Audio doesn't have a simple "getAudioCurrentTime" like the other lib
    // So we just always go to previous for now, or we could track start time manually.
    int prevIndex = currentSongIndex - 1;
    if (prevIndex < 0) prevIndex = totalSongs - 1;
    playSongAtIndex(prevIndex);
}

void togglePause() {
    if (currentState == STATE_PLAYING) {
        currentState = STATE_PAUSED;
        cleanSerialLine();
        Serial.println("Paused");
        blinkLED(2, 100);
    } else if (currentState == STATE_PAUSED) {
        currentState = STATE_PLAYING;
        cleanSerialLine();
        Serial.println("Resumed");
    }
}

void powerOff() {
    cleanSerialLine();
    Serial.println("Powering off...");
    fadeOut();
    mp3->stop();
    currentState = STATE_OFF;
    setLED(false);
    blinkLED(3, 200);
}

void powerOn() {
    cleanSerialLine();
    Serial.println("Powering on...");
    blinkLED(2, 100);
    
    if (!cardMounted) {
        if (mountSDCard()) {
            currentState = STATE_IDLE;
        } else {
            currentState = STATE_NO_CARD;
            return;
        }
    } else {
        currentState = STATE_IDLE;
    }
    playNextSong();
}

void toggleShuffle() {
    shuffleMode = !shuffleMode;
    cleanSerialLine();
    Serial.printf("Shuffle: %s\n", shuffleMode ? "ON" : "OFF");
    if (shuffleMode) blinkLED(3, 75);
    else blinkLED(1, 300);
}

void enterBluetoothMode() {
    cleanSerialLine();
    Serial.println("Switching to Bluetooth Mode (Rebooting)...");
    
    prefs.begin("player", false); // Read/Write
    prefs.putInt("mode", 1);
    prefs.end();
    
    blinkLED(3, 100);
    delay(500);
    ESP.restart();
}

void exitBluetoothMode() {
    cleanSerialLine();
    Serial.println("Exiting Bluetooth Mode (Rebooting)...");
    
    prefs.begin("player", false); // Read/Write
    prefs.putInt("mode", 0);
    prefs.end();
    
    blinkLED(3, 100);
    delay(500);
    ESP.restart();
}

// ============================================
// BUTTON CALLBACKS
// ============================================

void click1() {
    Serial.println("Button 1: Single Click (Play/Pause)");
    if (currentState == STATE_OFF) powerOn();
    else if (currentState == STATE_NO_CARD) { if (mountSDCard()) playNextSong(); }
    else if (currentState == STATE_IDLE) playNextSong();
    else togglePause();
}

void click2() {
    Serial.println("Button 1: Double Click (Next)");
    if (currentState == STATE_PLAYING || currentState == STATE_PAUSED) {
        cleanSerialLine();
        Serial.println("Next track...");
        fadeOut();
        mp3->stop();
        playNextSong();
    }
}

void clickMulti() {
    int n = btnOne.getNumberClicks();
    Serial.printf("Button 1: Multi Click (%d)\n", n);
    
    // Only handle 3+ clicks here if click1/click2 are attached separately
    if (n == 3) {
        Serial.println("Action: Prev Song");
        if (currentState == STATE_PLAYING || currentState == STATE_PAUSED) {
            fadeOut();
            playPreviousSong();
            if (lastVolume >= 0) fadeIn(lastVolume);
        }
    }
}

void longPressStart() {
    Serial.println("Button 1: Long Press (Toggle Shuffle)");
    toggleShuffle();
}

void clickBtnTwo() {
    Serial.println("Button 2: Resetting WiFi Settings...");
    WiFiManager wm;
    wm.resetSettings();
    blinkLED(5, 100);
    Serial.println("WiFi settings erased. Rebooting to Setup Mode...");
    delay(1000);
    ESP.restart();
}

void clickBtnThree() {
    Serial.println("Button 3: Switching Mode...");
    prefs.begin("player", false);
    int currentMode = prefs.getInt("mode", 0);
    int newMode = (currentMode == 0) ? 1 : 0; // Toggle 0 <-> 1
    prefs.putInt("mode", newMode);
    prefs.end();
    
    Serial.printf("Switching to %s Mode\n", newMode == 1 ? "BLUETOOTH" : "SD CARD");
    blinkLED(3, 100);
    delay(500);
    ESP.restart();
}

// ============================================
// SETUP
// ============================================

void setup() {
  // 1. Setup Serial
  Serial.begin(115200);
  delay(1000); // Give serial monitor time to catch up
  Serial.println("\n\n========================================");
  Serial.println("       ESP32 iPod Shuffle Clone");
  Serial.println("========================================");

  // 2. Initialize Buttons
  // (Handled by OneButton, but we can set pin modes if needed, though OneButton does it)

  // 4. Initialize SD Card
    // Anti-pop
    pinMode(I2S_BCLK, OUTPUT); digitalWrite(I2S_BCLK, LOW);
    pinMode(I2S_LRC, OUTPUT); digitalWrite(I2S_LRC, LOW);
    pinMode(I2S_DOUT, OUTPUT); digitalWrite(I2S_DOUT, LOW);
    
    pinMode(LED_PIN, OUTPUT); digitalWrite(LED_PIN, LOW);
    
    // OneButton Setup
    // We use explicit handlers for 1 and 2 clicks for better reliability
    btnOne.attachClick(click1);
    btnOne.attachDoubleClick(click2);
    btnOne.attachMultiClick(clickMulti); // Handles 3+ clicks
    btnOne.attachLongPressStart(longPressStart);
    btnOne.setClickTicks(400); // Make it snappier (default 600ms)
    
    btnTwo.attachClick(clickBtnTwo);
    btnThree.attachClick(clickBtnThree);
    
    // Legacy Buttons
    pinMode(BTN_SHUFFLE, INPUT_PULLUP);
    
    Serial.begin(115200);
    delay(500);
    
    Serial.println("\n========================================");
    Serial.println("       ESP32 iPod Shuffle Clone");
    Serial.println("========================================");
    
    Serial.printf("Chip Model: %s\n", ESP.getChipModel());
    Serial.printf("Chip Revision: %d\n", ESP.getChipRevision());
    Serial.printf("CPU Freq: %d MHz\n", ESP.getCpuFreqMHz());
    Serial.printf("Flash Size: %d MB\n", ESP.getFlashChipSize() / (1024 * 1024));
    Serial.printf("Free Heap: %d bytes\n", ESP.getFreeHeap());
    Serial.printf("SDK Version: %s\n", ESP.getSdkVersion());
    Serial.println("========================================\n");
    
    // Check Boot Mode
    prefs.begin("player", true); // Read Only
    bootMode = prefs.getInt("mode", 0);
    prefs.end();
    
    if (bootMode == 1) {
        Serial.println(">> Booting into BLUETOOTH MODE <<");
        
        // Ensure I2S drivers are clean before starting
        // This prevents "register I2S object failed" errors if the hardware is in a weird state
        i2s_driver_uninstall(I2S_NUM_0);
        
        currentState = STATE_BLUETOOTH;
        btManager.setup();
        btManager.start("ESP32-iPod");
        blinkLED(3, 100);
        return; // Skip SD setup
    }
    
    Serial.println(">> Booting into SD CARD MODE <<");
    
    // Check if user wants to reset WiFi settings (Hold BUTTON 2 on boot)
    bool resetWifi = false;
    if (digitalRead(BTN_NEXT) == LOW) {
        Serial.println("Reset WiFi requested!");
        blinkLED(5, 50);
        resetWifi = true;
    }

    // Sync time via WiFi (defined in src/WifiTime.cpp)
    syncTimeWithNTP(resetWifi);
    delay(2000); // Increased wait for power stabilization

    // Initialize ESP8266Audio Objects
    out = new AudioOutputI2S();
    out->SetPinout(I2S_BCLK, I2S_LRC, I2S_DOUT);
    out->SetGain(0.0); // Start muted
    out->SetOutputModeMono(true); // Force Mono
    
    mp3 = new AudioGeneratorMP3();

    // Initialize Volume from Potentiometer
    long sum = 0;
    for (int i = 0; i < 10; i++) { sum += analogRead(POT_PIN); delay(2); }
    int potValue = sum / 10;
    float startGain = map(potValue, 0, 4095, 0, 100) / 100.0;
    lastVolume = startGain * 100;
    out->SetGain(startGain);
    Serial.printf("Initial Volume: %.2f\n", startGain);
    
    if (mountSDCard()) {
        currentState = STATE_IDLE;
        blinkLED(2, 150);
        delay(500);
        playNextSong();
    } else {
        Serial.println("No SD card detected.");
        currentState = STATE_NO_CARD;
    }
}

// ============================================
// MAIN LOOP
// ============================================

void loop() {
    // === BUTTONS (Check First) ===
    // OneButton Tick - Must be called frequently
    btnOne.tick();
    btnTwo.tick();
    btnThree.tick();

    // === BLUETOOTH MODE LOOP ===
    if (bootMode == 1) {
        btManager.loop();
        
        // Check Shuffle Button for Long Press to Switch Back
        int currentShuffleState = digitalRead(BTN_SHUFFLE);
        if (lastShuffleState == HIGH && currentShuffleState == LOW) {
            shufflePressStartTime = millis();
            shuffleLongPressHandled = false;
        }
        if (currentShuffleState == LOW && !shuffleLongPressHandled) {
            if (millis() - shufflePressStartTime > 2000) { // 2 seconds
                shuffleLongPressHandled = true;
                exitBluetoothMode(); // Will reboot
            }
        }
        lastShuffleState = currentShuffleState;
        
        // LED Status for Bluetooth
        if (millis() - lastLedBlink > 200) { 
            lastLedBlink = millis();
            ledState = !ledState;
            setLED(ledState);
        }
        
        // Status Print
        static unsigned long lastStatusPrint = 0;
        if (millis() - lastStatusPrint > 1000) {
            lastStatusPrint = millis();
            Serial.printf("\r[BLUETOOTH] %s   ", btManager.isConnected() ? "Connected" : "Waiting...");
        }
        return; // Skip the rest of the loop
    }

    // === SD CARD MODE LOOP ===
    if (mp3->isRunning()) {
        if (currentState != STATE_PAUSED) {
            if (!mp3->loop()) {
                mp3->stop();
                shouldPlayNext = true;
                Serial.println("Song finished.");
            }
        }
    }
    
    if (shouldPlayNext) {
            shouldPlayNext = false;
            delay(100);
            playNextSong();
        }
        
        // --- SD Card Hot-Swap ---
        if (millis() - lastCardCheck > cardCheckInterval) {
            lastCardCheck = millis();
            
            // Only check if card is present, don't try to remount unless explicitly failed
            // Skip check if playing to avoid SPI conflict/glitches
            if (cardMounted && currentState != STATE_PLAYING && !checkCardPresent()) {
                cleanSerialLine();
                Serial.println("SD Card removed!");
                unmountSDCard();
                blinkLED(5, 100);
            } else if (!cardMounted) {
                if (mountSDCard()) {
                    cleanSerialLine();
                    Serial.println("SD Card inserted!");
                    currentState = STATE_IDLE;
                    blinkLED(2, 150);
                    delay(500);
                    playNextSong();
                }
            }
        }
    
    // --- LED Status ---
    if (currentState == STATE_NO_CARD) {
        if (millis() - lastLedBlink > 1000) {
            lastLedBlink = millis();
            ledState = !ledState;
            setLED(ledState);
        }
    } else if (currentState == STATE_PLAYING) {
        setLED(true);
    } else if (currentState == STATE_PAUSED) {
        if (millis() - lastLedBlink > 500) {
            lastLedBlink = millis();
            ledState = !ledState;
            setLED(ledState);
        }
    } else if (currentState == STATE_OFF) {
        setLED(false);
    }
    
    // === BUTTONS ===
    // Moved to top of loop for better responsiveness
    
    // Shuffle Button (Dedicated) - Short Press: Toggle Shuffle, Long Press: Toggle Bluetooth
    int currentShuffleState = digitalRead(BTN_SHUFFLE);
    
    if (lastShuffleState == HIGH && currentShuffleState == LOW) {
        shufflePressStartTime = millis();
        shuffleLongPressHandled = false;
    }
    
    if (currentShuffleState == LOW && !shuffleLongPressHandled) {
        if (millis() - shufflePressStartTime > 2000) { // 2 seconds
            shuffleLongPressHandled = true;
            enterBluetoothMode(); // Will reboot
        }
    }
    
    if (lastShuffleState == LOW && currentShuffleState == HIGH) {
        if (!shuffleLongPressHandled && (millis() - shufflePressStartTime > 50)) {
             // Short press action
             toggleShuffle();
        }
    }
    lastShuffleState = currentShuffleState;
    
    // Prev (Simple Press)
    // REMOVED: Handled by Button 1 Triple Click
    
    // Next
    // REMOVED: Handled by Button 1 Double Click
    
    // Volume
    if (millis() - lastVolCheck > 100) {
        lastVolCheck = millis();
        long sum = 0;
        for (int i = 0; i < 4; i++) { sum += analogRead(POT_PIN); } // Reduced samples to 4, removed delay
        int potValue = sum / 4;
        // Map to 0.0 - 1.0 for SetGain
        float newGain = map(potValue, 0, 4095, 0, 100) / 100.0;
        // Simple check to avoid spamming I2C
        if (abs(newGain - (lastVolume/100.0)) > 0.02) {
            out->SetGain(newGain);
            lastVolume = newGain * 100;
            cleanSerialLine();
            Serial.printf("Volume: %.2f\n", newGain);
        }
    }
    
    // === STATUS DISPLAY (Single Line) ===
    static unsigned long lastStatusPrint = 0;
    if (currentState == STATE_PLAYING && millis() - lastStatusPrint > 1000) {
        lastStatusPrint = millis();
        
        // DEBUG: Time function removed for testing
        // struct tm timeinfo;
        // bool timeRetrieved = getLocalTime(&timeinfo);
        // bool yearValid = (timeinfo.tm_year + 1900 > 2020);
        
        // Use \r to return to start of line, and pad with spaces to overwrite previous text
        Serial.printf("\r[%s] [WIFI-TEST] %d/%d | Vol: %d%% | Heap: %d (Min: %d) | Up: %lu s   ",
            shuffleMode ? "SHUF" : "SEQ",
            // (timeRetrieved && yearValid) ? getSystemTime().c_str() : "--:--",
            currentSongIndex + 1,
            totalSongs,
            lastVolume,
            ESP.getFreeHeap(), 
            ESP.getMinFreeHeap(),
            millis() / 1000);
        lastPrintWasStatus = true;
    }
    
    // Serial Commands
    if (Serial.available()) {
        String cmd = Serial.readStringUntil('\n');
        cmd.trim(); cmd.toLowerCase();
        cleanSerialLine();
        if (cmd == "next" || cmd == "n") { fadeOut(); mp3->stop(); playNextSong(); }
        else if (cmd == "prev" || cmd == "p") { fadeOut(); playPreviousSong(); }
        else if (cmd == "pause") togglePause();
        else if (cmd == "shuffle") toggleShuffle();
        else if (cmd == "rescan") { SD.remove("/playlist.m3u"); Serial.println("Cache deleted. Reboot to rescan."); }
        else if (cmd == "bench") {
            Serial.println("Starting SD Card Benchmark...");
            // CHANGED: Reduced buffer from 64KB to 16KB to fit in RAM
            size_t bufSize = 16 * 1024; 
            uint8_t *buf = (uint8_t*)malloc(bufSize);
            
            if (!buf) { Serial.println("Failed to allocate buffer for bench"); }
            else {
                File f = SD.open(getSongPath(currentSongIndex).c_str());
                if (f) {
                    unsigned long start = millis();
                    size_t bytesRead = 0;
                    // CHANGED: Increased loop count to still read 1MB total (64 * 16KB = 1MB)
                    for (int i=0; i<64; i++) { 
                        bytesRead += f.read(buf, bufSize);
                    }
                    unsigned long end = millis();
                    f.close();
                    float speed = (bytesRead / 1024.0) / ((end - start) / 1000.0);
                    Serial.printf("Read %d bytes in %lu ms. Speed: %.2f KB/s\n", bytesRead, end - start, speed);
                } else { Serial.println("Failed to open file for bench"); }
                free(buf);
            }
        }
        else if (cmd == "status") {
            Serial.printf("State: %d | Shuffle: %d | Songs: %d | Index: %d\n", currentState, shuffleMode, totalSongs, currentSongIndex);
            Serial.printf("Heap: %d\n", ESP.getFreeHeap());
        }
    }
}

// ============================================
// AUDIO CALLBACKS (REMOVED - Not used by ESP8266Audio)
// ============================================
// void audio_info(const char *info) { ... }
// void audio_bitrate(const char *info) { ... }
// void audio_eof_mp3(const char *info) { ... }
// void audio_id3data(const char *info) { ... }
// void audio_showstation(const char *info) {}
// void audio_showstreamtitle(const char *info) {}
