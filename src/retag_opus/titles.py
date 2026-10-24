"""Module for parsing the titles of songs and YouTube videos.

Titles often hold more than the name of the song, like its version, its
featured artists, notes about the video or the artist, e.g. "Artist -
Song (Live) (feat. Singer) [Official Video]". This module finds those
parts and removes them.
"""

import re
from typing import Final

from retag_opus import utils

# Regular expressions for the parts of a title that aren't the name of
# the song, e.g. "(Live)" or "feat. Singer". Each captures three named
# groups from the title it matches: "before", the title up to the part,
# "part", the part itself, and "after", the title after it. In "Song
# (Live) [HD]", the "live" expression captures "Song", "Live" and
# "[HD]". Code that removes a part keeps "before" and "after", and code
# that reads a part, e.g. the version, takes "part".
PATTERNS: Final[dict[str, str]] = {
    "featuring": (
        r"(?i)(?P<before>.*?)\s*[\(\[\ ](?:feat|ft|featuring)\.?\s+(?P<part>[^\]\)\(\[]+)[\)\]]*\s*(?P<after>.*)"
    ),
    "remaster_in_brackets": r"(?i)(?P<before>.*?)\s*[\(\[](?P<part>\d{0,4}\s*remaster.*)[\)\]]\s*(?P<after>.*)",
    "remaster_after_dash": r"(?i)(?P<before>.*?)\s*-\s*(?P<part>\d{0,4}.*remaster.*)(?P<after>.*)",
    "live": r"(?i)(?P<before>.*?)\s*[\(\[](?P<part>live.*?)[\)\]]\s*(?P<after>.*)",
    "instrumental_in_parentheses": r"(?i)(?P<before>.*?)\s*\((?P<part>.*instrumental.*)\)\s*(?P<after>.*)",
    "instrumental_in_square_brackets": r"(?i)(?P<before>.*?)\s*\[(?P<part>.*instrumental.*)\]\s*(?P<after>.*)",
    "remix_in_parentheses": r"(?i)(?P<before>.+)\s*\((?P<part>.*remix.*?)\)\s*(?P<after>.*)",
    "remix_after_dash": r"(?i)(?P<before>.+)\s*-\s*(?P<part>.*remix.*)\s*(?P<after>.*)",
    "albumversion": r"(?i)(?P<before>.*?)\s*[\(\[](?P<part>album version.*?)[\)\]]\s*(?P<after>.*)",
    # Notes about a YouTube video rather than the song, e.g. "(Official
    # Music Video)", "[Audio]" or "(Lyric Video)"
    "video_note": (
        r"(?i)(?P<before>.*?)\s*[\(\[]"
        r"(?P<part>(?:official\s+)?(?:music\s+|lyrics?\s+)?(?:video|audio|visuali[sz]er|lyrics?)|official)"
        r"[\)\]]\s*(?P<after>.*)"
    ),
    # Hashtags at the end of a video title, e.g. "#hiphop #india"
    "hashtags": r"(?P<before>.*?)\s*(?P<part>(?:#[^\W\d_]\w*\s*)+)(?P<after>)$",
}

# Patterns for versions of a song, e.g. "Live" or "2007 Remaster"
VERSION_PATTERN_NAMES: Final = [
    "live",
    "albumversion",
    "remix_in_parentheses",
    "remix_after_dash",
    "remaster_in_brackets",
    "remaster_after_dash",
]

INSTRUMENTAL_PATTERN_NAMES: Final = ["instrumental_in_parentheses", "instrumental_in_square_brackets"]

# Patterns for notes about a YouTube video, which say nothing about the
# song
VIDEO_NOTE_PATTERN_NAMES: Final = ["video_note", "hashtags"]

# Separates the artist and the title in a video title, e.g. "Artist -
# Title". Dashes inside words, like in "Jay-Z", have no spaces around.
ARTIST_TITLE_SEPARATOR: Final = r"\s+(?:-|–|—|--)\s+"

# Quotes that video titles put around the song title, e.g. "Artist -
# 'Title'"
QUOTE_PAIRS: Final = {"'": "'", '"': '"', "“": "”", "‘": "’", "「": "」"}


