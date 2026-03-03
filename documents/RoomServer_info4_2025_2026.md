# Project Tracking Sheet: Room Server Meshtastic

---

**Project Name:** RoomServer_info4_2025_2026

**Team Members:** Arhan UNAY, Adam TAWFIK

**Supervisors:** Francois LETELLIER

**Start Date:** January 20, 2026

**Hardware:** Raspberry Pi 3B + Seeed Studio Wio-E5 Mini

**Repository:** [Link to GitLab Repository] for later

---

## 1. Project Overview & Objectives

**Goal:** Design and implement a "Room Server" node for the Meshtastic network using a Raspberry Pi and Python. The
server must manage chat rooms, store messages persistently in a database, and ensure robustness against power failures.

**Key Features:**

* **LoRa Communication:** Sending/Receiving packets via Wio-E5 module.
* **Command Parsing:** Handling commands like `/room create`, `/room post`.
* **Persistence:** Storing history in a local SQLite database.
* **Robustness:** Auto-restart on power loss (Systemd).

---

## 2. Roadmap & Milestones

| Target Date     | Milestone                                      | Status      |
|:----------------|:-----------------------------------------------|:------------|
| **Jan 20 - 31** | Project Selection & Technical Analysis         | Done        |
| **Feb 02 - 06** | Hardware Acquisition & Backend Init (DB/Logic) | Done        |
| **Feb 09 - 13** | Git Setup, Documentation & Command Parser      | Done        |
| **Feb 17 - 21** | Hardware Integration (Wio-E5 Driver)           | In Progress |
| **Feb 24 - 28** | Full System Integration & Testing              | Planned     |
| **Mar 02 - 06** | Final Documentation & Defense                  | Planned   |

---

## 3. Weekly Log (Journal de Bord)

###  Week 4 (Feb 09 - Feb 13)

* **Focus:** Git Structure, Documentation, Parsing Logic.
* **Tasks Completed:**
    * **Git:** Created a private repository (due to GitLab outage) and structured folders (`Src/`, `Documents/`).
    * **Docs:** Created `Technical_Architecture.md` and this tracking sheet.
    * **Code:** Implemented `parser.py` (regex for commands) and updated `room_manager.py`.
    * **Hardware:** Solved the Raspberry Pi power issue (new adapter). Verified SQLite runs on the Pi.
* **Issues:** Official GitLab was not yet ready; work continued on local/private git.

###  Week 3 (Feb 02 - Feb 06)

* **Focus:** Hardware Pickup & Database Design.
* **Tasks Completed:**
    * Collected Raspberry Pi 3B and LoRa modules (Wio-E5) from FabLab.
    * **Backend:** Designed SQLite schema (`rooms`, `messages` tables).
    * **Code:** Wrote the initial `database.py` and `room_manager.py`.
    * **Testing:** Validated database logic on PC (Mock environment).
* **Issues:** Raspberry Pi failed to boot. **Diagnosis:** The power adapter provided was insufficient (low amperage).

###  Week 2 (Jan 27 - Jan 31)

* **Focus:** Technical Analysis & Component Selection.
* **Tasks Completed:**
    * Researched Meshtastic Python API documentation.
    * Compared storage options: **JSON vs SQLite**. Decided on SQLite for better data integrity during power cuts.
    * Drafted the initial software architecture (Modular design: Transport <-> Manager <-> DB).

###  Week 1 (Jan 20 - Jan 24)

* **Focus:** Project Discovery.
* **Tasks Completed:**
    * Team formation (Arhan & Adam).
    * Selection of the "Room Server" subject.
    * Analysis of requirements (specifications).
    * Defined the initial roadmap.

---

## 4. Risk Management & Solutions

| Risk Detected        | Impact                          | Mitigation Strategy / Solution                             |
|:---------------------|:--------------------------------|:-----------------------------------------------------------|
| **Power Failure**    | Data corruption / Server stops. | **Sol:** SQLite WAL mode + Systemd auto-restart service.   |
| **Hardware Failure** | Pi doesn't boot.                | **Sol:** Replaced power adapter (Feb 6).                   |
| **LoRa Bandwidth**   | Slow message retrieval.         | **Sol:** Limit `/room read` to last 5 messages by default. |
| **GitLab Outage**    | Not initialized yet.            | **Sol:** Used temporary private repo, will fork later.     |