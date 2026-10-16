"""Module for parsing text in the existing metadata keys.

This module is for parsing text in the existing metadata keys, rather
that the YouTube description.
"""
import re
from typing import Dict, Final, List

from retag_opus import constants
from retag_opus.utils import Utils

INTERPUNCT: Final[str] = "\u00b7"


class TagsParser:
    """Clean and parse already existing sets of tags.

    This class is for working with a set of tags and parsing metadata
    from them, such as the version of a song (e.g. "live version"), but
    also for cleaning up the tags by e.g. splitting them by pre-defined
    delimeters.
    """

    def __init__(self, tags: Dict[str, List[str]]):
        """Set attributes of the TagsParser."""
        self.tags: Dict[str, List[str]] = {}
        self.original_tags = tags

    def parse_tags(self) -> None:
        """Look through old tags for metadata.

        Go through some of the existing tags and see if they contain
        information that should go into another tag.
        """
        old_title = self.original_tags.get("title", [])

        old_artist = self.original_tags.get("artist", [])
        if len(old_artist) == 1:
            old_artist = Utils.split_tag(old_artist[0])
        new_artist = []

        old_version = self.original_tags.get("version", [])
        new_version = []

        old_genre = self.original_tags.get("genre", [])
        new_genre = []

        version_pattern_names = ["live", "albumversion", "remix", "remix2", "remaster", "remaster2"]
        instrumental_pattern_names = ["instrumental", "instrumental2"]

        for title in old_title:
            featuring_regex = constants.tag_parse_patterns["featuring"]
            featuring_match = re.match(featuring_regex, title)
            if featuring_match:
                featured_artists = featuring_match.group(2).strip()
                new_artist += Utils.split_tag(featured_artists)

            for pattern_name in version_pattern_names:
                version_regex = constants.tag_parse_patterns[pattern_name]
                version_match = re.match(version_regex, title)
                if version_match:
                    new_version.append(version_match.group(2).strip())

            for pattern_name in instrumental_pattern_names:
                instrumental_regex = constants.tag_parse_patterns[pattern_name]
                if re.match(instrumental_regex, title):
                    new_genre.append("Instrumental")

        if set(new_version) != set(old_version) and len(new_version) > 0:
            self.tags["version"] = Utils().remove_duplicates(old_version + new_version)

        if set(new_artist) != set(old_artist) and len(new_artist) > 0:
            self.tags["artist"] = Utils().remove_duplicates(old_artist + new_artist)

        if set(new_genre) != set(old_genre) and len(new_genre) > 0:
            self.tags["genre"] = Utils().remove_duplicates(old_genre + new_genre)

        if len(old_title) > 0:
            pruned_title = Utils().prune_title(old_title[0])
            if old_title[0] != pruned_title:
                self.tags["title"] = [pruned_title]

    def split_select_original_tags(self) -> None:
        """Split certain original tags on predefined separators.

        Split the genre and artist tag into a list if they contains
        pre-defined separators. New tags are only set if there is
        anything that differs from the old tags.
        """
        tags_to_split = ["genre", "artist"]

        for tag in tags_to_split:
            tags_tag = self.original_tags.get(tag)
            if tags_tag is not None and not len(tags_tag) > 1:
                new_tag = Utils().split_tag(tags_tag[0])
                if new_tag != tags_tag:
                    self.tags[tag] = new_tag
