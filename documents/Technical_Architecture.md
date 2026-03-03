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

## 4. Limitations

* **Bandwidth:** Due to LoRa duty cycles, the `read` command is limited to returning 3-5 messages at a time.
* **Latency:** Response time may vary between 2-10 seconds depending on network congestion.
