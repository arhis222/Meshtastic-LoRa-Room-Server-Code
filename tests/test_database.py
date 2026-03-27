import os
import sys
import pytest

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "Src"))
from database import StorageSQLite


# Pytest fixture: Gives us a fresh, in-memory DB for every single test
@pytest.fixture
def db():
    # Using :memory: so we don't leave junk .sqlite files on the disk
    storage = StorageSQLite(":memory:")
    yield storage


def test_create_and_check_room(db):
    assert db.create_room("general", "Main Chat") is True
    assert db.room_exists("general") is True
    assert db.room_exists("unknown") is False


def test_create_duplicate_room(db):
    db.create_room("general", "Main Chat")
    # Should fail if we try to create it again with the same name
    assert db.create_room("general", "Another") is False


def test_list_rooms(db):
    db.create_room("general", "main")
    db.create_room("random", "second")

    rooms = db.list_rooms()
    room_names = [room[0] for room in rooms]

    assert "general" in room_names
    assert "random" in room_names


def test_add_and_read_messages(db):
    db.create_room("general", "main")
    db.add_message("general", "!user1", 1000, "hello")
    db.add_message("general", "!user2", 1001, "world")

    messages = db.read_last_messages("general", 5)
    assert len(messages) == 2
    # Since we order by time DESC, the newest message comes first
    assert messages[0][2] == "world"
    assert messages[1][2] == "hello"


def test_delete_room(db):
    db.create_room("general", "main")
    assert db.delete_room("general") is True
    assert db.room_exists("general") is False
    # Deleting a non-existent room should safely return False
    assert db.delete_room("general") is False


def test_get_room_info(db):
    db.create_room("general", "main room")
    db.add_message("general", "!user1", 1000, "hello")

    info = db.get_room_info("general")
    assert info is not None
    # info format: (description, created_at, msg_count, last_active)
    assert info[0] == "main room"
    assert info[2] == 1  # Message count
    assert info[3] == 1000  # Last active timestamp

def test_get_room_info_unknown(db):
    info = db.get_room_info("unknown")
    assert info is None

def test_read_empty_room(db):
    db.create_room("general", "main")
    messages = db.read_last_messages("general", 5)
    assert messages == []