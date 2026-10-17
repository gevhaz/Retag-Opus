"""Module for parsing a YouTube description into tags.

A description can have a part that YouTube generated from the label's
data, which has a fixed layout and is parsed by
auto_generated_description. The rest is written by the uploader in any
way, so only a few common patterns and credits with known roles, e.g.
"Composer: Name", are read from it.
"""
import re
from typing import Final

from retag_opus import auto_generated_description, utils, youtube_credits

Tags = dict[str, list[str]]

# Patterns for tags in text written by uploaders. The value is the last
# group of the pattern.
UPLOADER_TEXT_PATTERNS: Final[dict[str, list[str]]] = {
    "title": [r".*“(.*)” by .* from ‘.*’"],
    "album": [r".*“.*” by .* from ‘(.*)’"],
    "artist": [r".*\([fF]eat. (.+?)\)", r".*“.*” by (.*) from ‘.*’"],
}


def parse_uploader_text(lines: list[str], manual_album_set: bool) -> Tags:
    """Parse the text an uploader wrote in a description.

    For example, "“Song” by Singer from ‘Album’" gives the title,
    artist and album, and "Guitar: Name" gives a guitarist. Lines whose
    roles aren't known, e.g. "Follow us: https://example.com", are
    skipped.

    :param lines: Lines written by the uploader.
    :param manual_album_set: Whether the user has set the album. Then
        the album of the song is its disc subtitle.

    :return: The tags found in the lines.
    """
    patterns = dict(UPLOADER_TEXT_PATTERNS)
    if manual_album_set:
        patterns["discsubtitle"] = patterns.pop("album")

    tags: Tags = {}
    for line in lines:
        for tag_name, tag_patterns in patterns.items():
            for pattern in tag_patterns:
                pattern_match = re.match(pattern, line)
                if pattern_match:
                    utils.add_values(tags, tag_name, [pattern_match.groups()[-1].strip()])
        if ": " in line:
            for tag_name, names in youtube_credits.parse_credit_line(line).items():
                utils.add_values(tags, tag_name, names)

    # A song has one title, so the first one found is used
    titles = tags.get("title")
    if titles:
        tags["title"] = [titles[0]]
    return tags


def parse(description: str, manual_album_set: bool = False) -> Tags:
    """Parse a YouTube description into tags.

    Where both the auto-generated part and the uploader's text have a
    tag, the value from the auto-generated part is used, since its
    layout is known.

    :param description: The whole YouTube description.
    :param manual_album_set: Whether the user has set the album. Then
        the album of the song is its disc subtitle.

    :return: The tags found in the description.
    """
    lines = []
    for line in description.splitlines():
        if line.strip():
            lines.append(line)

    uploader_lines = lines
    auto_generated_tags: Tags = {}
    auto_generated_part = auto_generated_description.find(lines)
    if auto_generated_part is not None:
        first_index, last_index = auto_generated_part
        index_after_last = last_index + 1
        auto_generated_lines = lines[first_index:index_after_last]
        auto_generated_tags = auto_generated_description.parse(auto_generated_lines, manual_album_set)
        uploader_lines = lines[:first_index] + lines[index_after_last:]

    tags = parse_uploader_text(uploader_lines, manual_album_set)
    tags.update(auto_generated_tags)

    artists = tags.get("artist")
    if artists:
        tags["albumartist"] = [artists[0]]
        single_artists: list[str] = []
        for joined_artists in artists:
            single_artists += utils.split_tag(joined_artists)
        tags["artist"] = utils.remove_duplicates(single_artists)
    return tags
