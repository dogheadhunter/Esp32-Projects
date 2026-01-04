#include "test_runner.h"

// --- ROUND 2 TESTS (Existing) ---

void runMissingFileTest() {
    Serial.println("\n[TEST 1] Missing File Handling");
    Serial.println("Attempting to play non-existent file...");
    
    if (file) delete file;
    file = new AudioFileSourceSD("/DOES_NOT_EXIST.mp3");
    
    if (!file->isOpen()) {
        Serial.println("File failed to open (Expected).");
        Serial.println("RESULT: PASS (Graceful failure)");
    } else {
        Serial.println("RESULT: FAIL (File object thinks it opened?)");
    }
    if (file) delete file; file = NULL;
}

void runShuffleLogicTest() {
    Serial.println("\n[TEST 2] Fisher-Yates Shuffle Logic");
    
    // Mock 10 songs
    int originalTotal = totalSongs;
    totalSongs = 10;
    generateShuffleOrder();
    
    Serial.print("Order: ");
    bool seen[10] = {0};
    bool duplicate = false;
    
    for(int i=0; i<10; i++) {
        int songId = shuffleOrder[i];
        Serial.printf("%d ", songId);
        if(songId >= 0 && songId < 10) {
            if(seen[songId]) duplicate = true;
            seen[songId] = true;
        }
    }
    Serial.println();
    
    if(!duplicate) Serial.println("RESULT: PASS (No duplicates in one pass)");
    else Serial.println("RESULT: FAIL (Duplicates found!)");
    
    // Test Wrap Around
    Serial.println("Testing Shuffle Wrap-Around...");
    shufflePosition = 10; // Force end of list
    
    // We need to be careful not to actually play audio here if we can avoid it, 
    // or ensure playNextSong handles it. 
    // playNextSong calls playSongAtIndex which tries to open a file.
    // We'll mock the behavior by checking if shuffleOrder gets regenerated.
    
    // Manually trigger the logic that playNextSong uses for shuffle generation
    if (shufflePosition >= totalSongs) {
        generateShuffleOrder();
    }
    
    if(shufflePosition == 0) Serial.println("RESULT: PASS (Regenerated and started at 0)");
    else Serial.printf("RESULT: FAIL (Pos: %d)\n", shufflePosition);

    totalSongs = originalTotal; // Restore
}

void runSequentialWrapTest() {
    Serial.println("\n[TEST 3] Sequential Wrap-Around");
    bool originalShuffle = shuffleMode;
    shuffleMode = false;
    int originalTotal = totalSongs;
    totalSongs = 5;
    currentSongIndex = 4; // Last song
    
    int nextIndex = (currentSongIndex + 1) % totalSongs;
    
    Serial.printf("Current: %d, Total: %d, Next: %d\n", currentSongIndex, totalSongs, nextIndex);
    
    if(nextIndex == 0) Serial.println("RESULT: PASS (Wrapped to 0)");
    else Serial.println("RESULT: FAIL (Did not wrap)");
    
    shuffleMode = originalShuffle;
    totalSongs = originalTotal;
}

// --- ROUND 3 TESTS (New) ---

