# Room Server

A Python-based application running on a Raspberry Pi that acts as a central "Room Server" for the Meshtastic LoRa mesh network. It allows users to create channels, join rooms, and store messages persistently.

---

## Features

* **Room Management:** Create, list, and delete chat rooms via LoRa messages.
* **Persistence:** All rooms and messages are stored in a local SQLite database.
* **Robustness:** Automatically recovers state after power failures.
* **Low Bandwidth Optimization:** Concise error messages and command feedback.

---

## Hardware Requirements

* 1x Raspberry Pi (Zero 2 W, 3, or 4).
* 1x Meshtastic LoRa Module (Heltec V3, T-Beam, or RAK) connected via USB. (2 ou plus pour tester le client)
* (Optional) A second Meshtastic device for client testing.

---

## Installation

### 1. Prerequisites

Ensure your Raspberry Pi is running Raspberry Pi OS and has Python 3 installed.

```bash
sudo apt update
sudo apt install python3-pip
```

### 2. Install Dependencies

This project relies on the official Meshtastic library.

```bash
pip3 install meshtastic
```

### 3. Clone the Repository

```bash
git clone [https://gricad-gitlab.univ-grenoble-alpes.fr/Projets-INFO4/25-26/03]
cd [YOUR_REPO_NAME]
```

---

## Configuration

### 1. Create the systemd service file

This creates the 'roomserver.service' file to auto-start the Python server

```bash
echo "Creating the systemd service file..."

cat << 'EOF' | sudo tee /etc/systemd/system/roomserver.service > /dev/null
[Unit]
Description=Meshtastic Room Server
After=network.target

[Service]
Type=simple

# Path to python and main.py

ExecStart=/usr/bin/python3 /home/pi/room_server/main.py

# Important: WorkingDirectory ensures SQLite DB is created in the right place

WorkingDirectory=/home/pi/room_server/

# Logging

StandardOutput=inherit
StandardError=inherit

# Auto-restart logic

Restart=always
RestartSec=10
User=pi

[Install]
WantedBy=multi-user.target

EOF
```

### 2. Enable and Start the service

```bash
echo "Reloading systemd daemon..."
sudo systemctl daemon-reload

echo "Enabling the service to start automatically on boot..."
sudo systemctl enable roomserver.service

echo "Starting the service now..."
sudo systemctl start roomserver.service

echo "Setup complete! The Room Server is now running in the background."
echo ""
```

### 3. Cheat Ssheet: How to read logs (Run these commands yourself later)

First connect to raspberrypi with this command and enter 'raspberry' for the password

```bash
ssh pi@raspberrypi.local

```

To watch live logs streaming in real-time (Press Ctrl+C to exit):

```bash
sudo journalctl -u roomserver.service -f
```

To see only the last 50 lines of the logs:

```bash
sudo journalctl -u roomserver.service -n 50
```

To check the current status (is it running, crashed, or waiting?):

```
sudo systemctl status roomserver.service
```

To manually stop the server:

```bash
sudo systemctl stop roomserver.service
```

---

## Usage manuel

### For the Server

Starting the Server
Run the main script:

```bash
python3 room_server.py
```

if permission is denied to access the USB device, you might need to run (change the port if your LoRa is on a different one):

```bash
sudo chmod 666 /dev/ttyUSB0
```

### For the Client

Run the following command to start the client interface to test with lora plugged into your computer:

```bash
python3 client.py
```

---

## Client Commands (Via LoRa)

Send these messages from your Meshtastic mobile app to the Node ID of the server:

* `/room create <room_name>` - Create a new chat room.
* `/room list` - List all available chat rooms.
* `/room join <room_name>` - Join a specific chat room.
* `/room leave` - Leave the current chat room.
* `/msg <message>` - Send a message to the current room.
* `/help` - Display help information.
* ...

---

## Architecture

The Room Server consists of the following components:

* main.py: Entry point that initializes the server.
* ...

---

## Console UX & Emoji-Based Feedback

To improve readability and make interactions clearer in a low-bandwidth LoRa environment, we intentionally use visual emojis in console logs and messages.

This helps to:

- Instantly distinguish success / error states
- Clearly separate transmitted (TX) and received (RX) messages
- Identify who sent the message
- Make connection state changes obvious
- Quickly detect hardware or USB failures
- Improve log readability with timestamps

Since the system runs headless on a Raspberry Pi and is monitored via journalctl, these visual markers significantly improve debugging and live monitoring.

### Example Console Outputs

Connection Lifecycle

```python
print(f"🔌 Connecting to port {port}...")
print("✅ CONNECTED! The system is ready.")
print("👋 Disconnecting... Goodbye!")
```

Error Handling

```python
print("❌ Error: No port specified.")
print("⚠️ ID must be an integer.")
log.error("🚨 USB Cable removed! Disconnecting interface...")
```

Transmission (TX)

```python
log.info(f"📡 [TX Hardware Broadcast] {text}")
print(f"👤 [{timestamp}] YOU ▶ {msg}")
```

Reception (RX)

```python
log.info(f"📩 [RX Hardware] From {sender_id}: {text}")
```

---

## Authors

* Arhan UNAY
* Adam TAWFIK
