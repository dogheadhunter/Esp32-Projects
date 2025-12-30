#include <Arduino.h>
#include "FS.h"
#include "SD.h"
#include "SPI.h"
#include "Audio.h"
#include <vector>
#include <algorithm> // For std::sort

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

Audio audio;

// --- State Machine ---
enum PlayerState {
    STATE_NO_CARD,
    STATE_IDLE,
    STATE_PLAYING,
    STATE_PAUSED,
    STATE_OFF
};
PlayerState currentState = STATE_NO_CARD;

// --- Playlist Management ---
std::vector<String> playlist;
int currentSongIndex = -1;
bool shuffleMode = false;

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

// Save the current playlist to a file for fast loading next time
void savePlaylistCache() {
    cleanSerialLine();
    Serial.println("Saving playlist cache to /playlist.m3u...");
    File f = SD.open("/playlist.m3u", FILE_WRITE);
    if (f) {
        for (const auto& path : playlist) {
            f.println(path);
        }
        f.close();
        Serial.println("Cache saved.");
    } else {
        Serial.println("Failed to save cache file!");
    }
}

// Load playlist from file
bool loadPlaylistCache() {
    if (!SD.exists("/playlist.m3u")) return false;
    
    cleanSerialLine();
    Serial.println("Loading playlist from cache...");
    File f = SD.open("/playlist.m3u");
    if (!f) return false;

    playlist.clear();
    while (f.available()) {
        String line = f.readStringUntil('\n');
        line.trim();
        if (line.length() > 0) {
            playlist.push_back(line);
        }
    }
    f.close();
    
    if (playlist.size() > 0) {
        Serial.printf("Loaded %d songs from cache.\n", playlist.size());
        return true;
    }
    return false;
}

// Scan directory for MP3s
void scanDirectory() {
    cleanSerialLine();
    Serial.println("Scanning SD card for MP3 files...");
    playlist.clear();
    
    File root = SD.open("/");
    if (!root) {
        Serial.println("Failed to open root directory!");
        return;
    }
    
    File entry;
    int count = 0;
    while (entry = root.openNextFile()) {
        yield(); // Prevent watchdog timeout
        
        String name = String(entry.name());
        if (!name.startsWith(".")) {
            if (!entry.isDirectory() && name.endsWith(".mp3")) {
                if (!name.startsWith("/")) name = "/" + name;
                playlist.push_back(name);
                count++;
                if (count % 10 == 0) Serial.print(".");
                
                // Memory safety check (ESP32 has ~300KB RAM, 2000 songs * 50 bytes = 100KB)
                if (ESP.getFreeHeap() < 40000) {
                    Serial.println("\nWARNING: Low memory! Stopping scan early.");
                    break;
                }
            }
        }
        entry.close();
    }
    root.close();
    Serial.println("\nScan complete.");
    
    // Sort playlist alphabetically to ensure consistent order
    Serial.println("Sorting playlist...");
    std::sort(playlist.begin(), playlist.end());
    
    if (playlist.size() > 0) {
        savePlaylistCache();
    }
}

void fadeOut() {
    int startVol = audio.getVolume();
    for (int v = startVol; v >= 0; v--) {
        audio.setVolume(v);
        unsigned long start = millis();
        while (millis() - start < 15) {
            audio.loop();
        }
    }
}

void fadeIn(int targetVol) {
    for (int v = 0; v <= targetVol; v++) {
        audio.setVolume(v);
        unsigned long start = millis();
        while (millis() - start < 20) {
            audio.loop();
        }
    }
}

// ============================================
// CARD MANAGEMENT
// ============================================

bool mountSDCard() {
    // Reduced SPI speed to 4MHz for better stability
    if (SD.begin(SD_CS, SPI, 4000000)) {
        cleanSerialLine();
        Serial.println("SD Card mounted.");
        
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
        
        Serial.printf("Total Songs: %d\n", playlist.size());
        
        // Seed random
        randomSeed(analogRead(POT_PIN) + millis());
        
        cardMounted = true;
        return true;
    }
    return false;
}

void unmountSDCard() {
    if (audio.isRunning()) audio.stopSong();
    SD.end();
    cardMounted = false;
    currentState = STATE_NO_CARD;
    playlist.clear();
    currentSongIndex = -1;
    cleanSerialLine();
    Serial.println("SD Card unmounted.");
}

bool checkCardPresent() {
    File test = SD.open("/");
    if (!test) return false;
    test.close();
    return true;
}

// ============================================
// PLAYBACK CONTROL
// ============================================

