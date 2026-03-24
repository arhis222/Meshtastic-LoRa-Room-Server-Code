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

    # Constructor takes a StorageSQLite instance as argument, which will be used to perform all database operations related to rooms and messages
    def __init__(self, storage: StorageSQLite):
        self.storage = storage
        self.user_cooldowns = {}  # Keeps track of the last message timestamp for each user to enforce cooldowns and prevent spamming
        self.COOLDOWN_SECONDS = 10  # Minimum number of seconds between messages from the same user

    def handle_message(self, msg: IncomingMessage) -> List[OutgoingMessage]:
        """Processes an incoming message and returns a list of responses."""
        text = msg.text.strip()  # Remove leading/trailing whitespace for more robust command parsing
        sender = msg.sender_id  # extract the ID of sender from the message object for easier access and readability in the code below

        # Check if it is a /room command
        if not CommandParser.is_room_command(text):
            return []  # if not, we send no response (empty list) and ignore the message

        # --- ANTI-SPAM COOLDOWN CHECK ---
        current_time = time.time()
        last_time = self.user_cooldowns.get(sender, 0) # If the sender is not in the cooldown dictionary, we assume their last message was at time 0 (the epoch),
        # which means they are not currently on cooldown and can send a message.

        if current_time - last_time < self.COOLDOWN_SECONDS:
            remaining = int(self.COOLDOWN_SECONDS - (current_time - last_time))
            log.warning(f"🛑 RATE LIMIT: {sender} is sending too fast. Dropping message.")
            # If the user is sending messages too quickly (i.e., within the cooldown period), we return an error message indicating that
            # they are being rate limited and how many seconds they need to wait before sending another message.
            # This helps prevent spam and abuse of the system, while also providing feedback to the user about why their message was not processed.
            return [OutgoingMessage(sender, f"ERR Spam protection! Wait {remaining}s.")]

        # If the user is not on cooldown, we update their last message timestamp to the current time, so that we can enforce the cooldown for their next message.
        self.user_cooldowns[sender] = current_time

        # Split the command into tokens (words) to analyze the action and its arguments
        tokens = CommandParser.parse_tokens(text)

        # Invalid or empty command
        if len(tokens) < 2:
            return [OutgoingMessage(sender, "ERR usage: /room help")]

        action = tokens[1].lower()  # The action is the second token (e.g., 'create', 'post', etc.) and we convert it to lowercase for case-insensitive matching
        log.info(f"Action received from {sender}: {action}")

        # --- Action Dispatch ---

        if action in ("help", "?"):
            return self._help_text(OutgoingMessage, sender)

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

        if action == "info":
            return self._handle_info(sender, tokens)

        if action == "announce":
            return self._handle_announce(sender, text)

        time.sleep(1) # Small delay before sending the error response to give the user some time to receive the original message and to avoid sending responses too quickly in case of multiple messages (e.g., if they are spamming commands, we don't want to flood them with error messages, but we still want to give feedback about the unknown command)
        return [OutgoingMessage(sender, f"ERR unknown action (try /room help)")]

    # --- Private Management Methods ---

    def _handle_create(self, sender: int, tokens: List[str]) -> List[OutgoingMessage]:
        if len(tokens) < 3:  # We need at least 3 tokens like : /room create <name>
            return [OutgoingMessage(sender, "ERR usage: /room create <name> [desc]")]
        name = tokens[2]
        desc = " ".join(tokens[3:]) if len(
            tokens) > 3 else ""  # Optional description can be provided after the given name
        ok = self.storage.create_room(name,
                                      desc)  # the create_room method should return True if the room was successfully created, or False if a room with the same name already exists (or if there was an error during creation)
        return [OutgoingMessage(sender, f"OK room '{name}' created" if ok else f"ERR room '{name}' exists")]

    def _handle_delete(self, sender: int, tokens: List[str]) -> List[OutgoingMessage]:
        if len(tokens) != 3:
            return [OutgoingMessage(sender, "ERR usage: /room delete <name>")]
        name = tokens[2]
        ok = self.storage.delete_room(
            name)  # The delete_room method should return True if the room was successfully deleted, or False if the room was not found
        return [OutgoingMessage(sender, f"OK room '{name}' deleted" if ok else f"ERR room '{name}' not found")]

    def _handle_list(self, sender: int) -> List[OutgoingMessage]:
        rooms = self.storage.list_rooms()  # The list_rooms method should return a list of tuples, where each tuple contains the name and description of a room. If there are no rooms, it should return an empty list.
        if not rooms:
            return [OutgoingMessage(sender, "Rooms: (none)")]

        names = [r[0] for r in
                 rooms]  # We extract just the names of the rooms from the list of tuples returned by list_rooms, since we only want to display the names in the response to the user (the description is not needed for the /room list command, but we could later add a /room list verbose or something like that to show descriptions as well)
        PER_PAGE = 3  # 3 rooms per message to avoid flooding the network
        MAX_ROOMS = 30  # security limit to avoid sending too many messages
        truncated = False  # We use a truncated flag to indicate if we had to cut the list of rooms due to the MAX_ROOMS limit

        if len(names) > MAX_ROOMS:  # if there are more rooms than the limit, we cut the list
            names = names[:MAX_ROOMS]
            truncated = True

        total_rooms = len(rooms)  # we calculate the total number of rooms
        total_pages = (len(names) + PER_PAGE - 1) // PER_PAGE  # we calculate the total number of pages needed to display all the rooms, based on the number of rooms we have (after truncation if needed) and the number of rooms we want to show per page.

        responses: List[OutgoingMessage] = []
        responses.append(OutgoingMessage(sender, f"Rooms ({total_rooms} total):"))

        for page in range(
                total_pages):  # we loop through each page and create a message for that page, showing the page number and the list of room names for that page.
            chunk = names[page * PER_PAGE: (page + 1) * PER_PAGE]
            line = ", ".join(chunk)
            responses.append(OutgoingMessage(sender, f"[{page + 1}/{total_pages}] {line}"))

        if truncated:  # if we had to truncate the list of rooms due to the MAX_ROOMS limit, we add a final message indicating that there are more rooms that are not being displayed, to give feedback to the user about the truncation and to avoid confusion about why they don't see all the rooms.
            responses.append(OutgoingMessage(sender, f"... (+{total_rooms - MAX_ROOMS} more)"))

        return responses

    # Previous version of _handle_post, which was based on splitting tokens, but it had issues with messages that contained multiple words (e.g., "/room post TestRoom Hello everyone, how are you?"), because it would split the message into multiple tokens and we would lose the original message structure. The new version _handle_post_from_raw takes the raw text of the command and splits it into a maximum of 4 parts: the command itself, the action, the room name, and the rest of the message as a single string, which allows us to preserve the full message content even if it contains spaces.
    """
    def _handle_post(self, sender: int, ts: float, tokens: List[str]) -> List[OutgoingMessage]:
        If len(tokens) < 4: #  We need at least 4 tokens: /room post <name> <msg>, and the message can contain multiple words
            return [OutgoingMessage(sender, "ERR usage: /room post <name> <msg>")]
        name = tokens[2]
        content = " ".join(tokens[3:])
        If not self.storage.room_exists(name): # We should check if the room exists before trying to post a message to it, and return an error if it doesn't exist
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

        if not self.storage.room_exists(
                name):  # We should check if the room exists before trying to post a message to it, and return an error if it doesn't exist
            return [OutgoingMessage(sender, f"ERR room '{name}' not found")]

        self.storage.add_message(name, sender, int(ts),
                                 content)  # The add_message method should save the message in the database, associating it with the specified room, sender, and timestamp. We convert the timestamp to an integer (Unix time) for consistency with how we store timestamps in the database.
        return [OutgoingMessage(sender, f"OK posted to '{name}'")]

    def _handle_read(self, sender: int, tokens: List[str]) -> List[OutgoingMessage]:
        if len(tokens) < 3:  # We need at least 3 tokens: /room read <name>, and optionally a 4th token for the number of messages to read
            return [OutgoingMessage(sender, "ERR usage: /room read <name> [n]")]

        name = tokens[2]
        n = 5  # Default number of messages to read

        if len(tokens) >= 4:
            try:
                n = int(tokens[3])
                if n < 1:  # We should validate that n is a positive integer, and return an error if it's not (e.g., if it's negative, zero, or not a number at all)
                    return [OutgoingMessage(sender, "ERR n must be positive integer")]
                if n > 10:
                    return [OutgoingMessage(sender, "ERR n must be at most 10")]
            except ValueError:
                return [OutgoingMessage(sender, "ERR n must be integer (1..10)")]

        if not self.storage.room_exists(
                name):  # We should check if the room exists before trying to read messages from it, and return an error if it doesn't exist
            return [OutgoingMessage(sender, f"ERR room '{name}' not found")]

        # The read_last_messages method should return a list of tuples, where each tuple contains the sender_id, received_at timestamp,  and content of a message.
        # The messages should be ordered from newest to oldest, and limited to the specified number n.
        # If there are no messages in the room, it should return an empty list.
        rows = self.storage.read_last_messages(name, n)
        responses = []

        if not rows:  # If there are no messages in the room, we should return a response indicating that the room is empty (instead of just showing the header with no messages)
            return [OutgoingMessage(sender, f"'{name}': (no messages)")]
        if len(rows) < n:  # If there are fewer messages than n, we should indicate that in the header (e.g., by showing the actual number of messages being displayed instead of n),
            # To avoid confusion for the user who might expect to see n messages but only sees a few
            responses.append(OutgoingMessage(sender, f"'{name}': (only {len(rows)} messages)"))

        # We display a header with the room name and the number of messages being displayed, and then we display each message with a timestamp, sender ID, and content.
        # We also wrap long messages into multiple lines for better readability on the LoRa network, which has limited message length.
        responses.append(OutgoingMessage(sender, f"--- '{name}' Last {len(rows)} Messages ---"))

        # For each message, we format the timestamp into a human-readable string (e.g., "2024-06-01 14:30"),  and we create a header line with the timestamp and sender
        # ID. Then we wrap the content of the message into multiple lines if it's too long (e.g., more than 32 characters),  and we prefix each line with an arrow (e.g., "->") to indicate that it's part of the same message.
        for sender_id, received_at, content in rows:
            t = time.strftime("%Y-%m-%d %H:%M", time.localtime(received_at))
            prefix_msg = f"{t} #{sender_id}:"
            responses.append(OutgoingMessage(sender, prefix_msg))

            chunks = textwrap.wrap(content, width=32)

            for chunk in chunks:  # we split the content into chunks of 32 characters (or less) to fit within the typical message length limits of LoRa, and we send each chunk as a separate message with a "->" prefix to indicate that it's part of the same original message.
                responses.append(OutgoingMessage(sender, f"-> {chunk}"))

        return responses

    def _help_text(self, OutgoingMessage, sender: int) -> List[OutgoingMessage]:
        """Returns the help menu as a list of smaller messages to respect LoRa payload limits."""
        # Split the help menu into individual lines to avoid the "Data payload too big" error
        help_lines = [
            "Available commands:",
            "/room create <name> [desc]",
            "/room delete <name>",
            "/room list",
            "/room post <name> <msg>",
            "/room read <name> [n]",
            "/room info <name>",
            "/room announce <msg>",
            "/room help or /room ?"
        ]

        # Create a separate OutgoingMessage for each line
        responses = []
        for line in help_lines:
            responses.append(OutgoingMessage(sender, line))

        return responses

    def _handle_info(self, sender: int, tokens: List[str]) -> List[OutgoingMessage]:
        """Provides information about a specific room, such as its description, creation date, total number of messages, and last active date."""
        if len(tokens) < 3:
            return [OutgoingMessage(sender, "ERR usage: /room info <name>")]

        name = tokens[2]
        info = self.storage.get_room_info(name)

        if not info:
            return [OutgoingMessage(sender, f"ERR room '{name}' not found")]

        desc, created_at, msg_count, last_active = info

        # Format the creation date and last active date into human-readable strings, and handle cases where the description is empty or the room has never been active (i.e., no messages posted yet, so last_active is None)
        created_str = time.strftime("%Y-%m-%d %H:%M", time.localtime(created_at))
        active_str = time.strftime("%Y-%m-%d %H:%M", time.localtime(last_active)) if last_active else "Never"
        desc_str = desc if desc else "No description"

        # Format for the LoRa response, splitting into multiple messages if needed to avoid payload limits, and including the room name, description (truncated if too long), creation date, total number of messages, and last active date.
        return [
            OutgoingMessage(sender, f"--- Info: '{name}' ---"),
            OutgoingMessage(sender, f"-> Desc: {desc_str[:30]}"),  #if its too long we cut it
            OutgoingMessage(sender, f"-> Created: {created_str}"),
            OutgoingMessage(sender, f"-> Total Msgs: {msg_count}"),
            OutgoingMessage(sender, f"-> Last Active: {active_str}")
        ]

    def _handle_announce(self, sender: int, raw_text: str) -> List[OutgoingMessage]:
        """Sends a broadcast message to ALL nodes in the network."""
        parts = raw_text.strip().split(maxsplit=2) # We split the raw text into a maximum of 3 parts: the command itself, the action, and the rest of the message
        # as a single string, which allows us to preserve the full announcement content even if it contains spaces.

        if len(parts) < 3:
            return [OutgoingMessage(sender, "ERR usage: /room announce <msg>")]

        announcement = parts[2]
        broadcast_msg = f"📢 ANNOUNCEMENT from #{sender}:\n{announcement}"

        responses = []

        # First we send the sender a confirmation message that their announcement is being broadcasted
        responses.append(OutgoingMessage(sender, "OK Broadcast sent!"))

        # Then we send the actual announcement as a broadcast message (target_id = None) to all nodes in the network.
        # We're using chunks like always
        chunks = textwrap.wrap(broadcast_msg, width=30)
        for chunk in chunks:
            responses.append(OutgoingMessage(None, chunk))

        return responses
