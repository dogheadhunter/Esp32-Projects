#include <Arduino.h>
#include <WiFi.h>
#include <WiFiManager.h> // Added WiFiManager
#include "time.h"
// #include "secrets.h" // Removed hardcoded secrets
#include "WifiTime.h"

// Timezone settings (Central Time)
// CST is UTC-6 (winter) = -21600 seconds
// CDT is UTC-5 (summer) = -18000 seconds
const long  gmtOffset_sec = -21600; 
const int   daylightOffset_sec = 3600;

// Flag to indicate if settings were saved
bool shouldSaveConfig = false;

// Callback notifying us of the need to save config
void saveConfigCallback () {
  Serial.println("Should save config");
  shouldSaveConfig = true;
}

void syncTimeWithNTP(bool resetSettings) {
    WiFiManager wm;
    
    // Set callback that gets called when connecting to previous WiFi fails, and enters Access Point mode
    wm.setAPCallback([](WiFiManager *myWiFiManager) {
      Serial.println("Entered config mode");
      Serial.println(WiFi.softAPIP());
      Serial.println(myWiFiManager->getConfigPortalSSID());
    });

    // Set callback that gets called when settings are saved
    wm.setSaveConfigCallback(saveConfigCallback);
    
    if (resetSettings) {
        Serial.println("Resetting WiFi Settings...");
        wm.resetSettings();
        // We don't return here, we let it proceed to autoConnect which will now fail and open AP
    }

    Serial.println("Connecting to WiFi to sync time...");
    
    // Set timeout to 180 seconds (3 minutes)
    // If it can't connect, it will start an AP.
    // If no one configures it in 3 mins, it returns false.
    wm.setConfigPortalTimeout(180); 
    
    // Enable Captive Portal (DNS Server)
    // This forces the phone to open the config page automatically
    wm.setCaptivePortalEnable(true);

    // Automatically connect using saved credentials,
    // if connection fails, it starts an access point named "ESP32-Radio-Setup"
    bool res = wm.autoConnect("ESP32-Radio-Setup"); 

    if(!res) {
        Serial.println("\nFailed to connect or hit timeout. Skipping time sync.");
        // We continue so the radio can still play music
    } else {
        // If we just saved new settings, restart to ensure a clean memory state
        if (shouldSaveConfig) {
            Serial.println("Settings saved. Restarting to free up memory...");
            delay(2000);
            ESP.restart();
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
        // Note: WiFiManager might reconnect if we don't handle this carefully, 
        // but for now we just disconnect.
        WiFi.disconnect(true);
        WiFi.mode(WIFI_OFF);
        Serial.println("WiFi disconnected.");
        delay(100); // Allow WiFi stack to shut down
    }
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
