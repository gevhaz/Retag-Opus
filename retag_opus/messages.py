"""Module for printing messages to the user, colored by their kind."""
from retag_opus import styles

_error = styles.ansi("31")
_warning = styles.ansi("33")
_success = styles.ansi("32")
_info = styles.ansi("34")
_conflict = styles.ansi("31")


def error(text: str) -> None:
    """Print that something went wrong."""
    print(_error(text))


def warning(text: str) -> None:
    """Print that something was skipped or needs attention."""
    print(_warning(text))


def success(text: str) -> None:
    """Print that something was done or matched."""
    print(_success(text))


def info(text: str) -> None:
    """Print what is happening."""
    print(_info(text))


def conflict(text: str) -> None:
    """Print that sources disagree and the user has to choose."""
    print(_conflict(text))
