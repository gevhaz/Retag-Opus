"""Module for parsing a YouTube descripton into metadata tags."""
import re
from copy import deepcopy

from retag_opus import constants
from retag_opus.utils import Utils

INTERPUNCT = "\u00b7"

Tags = dict[str, list[str]]


class DescriptionParser:
    """Parse tags from YouTube description."""

    def __init__(self, manual_album_set: bool = False) -> None:
        """Create tags dictionary that will hold the parsed tags."""
        self.tags: Tags = {}
        self.base_patterns = deepcopy(constants.all_tags)
        self.performer_patterns = deepcopy(constants.performer_tags)
        self.manual_album_set = manual_album_set
        if manual_album_set:
            self.base_patterns["discsubtitle"] = self.base_patterns["album"].copy()
            self.base_patterns["discsubtitle"]["print"] = "Disc subtitle"
            self.base_patterns["album"]["pattern"] = []

    def parse_artist_and_title(self, source_line: str) -> tuple[list[str], str]:
        """Parse artist and title from standard ContentID line.

        The standard ContentID description contains an interpunct
        character separating title and the artists. This function gets
        the artist and title of the song for this line.

        :param source_line: A string containing an interpunct character.

        :return: List or artists and title of song as string.
        """
        artist_and_title = source_line.split(" " + constants.INTERPUNCT + " ")
        title = artist_and_title[0]
        artist: list[str] = artist_and_title[1:]

        if len(artist) < 2 and ", " in artist[0]:
            artist = Utils.split_tag(artist[0])

        return artist, title

    def standard_pattern(self, field_name: str, regex: str, line: str) -> None:
        """Parse metadata from line with regex and put in field_name.

        Use a regex on a standard format to extract metadata from the
        string line and set the result to the tag field_value. If the
        value already exists, remove duplicate values.
        """
        pattern_match = re.match(regex, line)
        if pattern_match:
            field_value = pattern_match.groups()[-1].strip()
            existing_values = self.tags.get(field_name, [])
            self.tags[field_name] = Utils.remove_duplicates(existing_values + [field_value])

    def parse(self, description_tag_full: str) -> None:
        """Parse the provided youtube description.

        Parses the given description and puts the resulting tags in the
        internal tags variable of the object.

        :param description_tag_full: The full YouTube description as a
            string.
        """
        lines_since_title_artist: int = 1000

        description_tag_lines: list[str] = description_tag_full.splitlines(False)

        for description_line in description_tag_lines:
            if re.match(r"^\s*$", description_line):
                continue
            lines_since_title_artist = lines_since_title_artist + 1
            # Artist and title
            if INTERPUNCT in description_line:
                lines_since_title_artist = 0
                youtube_artist, youtube_title = self.parse_artist_and_title(description_line)
                if youtube_artist:
                    self.tags["artist"] = Utils.remove_duplicates(youtube_artist)
                self.tags["title"] = [youtube_title]

            if lines_since_title_artist == 1:
                if self.manual_album_set:
                    self.tags["discsubtitle"] = [description_line.strip()]
                else:
                    self.tags["album"] = [description_line.strip()]

            for tag_id, tag_data in self.base_patterns.items():
                for pattern in tag_data["pattern"]:
                    self.standard_pattern(tag_id, pattern, description_line)

            for tag_id, tag_data in self.performer_patterns.items():
                for pattern in tag_data["pattern"]:
                    self.standard_pattern(tag_id, pattern, description_line)

            title = self.tags.pop("title", None)
            if title:
                self.tags["title"] = [title[0]]

        artist = self.tags.get("artist")
        if artist:
            self.tags["albumartist"] = [artist[0]]
            single_artists: list[str] = []
            for joined_artists in artist:
                single_artists += Utils.split_tag(joined_artists)
            self.tags["artist"] = Utils.remove_duplicates(single_artists)

        # Loop over a copy of the names, since tags can't be deleted from
        # the dict while looping over it
        for tag_name in list(self.tags):
            if not self.tags[tag_name]:
                del self.tags[tag_name]

        # Basic pattern:
        # r".*[ ]   .*:\s*(.*)\s*"

        # Custom patterns
        for description_line in description_tag_lines:
            self.standard_pattern("copyright_date", r"\u2117 (\d\d\d\d)\s", description_line)

        copyright_date = self.tags.pop("copyright_date", None)
        date = self.tags.get("date")
        if copyright_date and not date:
            self.tags["date"] = copyright_date
