#include <Arduino.h>
#include <WiFi.h>
#include "time.h"
#include "secrets.h"
#include "WifiTime.h"

// Timezone settings (Central Time)
// CST is UTC-6 (winter) = -21600 seconds
// CDT is UTC-5 (summer) = -18000 seconds
const long  gmtOffset_sec = -21600; 
const int   daylightOffset_sec = 3600;

void syncTimeWithNTP() {
    Serial.println("Connecting to WiFi to sync time...");
    
    // Use credentials from secrets.h
    // Note: secrets.h uses WIFI_PASSWORD, not WIFI_PASS
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    
    int timeout = 0;
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
        timeout++;
        if (timeout > 20) { // 10 seconds timeout
            Serial.println("\nWiFi connection failed! Skipping time sync.");
            WiFi.disconnect(true);
            return;
        }
    }
    
    Serial.println("\nWiFi connected.");
    Serial.println("Fetching NTP time...");
    
    configTime(gmtOffset_sec, daylightOffset_sec, "pool.ntp.org", "time.nist.gov");
    
    // Wait for time to be set
    struct tm timeinfo;
    int retry = 0;
    while (!getLocalTime(&timeinfo) && retry < 5) {
        Serial.println("Waiting for time...");
        delay(1000);
        retry++;
    }
    
    if (retry < 5) {
        Serial.println("Time synced successfully!");
        Serial.println(&timeinfo, "Current time: %A, %B %d %Y %H:%M:%S");
    } else {
        Serial.println("Failed to obtain time.");
    }
    
    // Disconnect WiFi to save power and reduce audio noise
    WiFi.disconnect(true);
    WiFi.mode(WIFI_OFF);
    Serial.println("WiFi disconnected.");
    delay(100); // Allow WiFi stack to shut down
}

String getSystemTime() {
    struct tm timeinfo;
    if(!getLocalTime(&timeinfo)){
        return "--:--";
    }
    char timeStringBuff[10];
    // %I is 12-hour format (01-12), %M is minute
    // %p adds AM/PM
    strftime(timeStringBuff, sizeof(timeStringBuff), "%I:%M%p", &timeinfo);
    return String(timeStringBuff);
}
