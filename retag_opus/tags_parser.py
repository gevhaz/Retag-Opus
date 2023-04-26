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

        for title in old_title:
            featuring_regex = constants.tag_parse_patterns["featuring"]
            pattern_match = re.match(featuring_regex, title)
            if pattern_match:
                new_artist += Utils().split_tag(pattern_match.groups()[1].strip())

            live_regex = constants.tag_parse_patterns["live"]
            live_match = re.match(live_regex, title)
            if live_match:
                new_version.append(live_match.groups()[1].strip())

            albumversion_regex = constants.tag_parse_patterns["albumversion"]
            albumversion_match = re.match(albumversion_regex, title)
            if albumversion_match:
                new_version.append(albumversion_match.groups()[1].strip())

            instrumental_regex = constants.tag_parse_patterns["instrumental"]
            instrumental_match = re.match(instrumental_regex, title)
            if instrumental_match:
                new_genre.append("Instrumental")

            instrumental2_regex = constants.tag_parse_patterns["instrumental2"]
            instrumental2_match = re.match(instrumental2_regex, title)
            if instrumental2_match:
                new_genre.append("Instrumental")

            remix_regex = constants.tag_parse_patterns["remix"]
            remix_match = re.match(remix_regex, title)
            if remix_match:
                new_version.append(remix_match.groups()[1].strip())

            remix2_regex = constants.tag_parse_patterns["remix2"]
            remix2_match = re.match(remix2_regex, title)
            if remix2_match:
                new_version.append(remix2_match.groups()[1].strip())

            remaster_regex = constants.tag_parse_patterns["remaster"]
            remaster_match = re.match(remaster_regex, title)
            if remaster_match:
                new_version.append(remaster_match.groups()[1].strip())

            remaster2_regex = constants.tag_parse_patterns["remaster2"]
            remaster2_match = re.match(remaster2_regex, title)
            if remaster2_match:
                new_version.append(remaster2_match.groups()[1].strip())

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
