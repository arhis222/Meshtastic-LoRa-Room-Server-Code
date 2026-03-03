from dataclasses import dataclass
from typing import List, Optional


# --- Data Models ---

@dataclass
class IncomingMessage:
    """Represents a message received from the LoRa network."""
    sender_id: int
    text: str
    ts: float  # Unix Timestamp


@dataclass
class OutgoingMessage:
    """Represents a message to be sent to the LoRa network."""
    target_id: Optional[int]  # None = Broadcast
    text: str


# --- Parsing Logic ---

class CommandParser:
    """
    Responsible for analyzing raw strings
    to extract commands and arguments.
    """

    @staticmethod
    def is_room_command(text: str) -> bool:
        """Checks if the message starts with the command prefix."""
        return text.strip().startswith("/room")

    @staticmethod
    def parse_tokens(text: str) -> List[str]:
        """Splits text into tokens (words)."""
        return [t for t in text.strip().split() if t]