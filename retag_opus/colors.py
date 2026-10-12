"""Module containing the definition of colors used in the app."""
from typing import Final

from colorama import Fore

yt_col: Final[str] = Fore.MAGENTA
md_col: Final[str] = Fore.CYAN
man_col: Final[str] = Fore.GREEN
auto_col: Final[str] = Fore.YELLOW
# Orange, MusicBrainz' color, since green means resolved. Colorama has
# no orange, so it's the code of orange among the 256 terminal colors.
mb_col: Final[str] = "\x1b[38;5;208m"
