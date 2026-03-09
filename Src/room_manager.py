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

    def __init__(self, storage: StorageSQLite):
        self.storage = storage

    def handle_message(self, msg: IncomingMessage) -> List[OutgoingMessage]:
        """Processes an incoming message and returns a list of responses."""
        text = msg.text.strip()
        sender = msg.sender_id

        # Check if it is a /room command
        if not CommandParser.is_room_command(text):
            return []

        tokens = CommandParser.parse_tokens(text)

        # Invalid or empty command
        if len(tokens) < 2:
            return [OutgoingMessage(sender, "ERR usage: /room help")]

        action = tokens[1].lower()
        log.info(f"Action received from {sender}: {action}")

        # --- Action Dispatch ---
        if action in ("help", "?"):
            return [OutgoingMessage(sender, self._help_text())]

        #if action == "hello": # Special command to acknowledge new clients (not stored in DB)
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
        if len(tokens) < 3:
            return [OutgoingMessage(sender, "ERR usage: /room create <name> [desc]")]
        name = tokens[2]
        desc = " ".join(tokens[3:]) if len(tokens) > 3 else ""
        ok = self.storage.create_room(name, desc)
        return [OutgoingMessage(sender, f"OK room '{name}' created" if ok else f"ERR room '{name}' exists")]

    def _handle_delete(self, sender: int, tokens: List[str]) -> List[OutgoingMessage]:
        if len(tokens) != 3:
            return [OutgoingMessage(sender, "ERR usage: /room delete <name>")]
        name = tokens[2]
        ok = self.storage.delete_room(name)
        return [OutgoingMessage(sender, f"OK room '{name}' deleted" if ok else f"ERR room '{name}' not found")]


    def _handle_list(self, sender: int) -> List[OutgoingMessage]:
        rooms = self.storage.list_rooms()
        if not rooms:
            return [OutgoingMessage(sender, "Rooms: (none)")]

        names = [r[0] for r in rooms]

        PER_PAGE = 3      # ✅ 3 rooms par message
        MAX_ROOMS = 30    # sécurité (évite spam)

        truncated = False
        if len(names) > MAX_ROOMS:
            names = names[:MAX_ROOMS]
            truncated = True

        total_rooms = len(rooms)
        total_pages = (len(names) + PER_PAGE - 1) // PER_PAGE

        responses: List[OutgoingMessage] = []
        responses.append(OutgoingMessage(sender, f"Rooms ({total_rooms} total):"))

        for page in range(total_pages):
            chunk = names[page * PER_PAGE : (page + 1) * PER_PAGE]
            line = ", ".join(chunk)
            responses.append(OutgoingMessage(sender, f"[{page+1}/{total_pages}] {line}"))

        if truncated:
            responses.append(OutgoingMessage(sender, f"... (+{total_rooms - MAX_ROOMS} more)"))

        return responses
    def _handle_post(self, sender: int, ts: float, tokens: List[str]) -> List[OutgoingMessage]:
        if len(tokens) < 4:
            return [OutgoingMessage(sender, "ERR usage: /room post <name> <msg>")]
        name = tokens[2]
        content = " ".join(tokens[3:])
        if not self.storage.room_exists(name):
            return [OutgoingMessage(sender, f"ERR room '{name}' not found")]
        self.storage.add_message(name, sender, int(ts), content)
        return [OutgoingMessage(sender, f"OK posted to '{name}'")]
    def _handle_post_from_raw(self, sender: int, ts: float, raw_text: str) -> List[OutgoingMessage]:
        # Exemple: "/room post TestRoom bonjour tout le monde"
        parts = raw_text.strip().split(maxsplit=3)

        if len(parts) < 4:
            return [OutgoingMessage(sender, "ERR usage: /room post <name> <msg>")]

        name = parts[2]
        content = parts[3]  

        if not self.storage.room_exists(name):
            return [OutgoingMessage(sender, f"ERR room '{name}' not found")]

        self.storage.add_message(name, sender, int(ts), content)
        return [OutgoingMessage(sender, f"OK posted to '{name}'")]

    def _handle_read(self, sender: int, tokens: List[str]) -> List[OutgoingMessage]:
        if len(tokens) < 3:
            return [OutgoingMessage(sender, "ERR usage: /room read <name> [n]")]

        name = tokens[2]
        n = 5

        if len(tokens) >= 4:
            try:
                n = int(tokens[3])
                n = max(1, min(n, 10))
            except ValueError:
                return [OutgoingMessage(sender, "ERR n must be integer (1..10)")]

        if not self.storage.room_exists(name):
            return [OutgoingMessage(sender, f"ERR room '{name}' not found")]

        rows = self.storage.read_last_messages(name, n)
        if not rows:
            return [OutgoingMessage(sender, f"'{name}': (no messages)")]

        responses = []

        responses.append(OutgoingMessage(sender, f"--- '{name}' Last {len(rows)} Messages ---"))

        for sender_id, received_at, content in rows:
            t = time.strftime("%Y-%m-%d %H:%M", time.localtime(received_at))
            prefix_msg = f"{t} #{sender_id}:"
            responses.append(OutgoingMessage(sender, prefix_msg))

            chunks = textwrap.wrap(content, width=32)

            for chunk in chunks:
                responses.append(OutgoingMessage(sender, f"-> {chunk}"))

        return responses

    def _help_text(self) -> str:
        return (
            "Cmds:\n"
            "/room create <name>\n"
            "/room post <name> <msg>\n"
            "/room read <name>\n"
            "/room delete <name>\n"
            "/room list"
        )
