import sqlite3
import time
from typing import List, Tuple
from logger import log


class StorageSQLite:
    """
    Manages data persistence via SQLite.
    Ensures transaction robustness.
    """

    # Constructor of this class initializes the SQLite connection and sets up the database schema if it doesn't exist.
    def __init__(self, db_path: str = "room_server.db"):
        self.db_path = db_path  # Store the path for potential future use (e.g., migrations, backups)

        # check_same_thread=False is required because Meshtastic runs on a separate thread so this parameter allows sharing the connection across threads.
        # connect to the SQLite database (it will be created if it doesn't exist)
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False,
                                    isolation_level=None)  # isolation_level=None enables autocommit mode so we dont need to call commit() after every transactions
        self._configure_db()  # Set PRAGMAs for better performance and crash resilience
        self._init_schema()  # Create tables if they don't exist
        log.info(f"Database connected: {db_path}")

    def _configure_db(self):
        self.conn.execute("PRAGMA journal_mode=WAL;")  # More robust against crashes (Write-Ahead Logging)
        self.conn.execute(
            "PRAGMA synchronous=NORMAL;")  # Good balance between performance and durability (can lose last 1-2 transactions in a crash, but much faster than FULL)

    def _init_schema(self) -> None:
        """Creates necessary tables if they don't exist."""
        # Rooms table: name (PK), description, created_at timestamp (as integer) : we use INTEGER for timestamps to simplify queries and sorting, and because we don't need timezone-aware datetimes for this application (we can always convert to human-readable format in the application layer)
        self.conn.execute("""
                          CREATE TABLE IF NOT EXISTS rooms
                          (
                              name
                              TEXT
                              PRIMARY
                              KEY,
                              description
                              TEXT,
                              created_at
                              INTEGER
                              NOT
                              NULL
                          );
                          """)
        # Messages table: id (PK), room_name (FK), sender_id, received_at timestamp (as integer), content
        self.conn.execute("""
                          CREATE TABLE IF NOT EXISTS messages
                          (
                              id
                              INTEGER
                              PRIMARY
                              KEY
                              AUTOINCREMENT,
                              room_name
                              TEXT
                              NOT
                              NULL,
                              sender_id
                              TEXT
                              NOT
                              NULL,
                              received_at
                              INTEGER
                              NOT
                              NULL,
                              content
                              TEXT
                              NOT
                              NULL,
                              FOREIGN
                              KEY
                          (
                              room_name
                          ) REFERENCES rooms
                          (
                              name
                          ) ON DELETE CASCADE
                              );
                          """)

        # Index to speed up retrieval of last messages in a room (sorted by received_at DESC)
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_room_time ON messages(room_name, received_at DESC);")
        # Enable foreign key constraints (important for ON DELETE CASCADE to work)
        self.conn.execute("PRAGMA foreign_keys=ON;")

    ######################################################################################################################
    ################################# PUBLIC METHODS FOR ROOM MANAGEMENT AND MESSAGES ####################################
    ######################################################################################################################

    def create_room(self, name: str, description: str = "") -> bool:
        """Creates a new chat room."""
        now = int(time.time())  # Store timestamps as integers (Unix time) for simplicity and performance
        try:
            self.conn.execute(
                "BEGIN;")  # Start a transaction to ensure atomicity of the room creation process (especially important if we later add more complex operations like checking for duplicates or initializing related data)
            self.conn.execute(
                "INSERT INTO rooms(name, description, created_at) VALUES (?, ?, ?);",
                (name, description, now),
            )
            self.conn.execute("COMMIT;")  # Commit the transaction if everything went well
            return True
        except sqlite3.IntegrityError:  # This exception is raised if we try to insert a room with a name that already exists (due to the PRIMARY KEY constraint on the name column)
            self.conn.execute("ROLLBACK;")
            return False
        except Exception as e:  # Catch any other unexpected exceptions to prevent the server from crashing and to log the error for debugging purposes
            self.conn.execute("ROLLBACK;")
            log.error(f"DB Error (create_room): {e}")
            raise

    def delete_room(self, name: str) -> bool:
        """Deletes an existing room."""
        self.conn.execute("BEGIN;")
        cur = self.conn.execute("DELETE FROM rooms WHERE name = ?;", (name,))
        deleted = cur.rowcount > 0  # rowcount gives the number of rows affected by the last execute, so if it's > 0 it means a room was actually deleted (if it was 0, it means no room with that name was found)
        self.conn.execute("COMMIT;")
        return deleted

    def list_rooms(self) -> List[Tuple[str, str]]:
        """Lists all available rooms."""
        cur = self.conn.execute("SELECT name, COALESCE(description,'') FROM rooms ORDER BY name ASC;")
        return cur.fetchall()

    def room_exists(self, name: str) -> bool:
        """Checks if a room exists in the database."""
        cur = self.conn.execute("SELECT 1 FROM rooms WHERE name = ? LIMIT 1;",
                                (name,))  # Limit 1 for efficiency since we only need to know if at least one row exists, and we don't care about the actual data
        return cur.fetchone() is not None  # fetchone() returns None if there are no results, so if it's not None it means the room exists

    def add_message(self, room_name: str, sender_id: str, received_at: int, content: str) -> None:
        """Saves a message into a specific room."""
        self.conn.execute("BEGIN;")
        self.conn.execute(
            "INSERT INTO messages(room_name, sender_id, received_at, content) VALUES (?, ?, ?, ?);",
            (room_name, sender_id, received_at, content),
        )
        self.conn.execute("COMMIT;")

    def read_last_messages(self, room_name: str, n: int) -> List[Tuple[str, int, str]]:
        """Retrieves the last N messages from a room."""
        cur = self.conn.execute("""
                                SELECT sender_id, received_at, content
                                FROM messages
                                WHERE room_name = ?
                                ORDER BY received_at DESC, id DESC LIMIT ?;
                                """, (room_name, n))
        return cur.fetchall()

    def get_room_info(self, name: str):
        """Returns description, creation date, message count, and last message date."""
        cur = self.conn.execute("""
                                SELECT r.description, r.created_at, COUNT(m.id), MAX(m.received_at)
                                FROM rooms r
                                         LEFT JOIN messages m ON r.name = m.room_name
                                WHERE r.name = ?
                                GROUP BY r.name;
                                """, (name,))
        return cur.fetchone()
