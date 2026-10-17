"""Module for parsing a YouTube descripton into metadata tags."""
import re
from copy import deepcopy

from retag_opus import constants, utils, youtube_credits

INTERPUNCT = "\u00b7"

Tags = dict[str, list[str]]


class DescriptionParser:
    """Parse tags from YouTube description."""

    def __init__(self, manual_album_set: bool = False) -> None:
        """Create tags dictionary that will hold the parsed tags."""
        self.tags: Tags = {}
        self.description_patterns = deepcopy(constants.tags_printed_for_every_song)
        self.manual_album_set = manual_album_set
        if manual_album_set:
            self.description_patterns["discsubtitle"] = self.description_patterns["album"].copy()
            self.description_patterns["discsubtitle"]["print_name"] = "Disc subtitle"
            self.description_patterns["album"]["patterns"] = []

    def parse_artist_and_title(self, source_line: str) -> tuple[list[str], str]:
        """Parse artist and title from standard ContentID line.

        The standard ContentID description contains an interpunct
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

    def add_value_from_line(self, line: str, pattern: str, tag_name: str) -> None:
        """Add the value that a pattern finds in a line to a tag.

        The value is the last group of the pattern. For example, the
        pattern for the copyright year finds "2020" in "℗ 2020 Label".
        Nothing is added if the line doesn't match, or if the tag already
        has the value.
        """
        pattern_match = re.match(pattern, line)
        if pattern_match:
            parsed_value = pattern_match.groups()[-1].strip()
            existing_values = self.tags.get(tag_name, [])
            self.tags[tag_name] = utils.remove_duplicates(existing_values + [parsed_value])

    def add_credits(self, lines: list[str]) -> None:
        """Add the tags from lines with roles and a name.

        For example, "Associated Performer, Drums: Roger Taylor" adds
        "Roger Taylor" to the tag "performer:drums (drum set)". Lines
        whose roles aren't known, e.g. "Released on: 2020-01-01", are
        skipped.

        :param lines: Lines of a YouTube description.
        """
        for line in lines:
            if ": " not in line:
                continue
            credit_tags = youtube_credits.parse_credit_line(line)
            for tag_name, contributor_names in credit_tags.items():
                existing_names = self.tags.get(tag_name, [])
                self.tags[tag_name] = utils.remove_duplicates(existing_names + contributor_names)

    def parse(self, description: str) -> None:
        """Parse the provided youtube description.

        Parses the given description and puts the resulting tags in the
        internal tags variable of the object.

        :param description: The full YouTube description as a
            string.
        """
        lines_since_title_artist: int = 1000

        description_lines: list[str] = description.splitlines(False)

        for description_line in description_lines:
            if re.match(r"^\s*$", description_line):
                continue
            lines_since_title_artist = lines_since_title_artist + 1
            # Artist and title
            if INTERPUNCT in description_line:
                lines_since_title_artist = 0
                youtube_artists, youtube_title = self.parse_artist_and_title(description_line)
                if youtube_artists:
                    self.tags["artist"] = utils.remove_duplicates(youtube_artists)
                self.tags["title"] = [youtube_title]

            if lines_since_title_artist == 1:
                if self.manual_album_set:
                    self.tags["discsubtitle"] = [description_line.strip()]
                else:
                    self.tags["album"] = [description_line.strip()]

            for tag_id, tag_data in self.description_patterns.items():
                for pattern in tag_data["patterns"]:
                    self.add_value_from_line(line=description_line, pattern=pattern, tag_name=tag_id)

            title = self.tags.pop("title", None)
            if title:
                self.tags["title"] = [title[0]]

        self.add_credits(description_lines)

        artists = self.tags.get("artist")
        if artists:
            self.tags["albumartist"] = [artists[0]]
            single_artists: list[str] = []
            for joined_artists in artists:
                single_artists += utils.split_tag(joined_artists)
            self.tags["artist"] = utils.remove_duplicates(single_artists)

        # Loop over a copy of the names, since tags can't be deleted from
        # the dict while looping over it
        for tag_name in list(self.tags):
            if not self.tags[tag_name]:
                del self.tags[tag_name]

        # Without a release date, use the year in the copyright line
        copyright_year_pattern = r"\u2117 (\d\d\d\d)\s"
        for description_line in description_lines:
            self.add_value_from_line(line=description_line, pattern=copyright_year_pattern, tag_name="copyright_year")

        copyright_year = self.tags.pop("copyright_year", None)
        date = self.tags.get("date")
        if copyright_year and not date:
            self.tags["date"] = copyright_year
