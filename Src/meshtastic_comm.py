import time
from parser import IncomingMessage, OutgoingMessage
from room_manager import RoomManager
from logger import log


class TransportSim:
    """
    Simulation of the Meshtastic interface (Console).
    Later, this class will be replaced or inherited by 'TransportHardware'.
    Which be the real interface with the Meshtastic hardware via USB.
    """

    def send(self, out: OutgoingMessage) -> None:
        """Simulates sending a LoRa packet."""
        if out.target_id is None: #if target_id is None, it's a broadcast message
            print(f"📡 [TX Broadcast] {out.text}")
        else: # if target_id is not None, it's a direct message to a specific node
            print(f"📨 [TX to {out.target_id}] {out.text}")

    def run(self, manager: RoomManager) -> None:
        """Main reception loop (simulation via stdin)."""
        print("\n=== Room Server (SIMULATION Mode) ===")
        print("Format: sender_id: message")
        print("Example: 1234: /room create ProjectAlpha")
        print("Quit: Ctrl+C\n")

        while True: # loop to read user input and simulate incoming messages
            try:
                line = input("> ").strip()
                if not line:
                    continue

                # Simple simulation of "ID: Command" format
                if ":" not in line:
                    print("⚠️ Expected format -> sender_id: message")
                    continue

                left, right = line.split(":", 1) # split only on the first colon to allow colons in the message text
                try:
                    sender_id = int(left.strip())
                except ValueError:
                    print("⚠️ ID must be an integer.") # for now we'll just require integer IDs in the simulation, even though real Meshtastic nodeIds are strings like '!abcd1234'
                    continue

                # Creating the message object
                msg = IncomingMessage(
                    sender_id=sender_id,
                    text=right.strip(),
                    ts=time.time()
                )

                # Passing to the manager (RoomManager)
                responses = manager.handle_message(msg)

                # Sending responses from the manager
                for response in responses:
                    self.send(response)

            except KeyboardInterrupt:
                log.info("Stopping server...")
                break
            except Exception as e:
                log.error(f"Critical error in transport loop: {e}")
