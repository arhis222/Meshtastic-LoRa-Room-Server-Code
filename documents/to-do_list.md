 Meshtastic Room Server - Implementation Guide
Project: Room Server (INFO4 S8) Hardware: Raspberry Pi 3B + Seeed Studio Wio-E5 Mini (LoRa) Language: Python 3.x Persistence: SQLite3 Architecture: Modular (MVC-like)

📋 Table of Contents
Hardware Setup
Software Installation
Project Architecture & Files
Deployment Steps
Automation (Systemd Service)
Testing Protocol
1. Hardware Setup
Connect LoRa Module: Connect the Seeed Studio Wio-E5 Mini to the Raspberry Pi 3B using a USB data cable.
Power Up: Turn on the Raspberry Pi (ensure the power supply provides at least 2.5A).
Verify Connection: Run the following command to find the serial port:
ls /dev/ttyUSB*
(You should see /dev/ttyUSB0. If using a different port, update main.py).

2. Software Installation
Update the system and install the required Python libraries (Meshtastic and PubSub).

# 1. Update Linux System
sudo apt update && sudo apt upgrade -y

# 2. Install Python pip (if not installed)
sudo apt install python3-pip

# 3. Install dependencies
# 'meshtastic' handles the LoRa communication
# 'pubsub' handles the internal event messaging
pip3 install meshtastic pubsub --break-system-packages
(Note: --break-system-packages is required on newer Raspberry Pi OS Bookworm versions).

3. Project Architecture & Files
We use a modular architecture to separate concerns (Hardware vs Logic vs Data). Directory Structure: /home/pi/room_server/

├──src/                    
    └── main.py                # Entry point (orchestrator)
    └── database.py            # SQLite database management
    └── room_manager.py        # Business logic (room/message handling)
    └── parser.py              # Command parsing logic
    └── meshtastic_comm_hw.py  # Hardware communication (real LoRa)
    └── meshtastic_comm.py     # Simulation communication (console)
    └── client.py              # Client simulator (for testing)
    └── reset_db.py            # Utility to reset the database
    └── README.md              # Project documentation
└── documents/             # Additional documentation (cahier des charges, architecture, etc
4. Deployment Steps
Clone the Repository:
git clone [https://gricad-gitlab.univ-grenoble-alpes.fr/Projets-INFO4/25-26/03]
cd [YOUR_REPO_NAME]/src
Set Permissions: Ensure the user has permission to access the USB port:
sudo usermod -a -G dialout pi
Manual Test: Run the server manually to check for errors:
python3 main.py
(You should see "Room Server started" in the terminal).

5. Automation (Systemd Service)
To ensure the Room Server starts automatically on boot, we create a systemd service in raspberry pi.

Create Service File:

sudo nano /etc/systemd/system/room_server.service
Add the following content:

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
Enable and Start the Service:

sudo systemctl daemon-reload
sudo systemctl enable room_server.service
sudo systemctl start room_server.service
Check Service Status:

sudo systemctl status room_server.service
(You should see "active (running)" if everything is correct).

View Logs:
sudo journalctl -u roomserver -f
(This will show real-time logs from the service).

6. Security: Private Channel Setup
By default, Meshtastic uses a public LongFast channel. To ensure our Room Server is secure and isolated (Réseau Privé), we configure an AES-256 encrypted Private Channel.

Step 1: Generate Keys on the Client (Meshcore App)
Open the Meshcore app on your iPhone and connect to the SenseCAP T1000-E tracker.

Go to Channels -> Index 0.
Change the Name to your project name (e.g., S8_Project).
Change the PSK (Pre-Shared Key) to Random. This generates a secure AES key.
Save the configuration to the tracker. Copy the generated Hex Secret Key.
Step 2: Apply Keys to the Server (Raspberry Pi)
On the Raspberry Pi terminal, configure the Wio-E5 module to use the same credentials:

# 1. Stop the python server to free the USB port
sudo systemctl stop room_server.service

# 2. Set the exact same channel name
meshtastic --ch-set name "Project-S8" --ch-index 0

# 3. Set the encryption key (Must be prefixed with '0x')
# Replace the string below with your actual Meshcore secret key
meshtastic --ch-set psk "0x26471a28695f6f6bc5b90d27ae1149a7" --ch-index 0


# 4. Restart the python server
sudo systemctl start room_server.service 
Now, the Server and Client communicate in a completely encrypted, private LoRa environment.

source .venv/bin/activate
pip install meshtastic

python3 -m meshtastic --port /dev/ttyUSB0 --set lora.region EU868
python3 -m meshtastic --port /dev/ttyUSB0 --ch-set name "S8_Project" --ch-set psk random --ch-index 0
python3 -m meshtastic --port /dev/ttyUSB0 --info | grep "http"

python3 -m meshtastic --port /dev/ttyUSB0 --seturl  "https://meshtastic.org/e/#ChESAQEaClM4X1Byb2plY3QoARIRCAEQBzgDQANIAVAbaAHABgE"
7. Testing Protocol
To validate the system, you need two separate devices:

Server: Raspberry Pi + LoRa Module A (Running main.py via systemd).
Client: Laptop/PC + LoRa Module B (Running client.py).
Client Setup (On your Laptop)
Connect the second LoRa module to your computer.
Open a terminal (or Command Prompt) and navigate to the project folder.
Start the client script:
python3 client.py
Enter the serial port when prompted (e.g., COM3 on Windows or /dev/ttyACM0 on Linux).
Test A: Functional Testing
Scenario: Interact with the server using the Client terminal you just opened.

Create Room:

Input: /room create ProjectAlpha
Expected Reply: [SERVER]: OK room 'ProjectAlpha' created
Post Message:

Input: /room post ProjectAlpha Hello Team
Expected Reply: [SERVER]: OK posted to 'ProjectAlpha'
Read History:

Input: /room read ProjectAlpha
Expected Reply:
'ProjectAlpha':
14:30 #12345: Hello Team
Test B: Robustness ("Plug Pull" Test)
Scenario: Power failure simulation.

Ensure the server is running and has stored messages (from Test A).
Action: Physically unplug the power cable of the Raspberry Pi.
Action: Plug it back in and wait for boot (approx. 2 mins).
Action: On your Client terminal, request the room list.
Input: /room list
Success Criteria: The server responds, and ProjectAlpha is still listed. (This proves SQLite persistence and Systemd auto-start are working).
Maintenance
If the database becomes corrupted or needs a reset:

# Stop the service first
sudo systemctl stop roomserver.service

# Run the cleaner tool
python3 reset_db.py

# Restart service
sudo systemctl start roomserver

### Commandes de MAJ Raspberry Pi
ssh pi@raspberrypi.local 
cd ~/Desktop/repertoire/ProjetS8/Src 
scp *.py pi@raspberrypi.local:/home/pi/room_server/

