"""Module with helper functions for the rest of the app."""

import re
import unicodedata
from pathlib import Path


def remove_duplicates(values: list[str]) -> list[str]:
    """Remove duplicate elemets from given list."""
    return list(dict.fromkeys(values))


def add_values(tags_to_update: dict[str, list[str]], tag_name: str, new_values: list[str]) -> None:
    """Add values to a tag, leaving out the ones it already has.

    Example: with tags_to_update {"artist": ["A"]}, adding ["A", "B"]
    to "artist" gives {"artist": ["A", "B"]}.
    """
    existing_values = tags_to_update.get(tag_name, [])
    tags_to_update[tag_name] = remove_duplicates(existing_values + new_values)


def split_tag(joined_values: str) -> list[str]:
    """Split the provided tag by pre-defined delimeters."""
    split_values = re.split(", | and | & |; ", joined_values)
    stripped_values = [value.strip() for value in split_values]
    return stripped_values


def split_manual_value(tag_name: str, value: str) -> list[str]:
    """Split a manually entered value into the values of a tag.

    The sequence ' | ' separates values in all tags, like when tags
    are printed. Genres can also be separated by commas and
    semicolons, since genres, unlike e.g. artists and titles, don't
    contain them.

    :param tag_name: The tag the value is entered for.
    :param value: The value entered by the user.

    :return: The values of the tag.
    """
    if tag_name == "genre":
        values = re.split(r"\s*[,;|]\s*", value)
    else:
        values = value.split(" | ")
    return [v.strip() for v in values if v.strip()]


def file_path_to_song_name(file_path: Path) -> str:
    """Convert file name to readable string.

    Produce a string with song title and artist on a readable format
    from the name of the file being worked with.
    """
    text_to_print = str(file_path)
    basename_match = re.match(r"(.+/)*(.*).opus", text_to_print)
    if basename_match:
        text_to_print = basename_match.group(2)
        playlist_match = re.match(r"<(.*)> - <(.*?)(?: - Topic)*> - <(.*)> - <(.*)>", text_to_print)
        artist_title_match = re.match("<(.*?)(?: - Topic)*> - <(.*)>", text_to_print)
        title_only_match = re.match("<(.*)>", text_to_print)
        if playlist_match:
            text_to_print = playlist_match.group(2) + " - " + playlist_match.group(3)
        elif artist_title_match:
            text_to_print = artist_title_match.group(1) + " - " + artist_title_match.group(2)
        elif title_only_match:
            text_to_print = title_only_match.group(1)
    return text_to_print


def is_equal_when_stripped(values_1: list[str], values_2: list[str]) -> bool:
    """Compare lists disregarding whitespace.

    Check if content of lists of strings are the same after strings
    have been stripped.
    """
    cleaned_values_1 = [v.strip() for v in values_1]
    cleaned_values_2 = [v.strip() for v in values_2]
    return sorted(cleaned_values_1) == sorted(cleaned_values_2)


def normalize(text: str) -> str:
    """Make text comparable regardless of typography and case.

    MusicBrainz uses typographic apostrophes, quotes, and dashes,
    while YouTube and existing tags often don't.
    """
    text = unicodedata.normalize("NFKC", text)
    text = re.sub("[‘’‛´`]", "'", text)
    text = re.sub("[“”‟]", '"', text)
    text = re.sub("[‐-―]", "-", text)
    return " ".join(text.casefold().split())


def is_equal_when_normalized(values_1: list[str], values_2: list[str]) -> bool:
    """Compare lists disregarding typography, case, and order.

    Order is disregarded since tags with several values, like
    artists, may list them in different orders in different sources,
    just like in is_equal_when_stripped.
    """
    return sorted(map(normalize, values_1)) == sorted(map(normalize, values_2))
