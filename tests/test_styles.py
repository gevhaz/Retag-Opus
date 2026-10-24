"""Tests for styles.py."""

from unittest.mock import MagicMock

import pytest

from retag_opus import styles


@pytest.fixture
def force_color(monkeypatch: pytest.MonkeyPatch) -> None:
    """Turn colors on even though stdout is captured."""
    monkeypatch.delenv("NO_COLOR")
    monkeypatch.setenv("FORCE_COLOR", "1")


def test_no_color_wins_over_force_color(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that NO_COLOR turns colors off despite FORCE_COLOR."""
    monkeypatch.setenv("FORCE_COLOR", "1")
    assert not styles.use_color()


@pytest.mark.usefixtures("force_color")
def test_force_color_without_terminal(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that FORCE_COLOR colors output that isn't a terminal."""
    monkeypatch.setattr("sys.stdout", MagicMock(isatty=MagicMock(return_value=False)))
    assert styles.use_color()


@pytest.mark.parametrize("is_terminal", [True, False])
def test_terminal_decides_by_default(monkeypatch: pytest.MonkeyPatch, is_terminal: bool) -> None:
    """Test that colors follow whether stdout is a terminal."""
    monkeypatch.delenv("NO_COLOR")
    monkeypatch.delenv("FORCE_COLOR", raising=False)
    monkeypatch.setattr("sys.stdout", MagicMock(isatty=MagicMock(return_value=is_terminal)))
    assert styles.use_color() == is_terminal


@pytest.mark.usefixtures("force_color")
def test_ansi_colors_and_resets() -> None:
    """Test that a style colors text and resets the color after."""
    assert styles.ansi("31")("text") == "\x1b[31mtext\x1b[39m"


def test_ansi_without_color() -> None:
    """Test that a style leaves text as is when colors are off."""
    assert styles.ansi("31")("text") == "text"


@pytest.mark.usefixtures("force_color")
def test_sources_have_different_colors() -> None:
    """Test that the source of a tag can be told from its color."""
    sources = [
        styles.original,
        styles.youtube,
        styles.parsed_from_youtube,
        styles.parsed_from_original,
        styles.musicbrainz,
        styles.unset,
    ]
    assert len({source("text") for source in sources}) == len(sources)


@pytest.mark.usefixtures("force_color")
def test_changes_have_different_colors() -> None:
    """Test that each kind of tag has its own look.

    The kinds are changed, removed, unchanged and unset.
    """
    changes = [styles.changed, styles.removed, styles.original, styles.unset]
    assert len({change("text") for change in changes}) == len(changes)
