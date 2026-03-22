# Project Tracking Sheet: Room Server Meshtastic

---

**Project Name:** RoomServer_info4_2025_2026

**Team Members:** Arhan UNAY, Adam TAWFIK

**Supervisors:** Francois LETELLIER

**Start Date:** January 20, 2026

**Hardware:** Raspberry Pi 3B + Seeed Studio Wio-E5 Mini

**Repository:** GitLab repository / temporary private repository used during GitLab outage

---

## 1. Project Overview & Objectives

**Goal:** Design and implement a "Room Server" node for the Meshtastic network using a Raspberry Pi and Python.  
The server must manage chat rooms, store messages persistently in a database, and ensure robustness against power failures, USB disconnections, and low-bandwidth LoRa constraints. :contentReference[oaicite:4]{index=4} :contentReference[oaicite:5]{index=5}

**Key Features:**

* **LoRa Communication:** Sending and receiving packets through the Wio-E5 module.
* **Command Parsing:** Handling commands such as `/room create`, `/room list`, `/room post`, `/room read`, and `/room help`.
* **Persistence:** Storing message history in a local SQLite database.
* **Robustness:** Auto-restart on power loss or crash using `systemd`.
* **Private Network Testing:** Use of a dedicated private LoRa channel with a PSK to isolate the project from public traffic.
* **Operational Tooling:** Logging, reset utility, and a client-side CLI for testing and demonstration. :contentReference[oaicite:6]{index=6} :contentReference[oaicite:7]{index=7}

---

## 2. Roadmap & Milestones

| Target Date     | Milestone                                                | Status |
|:----------------|:---------------------------------------------------------|:------|
| **Jan 20 - 31** | Project Selection & Technical Analysis                   | Done |
| **Feb 02 - 06** | Hardware Acquisition & Backend Initialization            | Done |
| **Feb 09 - 13** | Git Setup, Documentation & Command Parser                | Done |
| **Feb 17 - 21** | RoomManager Development & First Hardware Preparation     | Done |
| **Feb 24 - 28** | LoRa Integration, Message Format Optimization, Private Network | Done |
| **Mar 02 - 06** | Backend Finalization, Client CLI, Logging, Systemd Robustness | Done |
| **Mar 09 - 15** | Validation, Architecture Diagrams, Technical Documentation | Done |
| **Mar 16 - 22** | Final Report, Flyer, and Final Project Packaging         | In Progress |

---

## 3. Weekly Log (Journal de Bord)

### Week 1 (Jan 20 - Jan 24)

* **Focus:** Project Discovery.
* **Tasks Completed:**
  * Team formation (Arhan & Adam).
  * Selection of the "Room Server" project.
  * Analysis of the official specifications.
  * Definition of the initial roadmap.
* **Issues:** None at this stage; work focused on understanding the project scope. :contentReference[oaicite:8]{index=8}

### Week 2 (Jan 27 - Jan 31)

* **Focus:** Technical Analysis & Component Selection.
* **Tasks Completed:**
  * Researched Meshtastic Python API documentation.
  * Compared storage strategies: **JSON vs SQLite**.
  * Chose **SQLite** for better integrity and transaction support in case of abrupt shutdown.
  * Drafted the first modular software architecture.
* **Issues:** Need to keep the design simple enough for embedded deployment. :contentReference[oaicite:9]{index=9}

### Week 3 (Feb 02 - Feb 06)

* **Focus:** Hardware Pickup & Database Design.
* **Tasks Completed:**
  * Collected Raspberry Pi 3B and Wio-E5 LoRa modules from FabLab.
  * Designed SQLite schema with `rooms` and `messages` tables.
  * Wrote the initial versions of `database.py` and `room_manager.py`.
  * Performed first local database tests on PC.
* **Issues:**
  * Raspberry Pi did not boot correctly.
  * Diagnosis showed that the provided power adapter was insufficient. :contentReference[oaicite:10]{index=10}

### Week 4 (Feb 09 - Feb 13)

* **Focus:** Git Structure, Documentation, Parsing Logic.
* **Tasks Completed:**
  * Created a temporary private repository due to GitLab outage.
  * Structured the project into `Src/` and `Documents/`.
  * Created `Technical_Architecture.md` and the tracking sheet.
  * Implemented `parser.py`.
  * Continued `RoomManager` development.
  * Solved the Raspberry Pi power issue with a proper adapter.
  * Validated SQLite operation directly on the Raspberry Pi.
* **Issues:**
  * Official GitLab was still unavailable.
  * The complete RoomManager logic was not finished yet. :contentReference[oaicite:11]{index=11}

### Week 5 (Feb 17 - Feb 21)

