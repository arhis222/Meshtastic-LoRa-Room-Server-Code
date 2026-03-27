import os
import sys
import pytest

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "Src"))
from parser import CommandParser, IncomingMessage, OutgoingMessage

def test_is_room_command():
    assert CommandParser.is_room_command("/room create test") is True
    # Should still work even with weird spaces
    assert CommandParser.is_room_command("   /room list  ") is True
    assert CommandParser.is_room_command("hello world") is False
    assert CommandParser.is_room_command("/room") is True

def test_parse_tokens():
    assert CommandParser.parse_tokens("/room create general") == ["/room", "create", "general"]
    # Make sure it ignores multiple spaces
    assert CommandParser.parse_tokens("  /room   post   test   hello  ") == ["/room", "post", "test", "hello"]

def test_message_dataclasses():
    in_msg = IncomingMessage(sender_id="!abcd", text="/room list", ts=123.45)
    assert in_msg.sender_id == "!abcd"
    assert in_msg.text == "/room list"

    out_msg = OutgoingMessage(target_id=None, text="Broadcast")
    assert out_msg.target_id is None
    assert out_msg.text == "Broadcast"