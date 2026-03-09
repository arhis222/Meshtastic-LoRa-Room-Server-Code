import os
import threading
import time
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
                self.interface.sendText(text)
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
            self.interface.sendText(text)

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
                if sender_id == my_id:
                    return

                # send the received message to the log for debugging and visibility
                log.info(f"📩 [RX Hardware] From {sender_id}: {text}")

                # Send the message to the Manager for processing
                msg = IncomingMessage(
                    sender_id=sender_id,
                    text=text,
                    ts=time.time()
                )

                if self.manager:  # Only process the message if the manager is attached (via run()), otherwise we might receive messages before we're fully ready
                    responses = self.manager.handle_message(
                        msg)  # Get responses from the manager (RoomManager) based on the incoming message

                    # create a separate thread to send responses with delay, so we don't block the main thread
                    # Send each response with a delay to avoid flooding the network and to give some time for the
                    # sender to receive the response before we send another one (especially important if there are
                    # multiple responses to the same message, like in /room list)
                    def send_responses_task():
                        time.sleep(2) # Wait a bit before sending the first response to give the sender some time to receive the original message and to avoid sending responses too quickly in case of multiple responses (e.g., /room list)
                        for resp in responses:
                            self.send(resp)
                            time.sleep(4)

                    threading.Thread(target=send_responses_task,
                                     daemon=True).start()  # Start the thread as a daemon so it doesn't block the program from exiting if we need to shut down

        except Exception as e:  # Catch any exceptions that occur during the processing of the received packet to prevent crashes and to log the error for debugging purposes
            log.error(f"Error processing packet: {e}")

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

                log.info("Retrying connection in 10 seconds...")
                time.sleep(10)