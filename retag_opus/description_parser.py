"""Module for parsing a YouTube descripton into metadata tags."""
import re
from typing import Final

from retag_opus import constants, utils, youtube_credits

Tags = dict[str, list[str]]

# Patterns for parsing tags from lines of YouTube descriptions. The
# value is the last group of the pattern. Credits, e.g. "Composer:
# Name", are parsed by youtube_credits instead.
DESCRIPTION_PATTERNS: Final[dict[str, list[str]]] = {
    "title": [r".*“(.*)” by .* from ‘.*’"],
    "album": [r".*“.*” by .* from ‘(.*)’"],
    "artist": [r".*\([fF]eat. (.+?)\)", r".*“.*” by (.*) from ‘.*’"],
    "date": [r"Released on:\s*(\d\d\d\d-\d\d-\d\d)"],
    "organization": [r"Provided to YouTube by (.+)\s*"],
    "copyright": [r"℗ (.+)\s*"],
}


def parse_artist_and_title(source_line: str) -> tuple[list[str], str]:
    """Parse artist and title from a line of an auto-generated description.

    An auto-generated YouTube description contains an interpunct
    character separating title and the artists. This function gets
    the artist and title of the song for this line.

    :param source_line: A string containing an interpunct character.

    :return: List or artists and title of song as string.
    """
    title_and_artists = source_line.split(" " + constants.INTERPUNCT + " ")
    title = title_and_artists[0]
    artists: list[str] = title_and_artists[1:]

    if len(artists) < 2 and ", " in artists[0]:
        artists = utils.split_tag(artists[0])

    return artists, title


def add_value_from_line(tags: Tags, line: str, pattern: str, tag_name: str) -> None:
    """Add the value that a pattern finds in a line to a tag.

    The value is the last group of the pattern. For example, the
    pattern for the copyright year finds "2020" in "℗ 2020 Label".
    Nothing is added if the line doesn't match, or if the tag already
    has the value.
    """
    pattern_match = re.match(pattern, line)
    if pattern_match:
        parsed_value = pattern_match.groups()[-1].strip()
        utils.add_values(tags_to_update=tags, tag_name=tag_name, new_values=[parsed_value])


def add_credits(tags: Tags, lines: list[str]) -> None:
    """Add the tags from lines with roles and a name.

    For example, "Associated Performer, Drums: Roger Taylor" adds
    "Roger Taylor" to the tag "performer:drums (drum set)". Lines
    whose roles aren't known, e.g. "Released on: 2020-01-01", are
    skipped.

    :param tags: The tags to add to.
    :param lines: Lines of a YouTube description.
    """
    for line in lines:
        if ": " not in line:
            continue
        for tag_name, names in youtube_credits.parse_credit_line(line).items():
            utils.add_values(tags_to_update=tags, tag_name=tag_name, new_values=names)


def parse(description: str, manual_album_set: bool = False) -> Tags:
    """Parse a YouTube description into tags.

    :param description: The full YouTube description as a string.
    :param manual_album_set: Whether the user has set the album. Then
        the album of the song is its disc subtitle.

    :return: The tags found in the description.
    """
    patterns = dict(DESCRIPTION_PATTERNS)
    if manual_album_set:
        patterns["discsubtitle"] = patterns.pop("album")

    tags: Tags = {}
    lines_since_title_artist: int = 1000

    description_lines: list[str] = description.splitlines(False)

    for description_line in description_lines:
        if re.match(r"^\s*$", description_line):
            continue
        lines_since_title_artist = lines_since_title_artist + 1
        # Artist and title
        if constants.INTERPUNCT in description_line:
            lines_since_title_artist = 0
            youtube_artists, youtube_title = parse_artist_and_title(description_line)
            if youtube_artists:
                tags["artist"] = utils.remove_duplicates(youtube_artists)
            tags["title"] = [youtube_title]

        if lines_since_title_artist == 1:
            if manual_album_set:
                tags["discsubtitle"] = [description_line.strip()]
            else:
                tags["album"] = [description_line.strip()]

        for tag_name, tag_patterns in patterns.items():
            for pattern in tag_patterns:
                add_value_from_line(tags, line=description_line, pattern=pattern, tag_name=tag_name)

        title = tags.pop("title", None)
        if title:
            tags["title"] = [title[0]]

    add_credits(tags, description_lines)

    artists = tags.get("artist")
    if artists:
        tags["albumartist"] = [artists[0]]
        single_artists: list[str] = []
        for joined_artists in artists:
            single_artists += utils.split_tag(joined_artists)
        tags["artist"] = utils.remove_duplicates(single_artists)

    # Loop over a copy of the names, since tags can't be deleted from
    # the dict while looping over it
    for tag_name in list(tags):
        if not tags[tag_name]:
            del tags[tag_name]

    # Without a release date, use the year in the copyright line
    copyright_year_pattern = r"℗ (\d\d\d\d)\s"
    for description_line in description_lines:
        add_value_from_line(tags, line=description_line, pattern=copyright_year_pattern, tag_name="copyright_year")

    copyright_year = tags.pop("copyright_year", None)
    date = tags.get("date")
    if copyright_year and not date:
        tags["date"] = copyright_year
    return tags
