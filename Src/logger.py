import logging
import sys


def setup_logger():
    """
    Configures the logging system.
    Displays logs in the console and (optionally) in a file.
    """
    logger = logging.getLogger("RoomServer")  # Create a named logger for our application
    logger.setLevel(
        logging.INFO)  # Set the logging level to INFO (we can change to DEBUG for more verbose output during development)

    # Log format
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s')  # Include timestamp, log level, and message in the logs for better readability

    # Console handler (stdout)
    ch = logging.StreamHandler(sys.stdout)  # Output logs to standard output (console)
    ch.setFormatter(formatter)  # Apply the log format to the console handler
    logger.addHandler(ch)  # Attach the console handler to the logger

    # (Optional we use it for debug) File handler to save logs to a file for later analysis or debugging
    # fh = logging.FileHandler('server.log')
    # fh.setFormatter(formatter)
    # logger.addHandler(fh)

    return logger


# Global instance
log = setup_logger()  # Initialize the logger and make it available as a global variable for easy use across the application (e.g., log.info(), log.error(), etc.)
