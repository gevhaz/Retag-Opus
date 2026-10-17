"""Module for holding constants.

This module holds variables that should be constant and can be accessed
in other parts of the app.
"""
from typing import Final

INTERPUNCT: Final = "\u00b7"
# PRINTED_SPACE = "\u00b7"
PRINTED_SPACE: Final = " "
VALUE_SEPARATOR: Final = " | "


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
    # Notes about a YouTube video rather than the song, e.g. "(Official
    # Music Video)", "[Audio]" or "(Lyric Video)"
    "video_note": (
        r"(?i)(.*?)\s*[\(\[]"
        r"((?:official\s+)?(?:music\s+|lyrics?\s+)?(?:video|audio|visuali[sz]er|lyrics?)|official)"
        r"[\)\]]\s*(.*)"
    ),
    # Hashtags at the end of a video title, e.g. "#hiphop #india"
    "hashtags": r"(.*?)\s*((?:#[^\W\d_]\w*\s*)+)()$",
}

# Tags that are printed for every song, and the names they're printed
# with
tags_printed_for_every_song: Final[dict[str, str]] = {
    "title": "Title",
    "album": "Album",
    "albumartist": "Album Artist",
    "artist": "Artist(s)",
    "date": "Date",
    "genre": "Genre",
    "version": "Version",
    "performer": "Performer",
    "organization": "Organization",
    "copyright": "Copyright",
    "composer": "Composer",
    "conductor": "Conductor",
    "arranger": "Arranger",
    "author": "Author",
    "producer": "Producer",
    "publisher": "Publisher",
    "lyricist": "Lyricist",
    "writer": "Writer",
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
