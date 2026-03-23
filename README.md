<p align="center">
  <img src="images/logo1.png" width="180">
</p>

<h1 align="center">
LoRa Room Server — Source Code
</h1>

<p align="center">
Polytech Grenoble – INFO4 – 2025-2026
</p>

---

## Description

This repository contains the source code of the **LoRa Room Server** project.

The Room Server is a Python application running on a Raspberry Pi connected to a LoRa / Meshtastic node.
It extends the Meshtastic mesh network by adding persistent chat rooms, message history, and structured commands.

The server works fully offline and stores all data locally using SQLite.

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

### 3. Cheat Sheet: How to read logs (Run these commands yourself later)

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

## Commandes Disponibles

Pour interagir avec le serveur, envoyez ces commandes par **Message Direct (DM)** au nœud "Room Server" depuis votre application mobile Meshtastic :

### 🏠 Gestion des Salons (Rooms)

* **/room create <nom> [description]** : Crée un nouveau salon (la description est optionnelle).
* **/room list** : Affiche la liste paginée de tous les salons disponibles sur le serveur.
* **/room info <nom>** : Affiche les métadonnées d'un salon (Description, Date de création, Nombre total de messages, Dernière activité).
* **/room delete <nom>** : Supprime un salon spécifique de la base de données SQLite.

### 💬 Messagerie et Lecture

* **/room post <nom> <message>** : Publie un message dans un salon spécifique.
* **/room read <nom> [n]** : Lit les `n` derniers messages d'un salon (par défaut n=5, max n=10).

### 📢 Interactions Globales

* **/room announce <message>** : Diffuse (**Broadcast**) un message à **TOUS** les utilisateurs du canal `S8_Project`.
* **/room help** (ou **/room ?**) : Affiche la liste des commandes et l'aide à l'utilisation.

---

## Optimisations et Robustesse (Architecture)

Pour garantir la fiabilité du système face aux contraintes du réseau LoRa, nous avons implémenté plusieurs mécanismes avancés :

### 1. Protection Anti-Spam (Rate Limiting)

Pour respecter la réglementation sur le temps d'occupation des fréquences (**Duty Cycle**) et protéger la bande passante, un délai de **10 secondes** est imposé entre chaque commande par utilisateur. Si un utilisateur envoie des requêtes trop rapidement, le serveur ignore la commande et demande de patienter.

### 2. Gestion des Files d'Attente (FIFO Queue)

Le matériel LoRa étant **Half-Duplex** (ne peut pas émettre et recevoir simultanément), nous avons implémenté une file d'attente **FIFO** (First-In-First-Out) pour les messages sortants. Cela garantit que les réponses ne s'entrecroisent pas et que chaque paquet est envoyé après un délai de repos du matériel.

### 3. Découpage des Messages (Chunking)

En raison de la limite de charge utile (payload) de ~200 octets du protocole Meshtastic, le serveur découpe automatiquement les réponses longues en blocs de **32 caractères**. Chaque bloc est envoyé avec un délai de 4 secondes pour assurer une réception sans perte.

### 4. Architecture Stateless

Le serveur est conçu pour être "sans état" : il n'est pas nécessaire de rejoindre (`join`) ou de quitter (`leave`) un salon. L'utilisateur interagit directement via les commandes `post` et `read`, ce qui réduit considérablement le trafic réseau inutile.

---

## Sécurité

Le canal `S8_Project` est protégé par un chiffrement **AES-128/256**. La présence du **cadenas vert** sur l'interface client garantit que seules les personnes possédant la clé PSK (Pre-Shared Key) peuvent lire ou envoyer des messages sur le réseau.
EOF

echo "✅ README.md a été créé avec succès !"

> **💡 Note on Architecture:** > Unlike traditional chat servers, this LoRa Room Server is *stateless*. There are no `/room join` or `/room leave` commands. You do not need to "enter" a room to participate; you simply target the room name using the `post` and `read` commands. This drastically reduces unnecessary network traffic and saves valuable LoRa airtime!</name></name></message></name></name>

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

## For the detailed documentation and flyers, please visit:

https://github.com/arhis222/Meshtastic-LoRa-Room-Server-Documents

## License

This project is provided for academic purposes.

