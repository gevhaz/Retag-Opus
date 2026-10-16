"""Shared test setup."""
import pytest


@pytest.fixture(autouse=True)
def no_color(monkeypatch: pytest.MonkeyPatch) -> None:
    """Print without color, so tests compare plain text.

    Tests that check colors set FORCE_COLOR and remove NO_COLOR.
    """
    monkeypatch.setenv("NO_COLOR", "1")
