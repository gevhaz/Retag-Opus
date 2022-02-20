from typing import Any, Dict

INTERPUNCT = '\u00b7'
SPACE = '\u00b7'
SPACE = ' '
SEP = " | "

tag_parse_patterns: Dict[str, str] = {
        "featuring": r"(.*?)\s*[\(\[][fF]eat.?\s+(.+?)[\)\]]\s*(.*)",
        "remastered": r"(.*?)\s*\(([rR]emastered.*)\)\s*(.*)",
        "live": r"(.*?)\s*[\(\[]([lL]ive.*)[\)\]]\s*(.*)",
        "instrumental": r"(.*?)\s*[\(\[]([iI]nstrumental.*)[\)\]]\s*(.*)",
        "remix": r"(.*?)\s*\((.*[rR]emix.*)\)\s*(.*)"
    }

all_tags: Dict[str, Dict[str, Any]] = {
    "title": {
        "print": "Title",
        "pattern": [
            r".*“(.*)” by .* from ‘.*’"
            ]
        },
    "album": {
        "print": "Album",
        "pattern": [
                r".*“.*” by .* from ‘(.*)’"
            ]
        },
    "albumartist": {
        "print": "Album Artist",
        "pattern": [
            ]
        },
    "artist": {
        "print": "Artist(s)",
        "pattern": [
            r"^(?!.*(https?|[mM]akeup|[fF]inishing)).*[aA]rtist.*:\s*(.+)\s*",
            r".*\([fF]eat. (.+?)\)",
            r".*“.*” by (.*) from ‘.*’"
            ]
        },
    "date": {
        "print": "Date",
        "pattern": [
                r"Released on:\s*(\d\d\d\d-\d\d-\d\d)"
            ]
        },
    "genre": {
        "print": "Genre",
        "pattern": [
            ]
        },
    "version": {
        "print": "Version",
        "pattern": [
            ]
        },
    "performer": {
        "print": "Performer",
        "pattern": [
            r".*[pP]erformer.*:\s*(.+)\s*"
            ]
        },
    "organization": {
        "print": "Organization",
        "pattern": [
            r"Provided to YouTube by (.+)\s*"
            ]
        },
    "copyright": {
        "print": "Copyright",
        "pattern": [
                r"\u2117 (.+)\s*"
            ]
        },
    "composer": {
        "print": "Composer",
        "pattern": [
            r".*?[cC]omposer.*:\s*(.+)\s*"
            ]
        },
    "conductor": {
        "print": "Conductor",
        "pattern": [
            r".*[cC]onductor.*:\s*(.+)\s*"
            ]
        },
    "arranger": {
        "print": "Arranger",
        "pattern": [
            r".*?[aA]rranged\s+[bB]y.*:\s*(.+)\s*",
            r".*?[aA]rranger.*:\s*(.+)\s*"
            ]
        },
    "author": {
        "print": "Author",
        "pattern": [
            r"(.*, )?[aA]uthor.*:\s*(.+)\s*"
            ]
        },
    "producer": {
        "print": "Producer",
        "pattern": [
            r"(.*, )?[pP]roducer.*:\s*(.+)\s*"
            ]
        },
    "publisher": {
        "print": "Publisher",
        "pattern": [
            r"(.*, )?[pP]ublisher.*:\s*(.+)\s*"
            ]
        },
    "lyricist": {
        "print": "Lyricist",
        "pattern": [
            r"(.*, )?[wW]riter.*:\s*(.+)\s*",
            r"(.*, )?[wW]ritten\s+[bB]y.*:\s*(.+)\s*",
            r".*[lL]yricist.*:\s*(.+)\s*"
            ]
        }
    }

performer_tags: Dict[str, Dict[str, Any]] = {
    "performer:vocals": {
        "print": "- Vocals",
        "pattern": [
            r"(.*, )?(Lead\s+)?[vV]ocal(?!.*[eE]ngineer).*:\s*(.+)\s*"
            ]
        },
    "performer:background vocals": {
        "print": "- Background Vocals",
        "pattern": [
            r"(.*, )?[bB]ackground\s+[vV]ocal.*:\s*(.+)\s*"
            ]
        },
    "performer:drums": {
        "print": "- Drums",
        "pattern": [
            r"(.*, )?[dD]rum.*:\s*(.+)\s*"
            ]
        },
    "performer:percussion": {
        "print": "- Percussion",
        "pattern": [
            r".*[pP]ercussion.*:\s*(.+)\s*"
            ]
        },
    "performer:keyboard": {
        "print": "- Keyboard",
        "pattern": [
            r"(.*, )?[kK]eyboard.*:\s*(.+)\s*"
            ]
        },
    "performer:piano": {
        "print": "- Piano",
        "pattern": [
            r"(.*, )?[pP]iano.*:\s*(.+)\s*"
            ]
        },
    "performer:synthesizer": {
        "print": "- Synthesizer",
        "pattern": [
            r".*[sS]ynth.*:\s*(.+)\s*"
            ]
        },
    "performer:guitar": {
        "print": "- Guitar",
        "pattern": [
            r"(.*, )?[gG]uitar.*:\s*(.+)\s*"
            r".*[eE]lectric\s+[gG]uitar.*:\s*(.+)\s*"
            ]
        },
    "performer:electric guitar": {
        "print": "- Electric guitar",
        "pattern": [
            ]
        },
    "performer:bass guitar": {
        "print": "- Bass guitar",
        "pattern": [
            r".*[bB]ass\s+[gG]uitar.*:\s*(.+)\s*"
            ]
        },
    "performer:acoustic guitar": {
        "print": "- Acoustic guitar",
        "pattern": [
            r".*[aA]coustic\s+[gG]uitar.*:\s*(.+)\s*"
            ]
        },
    "performer:ukulele": {
        "print": "- Ukulele",
        "pattern": [
            r".*[uU]kulele.*:\s*(.+)\s*"
            ]
        },
    "performer:violin": {
        "print": "- Violin",
        "pattern": [
            r"(.*, )?[vV]iolin.*:\s*(.+)\s*"
            ]
        },
    "performer:double bass": {
        "print": "- Double bass",
        "pattern": [
            r".*[dD]ouble\s+[bB]ass.*:\s*(.+)\s*"
            ]
        },
    "performer:cello": {
        "print": "- Cello",
        "pattern": [
            r"(.*, )?[cC]ello.*:\s*(.+)\s*"
            ]
        },
    "performer:programming": {
        "print": "- Programming",
        "pattern": [
            r"(.*, )?[pP]rogramm(er|ing).*:\s*(.+)\s*"
            ]
        },
    "performer:saxophone": {
        "print": "- Saxophone",
        "pattern": [
            r"(.*, )?[sS]axophone.*:\s*(.+)\s*"
            ]
        },
    "performer:flute": {
        "print": "- Flute",
        "pattern": [
            r"(.*, )?[fF]lute.*:\s*(.+)\s*"
            ]
        }
    }