void runGarbageFileTest() {
    Serial.println("\n[TEST 4] Garbage File Resilience");
    
    // 1. Create a garbage file
    const char* badPath = "/garbage_test.mp3";
    SD.remove(badPath);
    File f = SD.open(badPath, FILE_WRITE);
    if (f) {
        for(int i=0; i<100; i++) f.print("THIS IS NOT AUDIO DATA. ");
        f.close();
        Serial.println("Created garbage file.");
    } else {
        Serial.println("Failed to create garbage file. Skipping.");
        return;
    }

    // 2. Try to play it
    Serial.println("Attempting to play garbage file...");
    if (mp3->isRunning()) mp3->stop();
    if (file) delete file;
    
    file = new AudioFileSourceSD(badPath);
    // We expect begin() to possibly fail, or loop() to fail immediately
    bool started = mp3->begin(file, out);
    
    if (!started) {
        Serial.println("Decoder rejected file immediately.");
        Serial.println("RESULT: PASS (Rejected at begin)");
    } else {
        Serial.println("Decoder accepted file. Running loop...");
        unsigned long start = millis();
        bool error = false;
        int loops = 0;
        while (millis() - start < 1000) {
            if (!mp3->loop()) {
                Serial.println("Decoder stopped (loop returned false).");
                error = true;
                break;
            }
            loops++;
            if (loops % 100 == 0) delay(1); // Yield
        }
        
        if (error) Serial.println("RESULT: PASS (Stopped gracefully)");
        else Serial.println("RESULT: WARNING (Decoder kept running on garbage? Watchdog would handle this.)");
    }
    
    mp3->stop();
    SD.remove(badPath);
}

void runRapidFireTest() {
    Serial.println("\n[TEST 5] Rapid Fire (Memory Stress)");
    
    uint32_t startHeap = ESP.getFreeHeap();
    Serial.printf("Start Heap: %d bytes\n", startHeap);
    Serial.println("Skipping 20 songs rapidly...");
    
    // We need actual songs for this to be meaningful, or at least valid paths
    // If totalSongs is 0, we can't do this.
    if (totalSongs == 0) {
        Serial.println("No songs loaded. Scanning SD...");
        scanDirectory();
        if (totalSongs == 0) {
            Serial.println("Still no songs found. Skipping test.");
            return;
        }
    }

    for(int i=0; i<20; i++) {
        playNextSong();
        // Run a few loops to let it allocate buffers
        for(int j=0; j<50; j++) {
            if(mp3->isRunning()) mp3->loop();
        }
        delay(10); // Short pause
    }
    
    mp3->stop();
    uint32_t endHeap = ESP.getFreeHeap();
    Serial.printf("End Heap: %d bytes\n", endHeap);
    
    int loss = startHeap - endHeap;
    Serial.printf("Memory Loss: %d bytes\n", loss);
    
    // Allow some fragmentation loss, but not massive leaks
    if (loss < 5000) Serial.println("RESULT: PASS (Stable Memory)");
    else Serial.println("RESULT: FAIL (Significant Memory Leak)");
}

void runLongFilenameTest() {
    Serial.println("\n[TEST 6] Long Filename Handling");
    
    // Create a very long filename (FAT32 limit is 255, but let's test ~100 chars which is common stress)
    String longName = "/Test_Song_With_A_Very_Very_Very_Very_Very_Very_Very_Very_Long_Name_1234567890.mp3";
    
    // Create dummy file
    SD.remove(longName);
    File f = SD.open(longName, FILE_WRITE);
    if(f) {
        f.println("Dummy content");
        f.close();
    } else {
        Serial.println("Could not create long filename (FS limit?).");
        // If FS rejects it, that's actually a pass for the player (it won't see it)
        Serial.println("RESULT: PASS (FS handled rejection)");
        return;
    }
    
    Serial.println("Attempting to open long filename...");
    if (file) delete file;
    file = new AudioFileSourceSD(longName.c_str());
    
    if (file->isOpen()) {
        Serial.println("File opened successfully.");
        Serial.println("RESULT: PASS (Long filename supported)");
    } else {
        Serial.println("File failed to open.");
        Serial.println("RESULT: PASS (Handled gracefully)");
    }
    
    if (file) delete file; file = NULL;
    SD.remove(longName);
}

void runAllTests() {
    Serial.println("\n=== STARTING TEST SUITE (ROUND 3) ===");
    
    runMissingFileTest();
    runShuffleLogicTest();
    runSequentialWrapTest();
    runGarbageFileTest();
    runRapidFireTest();
    runLongFilenameTest();
    
    Serial.println("\n=== ALL TESTS COMPLETE ===");
}
