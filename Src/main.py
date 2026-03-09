from database import StorageSQLite
from room_manager import RoomManager
# from meshtastic_comm import TransportSim      # for simulation
from meshtastic_comm_hw import TransportHardware
from logger import log


def main():
    """Main entry point of the application."""

    log.info("Starting Room Server...")  # Log the startup event

    # 1. Persistence initialization
    storage = StorageSQLite("room_server.db")

    # 2. Business logic initialization
    manager = RoomManager(storage)

    # 3. Transport initialization (Simulation)
    # transport = TransportSim()

    # 3. Transport initialization (Real Hardware)
    transport = TransportHardware("/dev/ttyUSB0")
    # if permission is denied to access the USB device, you might need to run:
    # sudo chmod 666 /dev/ttyUSB0

    # 4. Starting the main loop
    transport.run(manager)


if __name__ == "__main__":
    main()
