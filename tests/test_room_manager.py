import os
import sys
import time
import pytest

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "Src"))
from database import StorageSQLite
from parser import IncomingMessage
from room_manager import RoomManager


# Fixture to provide a ready-to-use manager with an in-memory DB
@pytest.fixture
def manager():
    db = StorageSQLite(":memory:")
    return RoomManager(db)


# Quick helper to build messages
def make_msg(sender: str, text: str):
    return IncomingMessage(sender_id=sender, text=text, ts=time.time())


# Hack to bypass the 10-second spam protection during tests.
# This saves us from having to put time.sleep(11) everywhere!
def reset_cooldown(manager, sender):
    manager.user_cooldowns[sender] = 0


def test_create_room_command(manager):
    responses = manager.handle_message(make_msg("!u1", "/room create general"))
    assert any("OK room 'general' created" in r.text for r in responses)


def test_list_rooms_command(manager):
    manager.handle_message(make_msg("!u1", "/room create general"))
    reset_cooldown(manager, "!u1")

    responses = manager.handle_message(make_msg("!u1", "/room list"))
    assert any("general" in r.text for r in responses)


def test_post_and_read_message(manager):
    manager.handle_message(make_msg("!u1", "/room create general"))
    reset_cooldown(manager, "!u1")

    # Send a message
    responses = manager.handle_message(make_msg("!u1", "/room post general hello world!"))
    assert any("OK posted" in r.text for r in responses)
    reset_cooldown(manager, "!u1")

    # Read it back
    responses = manager.handle_message(make_msg("!u1", "/room read general 5"))
    joined_texts = " ".join(r.text for r in responses)
    assert "hello world!" in joined_texts


def test_rate_limit_blocks_spam(manager):
    # First message should pass just fine
    first = manager.handle_message(make_msg("!u1", "/room create general"))

    # Second message sent immediately should trigger the anti-spam error
    second = manager.handle_message(make_msg("!u1", "/room list"))

    assert any("OK" in r.text for r in first)
    assert any("ERR Spam protection" in r.text for r in second)


def test_info_command(manager):
    manager.handle_message(make_msg("!u1", "/room create general test_desc"))
    reset_cooldown(manager, "!u1")

    responses = manager.handle_message(make_msg("!u1", "/room info general"))
    joined_texts = " ".join(r.text for r in responses)
    assert "test_desc" in joined_texts


def test_announce_command(manager):
    responses = manager.handle_message(make_msg("!u1", "/room announce Attention everyone!"))
    # Should return an OK to the sender AND a broadcast message to everyone (target_id = None)
    assert any("OK Broadcast sent" in r.text for r in responses)
    assert any("Attention everyone!" in r.text for r in responses if r.target_id is None)


def test_unknown_command(manager):
    responses = manager.handle_message(make_msg("!u1", "/room banana"))
    assert any("ERR unknown action" in r.text for r in responses)