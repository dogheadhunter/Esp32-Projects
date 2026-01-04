#ifndef TEST_RUNNER_H
#define TEST_RUNNER_H

#include <Arduino.h>
#include <vector>
#include "AudioGeneratorMP3.h"
#include "AudioFileSourceSD.h"
#include "AudioOutputI2S.h"
#include "SD.h"

// Access to globals from main.cpp
extern AudioGeneratorMP3 *mp3;
extern AudioFileSourceSD *file;
extern AudioOutputI2S *out;
extern int totalSongs;
extern int currentSongIndex;
extern bool shuffleMode;
extern std::vector<int> shuffleOrder;
extern int shufflePosition;

// Function prototypes from main.cpp
void playNextSong();
void generateShuffleOrder();
void playSongAtIndex(int index);
void scanDirectory();

// Test Functions
void runMissingFileTest();
void runShuffleLogicTest();
void runSequentialWrapTest();
void runGarbageFileTest();
void runRapidFireTest();
void runLongFilenameTest();
void runLatencyTest();

// Master Runner
void runAllTests();

#endif
