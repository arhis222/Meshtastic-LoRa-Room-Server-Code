import os
import threading
import time
import queue
import meshtastic.serial_interface

from pubsub import pub
from parser import IncomingMessage, OutgoingMessage
from room_manager import RoomManager
from logger import log


class TransportHardware:
    """
    Real interface with Meshtastic hardware via USB.
    """

    # constructor takes the device path (e.g., /dev/ttyUSB0) as argument, which can be configured by the user at startup
    def __init__(self, dev_path: str):
        self.interface = None  # Will hold the Meshtastic SerialInterface instance once connected
        self.dev_path = dev_path
        self.manager = None  # Will be attached via run()
        self.tx_queue = queue.Queue()  # The FIFO queue for outgoing messages
        # Tunable delays for safer LoRa transmissions
        self.first_tx_delay = 1
        self.between_tx_delay = 2

        # Start one dedicated worker thread that sends messages strictly in FIFO order
        self.tx_thread = threading.Thread(target=self._tx_worker, daemon=True)
        self.tx_thread.start()

    def _tx_worker(self):
        """
        Background worker that sends outgoing messages in strict FIFO order.

        Why this exists:
        - LoRa hardware is half-duplex
        - We must avoid concurrent sends from multiple threads
        - We want one single transmission pipeline for all outgoing responses
        """
        while True:
            # Wait until a message is available in the FIFO queue
            out_msg = self.tx_queue.get()

            try:
                # If hardware is not ready yet, wait before sending
                while self.interface is None:
                    log.warning("⚠️ Waiting for hardware interface before sending queued message...")
                    time.sleep(1)

                # Small delay before each transmission
                time.sleep(self.first_tx_delay)

                # Send exactly one message
                self.send(out_msg)

                # Delay between messages to reduce collisions and respect LoRa constraints
                time.sleep(self.between_tx_delay)

            except Exception as e:
                log.error(f"❌ Error in TX background worker: {e}")

            finally:
                # Mark the queue item as processed
                self.tx_queue.task_done()

    def send(self, out: OutgoingMessage) -> None:
        """
        Send a message via Meshtastic.
        - If out.target_id is None -> broadcast
        - If out.target_id is a Meshtastic nodeId string like '!abcd1234' -> direct message
        - Otherwise -> fallback to broadcast (to avoid silent failures)
        """
        if not self.interface:  # If the interface is not initialized, we cannot send messages
            log.warning("⚠️ Meshtastic interface not initialized. Cannot send.")
            return

        try:
            target = getattr(out, "target_id", None)  # Use getattr to avoid AttributeError if target_id is missing
            text = getattr(out, "text", "")

            if not text:  # If text is empty or missing, we should not send an empty message
                log.warning("⚠️ Empty message, nothing to send.")
                return

            # Broadcast
            if target is None:
                log.info(f"📡 [TX Hardware Broadcast] {text}")
                # self.interface.sendText(text)
                target_ch_index = 0  # default channel is 0
                if self.interface.localNode and self.interface.localNode.channels:  # we try to find the channel index for "S8_Project" for broadcast if it exists, otherwise we use the default channel 0
                    for ch in self.interface.localNode.channels:
                        if ch.settings.name == "S8_Project":
                            target_ch_index = ch.index
                            break
                self.interface.sendText(text, channelIndex=target_ch_index)
                return

            # DM only works reliably with nodeId strings like '!a1b2c3d4'
            if isinstance(target, str) and target.strip().startswith("!"):
                dest = target.strip()
                log.info(f"📡 [TX Hardware DM to {dest}] {text}")
                self.interface.sendText(text, destinationId=dest)
                return

            # Fallback: unknown/unsupported target format (e.g., int nodeNum)
            log.warning(f"⚠️ target_id format not supported ({target!r}). Fallback to broadcast.")
            log.info(f"📡 [TX Hardware Broadcast] {text}")

            target_ch_index = 0
            if self.interface.localNode and self.interface.localNode.channels:
                for ch in self.interface.localNode.channels:
                    if ch.settings.name == "S8_Project":
                        target_ch_index = ch.index
                        break

            self.interface.sendText(text, channelIndex=target_ch_index)

        # Catch any exceptions from the Meshtastic library (e.g., if the device is disconnected while sending) and log them without crashing the server
        except Exception as e:
            log.error(f"❌ Error while sending message: {e}")

    def on_receive(self, packet, interface):
        """Callback triggered when a packet arrives."""
        try:
            # We only accept text messages that have been decoded by the Meshtastic library (e.g., not raw binary packets or other types of messages)
            # "portnum": "TEXT_MESSAGE_APP",
            if 'decoded' in packet and 'text' in packet['decoded']:
                text = packet['decoded']['text']
                sender_id = packet['fromId']

                # Ignore messages from ourselves (Echo)
                my_id = self.interface.myInfo.my_node_num
                my_id_str = getattr(self.interface.myInfo, "my_node_id", None)

                if sender_id == my_id or sender_id == my_id_str:
                    return

                # send the received message to the log for debugging and visibility
                log.info(f"📩 [RX Hardware] From {sender_id}: {text}")

                # Send the message to the Manager for processing
                msg = IncomingMessage(
                    sender_id=sender_id,
                    text=text,
                    ts=time.time()
                )

                if self.manager:  # Only process the message if the manager is attached
                    responses = self.manager.handle_message(msg)
                    self.enqueue_responses(responses)

        except Exception as e:  # Catch any exceptions that occur during the processing of the received packet to prevent crashes and to log the error for debugging purposes
            log.error(f"Error processing packet: {e}")

    def enqueue_responses(self, responses: list[OutgoingMessage]) -> None:
        """
        Push all generated responses into the central FIFO queue.

        This ensures that replies from all users go through one single
        transmission channel instead of multiple concurrent sender threads.
        """
        if not responses:
            return

        for response in responses:
            self.tx_queue.put(response)

    def run(self, manager: RoomManager) -> None:
        """Starts listening on the USB port, with auto-reconnect."""
        self.manager = manager  # Attach the manager so we can pass received messages to it for processing

        # loop externe to handle auto-reconnection if the device is unplugged or not found at startup
        while True:
            log.info(f"Connecting to Meshtastic on {self.dev_path}...")

            # if the device is not connected, wait and retry (instead of crashing)
            if not os.path.exists(self.dev_path):
                log.warning(f"⚠️ Device not found at {self.dev_path}. Waiting for USB connection...")
                time.sleep(5)
                continue

            try:
                # Connect to the Meshtastic interface via the specified serial port
                self.interface = meshtastic.serial_interface.SerialInterface(self.dev_path)
                self.interface.waitForConfig()  # Wait for the device to be ready and configured (e.g., node ID, settings, etc.)

                # Subscribe to receive events from the Meshtastic interface and set the callback function to handle incoming messages
                pub.subscribe(self.on_receive, "meshtastic.receive")

                log.info("✅ Hardware Connected successfully!")

                # Loop interne which keeps the connection alive and checks for disconnection (e.g., USB cable removal)
                while True:
                    time.sleep(2)

                    # if the device is removed while we're connected, we should detect it and break to outer loop to retry connection
                    if not os.path.exists(self.dev_path):
                        log.error("🚨 USB Cable removed! Disconnecting interface...")
                        break

            except Exception as e:  # Catch any exceptions that occur during connection or while the interface is active
                # (e.g., disconnection, hardware errors, etc.) to prevent crashes and to log the error for debugging purposes
                log.error(f"⚠️ Hardware Error: {e}")

            finally:
                # if the interface was created but we are here due to an error, we make sure to clean up and unsubscribe
                # to avoid multiple subscriptions on retry in 10 seconds
                if self.interface:
                    try:
                        self.interface.close()
                        pub.unsubscribe(self.on_receive, "meshtastic.receive")
                    except:
                        pass
                    finally:
                        #  mark the interface as unavailable for the TX worker
                        self.interface = None

                log.info("Retrying connection in 10 seconds...")
                time.sleep(10)
