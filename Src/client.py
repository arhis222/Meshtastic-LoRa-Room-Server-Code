import meshtastic.serial_interface
from pubsub import pub
import time
import sys

MAX_SAFE_COMMAND_LEN = 200

# Dependency installation if not already done:
# pip install meshtastic pubsub

def on_receive(packet, interface):
    """
    Callback triggered when a message is received from the server.
    """
    try:
        if 'decoded' in packet and 'text' in packet['decoded']:
            text = packet['decoded']['text']
            sender = packet['fromId']

            # Ignore our own messages (Echo cancellation)
            my_id = interface.myInfo.my_node_num
            if sender == my_id:
                return

            timestamp = time.strftime("%H:%M:%S")

            # Clean display of received message
            print(f"\n🖥️  [{timestamp}] SERVER ▶ {text}")
            print("> ", end="", flush=True)

    except Exception as e:
        print(f"\n⚠️ Error while receiving message: {e}")


def main():
    print("\n========================================")
    print("   LORA MESSAGING CLIENT (Project S8)   ")
    print("========================================")

    # Ask the user for the serial port because it can vary by system and setup
    print("Please enter the port of your LoRa device:")
    print(" - Windows: COM3, COM4, etc.")
    print(" - Mac/Linux: /dev/ttyUSB0, /dev/ttyACM0")
    port = input("Port > ").strip()

    if not port:
        print("❌ Error: No port specified.")
        return

    print(f"🔌 Connecting to port {port}...")

    try:
        # Connection to the Meshtastic interface via the specified serial port
        interface = meshtastic.serial_interface.SerialInterface(port)

        # Wait for the device to be ready and configured (params like node ID , settings, etc.)
        interface.waitForConfig()

        # Subscribe to incoming messages from the Meshtastic interface and set the callback function
        pub.subscribe(on_receive, "meshtastic.receive")

        print("\n✅ CONNECTED! The system is ready.")

        ###############THIS PART IS ABOTED FOR NOW ################
        # Send an initial message to the server to announce our presence like handshake
        # print("(Sending connection request to the server...)")
        # interface.sendText("/room hello")
        # give it a tiny delay so the text doesn't overlap weirdly
        # time.sleep(1)
        ############################################################

        # Displaying available commands to the user
        print("Available commands:")
        print("  /room create <name>          -> Create a room")
        print("  /room post <name> <message>  -> Post a message")
        print("  /room list                  -> View rooms")
        print("  /room read <name>            -> Read messages")
        print("  /room delete <name>          -> Delete a room")
        print("  /room help                  -> Show this help")
        print("  /room info <name>          -> Show info about a room")
        print("  /room announce <message>  -> Announce a message to all members (broadcast)")
        print("--------------------------------------------------")
        print("(Press Ctrl+C to quit)\n")

        # Main loop to read user input and send messages to the server
        while True:
            msg = input("> ").strip()

            if msg:
                # LORA PAYLOAD LIMIT CHECK (BYTE LEVEL)
                # Based on CLI configuration 'lora.modem_preset: SHORT_FAST':
                # The physical MTU is increased, allowing a safe net payload of ~200 bytes
                # after accounting for the ~16-byte Meshtastic protocol overhead.
                # We calculate the UTF-8 byte length instead of the character count,
                # because special characters (é, ç, ı, à) and emojis consume multiple bytes.
                payload_bytes = len(msg.encode('utf-8')) # byte lenght of the message

                if payload_bytes > MAX_SAFE_COMMAND_LEN:
                    print(f"⚠️ ERROR: Message too heavy ({payload_bytes} bytes).")
                    print("Due to LoRa hardware limitations, please keep it under 200 bytes.")
                    print("(Note: Special characters and emojis consume more space!)")
                    continue  # Skip the rest of the loop and do not send the message

                # Sending message via LoRa
                try:
                    # The timestamp is only for the local display, it is not sent over LoRa
                    timestamp = time.strftime("%H:%M:%S")
                    interface.sendText(msg)  # Send the raw text to the server
                    print(f"👤 [{timestamp}] YOU ▶ {msg}")
                except Exception as e:
                    # Catch any hardware or library rejections to prevent a crash
                    print(f"❌ Transmission Error: Message could not be sent. Details: {e}")

    # Handle potential errors when connecting to the serial port (e.g., device not found, permission issues)
    except OSError as e:
        print(f"\n❌ CONNECTION ERROR: Unable to open port {port}.")
        print(f"Detail: {e}")
        print("Check that the device is plugged in and the port is correct.")

    # Handle any other unexpected exceptions that may occur during runtime or ctrl+c for graceful shutdown
    except KeyboardInterrupt:
        print("\n👋 Disconnecting... Goodbye!")
        if 'interface' in locals():
            interface.close()


if __name__ == "__main__":
    main()