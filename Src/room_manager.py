import time
import textwrap
from typing import List
from database import StorageSQLite
from parser import IncomingMessage, OutgoingMessage, CommandParser
from logger import log


class RoomManager:
    """
    Contains business logic to manage chat rooms.
    Orchestrates interactions between parsed commands and the database.
    """

    # constructor takes a StorageSQLite instance as argument, which will be used to perform all database operations related to rooms and messages
    def __init__(self, storage: StorageSQLite):
        self.storage = storage

    def handle_message(self, msg: IncomingMessage) -> List[OutgoingMessage]:
        """Processes an incoming message and returns a list of responses."""
        text = msg.text.strip()  # Remove leading/trailing whitespace for more robust command parsing
        sender = msg.sender_id  # extract the ID of sender

        # Check if it is a /room command
        if not CommandParser.is_room_command(text):
            return []  # if not we send no response (empty list) and ignore the message

        # split the command into tokens (words) to analyze the action and its arguments
        tokens = CommandParser.parse_tokens(text)

        # Invalid or empty command
        if len(tokens) < 2:
            return [OutgoingMessage(sender, "ERR usage: /room help")]

        action = tokens[
            1].lower()  # The action is the second token (e.g., 'create', 'post', etc.) and we convert it to lowercase for case-insensitive matching
        log.info(f"Action received from {sender}: {action}")

        # --- Action Dispatch ---

        if action in ("help", "?"):
            return [OutgoingMessage(sender, self._help_text())]

        # if action == "hello": # Special command to acknowledge new clients (not stored in DB)
        #    log.info(f"🟢 NEW CLIENT CONNECTED: ID {sender}")
        #    return [OutgoingMessage(sender, f"Successfully connected to the server! (Your ID: {sender})")]

        if action == "create":
            return self._handle_create(sender, tokens)

        if action == "delete":
            return self._handle_delete(sender, tokens)

        if action == "list":
            return self._handle_list(sender)

        if action == "post":
            return self._handle_post_from_raw(sender, msg.ts, text)

        if action == "read":
            return self._handle_read(sender, tokens)

        return [OutgoingMessage(sender, f"ERR unknown action '{action}' (try /room help)")]

    # --- Private Management Methods ---

    def _handle_create(self, sender: int, tokens: List[str]) -> List[OutgoingMessage]:
        if len(tokens) < 3:  # We need at least 3 tokens: /room create <name>
            return [OutgoingMessage(sender, "ERR usage: /room create <name> [desc]")]
        name = tokens[2]
        desc = " ".join(tokens[3:]) if len(tokens) > 3 else ""  # Optional description can be provided after the name
        ok = self.storage.create_room(name,
                                      desc)  # The create_room method should return True if the room was successfully created, or False if a room with the same name already exists (or if there was an error during creation)
        return [OutgoingMessage(sender, f"OK room '{name}' created" if ok else f"ERR room '{name}' exists")]

    def _handle_delete(self, sender: int, tokens: List[str]) -> List[OutgoingMessage]:
        if len(tokens) != 3:
            return [OutgoingMessage(sender, "ERR usage: /room delete <name>")]
        name = tokens[2]
        ok = self.storage.delete_room(
            name)  # The delete_room method should return True if the room was successfully deleted, or False if the room was not found (or could not be deleted for some reason)
        return [OutgoingMessage(sender, f"OK room '{name}' deleted" if ok else f"ERR room '{name}' not found")]

    def _handle_list(self, sender: int) -> List[OutgoingMessage]:
        rooms = self.storage.list_rooms()  # The list_rooms method should return a list of tuples, where each tuple contains the name and description of a room (e.g., [('Room1', 'Description1'), ('Room2', 'Description2'), ...]). If there are no rooms, it should return an empty list.
        if not rooms:
            return [OutgoingMessage(sender, "Rooms: (none)")]
        names = ", ".join([r[0] for r in rooms])
        return [OutgoingMessage(sender, f"Rooms: {names}")]

    #previous version of _handle_post, which was based on splitting tokens, but it had issues with messages that contained multiple words (e.g., "/room post TestRoom Hello everyone, how are you?"), because it would split the message into multiple tokens and we would lose the original message structure. The new version _handle_post_from_raw takes the raw text of the command and splits it into a maximum of 4 parts: the command itself, the action, the room name, and the rest of the message as a single string, which allows us to preserve the full message content even if it contains spaces.
    """
    def _handle_post(self, sender: int, ts: float, tokens: List[str]) -> List[OutgoingMessage]:
        if len(tokens) < 4: #  We need at least 4 tokens: /room post <name> <msg>, and the message can contain multiple words
            return [OutgoingMessage(sender, "ERR usage: /room post <name> <msg>")]
        name = tokens[2]
        content = " ".join(tokens[3:])
        if not self.storage.room_exists(name): # We should check if the room exists before trying to post a message to it, and return an error if it doesn't exist
            return [OutgoingMessage(sender, f"ERR room '{name}' not found")]
        self.storage.add_message(name, sender, int(ts), content) # The add_message method should save the message in the database, associating it with the specified room, sender, and timestamp. We convert the timestamp to an integer (Unix time) for consistency with how we store timestamps in the database.
        return [OutgoingMessage(sender, f"OK posted to '{name}'")]
    """

    def _handle_post_from_raw(self, sender: int, ts: float, raw_text: str) -> List[OutgoingMessage]:
        # Exemple: "/room post TestRoom bonjour tout le monde"
        parts = raw_text.strip().split(maxsplit=3)

        if len(parts) < 4:
            return [OutgoingMessage(sender, "ERR usage: /room post <name> <msg>")]

        name = parts[2]
        content = parts[3]

        if not self.storage.room_exists(name): # We should check if the room exists before trying to post a message to it, and return an error if it doesn't exist
            return [OutgoingMessage(sender, f"ERR room '{name}' not found")]

        self.storage.add_message(name, sender, int(ts), content) # The add_message method should save the message in the database, associating it with the specified room, sender, and timestamp. We convert the timestamp to an integer (Unix time) for consistency with how we store timestamps in the database.
        return [OutgoingMessage(sender, f"OK posted to '{name}'")]

    def _handle_read(self, sender: int, tokens: List[str]) -> List[OutgoingMessage]:
        if len(tokens) < 3: # We need at least 3 tokens: /room read <name>, and optionally a 4th token for the number of messages to read
            return [OutgoingMessage(sender, "ERR usage: /room read <name> [n]")]

        name = tokens[2]
        n = 5  # Default number of messages to read

        if len(tokens) >= 4:
            try:
                n = int(tokens[3])
                if n < 1: # We should validate that n is a positive integer, and return an error if it's not (e.g., if it's negative, zero, or not a number at all)
                    return [OutgoingMessage(sender, "ERR n must be positive integer")]
                if n > 10:
                    return [OutgoingMessage(sender, "ERR n must be at most 10")]
            except ValueError:
                return [OutgoingMessage(sender, "ERR n must be integer (1..10)")]

        if not self.storage.room_exists(name): # We should check if the room exists before trying to read messages from it, and return an error if it doesn't exist
            return [OutgoingMessage(sender, f"ERR room '{name}' not found")]

        # The read_last_messages method should return a list of tuples, where each tuple contains the sender_id, received_at timestamp, and content of a message.
        # The messages should be ordered from newest to oldest,
        # and limited to the specified number n. If there are no messages in the room, it should return an empty list.
        rows = self.storage.read_last_messages(name, n)
        responses = []

        if not rows: # If there are no messages in the room, we should return a response indicating that the room is empty (instead of just showing the header with no messages)
            return [OutgoingMessage(sender, f"'{name}': (no messages)")]
        if len(rows) < n: # If there are fewer messages than n, we should indicate that in the header (e.g., by showing the actual number of messages being displayed instead of n),
            # to avoid confusion for the user who might expect to see n messages but only sees a few
            responses.append(OutgoingMessage(sender, f"'{name}': (only {len(rows)} messages)"))

        # We display a header with the room name and the number of messages being displayed, and then we display each message with a timestamp, sender ID, and content.
        # We also wrap long messages into multiple lines for better readability on the LoRa network, which has limited message length.
        responses.append(OutgoingMessage(sender, f"--- '{name}' Last {len(rows)} Messages ---"))

        # For each message, we format the timestamp into a human-readable string (e.g., "2024-06-01 14:30"), and we create a header line with the timestamp and sender
        # ID. Then we wrap the content of the message into multiple lines if it's too long (e.g., more than 32 characters), and we prefix each line with an arrow (e.g., "->") to indicate that it's part of the same message.
        for sender_id, received_at, content in rows:
            t = time.strftime("%Y-%m-%d %H:%M", time.localtime(received_at))
            prefix_msg = f"{t} #{sender_id}:"
            responses.append(OutgoingMessage(sender, prefix_msg))

            chunks = textwrap.wrap(content, width=32)

            for chunk in chunks: # We split the content into chunks of 32 characters (or less) to fit within the typical message length limits of LoRa, and we send each chunk as a separate message with a "->" prefix to indicate that it's part of the same original message.
                responses.append(OutgoingMessage(sender, f"-> {chunk}"))

        return responses

    def _help_text(self) -> str:
        # The help text provides a summary of the available commands and their usage. It is returned as a single string, which can be sent as a response to the user when they request help or when they enter an invalid command.
        return (
            "Cmds:\n"
            "/room create <name>\n"
            "/room post <name> <msg>\n"
            "/room read <name>\n"
            "/room list"
            "/room delete <name>\n"
            "/room help"
        )