def remove_parts(title: str, pattern_names: list[str]) -> str:
    """Remove the parts of a title that the given patterns find.

    Example: remove_parts("Song (Live) [HD]", ["live"]) returns
    "Song [HD]".

    :param title: The title to remove parts from.
    :param pattern_names: Keys of PATTERNS, tried in the given order.

    :return: The title without the parts, and without leading and
        trailing whitespace.
    """
    remaining_title = title
    for pattern_name in pattern_names:
        # Keep the text before and after the part
        remaining_title = re.sub(PATTERNS[pattern_name], r"\g<before> \g<after>", remaining_title)
    return remaining_title.strip()


def find_parts(title: str, pattern_names: list[str]) -> list[str]:
    """Find the parts of a title that the given patterns find.

    Example: find_parts("Song (Live) - 2007 Remaster", ["live",
    "remaster_after_dash"]) returns ["Live", "2007 Remaster"].

    :param title: The title to find parts in.
    :param pattern_names: Keys of PATTERNS, tried in the given order.

    :return: The part found by each pattern that matches, without
        leading and trailing whitespace.
    """
    parts_found = []
    for pattern_name in pattern_names:
        part_match = re.match(PATTERNS[pattern_name], title)
        if part_match is not None:
            parts_found.append(part_match.group("part").strip())
    return parts_found


def prune_title(original_title: str) -> str:
    """Get the name of a song from its title.

    Everything that the patterns in PATTERNS find is removed, like the
    version of the song, its featured artists and notes about a YouTube
    video, and so are leading and trailing whitespace.

    Example: "Song (Live) (feat. Singer)" becomes "Song".
    """
    return remove_parts(original_title, list(PATTERNS))


def remove_video_notes(video_title: str) -> str:
    """Remove notes about a YouTube video from its title.

    Unlike prune_title(), this keeps everything about the song, like
    its version and featured artists.

    Example: "Song (Live) (Official Video) #rock" becomes "Song (Live)".
    """
    return remove_parts(video_title, VIDEO_NOTE_PATTERN_NAMES)


def featured_artists(title: str) -> list[str]:
    """Get the featured artists named in a title.

    Example: featured_artists("Song (feat. Singer & Rapper)") returns
    ["Singer", "Rapper"].

    :return: The featured artists, or an empty list if the title names
        none.
    """
    featured_artists_in_title = []
    for featured_artists_text in find_parts(title, ["featuring"]):
        featured_artists_in_title += utils.split_tag(featured_artists_text)
    return featured_artists_in_title


def remove_featured_artists(text: str) -> str:
    """Remove the featured artists from a title or an artist credit.

    Example: remove_featured_artists("A (feat. C) & D") returns
    "A & D", and remove_featured_artists("A & B feat. C") returns
    "A & B".
    """
    return remove_parts(text, ["featuring"])


def versions(title: str) -> list[str]:
    """Get the versions of a song named in its title.

    Example: versions("Song (Live) - 2007 Remaster") returns ["Live",
    "2007 Remaster"].

    :return: The versions, or an empty list if the title names none.
    """
    return find_parts(title, VERSION_PATTERN_NAMES)


def is_instrumental(title: str) -> bool:
    """Check whether a title says that the song is instrumental.

    Example: is_instrumental("Song [Instrumental]") is True.
    """
    instrumental_parts = find_parts(title, INSTRUMENTAL_PATTERN_NAMES)
    return len(instrumental_parts) > 0


def names_artist(text: str, artist: str) -> bool:
    """Check whether a text is the name of an artist.

    Typography and case don't matter. The artist can have words after
    the name in the text, since YouTube channels often add a word to
    the artist's name, like the channel "Ellen Allien UFO" for Ellen
    Allien. A text of a single word has to be the whole name, though,
    so that the song "Love" isn't taken to be the channel "Love Bites".

    Example: names_artist("Ellen Allien", "Ellen Allien UFO") is True.
    """
    text_words = utils.normalize(text).split()
    artist_words = utils.normalize(artist).split()
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
    # index where the dash and its spaces start and the index right
    # after them. In "A - B - C", they are (1, 4) and (5, 8).
    separators = list(re.finditer(ARTIST_TITLE_SEPARATOR, title))
    if not separators:
        return None
    first_separator_start, first_separator_end = separators[0].span()
    last_separator_start, last_separator_end = separators[-1].span()

    # The artist is either before the first dash, as in "Artist -
    # Title", or after the last one, as in "Title - Artist". The song
    # title is all the rest, so that it keeps any dash of its own, e.g.
    # "Artist - Song (Song - 2021)". In "A - B - C", the text before the
    # first dash is "A", and the text after the last dash is "C".
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
