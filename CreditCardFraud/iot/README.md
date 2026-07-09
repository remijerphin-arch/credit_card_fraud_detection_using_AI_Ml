# ESP32 IoT Hardware Integration Guide

This directory contains the ESP32 integration guide, wiring diagrams, JSON payload format, REST API communication flow, and future hardware implementation notes.

---

## 1. System Communication Workflow

The physical ESP32 communicates with the backend REST API over Wi-Fi. The data flows as follows:

```text
Physical ESP32 (Wi-Fi) ──► POST /api/v1/predict (JSON) ──► Input Validation ──► Feature Mapping ──► ML Model ──► SQLite DB ──► Dashboard UI
```

No changes to the backend server are required to connect physical hardware; it already exposes the production endpoint `/api/v1/predict`.

---

## 2. API Endpoint Specification

* **HTTP Method**: `POST`
* **Path**: `/api/v1/predict`
* **Content-Type**: `application/json`

### Expected JSON Payload:
```json
{
  "card_id": "card_xxxx_xxxx_xxxx",
  "amount": 120.50,
  "merchant": "Amazon Store",
  "transaction_time": "2026-07-09T07:20:58",
  "location": "New York, USA",
  "device_id": "esp32_terminal_01",
  "transaction_type": "Genuine",
  "latitude": 40.7128,
  "longitude": -74.0060
}
```

### JSON Response Format (HTTP 200):
```json
{
  "prediction": "Genuine",
  "risk_score": 0.08
}
```

---

## 3. Future Hardware Integration Workflow

1. **Hardware Requirements**:
   * ESP32 Development Board (e.g., ESP32-WROOM-32)
   * RFID-RC522 module (to read credit cards/tags)
   * SPI connections and breadboard wires
2. **Firmware Execution**:
   * Connect ESP32 to local Wi-Fi.
   * Scan card using RFID-RC522 to read `card_id`.
   * Formulate the JSON payload (populate location, coordinates, amount, time, and device_id).
   * Dispatch HTTP POST request using `HTTPClient` library in Arduino IDE.
   * Parse the JSON response containing the prediction and risk score.
   * Display the result on an LCD screen or light up green (Genuine) or red (Fraud) LEDs.

---

## 4. Hardware Wiring Plan (RC522 to ESP32)

| RFID RC522 Pin | ESP32 GPIO Pin | Description |
|---|---|---|
| **SDA (SS)** | GPIO 5 | SPI Chip Select |
| **SCK** | GPIO 18 | SPI Clock |
| **MOSI** | GPIO 23 | SPI MOSI |
| **MISO** | GPIO 19 | SPI MISO |
| **IRQ** | *Not Connected* | Interrupt request |
| **GND** | GND | Ground |
| **RST** | GPIO 22 | Reset pin |
| **3.3V** | 3.3V | Power supply (Caution: 3.3V only, not 5V) |

---

## 5. Sample ESP32 C++ Code (Arduino IDE)

Below is the sketch to deploy to your ESP32 board:

```cpp
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";
const char* serverUrl = "http://<YOUR_SERVER_IP>:5000/api/v1/predict";

void setup() {
  Serial.begin(115200);
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected.");
}

void loop() {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(serverUrl);
    http.addHeader("Content-Type", "application/json");

    // Create JSON Document
    StaticJsonDocument<500> doc;
    doc["card_id"] = "card_8921_3920_4812";
    doc["amount"] = 85.00;
    doc["merchant"] = "Target Store #102";
    doc["transaction_time"] = "12:30:00"; // Can fetch from NTP server
    doc["location"] = "New York, USA";
    doc["device_id"] = "esp32_terminal_01";
    doc["transaction_type"] = "Genuine";
    doc["latitude"] = 40.7128;
    doc["longitude"] = -74.0060;

    String requestBody;
    serializeJson(doc, requestBody);

    int httpResponseCode = http.POST(requestBody);

    if (httpResponseCode > 0) {
      String response = http.getString();
      Serial.println("Response Code: " + String(httpResponseCode));
      Serial.println("Response JSON: " + response);
    } else {
      Serial.println("Error on sending POST: " + String(httpResponseCode));
    }
    http.end();
  }
  
  delay(10000); // Send transaction every 10 seconds for testing
}
```
