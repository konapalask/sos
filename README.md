# SOS Emergency Alert System

A production-ready, modular Emergency Alert System integrating an **ESP32** microcontroller, a **Python Flask** REST API, an **SQLite** database, and automated **WhatsApp Web notifications** driven by Selenium WebDriver. 

When the physical hardware button is pressed, a buzzer sounds instantly for 5 seconds while the backend server logs the event and automatically forwards emergency warnings to multiple WhatsApp contacts in the background.

---

## Folder Structure

```text
SOS_Project/
│
├── esp32/
│   └── sos.ino                  # ESP32 C++ Arduino Firmware
│
├── backend/
│   ├── app.py                   # Main Flask application entrypoint
│   ├── config.py                # Environment parser & validation config
│   ├── database.py              # SQLite connection builder & table creation
│   ├── whatsapp.py              # Selenium WebDriver wrapper automation
│   ├── logger.py                # System-wide file & console logger
│   ├── requirements.txt         # Python dependencies
│   │
│   ├── routes/
│   │   └── sos.py               # REST API blueprints (/sos, /alerts, /status)
│   │
│   ├── services/
│   │   ├── wifi.py              # Connection verification utilities
│   │   ├── notification.py      # Alert message formatter and sender
│   │   └── database_service.py  # SQLite queries wrapper
│   │
│   ├── database/
│   │   └── sos.db               # SQLite database file (auto-generated)
│   │
│   ├── logs/
│   │   └── sos.log              # Persistent operation logs (auto-generated)
│   │
│   ├── templates/               # (Auto-generated structure template)
│   └── static/                  # (Auto-generated static folder)
│
├── dashboard/
│   ├── index.html               # Real-time monitor command center UI
│   ├── style.css                # Custom glassmorphic styles (dark-theme)
│   └── script.js                # Live fetching, search, and table updater
│
├── .env                         # Configuration variables
└── README.md                    # Project documentation (this file)
```

---

## Hardware Configurations (ESP32)

### Pin Routing
*   **GPIO 4**: Push Button (configured with internal `INPUT_PULLUP`). Connect between **GPIO 4** and **GND**.
*   **GPIO 18**: Buzzer Output (Active HIGH). Drives the 12V Buzzer through a transistor circuit (e.g., NPN transistor like 2N2222 or TIP120 with flyback diode protection).

### Circuit Wiring Concept
```text
           +---------------------------------+
           |             ESP32               |
           |                                 |
           |   GND -----[ Button ]----- GPIO4 |
           |                                 |
           |  GPIO18 ---[ R 1k ]---+         |
           +-----------------------|---------+
                                   |
                                 Base (B)
                           NPN   /
                    Collector   |
                   +--[12V Buzzer]
                   |    |
          +12V ----+    +-- Emitter (E) -> GND
```

---

## Installation & Setup

### 1. Python Server Configuration
1. **Navigate to the Backend Directory**:
   ```bash
   cd backend
   ```
2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Configure Environment Variables**:
   Open the `.env` file in the root of the project directory and update the settings:
   *   `WHATSAPP_CONTACTS`: Enter a list of emergency phone numbers separated by commas (with country code, but **do not** include `+`, spaces, or symbols). E.g., `919876543210,15550199`.
   *   `SELENIUM_HEADLESS`: Set to `false` (default) during initial setup so that Chrome opens visibly to scan the QR code.
   *   `WIFI_SSID` & `WIFI_PASSWORD`: Setup your local network credentials (referenced in the ESP32 code).

### 2. WhatsApp Authentication (Crucial First Step)
Before running the device in production, establish your WhatsApp session:
1. **Start the Flask Backend**:
   ```bash
   python app.py
   ```
2. On startup, a Chrome browser window will open automatically navigating to `https://web.whatsapp.com`.
3. Scan the displayed **QR Code** using your phone's WhatsApp application (*Linked Devices > Link a Device*).
4. Keep the server running. The session files will be saved in `backend/selenium_session/` so you **do not** need to re-scan the QR code on future restarts.

### 3. Flash the ESP32
1. Open the [esp32/sos.ino](file:///d:/SOS_Project/esp32/sos.ino) file in your Arduino IDE.
2. In the configurations at the top, update:
   *   `ssid` & `password` to match your local Wi-Fi router.
   *   `serverUrl` to point to the IP address of your computer running the Flask server. For example: `http://192.168.1.150:5000/sos`.
3. Connect your ESP32 board and upload the code.
4. Open the Arduino IDE Serial Monitor (baud rate `115200`) to view status logs.

### 4. Open the Dashboard Command Center
*   Access the web dashboard in one of two ways:
    *   Open `http://localhost:5000/` in your browser (served by the Flask app).
    *   Or double-click the [dashboard/index.html](file:///d:/SOS_Project/dashboard/index.html) file directly to load it as a static page (CORS is supported).

---

## Operating Instructions

### Button Trigger Action
1. Press the emergency button.
2. **ESP32 Response**:
   *   The 12V buzzer sounds immediately.
   *   The ESP32 prints status messages to the Serial Monitor.
   *   It sends an HTTP POST request to the Flask server.
   *   Exactly 5 seconds after pressing, the buzzer stops sounding.
   *   Holding down the button will **not** trigger duplicate requests (the system uses rising/falling edge transition filters).
3. **Backend Response**:
   *   The Flask server processes the incoming POST request, creates a record inside the SQLite database, and returns a JSON response to the ESP32 instantly.
   *   It spawns a background thread which directs the Chrome Selenium browser to navigate to the WhatsApp chat link for each configured number and dispatch the SOS message.
   *   Logs are appended immediately in `backend/logs/sos.log`.
4. **Dashboard**:
   *   The metrics cards and data tables refresh dynamically. The new alert card flashes neon red.

---

## Vercel Deployment

This project includes a `vercel.json` configuration file, which allows you to deploy the backend and the dashboard directly to Vercel as serverless endpoints.

### How to Deploy
1. Install the Vercel CLI:
   ```bash
   npm install -g vercel
   ```
2. Run the deployment command from the root directory of the project:
   ```bash
   vercel
   ```
3. Add your environment variables (such as `WHATSAPP_CONTACTS`) in your Vercel Dashboard under **Settings > Environment Variables**.

> [!WARNING]
> **Serverless Runtime Limitations**
> Deploying to a serverless platform like Vercel introduces two key limitations:
> 1. **Selenium / Chrome Compatibility**: Selenium requires Chrome/Chromium and ChromeDriver binaries installed in the host OS. Since Vercel's serverless containers do not contain Chrome, WhatsApp automation will fail (though the Flask server handles this error gracefully and will continue serving endpoints).
> 2. **SQLite Ephemeral Storage**: Vercel serverless environments are stateless. The SQLite database (`sos.db`) is written to ephemeral storage and will reset every time Vercel scales down or spins up a new instance.
> 
> *Recommendation*: For hosting in the cloud, run this server on a persistent VM (like AWS EC2, DigitalOcean Droplet, or Raspberry Pi) to support WhatsApp Web automation and SQLite data persistence.

---

## Troubleshooting

### Chrome Driver / Selenium Issues
*   **Version Mismatch**: The application uses `webdriver-manager` inside Selenium 4, which automatically downloads the correct driver for your local Chrome version. Ensure Chrome is updated on your server computer.
*   **Browser Crash**: If you close the Chrome window manually or Chrome crashes, the server will detect it and auto-reinitialize a fresh browser window on the next incoming SOS event.
*   **Headless Mode**: You can set `SELENIUM_HEADLESS=true` in `.env` only *after* you have successfully scanned the QR code in visible mode.

