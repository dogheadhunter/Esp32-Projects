#ifndef WIFI_TIME_H
#define WIFI_TIME_H

#include <Arduino.h>

// Syncs the internal RTC with NTP servers via WiFi
// Returns true if successful, false if timed out
bool syncTimeWithNTP(bool resetSettings = false);

// Global flag to indicate if time is valid
extern bool timeSynced;

// Returns a formatted string "HH:MM" of the current system time
String getSystemTime();

#endif
