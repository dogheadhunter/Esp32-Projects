#ifndef WIFI_TIME_H
#define WIFI_TIME_H

#include <Arduino.h>

// Syncs the internal RTC with NTP servers via WiFi
void syncTimeWithNTP();

// Returns a formatted string "HH:MM" of the current system time
String getSystemTime();

#endif