void playSongAtIndex(int index) {
    if (index < 0 || index >= playlist.size()) return;
    
    currentSongIndex = index;
    String path = playlist[index];
    
    cleanSerialLine();
    Serial.printf("Playing [%d/%d]: %s\n", index + 1, playlist.size(), path.c_str());
    
    if (audio.isRunning()) audio.stopSong();
    audio.connecttoFS(SD, path.c_str());
    
    currentState = STATE_PLAYING;
    if (lastVolume >= 0) audio.setVolume(lastVolume);
}

void playNextSong() {
    if (playlist.empty()) return;
    
    int nextIndex;
    if (shuffleMode) {
        // Pick random index
        nextIndex = random(0, playlist.size());
        // Avoid repeating same song if possible
        if (playlist.size() > 1 && nextIndex == currentSongIndex) {
            nextIndex = (nextIndex + 1) % playlist.size();
        }
    } else {
        // Sequential
        nextIndex = (currentSongIndex + 1) % playlist.size();
    }
    
    playSongAtIndex(nextIndex);
}

void playPreviousSong() {
    if (playlist.empty()) return;
    
    // If more than 3 seconds in, restart current song
    if (audio.getAudioCurrentTime() > 3) {
        cleanSerialLine();
        Serial.println("Restarting current song...");
        playSongAtIndex(currentSongIndex);
    } else {
        int prevIndex = currentSongIndex - 1;
        if (prevIndex < 0) prevIndex = playlist.size() - 1;
        playSongAtIndex(prevIndex);
    }
}

void togglePause() {
    if (currentState == STATE_PLAYING) {
        audio.pauseResume();
        currentState = STATE_PAUSED;
        cleanSerialLine();
        Serial.println("Paused");
        blinkLED(2, 100);
    } else if (currentState == STATE_PAUSED) {
        audio.pauseResume();
        currentState = STATE_PLAYING;
        cleanSerialLine();
        Serial.println("Resumed");
    }
}

