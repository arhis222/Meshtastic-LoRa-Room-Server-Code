# Project Tracking Sheet: Room Server Meshtastic

---

**Project Name:** RoomServer_info4_2025_2026

**Team Members:** Arhan UNAY, Adam TAWFIK

**Supervisors:** Francois LETELLIER

**Start Date:** January 20, 2026

**Hardware:** Raspberry Pi 3B + Seeed Studio Wio-E5 Mini

**Repository:** https://github.com/arhis222/Meshtastic-LoRa-Room-Server-Code

---

## 1. Project Overview & Objectives

**Goal:** Design and implement a "Room Server" node for the Meshtastic network using a Raspberry Pi and Python.
The server manages chat rooms, stores messages persistently in SQLite, and remains robust against power failures.

**Key Features:**

* **LoRa Communication:** Sending/Receiving packets via Wio-E5 module.
* **Command Parsing:** Handling commands like `/room create`, `/room post`.
* **Persistence:** Storing history in a local SQLite database.
* **Robustness:** Auto-restart on power loss (Systemd).
* **Multi-client support**
* **Anti-spam protection**
* **Message chunking for LoRa limits**

---

## 2. Roadmap & Milestones


| Target Date     | Milestone                                      | Status      |
| :-------------- | :--------------------------------------------- | :---------- |
| **Jan 20 - 31** | Project Selection & Technical Analysis         | Done        |
| **Feb 02 - 06** | Hardware Acquisition & Backend Init (DB/Logic) | Done        |
| **Feb 09 - 13** | Git Setup, Documentation & Command Parser      | Done        |
| **Feb 16 - 20** | Winter Holiday                                 | Done        |
| **Feb 23 - 27** | LoRa Integration & Raspberry Pi Testing        | Done        |
| **Mar 02 - 06** | Backend Finalization & Robustness              | Done        |
| **Mar 09 - 13** | Optimization & Multi-client Tests              | Done        |
| **Mar 16 - 20** | Diagrams, Poster & Flyer                       | Done        |
| **Mar 23 - 27** | Final Report & Presentation                    | In Progress |

---

## 3. Weekly Log (Journal de Bord)

### Week 1 (Jan 20 - Jan 24)

* **Focus:** Project Discovery.
* **Tasks Completed:**
  * Team formation (Arhan & Adam).
  * Selection of the "Room Server" subject.
  * Analysis of requirements (specifications).
  * Defined the initial roadmap.


### Week 2 (Jan 27 - Jan 31)

* **Focus:** Technical Analysis & Component Selection.
* **Tasks Completed:**
  * Researched Meshtastic Python API documentation.
  * Compared storage options: **JSON vs SQLite**.
  * Selected SQLite for better reliability during power cuts.
  * Drafted the initial software architecture (Transport <-> Manager <-> DB).


### Week 3 (Feb 02 - Feb 06)

* **Focus:** Hardware Pickup & Database Design.
* **Tasks Completed:**
  * Collected Raspberry Pi 3B and LoRa modules (Wio-E5).
  * Designed SQLite schema (`rooms`, `messages` tables).
  * Implemented `database.py` and initial `room_manager.py`.
  * Tested database logic on PC.
* **Issues:**
  * Raspberry Pi failed to boot → fixed by replacing power adapter.


### Week 4 (Feb 09 - Feb 13)

* **Focus:** Git Structure, Documentation, Parser.
* **Tasks Completed:**
  * Created repository structure (`Src/`, `Documents/`).
  * Wrote `Technical_Architecture.md`.
  * Implemented `parser.py`.
  * Updated `room_manager.py`.
  * Verified SQLite on Raspberry Pi.


### Week 5 (Feb 16 - Feb 20)

* **Focus:** Holiday.
* **Tasks Completed:**
  * No development during this week.


### Week 6 (Feb 23 - Feb 27)

* **Focus:** LoRa Integration.
* **Tasks Completed:**
  * Connected Wio-E5 module.
  * Implemented communication layer.
  * Tested message send/receive.
  * Integrated with Raspberry Pi.
  * Created private LoRa network.
  * Added `/room help`, `/room post`, `/room read`.


### Week 7 (Mar 02 - Mar 06)

* **Focus:** Backend Finalization.
* **Tasks Completed:**
  * Completed `main.py`.
  * Added `logger.py`.
  * Added `reset_db.py`.
  * Added `client.py`.
  * Configured systemd auto restart.
  * Robustness tests.


### Week 8 (Mar 09 - Mar 13)

* **Focus:** Optimization.
* **Tasks Completed:**
  * Implemented `/room info`.
  * Implemented `/room announce`.
  * Added payload splitting.
  * Added anti-spam cooldown.
  * Tested multi-client usage.
  * Performance validation.


### Week 9 (Mar 16 - Mar 20)

* **Focus:** Documentation & Visuals.
* **Tasks Completed:**
  * General architecture diagram.
  * Software architecture diagram.
  * Sequence diagram.
  * Class diagram.
  * Poster creation.
  * Flyer creation.


### Week 10 (Mar 23 - Mar 27)

* **Focus:** Final Deliverables.
* **Tasks Completed:**
  * Final report writing.
  * Slides preparation.
  * Repository cleanup.
  * Final validation tests.

---

## 4. Risk Management & Solutions


| Risk Detected        | Impact                          | Mitigation Strategy / Solution                                        |
|:---------------------|:--------------------------------|:----------------------------------------------------------------------|
| **Power Failure**    | Data corruption / Server stops. | **Sol:** SQLite WAL mode + Systemd auto-restart service.              |
| **Hardware Failure** | Pi doesn't boot.                | **Sol:** Replaced power adapter (Feb 6).                              |
| **LoRa Bandwidth**   | Slow message retrieval.         | **Sol:** Limit `/room read` to last 5 messages by default + chunking. |
| **GitLab Outage**    | Not initialized yet.            | **Sol:** Used temporary private repo, will fork later.                |
| **Multiple clients** | Collision / spam                | **Sol:** Cooldown + queue.                                            |
| **Payload limit**    | Packet overflow.                | **Sol:** Message splitting.                                           |