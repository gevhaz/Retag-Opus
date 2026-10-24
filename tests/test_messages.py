"""Tests for messages.py."""

from collections.abc import Callable

import pytest

from retag_opus import messages

MESSAGES = [messages.error, messages.warning, messages.success, messages.info, messages.conflict]


@pytest.mark.parametrize("message", MESSAGES)
def test_message_prints_line(capsys: pytest.CaptureFixture[str], message: Callable[[str], None]) -> None:
    """Test that a message is printed as a line of its own."""
    message("text")
    assert capsys.readouterr().out == "text\n"


def test_message_kinds_have_different_colors(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test that errors, warnings, successes and info differ."""
    monkeypatch.delenv("NO_COLOR")
    monkeypatch.setenv("FORCE_COLOR", "1")
    kinds = [messages.error, messages.warning, messages.success, messages.info]
    printed = []
    for kind in kinds:
        kind("text")
        printed.append(capsys.readouterr().out)
    assert all(line.startswith("\x1b[") and line.endswith("text\x1b[39m\n") for line in printed)
    assert len(set(printed)) == len(kinds)
