# Technical Architecture & Design Choices

---

## 1. Global Architecture

The system follows a modular architecture to separate communication logic from business logic.

### Hardware Setup

[ Raspberry Pi ] <--(USB Serial)--> [ LoRa Module ] <~~(Radio)~~> [ Client Nodes ]

### Detailed Software Architecture

Here is the technical description of each Python module composing the **Room Server LoRa** project:


| File / Module               | Main Role                            | Technical Description                                                                                                                                              |
| :-------------------------- | :----------------------------------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **`main.py`**               | **Entry Point (Orchestrator)**       | This is the file executed to start the server. It initializes the database, the`RoomManager`, and connects the hardware.                                           |
| **`database.py`**           | **Data Management (Storage)**        | Manages the**SQLite** connection. It creates the tables (`rooms`, `messages`) and contains functions to insert or read data (CRUD).                                |
| **`room_manager.py`**       | **Business Logic (Brain)**           | Decides what to do with a message. If it's a command, it executes it. If it's a message, it stores it. It acts as the link between the`Parser` and the `Database`. |
| **`parser.py`**             | **Syntax Parser (Translator)**       | Analyzes the received text. It detects if the message starts with`/` (e.g., `/room create`) and separates the action from the arguments.                           |
| **`meshtastic_comm_hw.py`** | **Hardware Interface (Real Driver)** | This is the Wio-E5 "driver". It listens to the USB port (`/dev/ttyUSB0`), captures incoming LoRa signals, and sends responses.                                     |
| **`meshtastic_comm.py`**    | **Simulation Interface (Mock)**      | Simulates the LoRa interface via the console. Allows testing the entire server logic without connected hardware, using the keyboard as input and screen as output. |
| **`client.py`**             | **Client Simulator (Tester)**        | The script used on the test computer. It allows sending messages to the server via a second LoRa module, simulating a real user.                                   |
| **`reset_db.py`**           | **Maintenance Tool (Cleaner)**       | A small utility script to cleanly delete the`.db` file and reset the database to zero in case of problems.                                                         |
| **`logger.py`**             | **Logging (Tracker)**                | (Integrated into other files) Used to display colored messages in the terminal (`INFO`, `ERROR`, `DEBUG`) to facilitate debugging.                                 |

### How they interact (Data Flow)

To illustrate the system operation, here is the logical flow of a command (example: creating a room) through the different modules:

1. **`meshtastic_comm_hw.py`** receives a radio signal 📡 ➔ Transmits raw text to the system.
2. **`parser.py`** analyzes the text 🧐 ➔ Determines: "It is a `/room create` command".
3. **`room_manager.py`** receives the order 🧠 ➔ Decides: "I must create a room".
4. **`database.py`** executes the order 💾 ➔ Writes: "Room created in SQL table".
5. **`room_manager.py`** prepares the response ✅ ➔ Generates the text: "OK, room created".
6. **`meshtastic_comm_hw.py`** sends the response back via radio 📡 ➔ Emits the signal to the user.

---

## 2. Data Persistence Strategy

We selected **SQLite** as our storage engine.

* **Justification:** unlike a flat JSON file, SQLite supports atomic transactions. This is crucial for the "Brutal Shutdown" requirement. If power is lost during a write operation, the database file is less likely to be corrupted compared to a text file.
* **Schema:**
  * `rooms` (id, name, description, created_at)
  * `messages` (id, room_id, sender_node_id, timestamp, content)

---

## 3. Sequence Diagrams

[[sequence_diagram.png]])* TODOOOOOOOOOOO

**Scenario: Posting a Message**

1. **User** sends `/room post General Hello`.
2. **Comm Layer** receives packet -> extracts text.
3. **Parser** identifies command `post`, target `General`.
4. **Controller** checks if `General` exists.
5. **DB** inserts message record.
6. **Comm Layer** sends acknowledgment "Message Saved".

---

