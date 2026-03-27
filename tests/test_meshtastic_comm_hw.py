import os
import sys
import pytest
from unittest.mock import MagicMock, patch

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "Src"))
from meshtastic_comm_hw import TransportHardware
from parser import OutgoingMessage


# Fixture to fake the USB hardware connection.
# This way we can run tests without plugging in the Wio-E5 every time!
@pytest.fixture
def hw():
    # Hack: Patch time.sleep so our background worker doesn't actually pause.
    # Saves us from waiting seconds per test.
    with patch("meshtastic_comm_hw.time.sleep"):
        transport = TransportHardware("/dev/fakeUSB")

        # Create a dummy interface to trick the code into thinking it's connected
        transport.interface = MagicMock()
        transport.interface.localNode.channels = []

        # Set up a fake node ID so we can test the echo cancellation
        transport.interface.myInfo.my_node_num = 12345
        transport.interface.myInfo.my_node_id = "!fake123"

        yield transport


def test_send_broadcast(hw):
    # Target is None, which means it should broadcast to everyone
    msg = OutgoingMessage(target_id=None, text="Hello Mesh!")
    hw.send(msg)

    # Check if the Meshtastic library's sendText was called on channel 0
    hw.interface.sendText.assert_called_with("Hello Mesh!", channelIndex=0)


def test_send_direct_message(hw):
    # Starts with '!', so it's a DM
    msg = OutgoingMessage(target_id="!abcd", text="Secret info")
    hw.send(msg)

    hw.interface.sendText.assert_called_with("Secret info", destinationId="!abcd")


def test_on_receive_ignores_echo(hw):
    # Simulate a packet coming from our own node
    packet = {
        'fromId': '!fake123',
        'decoded': {'text': '/room list'}
    }

    # Spy on the manager
    hw.manager = MagicMock()
    hw.on_receive(packet, hw.interface)

    # Manager shouldn't do anything because we ignore our own echo
    hw.manager.handle_message.assert_not_called()


def test_on_receive_valid_packet(hw):
    # A normal message from someone else
    packet = {
        'fromId': '!user99',
        'decoded': {'text': '/room help'}
    }

    hw.manager = MagicMock()
    hw.manager.handle_message.return_value = [OutgoingMessage("!user99", "Help menu")]

    hw.on_receive(packet, hw.interface)

    # Make sure the manager processed it and pushed a response to the TX queue
    assert hw.manager.handle_message.called
    assert hw.tx_queue.qsize() == 1


def test_fifo_strict_ordering(hw):
    """
    Proof for the jury: The queue actually maintains strict FIFO order,
    which prevents LoRa collisions when multiple users send commands.
    """
    # Block the actual send method so we can track the calls
    hw.send = MagicMock()

    # Push 3 messages in a specific order
    responses = [
        OutgoingMessage("!user1", "First"),
        OutgoingMessage("!user2", "Second"),
        OutgoingMessage(None, "Third")
    ]

    hw.enqueue_responses(responses)

    # Wait for the background worker to finish processing the queue
    hw.tx_queue.join()

    # Check if it fired exactly 3 times
    assert hw.send.call_count == 3

    # Check if the output order exactly matches the input order (Strict FIFO)
    calls = hw.send.call_args_list
    assert calls[0][0][0].text == "First"
    assert calls[1][0][0].text == "Second"
    assert calls[2][0][0].text == "Third"