* **Focus:** RoomManager Completion & Hardware Communication Preparation.
* **Tasks Completed:**
  * Continued implementing room and message management logic.
  * Prepared the first hardware communication tests between Python and the LoRa module.
  * Confirmed that the software chain was ready for real LoRa integration.
* **Issues:**
  * Hardware integration still needed stabilization before complete end-to-end validation.

### Week 6 (Feb 23 - Feb 27)

* **Focus:** LoRa Integration & Communication Tests.
* **Tasks Completed:**
  * Configured the LoRa region (`EU_868`) and tested the serial connection through Meshtastic CLI.
  * Validated short message exchange between two physical nodes.
  * Tested `/room` commands over the LoRa link.
  * Optimized the message format to cope with payload limitations.
  * Improved `RoomManager` for `/room help`, `/room post`, and `/room read`.
  * Corrected parsing of multi-word messages.
  * Tested the server directly on Raspberry Pi.
  * Verified persistent storage after restart.
  * Configured a **private LoRa network** with a dedicated PSK and channel.
* **Issues:**
  * Long messages were not always correctly received.
  * Some message loss was observed due to LoRa bandwidth constraints.
  * Regional configuration and payload size limitations required several adjustments. 

### Week 7 (Mar 02 - Mar 06)

* **Focus:** Client Validation, Backend Finalization & Robustness.
* **Tasks Completed:**
  * Held the client/supervisor meeting on March 2 to validate specifications and project direction.
  * Finalized `main.py` as the system entry point.
  * Implemented `logger.py` for centralized logging.
  * Implemented `reset_db.py` for safe test database cleanup.
  * Developed `client.py`, the command-line interface for user-side testing.
  * Deployed the complete software suite on Raspberry Pi.
  * Solved USB disconnection crash issues by monitoring hardware path presence.
  * Configured a `systemd` service to automatically restart the server after crash or reboot.
* **Issues:**
  * Debugging the server in background mode was initially difficult.
  * This was mitigated through structured logs and `journalctl`. 

### Week 8 (Mar 09 - Mar 15)

* **Focus:** Validation, Analysis, and Technical Documentation.
* **Tasks Completed:**
  * Continued end-to-end validation on real hardware.
  * Confirmed the main demonstrator scenarios: room creation, message posting, room reading, and persistence after reboot.
  * Consolidated architecture notes, planning, and project management documentation.
  * Started preparing diagrams for the final report.
* **Issues:**
  * Quantitative benchmarking remained limited because of time and hardware constraints. 

### Week 9 (Mar 16 - Mar 22)

* **Focus:** Final Report, Diagrams, and Deliverables Packaging.
* **Tasks Completed:**
  * Completed the final report structure.
  * Added the project planning timeline, architecture diagram, software architecture diagram, sequence diagram, and class diagram.
  * Prepared the flyer and final documentation package.
  * Consolidated bibliography, appendices, and lessons learned.
* **Issues:**
  * Final polishing and formatting adjustments remained to be completed before final submission. 

---

## 4. Risk Management & Solutions

| Risk Detected | Impact | Mitigation Strategy / Solution | Status |
|:--|:--|:--|:--|
| **Power Failure** | Data corruption / server stops | Use SQLite transactions and a `systemd` auto-restart service | Observed and mitigated |
| **Insufficient Raspberry Pi Power Supply** | Raspberry Pi fails to boot | Replaced the power adapter with a suitable one | Observed and solved |
| **LoRa Payload Size Limits** | Message truncation or packet loss | Reduced payload size, simplified formatting, and split content when needed | Observed and mitigated |
| **USB Hardware Disconnection** | Server hang / no communication | Monitor device presence and rely on `systemd` watchdog behavior | Observed and mitigated |
| **Public Channel Interference** | Noise from external Meshtastic users | Configure a private channel with a dedicated PSK | Observed and mitigated |
| **GitLab Outage** | Delayed official repository usage | Used a temporary private repository during the outage | Observed and mitigated |
| **Limited Time for Large-Scale Benchmarking** | Incomplete quantitative validation | Prioritized functional validation and demonstrator robustness | Partially accepted | 

---

## 5. Current Project Status

**Overall Status:** Advanced / Finalization phase

### What has been completed
* Core backend architecture
* SQLite persistence layer
* Parser and RoomManager logic
* LoRa communication tests
* Raspberry Pi deployment
* Private LoRa network configuration
* `main.py`, `client.py`, `logger.py`, `reset_db.py`
* `systemd` auto-restart service
* Technical report with diagrams
* Planning and project documentation

### What remains
* Final proofreading and formatting of documents
* Last consistency check between report, flyer, and repository
* Final packaging for submission

### Main Demonstrated Results
* Room creation and listing
* Message posting and history retrieval
* Persistence after restart
* Robustness after USB disconnection
* End-to-end demonstrator on real hardware 