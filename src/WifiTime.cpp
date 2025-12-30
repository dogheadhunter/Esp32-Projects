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

// Global flag for time sync status
bool timeSynced = false;

// Callback notifying us of the need to save config
void saveConfigCallback () {
  Serial.println("Should save config");
  shouldSaveConfig = true;
}

bool syncTimeWithNTP(bool resetSettings) {
    timeSynced = false; // Reset flag
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
    
    // Set timeout to 20 seconds
    wm.setConfigPortalTimeout(20); 
    
    // Enable Captive Portal (DNS Server)
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
        Serial.print("IP Address: "); Serial.println(WiFi.localIP());
        Serial.print("Subnet Mask: "); Serial.println(WiFi.subnetMask());
        Serial.print("Gateway IP: "); Serial.println(WiFi.gatewayIP());
        Serial.print("DNS Server: "); Serial.println(WiFi.dnsIP());
        Serial.print("BSSID: "); Serial.println(WiFi.BSSIDstr());
        Serial.print("RSSI (Signal Strength): "); Serial.print(WiFi.RSSI()); Serial.println(" dBm");
        
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
            timeSynced = true; // SAFE MODE: Only set true if we actually got time
        } else {
            Serial.println("Failed to obtain time.");
            timeSynced = false;
        }
    }
    
    // ALWAYS Disconnect WiFi to save power and reduce audio noise
    // This fixes the "blips" / interference when WiFi fails but radio stays on
    WiFi.disconnect(true);
    WiFi.mode(WIFI_OFF);
    Serial.println("WiFi disconnected (Radio OFF).");
    delay(100); // Allow WiFi stack to shut down
    
    return res;
}

String getSystemTime() {
    struct tm timeinfo;
    // DEBUG: Print raw time info if needed
    if(!getLocalTime(&timeinfo)){
        // Serial.println("[DEBUG] getSystemTime: getLocalTime failed");
        return "--:--";
    }
    // Serial.printf("[DEBUG] getSystemTime: Year=%d\n", timeinfo.tm_year + 1900);
    
    char timeStringBuff[10];
    // %I is 12-hour format (01-12), %M is minute
    // %p adds AM/PM
    strftime(timeStringBuff, sizeof(timeStringBuff), "%I:%M%p", &timeinfo);
    return String(timeStringBuff);
}
