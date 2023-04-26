"""Module for holding constants.

This module holds variables that should be constant and can be accessed
in other parts of the app.
"""
from typing import Final, TypedDict

INTERPUNCT: Final = "\u00b7"
# SPACE = "\u00b7"
SPACE: Final = " "
SEP: Final = " | "


class ParsingReference(TypedDict):
    """This is dictionary with a tag name and regex for parsing it."""

    print: str
    pattern: list[str]


tag_parse_patterns: Final[dict[str, str]] = {
    "featuring": r"(?i)(.*?)\s*[\(\[\ ](?:feat|ft|featuring)\.?\s+([^\]\)\(\[]+)[\)\]]*\s*(.*)",
    "remaster": r"(?i)(.*?)\s*[\(\[](\d{0,4}\s*remaster.*)[\)\]]\s*(.*)",
    "remaster2": r"(?i)(.*?)\s*-\s*(\d{0,4}.*remaster.*)(.*)",
    "live": r"(?i)(.*?)\s*[\(\[](live.*?)[\)\]]\s*(.*)",
    "instrumental": r"(?i)(.*?)\s*\((.*instrumental.*)\)\s*(.*)",
    "instrumental2": r"(?i)(.*?)\s*\[(.*instrumental.*)\]\s*(.*)",
    "remix": r"(?i)(.+)\s*\((.*remix.*?)\)\s*(.*)",
    "remix2": r"(?i)(.+)\s*-\s*(.*remix.*)\s*(.*)",
    "albumversion": r"(?i)(.*?)\s*[\(\[](album version.*?)[\)\]]\s*(.*)",
}

all_tags: Final[dict[str, ParsingReference]] = {
    "title": {"print": "Title", "pattern": [r".*“(.*)” by .* from ‘.*’"]},
    "album": {"print": "Album", "pattern": [r".*“.*” by .* from ‘(.*)’"]},
    "albumartist": {"print": "Album Artist", "pattern": []},
    "artist": {
        "print": "Artist(s)",
        "pattern": [
            r"^(?!.*(https?|[mM]akeup|[fF]inishing)).*[aA]rtist.*:\s*(.+)\s*",
            r".*\([fF]eat. (.+?)\)",
            r".*“.*” by (.*) from ‘.*’",
        ],
    },
    "date": {"print": "Date", "pattern": [r"Released on:\s*(\d\d\d\d-\d\d-\d\d)"]},
    "genre": {"print": "Genre", "pattern": []},
    "version": {"print": "Version", "pattern": []},
    "performer": {"print": "Performer", "pattern": [r".*[pP]erformer.*:\s*(.+)\s*"]},
    "organization": {"print": "Organization", "pattern": [r"Provided to YouTube by (.+)\s*"]},
    "copyright": {"print": "Copyright", "pattern": [r"\u2117 (.+)\s*"]},
    "composer": {"print": "Composer", "pattern": [r".*?[cC]omposer.*:\s*(.+)\s*"]},
    "conductor": {"print": "Conductor", "pattern": [r".*[cC]onductor.*:\s*(.+)\s*"]},
    "arranger": {
        "print": "Arranger",
        "pattern": [r".*?[aA]rranged\s+[bB]y.*:\s*(.+)\s*", r".*?[aA]rranger.*:\s*(.+)\s*"],
    },
    "author": {"print": "Author", "pattern": [r"(.*, )?[aA]uthor.*:\s*(.+)\s*"]},
    "producer": {"print": "Producer", "pattern": [r"(.*, )?[pP]roducer.*:\s*(.+)\s*"]},
    "publisher": {"print": "Publisher", "pattern": [r"(.*, )?[pP]ublisher.*:\s*(.+)\s*"]},
    "lyricist": {
        "print": "Lyricist",
        "pattern": [
            r"(.*, )?[wW]riter.*:\s*(.+)\s*",
            r"(.*, )?[wW]ritten\s+[bB]y.*:\s*(.+)\s*",
            r".*[lL]yricist.*:\s*(.+)\s*",
        ],
    },
}

performer_tags: Final[dict[str, ParsingReference]] = {
    "performer:vocals": {"print": "- Vocals", "pattern": [r"(.*, )?(Lead\s+)?[vV]ocal(?!.*[eE]ngineer).*:\s*(.+)\s*"]},
    "performer:background vocals": {
        "print": "- Background Vocals",
        "pattern": [r"(.*, )?[bB]ackground\s+[vV]ocal.*:\s*(.+)\s*"],
    },
    "performer:drums": {"print": "- Drums", "pattern": [r"(.*, )?[dD]rum.*:\s*(.+)\s*"]},
    "performer:percussion": {"print": "- Percussion", "pattern": [r".*[pP]ercussion.*:\s*(.+)\s*"]},
    "performer:keyboard": {"print": "- Keyboard", "pattern": [r"(.*, )?[kK]eyboard.*:\s*(.+)\s*"]},
    "performer:piano": {"print": "- Piano", "pattern": [r"(.*, )?[pP]iano.*:\s*(.+)\s*"]},
    "performer:synthesizer": {"print": "- Synthesizer", "pattern": [r".*[sS]ynth.*:\s*(.+)\s*"]},
    "performer:guitar": {
        "print": "- Guitar",
        "pattern": [r"(.*, )?[gG]uitar.*:\s*(.+)\s*" r".*[eE]lectric\s+[gG]uitar.*:\s*(.+)\s*"],
    },
    "performer:electric guitar": {"print": "- Electric guitar", "pattern": []},
    "performer:bass guitar": {"print": "- Bass guitar", "pattern": [r".*[bB]ass\s+[gG]uitar.*:\s*(.+)\s*"]},
    "performer:acoustic guitar": {"print": "- Acoustic guitar", "pattern": [r".*[aA]coustic\s+[gG]uitar.*:\s*(.+)\s*"]},
    "performer:ukulele": {"print": "- Ukulele", "pattern": [r".*[uU]kulele.*:\s*(.+)\s*"]},
    "performer:violin": {"print": "- Violin", "pattern": [r"(.*, )?[vV]iolin.*:\s*(.+)\s*"]},
    "performer:double bass": {"print": "- Double bass", "pattern": [r".*[dD]ouble\s+[bB]ass.*:\s*(.+)\s*"]},
    "performer:cello": {"print": "- Cello", "pattern": [r"(.*, )?[cC]ello.*:\s*(.+)\s*"]},
    "performer:programming": {"print": "- Programming", "pattern": [r"(.*, )?[pP]rogramm(er|ing).*:\s*(.+)\s*"]},
    "performer:saxophone": {"print": "- Saxophone", "pattern": [r"(.*, )?[sS]axophone.*:\s*(.+)\s*"]},
    "performer:flute": {"print": "- Flute", "pattern": [r"(.*, )?[fF]lute.*:\s*(.+)\s*"]},
}
