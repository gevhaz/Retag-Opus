"""Module for parsing the titles of songs and YouTube videos.

Titles often hold more than the name of the song, like its version, its
featured artists, notes about the video or the artist, e.g. "Artist -
Song (Live) (feat. Singer) [Official Video]". This module finds those
parts and removes them.
"""

import re
from typing import Final

from retag_opus.tags import normalize, split_tag

# Regular expressions for the parts of a title that aren't the name of
# the song, e.g. "(Live)" or "feat. Singer". Each captures three named
# groups from the title it matches: "before", the title up to the part,
# "part", the part itself, and "after", the title after it. In "Song
# (Live) [HD]", LIVE_PATTERN captures "Song", "Live" and "[HD]". Code
# that removes a part keeps "before" and "after", and code that reads a
# part, e.g. the version, takes "part".
FEATURING_PATTERN: Final = (
    r"(?i)(?P<before>.*?)\s*[\(\[\ ](?:feat|ft|featuring)\.?\s+(?P<part>[^\]\)\(\[]+)[\)\]]*\s*(?P<after>.*)"
)
REMASTER_IN_BRACKETS_PATTERN: Final = (
    r"(?i)(?P<before>.*?)\s*[\(\[](?P<part>\d{0,4}\s*remaster.*)[\)\]]\s*(?P<after>.*)"
)
REMASTER_AFTER_DASH_PATTERN: Final = r"(?i)(?P<before>.*?)\s*-\s*(?P<part>\d{0,4}.*remaster.*)(?P<after>.*)"
LIVE_PATTERN: Final = r"(?i)(?P<before>.*?)\s*[\(\[](?P<part>live.*?)[\)\]]\s*(?P<after>.*)"
INSTRUMENTAL_IN_PARENTHESES_PATTERN: Final = r"(?i)(?P<before>.*?)\s*\((?P<part>.*instrumental.*)\)\s*(?P<after>.*)"
INSTRUMENTAL_IN_SQUARE_BRACKETS_PATTERN: Final = r"(?i)(?P<before>.*?)\s*\[(?P<part>.*instrumental.*)\]\s*(?P<after>.*)"
REMIX_IN_PARENTHESES_PATTERN: Final = r"(?i)(?P<before>.+)\s*\((?P<part>.*remix.*?)\)\s*(?P<after>.*)"
REMIX_AFTER_DASH_PATTERN: Final = r"(?i)(?P<before>.+)\s*-\s*(?P<part>.*remix.*)\s*(?P<after>.*)"
ALBUM_VERSION_PATTERN: Final = r"(?i)(?P<before>.*?)\s*[\(\[](?P<part>album version.*?)[\)\]]\s*(?P<after>.*)"
# Notes about a YouTube video rather than the song, e.g. "(Official
# Music Video)", "[Audio]" or "(Lyric Video)"
VIDEO_NOTE_PATTERN: Final = (
    r"(?i)(?P<before>.*?)\s*[\(\[]"
    r"(?P<part>(?:official\s+)?(?:music\s+|lyrics?\s+)?(?:video|audio|visuali[sz]er|lyrics?)|official)"
    r"[\)\]]\s*(?P<after>.*)"
)
# Hashtags at the end of a video title, e.g. "#hiphop #india"
HASHTAGS_PATTERN: Final = r"(?P<before>.*?)\s*(?P<part>(?:#[^\W\d_]\w*\s*)+)(?P<after>)$"

# Every pattern, in the order prune_title() removes their parts in.
# Removing a part changes the text the next pattern is matched against,
# so the order can matter.
ALL_PATTERNS: Final = [
    FEATURING_PATTERN,
    REMASTER_IN_BRACKETS_PATTERN,
    REMASTER_AFTER_DASH_PATTERN,
    LIVE_PATTERN,
    INSTRUMENTAL_IN_PARENTHESES_PATTERN,
    INSTRUMENTAL_IN_SQUARE_BRACKETS_PATTERN,
    REMIX_IN_PARENTHESES_PATTERN,
    REMIX_AFTER_DASH_PATTERN,
    ALBUM_VERSION_PATTERN,
    VIDEO_NOTE_PATTERN,
    HASHTAGS_PATTERN,
]

# Patterns for versions of a song, e.g. "Live" or "2007 Remaster"
VERSION_PATTERNS: Final = [
    LIVE_PATTERN,
    ALBUM_VERSION_PATTERN,
    REMIX_IN_PARENTHESES_PATTERN,
    REMIX_AFTER_DASH_PATTERN,
    REMASTER_IN_BRACKETS_PATTERN,
    REMASTER_AFTER_DASH_PATTERN,
]

INSTRUMENTAL_PATTERNS: Final = [INSTRUMENTAL_IN_PARENTHESES_PATTERN, INSTRUMENTAL_IN_SQUARE_BRACKETS_PATTERN]

# Patterns for notes about a YouTube video, which say nothing about the
# song
VIDEO_NOTE_PATTERNS: Final = [VIDEO_NOTE_PATTERN, HASHTAGS_PATTERN]

