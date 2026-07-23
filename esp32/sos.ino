/*
 * SOS Emergency Alert System - ESP32 Firmware
 * 
 * Hardware Wiring:
 * - Push Button: Connected between GPIO 4 and GND (uses internal INPUT_PULLUP)
 * - 12V Buzzer: Controlled via transistor/relay connected to GPIO 18 (Active HIGH)
 * 
 * Objectives:
 * 1. Turn ON buzzer immediately on button press.
 * 2. Connect to Wi-Fi if not connected.
 * 3. Send HTTP POST request to the local Flask server.
 * 4. Stop the buzzer after exactly 5 seconds (non-blocking).
 * 5. Prevent multiple alerts while the button is held down.
 */

#include <WiFi.h>
#include <HTTPClient.h>

// --- PIN CONFIGURATIONS ---
const int BUTTON_PIN = 4;   // Input Push Button (Active LOW)
const int BUZZER_PIN = 18;  // Output Buzzer Driver (Active HIGH)

// --- WIFI & SERVER CONFIGURATIONS ---
const char* ssid = "YOUR_WIFI_SSID";          // Replace with your WiFi SSID
const char* password = "YOUR_WIFI_PASSWORD";  // Replace with your WiFi Password
const char* serverUrl = "http://192.168.1.100:5000/sos"; // Replace with your Flask server IP

// --- DEVICE SETTINGS ---
const char* deviceId = "SOS001";

// --- SYSTEM STATE VARIABLES ---
int lastButtonState = HIGH;      // Previous state of button (pullup default is HIGH)
unsigned long buzzerEndTime = 0; // Timestamp when buzzer should turn off
bool isBuzzerActive = false;

// --- DEBOUNCE CONSTANTS ---
unsigned long lastDebounceTime = 0;
const unsigned long debounceDelay = 50; // 50 milliseconds debounce filter

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("\n--- SOS Emergency Alert System Initializing ---");

  // Configure Pin Modes
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  pinMode(BUZZER_PIN, OUTPUT);
  digitalWrite(BUZZER_PIN, LOW); // Start with buzzer OFF

  // Initialize WiFi Connection
  setupWiFi();
}

void loop() {
  // 1. Non-blocking Buzzer Timer
  if (isBuzzerActive && millis() >= buzzerEndTime) {
    digitalWrite(BUZZER_PIN, LOW);
    isBuzzerActive = false;
    Serial.println("[SYSTEM] Buzzer turned OFF after 5 seconds.");
  }

  // 2. Read Button Input with debouncing
  int reading = digitalRead(BUTTON_PIN);
  
  // Reset debounce timer if state changed
  static int lastReading = HIGH;
  if (reading != lastReading) {
    lastDebounceTime = millis();
  }
  lastReading = reading;

  if ((millis() - lastDebounceTime) > debounceDelay) {
    // Check for State Change Transition (Falling Edge: HIGH to LOW)
    // This triggers ONLY when the button is first pressed down
    if (reading == LOW && lastButtonState == HIGH) {
      triggerEmergencyAlert();
    }
    lastButtonState = reading;
  }
}

// Initial WiFi config
void setupWiFi() {
  Serial.println("[WIFI] Initializing Wi-Fi...");
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  
  // Try connecting for 8 seconds, don't block boot indefinitely
  unsigned long startConnect = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - startConnect < 8000) {
    delay(500);
    Serial.print(".");
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n[WIFI] Connected successfully!");
    Serial.print("[WIFI] IP Address: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\n[WIFI] Initial connection failed. Will auto-reconnect on alert.");
  }
}

// Ensure WiFi is active before making requests
bool ensureWiFiConnected() {
  if (WiFi.status() == WL_CONNECTED) {
    return true;
  }
  
  Serial.println("[WIFI] Connection lost. Attempting reconnection...");
  WiFi.disconnect();
  WiFi.begin(ssid, password);
  
  unsigned long startConnect = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - startConnect < 6000) {
    delay(400);
    Serial.print(".");
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n[WIFI] Reconnected!");
    return true;
  } else {
    Serial.println("\n[WIFI] Reconnection failed!");
    return false;
  }
}

// Core alert trigger logic
void triggerEmergencyAlert() {
  Serial.println("\n[EMERGENCY] Button pressed! Activating Alert...");

  // 1. Immediately sound the buzzer
  digitalWrite(BUZZER_PIN, HIGH);
  isBuzzerActive = true;
  buzzerEndTime = millis() + 5000; // Set buzzer to stop in 5 seconds
  Serial.println("[SYSTEM] 12V Buzzer turned ON.");

  // 2. Ensure connection is active
  if (!ensureWiFiConnected()) {
    Serial.println("[HTTP] Cannot send alert - No WiFi connectivity.");
    return;
  }

  // 3. Dispatch POST Request
  HTTPClient http;
  http.begin(serverUrl);
  http.addHeader("Content-Type", "application/json");

  // Read Battery level 
  // Code snippet for actual hardware:
  // int raw = analogRead(34); // ADC input connected to battery voltage divider
  // float voltage = (raw / 4095.0) * 3.3 * 2; // Adjust multiplier based on divider resistors
  // int batteryPct = map(voltage * 100, 320, 420, 0, 100); // 3.2V (empty) to 4.2V (full)
  int batteryLevel = 100; // Simulated battery level default

  // Construct JSON String manually to save binary size & avoid libraries dependencies
  String jsonPayload = "{\"device\":\"" + String(deviceId) + 
                       "\",\"status\":\"Emergency" + 
                       "\",\"battery\":\"" + String(batteryLevel) + 
                       "\",\"timestamp\":\"auto\"}";

  Serial.println("[HTTP] Sending POST payload: " + jsonPayload);
  int httpResponseCode = http.POST(jsonPayload);

  if (httpResponseCode > 0) {
    String response = http.getString();
    Serial.print("[HTTP] Success Code: ");
    Serial.println(httpResponseCode);
    Serial.println("[HTTP] Server Response JSON: ");
    Serial.println(response);
  } else {
    Serial.print("[HTTP] Failed. Error code: ");
    Serial.println(http.errorToString(httpResponseCode).c_str());
  }

  http.end(); // Close HTTP Client resources
}