void powerOff() {
    cleanSerialLine();
    Serial.println("Powering off...");
    fadeOut();
    audio.stopSong();
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

// ============================================
// SETUP
// ============================================

void setup() {
    // Anti-pop
    pinMode(I2S_BCLK, OUTPUT); digitalWrite(I2S_BCLK, LOW);
    pinMode(I2S_LRC, OUTPUT); digitalWrite(I2S_LRC, LOW);
    pinMode(I2S_DOUT, OUTPUT); digitalWrite(I2S_DOUT, LOW);
    
    pinMode(LED_PIN, OUTPUT); digitalWrite(LED_PIN, LOW);
    
    pinMode(BTN_PLAY_PAUSE, INPUT_PULLUP);
    pinMode(BTN_NEXT, INPUT_PULLUP);
    pinMode(BTN_PREV, INPUT_PULLUP);
    pinMode(BTN_SHUFFLE, INPUT_PULLUP);
    
    Serial.begin(115200);
    delay(500);
    
    Serial.println("\n========================================");
    Serial.println("       ESP32 iPod Shuffle Clone");
    Serial.println("========================================");
    
    audio.setPinout(I2S_BCLK, I2S_LRC, I2S_DOUT);
    audio.setVolume(0);
    audio.forceMono(true); // Force mono output for single speaker
    audio.setBufsize(64000, 0); // Increase buffer size to 64KB to prevent underruns
    
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
    if (cardMounted) audio.loop();
    
    if (shouldPlayNext) {
        shouldPlayNext = false;
        delay(100);
        playNextSong();
    }
    
    // --- SD Card Hot-Swap ---
    if (millis() - lastCardCheck > cardCheckInterval) {
        lastCardCheck = millis();
        if (cardMounted && !checkCardPresent()) {
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
    
    // Play/Pause
    int currentPlayPauseState = digitalRead(BTN_PLAY_PAUSE);
    if (lastPlayPauseState == HIGH && currentPlayPauseState == LOW) {
        playPausePressStartTime = millis();
        playPauseLongPressHandled = false;
    }
    if (currentPlayPauseState == LOW && !playPauseLongPressHandled) {
        if (millis() - playPausePressStartTime > longPressDuration) {
            if (currentState != STATE_OFF && currentState != STATE_NO_CARD) powerOff();
            playPauseLongPressHandled = true;
        }
    }
    if (lastPlayPauseState == LOW && currentPlayPauseState == HIGH) {
        if (!playPauseLongPressHandled && (millis() - playPausePressStartTime > 50)) {
            if (currentState == STATE_OFF) powerOn();
            else if (currentState == STATE_NO_CARD) { if (mountSDCard()) playNextSong(); }
            else if (currentState == STATE_IDLE) playNextSong();
            else togglePause();
        }
    }
    lastPlayPauseState = currentPlayPauseState;
    
    // Shuffle Button (Dedicated)
    int currentShuffleState = digitalRead(BTN_SHUFFLE);
    if (lastShuffleState == HIGH && currentShuffleState == LOW) {
        // Pressed
        if (millis() - lastDebounceTime > 200) {
            lastDebounceTime = millis();
            toggleShuffle();
        }
    }
    lastShuffleState = currentShuffleState;
    
    // Prev (Simple Press)
    int currentPrevState = digitalRead(BTN_PREV);
    if (lastPrevState == HIGH && currentPrevState == LOW) {
        if (millis() - lastDebounceTime > 200) {
            lastDebounceTime = millis();
            if (currentState == STATE_PLAYING || currentState == STATE_PAUSED) {
                fadeOut();
                playPreviousSong();
                if (lastVolume >= 0) fadeIn(lastVolume);
            }
        }
    }
    lastPrevState = currentPrevState;
    
    // Next
    if (millis() - lastDebounceTime > debounceDelay) {
        if (digitalRead(BTN_NEXT) == LOW) {
            lastDebounceTime = millis();
            if (currentState == STATE_PLAYING || currentState == STATE_PAUSED) {
                cleanSerialLine();
                Serial.println("Next track...");
                fadeOut();
                audio.stopSong();
                playNextSong();
            }
        }
    }
    
    // Volume
    if (millis() - lastVolCheck > 100) {
        lastVolCheck = millis();
        long sum = 0;
        for (int i = 0; i < 4; i++) { sum += analogRead(POT_PIN); } // Reduced samples to 4, removed delay
        int potValue = sum / 4;
        int newVolume = map(potValue, 0, 4095, 0, 21);
        if (newVolume != lastVolume) {
            audio.setVolume(newVolume);
            lastVolume = newVolume;
            cleanSerialLine();
            Serial.printf("Volume: %d\n", newVolume);
        }
    }
    
    // === STATUS DISPLAY (Single Line) ===
    static unsigned long lastStatusPrint = 0;
    if (currentState == STATE_PLAYING && millis() - lastStatusPrint > 1000) {
        lastStatusPrint = millis();
        // Use \r to return to start of line, and pad with spaces to overwrite previous text
        Serial.printf("\r[%s] %d/%d | %02d:%02d/%02d:%02d | Vol: %d   ",
            shuffleMode ? "SHUF" : "SEQ",
            currentSongIndex + 1,
            playlist.size(),
            audio.getAudioCurrentTime() / 60, audio.getAudioCurrentTime() % 60,
            audio.getAudioFileDuration() / 60, audio.getAudioFileDuration() % 60,
            audio.getVolume());
        lastPrintWasStatus = true;
    }
    
    // Serial Commands
    if (Serial.available()) {
        String cmd = Serial.readStringUntil('\n');
        cmd.trim(); cmd.toLowerCase();
        cleanSerialLine();
        if (cmd == "next" || cmd == "n") { fadeOut(); audio.stopSong(); playNextSong(); }
        else if (cmd == "prev" || cmd == "p") { fadeOut(); playPreviousSong(); }
        else if (cmd == "pause") togglePause();
        else if (cmd == "shuffle") toggleShuffle();
        else if (cmd == "rescan") { SD.remove("/playlist.m3u"); Serial.println("Cache deleted. Reboot to rescan."); }
        else if (cmd == "status") {
            Serial.printf("State: %d | Shuffle: %d | Songs: %d | Index: %d\n", currentState, shuffleMode, playlist.size(), currentSongIndex);
            Serial.printf("Heap: %d\n", ESP.getFreeHeap());
        }
    }
}

// ============================================
// AUDIO CALLBACKS
// ============================================
void audio_info(const char *info) {
    String msg = String(info);
    // Filter out common spammy info messages
    if (msg.indexOf("decode error") == -1 && msg.indexOf("syncword") == -1 && msg.indexOf("stream ready") == -1) {
        cleanSerialLine();
        Serial.print("info: "); Serial.println(info);
    }
}
void audio_eof_mp3(const char *info) {
    cleanSerialLine();
    Serial.print("eof: "); Serial.println(info);
    shouldPlayNext = true;
}
void audio_showstation(const char *info) {}
void audio_showstreamtitle(const char *info) {}