## 4. Optimisation du Réseau : Réponses en Messages Privés (Direct Messages)

Lors de l'utilisation du serveur, vous remarquerez que si vous envoyez une commande (ex: `/room list` ou `/room read`) dans le canal public du projet (ex: `projet_s8`), le serveur ne répond pas dans ce même canal public, mais ouvre une **conversation privée** avec votre téléphone.

### Pourquoi ce choix technique ?

1. **Économie de la bande passante (Duty Cycle) :** Le réseau LoRa est extrêmement contraint. Si le serveur diffusait (Broadcast) la liste de tous les salons ou l'historique des messages dans le canal public, cela monopoliserait l'antenne et spammerait l'écran de tous les utilisateurs du réseau.
2. **Expérience Utilisateur (UX) :** Chaque téléphone (nœud client) reçoit ses propres requêtes de manière isolée et privée, rendant la lecture beaucoup plus claire. Le canal public reste ainsi propre et réservé aux communications globales.

### Configuration de l'identité du Serveur

Par défaut, le module Wio-E5 branché au Raspberry Pi s'identifie sur le réseau avec un nom générique lié à son adresse MAC (par exemple : `Meshtastic 1446`).

Pour rendre l'interface plus intuitive pour les utilisateurs finaux, nous avons renommé le nœud serveur pour qu'il apparaisse clairement comme le **"Room Server"** lors de l'envoi des messages privés.

Cette configuration a été appliquée via la commande Meshtastic CLI suivante sur le Raspberry Pi :

```bash
meshtastic --set-owner "Room Server" --set-owner-short "SRV"
```

## 5. Limitations et Optimisations (Contraintes LoRa)

* **Bande Passante (Bandwidth) :** En raison des règles strictes de temps d'antenne (*Duty Cycle* LoRa) et du faible débit, la commande `read` est volontairement limitée pour ne retourner que 1 à 10 messages à la fois afin d'éviter de saturer le réseau.
* **Latence (Latency) :** Le temps de réponse asynchrone peut varier entre 2 et 30 secondes en fonction de la congestion du réseau et des sauts radio (hops) nécessaires.
* **Taille des Messages (Chunking à 32 caractères) :** Bien que la charge utile (payload) maximale théorique d'un paquet Meshtastic soit d'environ 200 octets, nous avons conçu le serveur pour découper systématiquement les messages longs en blocs de **32 caractères maximum**. Ce choix technique répond à deux enjeux majeurs :
  1. *Réduction du "Time-on-Air" et des pertes :* Des paquets très courts minimisent le temps d'émission radio. Cela réduit drastiquement le risque de collisions en vol et de pertes de paquets (Packet Loss), rendant notre système beaucoup plus robuste.
  2. *Expérience Utilisateur (UX) optimisée :* La limite de 32 caractères correspond à la largeur de lecture idéale pour les petits écrans matériels (ex: écrans OLED des modules Heltec) et les terminaux mobiles, garantissant un affichage propre sans coupure arbitraire des mots au milieu d'une phrase.

## 6. Protection Anti-Spam (Rate Limiting)

* **Protection contre le Spam :** Afin d'éviter la saturation du réseau LoRa et les abus potentiels, le serveur implémente un mécanisme de **cooldown par utilisateur**. Chaque nœud doit attendre **10 secondes** entre deux commandes `/room`.
* **Gestion du Débit Réseau :** Cette limitation empêche l'envoi de commandes en rafale qui pourraient monopoliser l'antenne et perturber les communications des autres utilisateurs sur le réseau Meshtastic.
* **Retour Utilisateur (Feedback) :** Si un utilisateur tente d'envoyer une commande avant la fin du délai, le serveur rejette la requête et renvoie un message d'erreur indiquant le temps restant avant la prochaine commande autorisée.
Exemple de réponse :
Ce mécanisme contribue à maintenir **la stabilité et la fiabilité du serveur** dans un environnement radio contraint comme LoRa.