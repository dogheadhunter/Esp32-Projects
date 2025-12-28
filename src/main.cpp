#include <Arduino.h>
#include "FS.h"
#include "SD.h"
#include "SPI.h"
#include "Audio.h"
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

// Button Pins
#define BTN_PLAY_PAUSE 27
#define BTN_NEXT       14
#define BTN_PREV       13

Audio audio;
std::vector<String> playlist;
int currentSongIndex = 0;

// New flag to handle song transitions safely
bool shouldPlayNext = false;

int lastVolume = -1;
unsigned long lastVolCheck = 0;

// Button State Variables
unsigned long lastDebounceTime = 0;
const unsigned long debounceDelay = 200; // ms

// Play/Pause Button State for Long Press
int lastPlayPauseState = HIGH;
unsigned long playPausePressStartTime = 0;
bool playPauseLongPressHandled = false;
const unsigned long longPressDuration = 1000; // 1 second for long press
bool isSystemOff = false;

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

void fadeOut() {
    int startVol = audio.getVolume();
    for (int v = startVol; v >= 0; v--) {
        audio.setVolume(v);
        // Keep audio loop running while fading to prevent glitches
        unsigned long start = millis();
        while (millis() - start < 15) { 
            audio.loop();
        }
    }
}

void playCurrentSong() {
    if (playlist.empty()) return;
    
    // Ensure index is valid
    if (currentSongIndex >= playlist.size()) currentSongIndex = 0;
    if (currentSongIndex < 0) currentSongIndex = playlist.size() - 1;

    String songName = playlist[currentSongIndex];
    Serial.printf("Playing: %s\n", songName.c_str());
    
    // Ensure previous playback is fully stopped before starting new one
    if(audio.isRunning()) audio.stopSong();
    
    audio.connecttoFS(SD, songName.c_str());
    
    // Force volume update in loop() so it snaps back to pot value
    lastVolume = -1; 
}

// -------------------------------------

void setup() {
    // 0. Anti-pop: Drive I2S pins low immediately to stabilize them
    pinMode(I2S_BCLK, OUTPUT);
    digitalWrite(I2S_BCLK, LOW);
    pinMode(I2S_LRC, OUTPUT);
    digitalWrite(I2S_LRC, LOW);
    pinMode(I2S_DOUT, OUTPUT);
    digitalWrite(I2S_DOUT, LOW);

    // Initialize Buttons with Internal Pull-ups
    pinMode(BTN_PLAY_PAUSE, INPUT_PULLUP);
    pinMode(BTN_NEXT, INPUT_PULLUP);
    pinMode(BTN_PREV, INPUT_PULLUP);

    Serial.begin(115200);
    delay(1000); // Give power a moment to settle
    
    Serial.println("--- Starting SD Card & Audio Test ---");

    // 1. Initialize SD Card
    // Note: We use the default SPI bus, so we don't need to pass SPI instance if using default pins
    // Lower SPI frequency to 4MHz to improve stability and reduce read errors (INVALID_FRAMEHEADER)
    if(!SD.begin(SD_CS, SPI, 4000000)){
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
    audio.setVolume(0); // Start silent to reduce pops. Loop will set correct volume.

    // 4. Build Playlist
    Serial.println("Scanning for MP3 files...");
    File root = SD.open("/");
    File file = root.openNextFile();
    while(file){
        String fileName = String(file.name());
        if(!file.isDirectory() && fileName.endsWith(".mp3")){
            if(!fileName.startsWith("/")) fileName = "/" + fileName;
            playlist.push_back(fileName);
            Serial.printf("Added to playlist: %s\n", fileName.c_str());
        }
        file = root.openNextFile();
    }
    
    if (!playlist.empty()) {
        Serial.printf("Found %d songs.\n", playlist.size());
        playCurrentSong();
    } else {
        Serial.println("No MP3 files found!");
    }
}

void loop() {
    audio.loop();

    // Check if we need to play the next song (triggered by EOF)
    if (shouldPlayNext) {
        shouldPlayNext = false; // Reset flag
        // Small delay to ensure previous file handle is fully closed
        delay(100); 
        currentSongIndex++;
        playCurrentSong();
    }

    // --- Play/Pause Button Handling (Short Press = Toggle, Long Press = Stop) ---
    int currentPlayPauseState = digitalRead(BTN_PLAY_PAUSE);

    // Button Pressed (Falling Edge)
    if (lastPlayPauseState == HIGH && currentPlayPauseState == LOW) {
        playPausePressStartTime = millis();
        playPauseLongPressHandled = false;
    }
    
    // Button Held Down
    if (currentPlayPauseState == LOW) {
        if (!playPauseLongPressHandled && (millis() - playPausePressStartTime > longPressDuration)) {
            Serial.println("Long Press Detected: Stopping Song");
            audio.stopSong();
            isSystemOff = true;
            playPauseLongPressHandled = true; // Ensure we don't trigger again
        }
    }

    // Button Released (Rising Edge)
    if (lastPlayPauseState == LOW && currentPlayPauseState == HIGH) {
        // Only trigger short press action if long press wasn't handled
        if (!playPauseLongPressHandled) {
             // Simple debounce for release
            if (millis() - playPausePressStartTime > 50) { 
                if (isSystemOff) {
                    // Wake up from off state
                    isSystemOff = false;
                    playCurrentSong();
                } else {
                    // Toggle Pause/Resume
                    audio.pauseResume();
                    Serial.println("Pause/Resume toggled");
                }
            }
        }
    }
    lastPlayPauseState = currentPlayPauseState;


    // --- Other Buttons (Simple Debounce) ---
    if (millis() - lastDebounceTime > debounceDelay) {
        // Next Track
        if (digitalRead(BTN_NEXT) == LOW) {
            lastDebounceTime = millis();
            if (!isSystemOff) {
                Serial.println("Next button pressed");
                fadeOut();
                audio.stopSong();
                currentSongIndex++;
                playCurrentSong();
            }
        }
        // Prev Track
        else if (digitalRead(BTN_PREV) == LOW) {
            lastDebounceTime = millis();
            if (!isSystemOff) {
                Serial.println("Prev button pressed");
                fadeOut();
                audio.stopSong();
                currentSongIndex--;
                if (currentSongIndex < 0) currentSongIndex = playlist.size() - 1;
                playCurrentSong();
            }
        }
    }

    // Check potentiometer every 100ms
    if (millis() - lastVolCheck > 100) {
        lastVolCheck = millis();
        int potValue = analogRead(POT_PIN);
        // Map 0-4095 (12-bit ADC) to 0-21 (Audio library volume range)
        int newVolume = map(potValue, 0, 4095, 0, 21);
        
        // Only update if volume changed to prevent jitter
        if (newVolume != lastVolume) {
            audio.setVolume(newVolume);
            lastVolume = newVolume;
            Serial.printf("Volume Changed: %d\n", newVolume); 
        }
    }

    // Print song time and volume every second
    static unsigned long lastTimePrint = 0;
    if (audio.isRunning() && millis() - lastTimePrint > 1000) {
        lastTimePrint = millis();
        Serial.printf("Time: %3d / %3d sec | Vol: %d\n", 
            audio.getAudioCurrentTime(), 
            audio.getAudioFileDuration(),
            audio.getVolume());
    }
    
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
    // Auto-advance to next song safely via loop
    shouldPlayNext = true;
}
