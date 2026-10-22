"""Module with helper functions for the rest of the app."""

import re
import unicodedata
from pathlib import Path
from typing import List

from simple_term_menu import TerminalMenu

from retag_opus import constants, messages


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


def prune_title(original_title: str) -> str:
    """Clean up title tag value.

    Remove things such as live version specification and featured
    artist information from the title of a song, and remove leading
    and trailing whitespace.
    """
    pruned = original_title
    for pattern in constants.title_parse_patterns.values():
        pruned = re.sub(pattern, r"\1 \3", pruned)
    return pruned.strip()


# Separates the artist and the title in a video title, e.g. "Artist -
# Title". Dashes inside words, like in "Jay-Z", have no spaces around.
ARTIST_TITLE_SEPARATOR = r"\s+(?:-|–|—|--)\s+"

# Quotes that video titles put around the song title, e.g. "Artist -
# 'Title'"
QUOTE_PAIRS = {"'": "'", '"': '"', "“": "”", "‘": "’", "「": "」"}


def names_artist(text: str, artist: str) -> bool:
    """Check whether a text is the name of an artist.

    Typography and case don't matter. The artist can have words after
    the name in the text, since YouTube channels often add a word to
    the artist's name, like the channel "Ellen Allien UFO" for Ellen
    Allien. A text of a single word has to be the whole name, though,
    so that the song "Love" isn't taken to be the channel "Love Bites".

    Example: names_artist("Ellen Allien", "Ellen Allien UFO") is True.
    """
    text_words = normalize(text).split()
    artist_words = normalize(artist).split()
    if text_words == artist_words:
        return True
    word_count = len(text_words)
    is_start_of_artist = artist_words[:word_count] == text_words
    return len(text_words) >= 2 and is_start_of_artist


def remove_quotes(title: str) -> str:
    """Remove quotes around a title, e.g. "'softscars'" becomes "softscars"."""
    if len(title) >= 2 and QUOTE_PAIRS.get(title[0]) == title[-1]:
        return title[1:-1].strip()
    return title


def split_artist_from_title(title: str, artists: list[str]) -> tuple[str, str, str] | None:
    """Split a video title like "Artist - Title" into artist and title.

    A dash also separates other things in video titles, like a movie
    and a song or a song and its version, so the title is only split
    when the text on one side of the dash is one of the given artists.
    Those are usually the YouTube channel, which yt-dlp puts in the
    artist tag, and the channel of an artist is named after the artist.
    The artist can be on either side, since some titles are "Title -
    Artist". Quotes around the title are removed.

    Example: split_artist_from_title("yeule - 'softscars'", ["yeule"])
    returns ("yeule", "yeule", "softscars").

    :param title: The video title, with notes like "(Official Video)"
        already removed.
    :param artists: The artists the song is known to be by.

    :return: The artist that the title names, the artist as written in
        the title, and the song title, or None if no side of a dash is
        one of the artists.
    """
    # re.finditer() finds every dash with spaces around it, from left to
    # right. Each match knows where in the title it is: span() gives the
    # index where the dash and its spaces start and the index right after
    # them. In "A - B - C", they are (1, 4) and (5, 8).
    separators = list(re.finditer(ARTIST_TITLE_SEPARATOR, title))
    if not separators:
        return None
    first_separator_start, first_separator_end = separators[0].span()
    last_separator_start, last_separator_end = separators[-1].span()

    # The artist is either before the first dash, as in "Artist - Title",
    # or after the last one, as in "Title - Artist". The song title is
    # all the rest, so that it keeps any dash of its own, e.g. "Artist -
    # Song (Song - 2021)". In "A - B - C", the text before the first dash
    # is "A", and the text after the last dash is "C".
    text_before_first_separator = title[:first_separator_start]
    text_after_last_separator = title[last_separator_end:]
    for artist in artists:
        if names_artist(text_before_first_separator, artist):
            song_title = title[first_separator_end:]
            return artist, text_before_first_separator, remove_quotes(song_title)
        if names_artist(text_after_last_separator, artist):
            song_title = title[:last_separator_start]
            return artist, text_after_last_separator, remove_quotes(song_title)
    return None


def remove_video_notes(video_title: str) -> str:
    """Remove notes about a YouTube video from its title.

    Unlike prune_title(), this keeps everything about the song, like
    its version and featured artists.

    Example: "Song (Live) (Official Video) #rock" becomes "Song (Live)".
    """
    title_without_notes = video_title
    for pattern_name in ["video_note", "hashtags"]:
        pattern = constants.title_parse_patterns[pattern_name]
        title_without_notes = re.sub(pattern, r"\1 \3", title_without_notes)
    return title_without_notes.strip()


def split_tag(joined_values: str) -> List[str]:
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


def select_single_value(candidates: list[str]) -> list[str]:
    """Select a single value to keep for a tag from a menu.

    Lets the user select one of the candidate values and returns
    a list with that as the only item. The user can also choose to
    skip with q, escape, or choosing the --No change-- item.

    :param candidates: The values to choose between.

    :return: A list with the selected candidate or an empty list if
    none is selected.
    """
    candidates.append("--No change--")
    choose_one_tag_menu = TerminalMenu(candidates, title="Choose one tag to use")
    choice = choose_one_tag_menu.show()
    if choice is None:
        messages.warning("No tag selected")
    elif isinstance(choice, int) and choice != len(candidates) - 1:
        messages.info(f"Using {candidates[choice]} as tag for this song")
        return [candidates[choice]]
    return []


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
