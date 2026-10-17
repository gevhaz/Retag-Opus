"""Module for holding constants.

This module holds variables that should be constant and can be accessed
in other parts of the app.
"""
from typing import Final, TypedDict

INTERPUNCT: Final = "\u00b7"
# PRINTED_SPACE = "\u00b7"
PRINTED_SPACE: Final = " "
VALUE_SEPARATOR: Final = " | "


class PrintNameAndPatterns(TypedDict):
    """The name a tag is printed with, and patterns for parsing it from descriptions."""

    print_name: str
    patterns: list[str]


title_parse_patterns: Final[dict[str, str]] = {
    "featuring": r"(?i)(.*?)\s*[\(\[\ ](?:feat|ft|featuring)\.?\s+([^\]\)\(\[]+)[\)\]]*\s*(.*)",
    "remaster_in_brackets": r"(?i)(.*?)\s*[\(\[](\d{0,4}\s*remaster.*)[\)\]]\s*(.*)",
    "remaster_after_dash": r"(?i)(.*?)\s*-\s*(\d{0,4}.*remaster.*)(.*)",
    "live": r"(?i)(.*?)\s*[\(\[](live.*?)[\)\]]\s*(.*)",
    "instrumental_in_parentheses": r"(?i)(.*?)\s*\((.*instrumental.*)\)\s*(.*)",
    "instrumental_in_square_brackets": r"(?i)(.*?)\s*\[(.*instrumental.*)\]\s*(.*)",
    "remix_in_parentheses": r"(?i)(.+)\s*\((.*remix.*?)\)\s*(.*)",
    "remix_after_dash": r"(?i)(.+)\s*-\s*(.*remix.*)\s*(.*)",
    "albumversion": r"(?i)(.*?)\s*[\(\[](album version.*?)[\)\]]\s*(.*)",
}

# Tags that are printed for every song, and patterns for parsing them
# from YouTube descriptions. Credits, e.g. "Composer: Name", are parsed
# by youtube_credits instead.
tags_printed_for_every_song: Final[dict[str, PrintNameAndPatterns]] = {
    "title": {"print_name": "Title", "patterns": [r".*“(.*)” by .* from ‘.*’"]},
    "album": {"print_name": "Album", "patterns": [r".*“.*” by .* from ‘(.*)’"]},
    "albumartist": {"print_name": "Album Artist", "patterns": []},
    "artist": {
        "print_name": "Artist(s)",
        "patterns": [r".*\([fF]eat. (.+?)\)", r".*“.*” by (.*) from ‘.*’"],
    },
    "date": {"print_name": "Date", "patterns": [r"Released on:\s*(\d\d\d\d-\d\d-\d\d)"]},
    "genre": {"print_name": "Genre", "patterns": []},
    "version": {"print_name": "Version", "patterns": []},
    "performer": {"print_name": "Performer", "patterns": []},
    "organization": {"print_name": "Organization", "patterns": [r"Provided to YouTube by (.+)\s*"]},
    "copyright": {"print_name": "Copyright", "patterns": [r"\u2117 (.+)\s*"]},
    "composer": {"print_name": "Composer", "patterns": []},
    "conductor": {"print_name": "Conductor", "patterns": []},
    "arranger": {"print_name": "Arranger", "patterns": []},
    "author": {"print_name": "Author", "patterns": []},
    "producer": {"print_name": "Producer", "patterns": []},
    "publisher": {"print_name": "Publisher", "patterns": []},
    "lyricist": {"print_name": "Lyricist", "patterns": []},
    "writer": {"print_name": "Writer", "patterns": []},
}

# Prefix of tags with a performer's role, e.g. "performer:lead vocals".
# Quod Libet uses the same tags, and Picard reads them.
PERFORMER_PREFIX: Final = "performer:"

# Common performer tags, which are printed first, in this order. Their
# roles are recognized in YouTube credits on their own, e.g. "Piano:
# Name", while other roles have to come after "Associated Performer".
# The roles are named as on MusicBrainz, so that values from MusicBrainz
# and from YouTube end up in the same tag and can be compared.
common_performer_tags: Final[list[str]] = [
    "performer:lead vocals",
    "performer:background vocals",
    "performer:drums (drum set)",
    "performer:percussion",
    "performer:keyboard",
    "performer:piano",
    "performer:synthesizer",
    "performer:guitar",
    "performer:electric guitar",
    "performer:bass guitar",
    "performer:acoustic guitar",
    "performer:ukulele",
    "performer:violin",
    "performer:double bass",
    "performer:cello",
    "performer:saxophone",
    "performer:flute",
]

# Prefix of tags with MusicBrainz identifiers. The user can't judge
# identifiers, only the MusicBrainz match they come from.
MUSICBRAINZ_ID_PREFIX: Final = "musicbrainz_"

# Tags that are only right if the song was matched to the right track
# on MusicBrainz, which is announced once. They're set without a message
# each, but still shown.
track_position_tags: Final[list[str]] = ["tracknumber", "totaltracks", "discnumber", "totaldiscs"]

# Tags that describe the release a song was found on, which are only
# right for the album if it's that release
release_tags: Final[list[str]] = track_position_tags + [
    "musicbrainz_albumid",
    "musicbrainz_albumartistid",
    "musicbrainz_releasegroupid",
]