# Separates the artist and the title in a video title, e.g. "Artist -
# Title". Dashes inside words, like in "Jay-Z", have no spaces around.
ARTIST_TITLE_SEPARATOR: Final = r"\s+(?:-|–|—|--)\s+"

# Quotes that video titles put around the song title, e.g. "Artist -
# 'Title'"
QUOTE_PAIRS: Final = {"'": "'", '"': '"', "“": "”", "‘": "’", "「": "」"}


def remove_parts(title: str, patterns: list[str]) -> str:
    """Remove the parts that the patterns find, in the given order.

    Example: remove_parts("Song (Live) [HD]", [LIVE_PATTERN]) returns
    "Song [HD]".
    """
    remaining_title = title
    for pattern in patterns:
        # Keep the text before and after the part
        remaining_title = re.sub(pattern, r"\g<before> \g<after>", remaining_title)
    return remaining_title.strip()


def find_parts(title: str, patterns: list[str]) -> list[str]:
    """Get the part that each matching pattern finds.

    Example: find_parts("Song (Live) - 2007 Remaster", [LIVE_PATTERN,
    REMASTER_AFTER_DASH_PATTERN]) returns ["Live", "2007 Remaster"].
    """
    parts_found = []
    for pattern in patterns:
        part_match = re.match(pattern, title)
        if part_match is not None:
            parts_found.append(part_match.group("part").strip())
    return parts_found


def prune_title(title: str) -> str:
    """Get the name of a song from its title.

    Example: "Song (Live) (feat. Singer)" becomes "Song".
    """
    return remove_parts(title, ALL_PATTERNS)


def remove_video_notes(title: str) -> str:
    """Remove notes about a YouTube video, but not about the song.

    Example: "Song (Live) (Official Video) #rock" becomes "Song (Live)".
    """
    return remove_parts(title, VIDEO_NOTE_PATTERNS)


def featured_artists(title: str) -> list[str]:
    """Get the featured artists named in a title.

    Example: "Song (feat. Singer & Rapper)" gives ["Singer", "Rapper"].
    """
    featured_artists_in_title = []
    for featured_artists_text in find_parts(title, [FEATURING_PATTERN]):
        featured_artists_in_title += split_tag(featured_artists_text)
    return featured_artists_in_title


def remove_featured_artists(text: str) -> str:
    """Remove the featured artists from a title or an artist credit.

    Example: "A (feat. C) & D" becomes "A & D".
    """
    return remove_parts(text, [FEATURING_PATTERN])


def versions(title: str) -> list[str]:
    """Get the versions of a song named in its title.

    Example: "Song (Live) - Remaster" gives ["Live", "Remaster"].
    """
    return find_parts(title, VERSION_PATTERNS)


def is_instrumental(title: str) -> bool:
    """Check whether a title says that the song is instrumental."""
    instrumental_parts = find_parts(title, INSTRUMENTAL_PATTERNS)
    return len(instrumental_parts) > 0


def names_artist(text: str, artist: str) -> bool:
    """Check whether a text is the name of an artist.

    Typography and case don't matter, and the text can leave out words
    at the end, e.g. "Ellen Allien" names "Ellen Allien UFO". A single
    word must be the whole name, so "Love" doesn't name "Love Bites".
    """
    text_words = normalize(text).split()
    artist_words = normalize(artist).split()
    if text_words == artist_words:
        return True
    word_count = len(text_words)
    is_start_of_artist = artist_words[:word_count] == text_words
    return len(text_words) >= 2 and is_start_of_artist


def remove_quotes(title: str) -> str:
    """Remove quotes around a title: "'softscars'" → "softscars"."""
    if len(title) >= 2 and QUOTE_PAIRS.get(title[0]) == title[-1]:
        return title[1:-1].strip()
    return title


def split_artist_from_title(title: str, artists: list[str]) -> tuple[str, str, str] | None:
    """Split a video title like "Artist - Title" into artist and title.

    The title is only split at a dash with one of the artists on either
    side of it, and quotes around the song title are removed. Notes like
    "(Official Video)" should be removed from the title first.

    Example: split_artist_from_title("yeule - 'softscars'", ["yeule"])
    returns ("yeule", "yeule", "softscars").

    :return: The artist that the title names, the artist as written in
        the title, and the song title, or None if no side of a dash is
        one of the artists.
    """
    # re.finditer() finds every dash with spaces around it, from left to
    # right. Each match knows where in the title it is: span() gives the
    # index where the dash and its spaces start and the index right
    # after them. In "A - B - C", they are (1, 4) and (5, 8).
    separators = list(re.finditer(ARTIST_TITLE_SEPARATOR, title))
    if not separators:
        return None
    first_separator_start, first_separator_end = separators[0].span()
    last_separator_start, last_separator_end = separators[-1].span()

    # A dash also separates other things, like a movie and a song, so
    # one side has to be one of the artists. That side is either before
    # the first dash, as in "Artist - Title", or after the last one, as
    # in "Title - Artist". The song title is all the rest, so that it
    # keeps any dash of its own, e.g. "Artist - Song (Song - 2021)". In
    # "A - B - C", the text before the first dash is "A", and the text
    # after the last dash is "C".
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
