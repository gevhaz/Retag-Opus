"""Module with styles that color text according to what it is.

A style is a function that wraps text in an ANSI color code and resets
the color after it. Whether to use color is decided every time a style
is applied: there is no color when NO_COLOR is set, or when stdout is
not a terminal unless FORCE_COLOR is set.
"""

import os
import sys
from collections.abc import Callable

Style = Callable[[str], str]


def use_color() -> bool:
    """Decide whether output should be colored."""
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR"):
        return True
    return sys.stdout.isatty()


def ansi(code: str) -> Style:
    """Create a style that colors text with the given ANSI color code."""

    def apply(text: str) -> str:
        if not use_color():
            return text
        return f"\x1b[{code}m{text}\x1b[39m"

    return apply


# Sources of tags
original = ansi("36")
youtube = ansi("35")
parsed_from_youtube = ansi("32")
parsed_from_original = ansi("33")
# Orange, MusicBrainz' color, since green means resolved. It's the code
# of orange among the 256 terminal colors.
musicbrainz = ansi("38;5;208")

# Tags about to be saved
changed = ansi("32")
removed = ansi("31")
unset = ansi("90")
