"""The foreground timer interrupts blocking work and restores its signal state."""

import signal
import time

import pytest

from soulkiller_text import local_model_budget
from soulkiller_text.dialogue_error import DialogueError


def test_local_deadline_interrupts_and_restores_signal_state(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Raise the fixed timeout category and leave the process timer disarmed."""
    # Arrange
    monkeypatch.setattr(local_model_budget, "MAX_SECONDS", 0.01)
    previous = signal.getsignal(signal.SIGALRM)
    # Act
    with pytest.raises(DialogueError, match="local_model_timeout"):
        with local_model_budget.local_deadline():
            time.sleep(1)
    # Assert
    assert signal.getitimer(signal.ITIMER_REAL) == (0.0, 0.0)
    assert signal.getsignal(signal.SIGALRM) == previous
