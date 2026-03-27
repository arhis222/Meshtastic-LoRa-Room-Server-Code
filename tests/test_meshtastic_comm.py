import os
import sys
import pytest
from unittest.mock import patch, MagicMock

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "Src"))
from meshtastic_comm import TransportSim
from parser import OutgoingMessage


@pytest.fixture
def sim():
    return TransportSim()


def test_sim_send_broadcast(sim, capsys):
    # capsys is a Pytest trick (that I learned in my previous intern) to capture what gets printed to the terminal
    msg = OutgoingMessage(target_id=None, text="Testing broadcast")
    sim.send(msg)

    captured = capsys.readouterr()
    assert "[TX Broadcast] Testing broadcast" in captured.out


def test_sim_send_direct_message(sim, capsys):
    msg = OutgoingMessage(target_id="!u1", text="Testing DM")
    sim.send(msg)

    captured = capsys.readouterr()
    assert "[TX to !u1] Testing DM" in captured.out


@patch('builtins.input')
def test_sim_run_loop(mock_input, sim):
    # Hack to test the 'while True' loop without freezing the terminal.
    # We feed it a good command, a bad command, and then Ctrl+C to exit.
    mock_input.side_effect = [
        "!user1: /room help",
        "bad_format_no_colon",
        KeyboardInterrupt()
    ]

    mock_manager = MagicMock()
    mock_manager.handle_message.return_value = [OutgoingMessage("!user1", "Help info")]

    # Run it. It should process the inputs and then break cleanly on KeyboardInterrupt
    sim.run(mock_manager)

    # Make sure the manager was called at least once for the valid input
    assert mock_manager.handle_message.called

@patch("builtins.input")
def test_sim_run_invalid_sender(mock_input, sim):
    mock_input.side_effect = [
        ": /room help",
        KeyboardInterrupt()
    ]

    mock_manager = MagicMock()
    sim.run(mock_manager)

    assert not mock_manager.handle_message.called