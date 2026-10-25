"""Module for parsing a YouTube description into tags.

A description can have a part that YouTube generated from the label's
data, which has a fixed layout and is parsed by
auto_generated_description. The rest is written by the uploader in any
way, so only a few common patterns and credits with known roles, e.g.
"Composer: Name", are read from it.
"""

import re
from typing import Final

from retag_opus import auto_generated_description, youtube_credits
from retag_opus.tags import Tags, add_values, remove_duplicates, split_tag

# Patterns for tags in text written by uploaders. The value is the last
# group of the pattern.
UPLOADER_TEXT_PATTERNS: Final[dict[str, list[str]]] = {
    "title": [r".*“(.*)” by .* from ‘.*’"],
    "album": [r".*“.*” by .* from ‘(.*)’"],
    "artist": [r".*\([fF]eat. (.+?)\)", r".*“.*” by (.*) from ‘.*’"],
}


def parse_uploader_text(lines: list[str]) -> Tags:
    """Parse the text an uploader wrote in a description.

    For example, "“Song” by Singer from ‘Album’" gives the title,
    artist and album, and "Guitar: Name" gives a guitarist. Lines whose
    roles aren't known, e.g. "Follow us: https://example.com", are
    skipped.

    :param lines: Lines written by the uploader.

    :return: The tags found in the lines.
    """
    tags: Tags = {}
    for line in lines:
        for tag_name, tag_patterns in UPLOADER_TEXT_PATTERNS.items():
            for pattern in tag_patterns:
                pattern_match = re.match(pattern, line)
                if pattern_match:
                    parsed_value = pattern_match.groups()[-1].strip()
                    add_values(tags_to_update=tags, tag_name=tag_name, new_values=[parsed_value])
        if ": " in line:
            for tag_name, names in youtube_credits.parse_credit_line(line).items():
                add_values(tags_to_update=tags, tag_name=tag_name, new_values=names)

    # A song has one title, so the first one found is used
    titles = tags.get("title")
    if titles:
        tags["title"] = [titles[0]]
    return tags


def non_empty_lines(description: str) -> list[str]:
    """Get the lines of a description that aren't blank."""
    lines = []
    for line in description.splitlines():
        if line.strip():
            lines.append(line)
    return lines


def is_auto_generated(description: str) -> bool:
    """Check whether a YouTube description has an auto-generated part.

    Such a part comes from the label's data, so it's more reliable than
    text written by the uploader. It counts even if the uploader pasted
    it among their own text, e.g. "Our new video!" before "Provided to
    YouTube by Label".
    """
    return auto_generated_description.find(non_empty_lines(description)) is not None


def parse(description: str) -> Tags:
    """Parse a YouTube description into tags.

    If the description has a part that YouTube generated, only that part
    is read, by its layout, and any text the uploader wrote around it is
    left out. Otherwise the whole description is read as the uploader's
    text.

    :param description: The whole YouTube description.

    :return: The tags found in the description.
    """
    lines = non_empty_lines(description)
    auto_generated_part = auto_generated_description.find(lines)
    if auto_generated_part is not None:
        first_index, last_index = auto_generated_part
        index_after_last = last_index + 1
        tags = auto_generated_description.parse(lines[first_index:index_after_last])
    else:
        tags = parse_uploader_text(lines)

    artists = tags.get("artist")
    if artists:
        single_artists: list[str] = []
        for joined_artists in artists:
            single_artists += split_tag(joined_artists)
        tags["artist"] = remove_duplicates(single_artists)
    return tags
