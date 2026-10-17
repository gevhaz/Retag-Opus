"""Module for parsing text in the existing metadata keys.

This module is for parsing text in the existing metadata keys, rather
that the YouTube description.
"""
import re
from typing import Dict, Final, List

from retag_opus import constants, utils

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
        original_titles = self.original_tags.get("title", [])

        original_artists = self.original_tags.get("artist", [])
        if len(original_artists) == 1:
            original_artists = utils.split_tag(original_artists[0])
        featured_artists = []

        original_versions = self.original_tags.get("version", [])
        versions_from_titles = []

        original_genres = self.original_tags.get("genre", [])
        genres_from_titles = []

        version_pattern_names = [
            "live",
            "albumversion",
            "remix_in_parentheses",
            "remix_after_dash",
            "remaster_in_brackets",
            "remaster_after_dash",
        ]
        instrumental_pattern_names = ["instrumental_in_parentheses", "instrumental_in_square_brackets"]

        for title in original_titles:
            featuring_regex = constants.title_parse_patterns["featuring"]
            featuring_match = re.match(featuring_regex, title)
            if featuring_match:
                featured_artists_text = featuring_match.group(2).strip()
                featured_artists += utils.split_tag(featured_artists_text)

            for pattern_name in version_pattern_names:
                version_regex = constants.title_parse_patterns[pattern_name]
                version_match = re.match(version_regex, title)
                if version_match:
                    versions_from_titles.append(version_match.group(2).strip())

            for pattern_name in instrumental_pattern_names:
                instrumental_regex = constants.title_parse_patterns[pattern_name]
                if re.match(instrumental_regex, title):
                    genres_from_titles.append("Instrumental")

        if set(versions_from_titles) != set(original_versions) and len(versions_from_titles) > 0:
            self.tags["version"] = utils.remove_duplicates(original_versions + versions_from_titles)

        if set(featured_artists) != set(original_artists) and len(featured_artists) > 0:
            self.tags["artist"] = utils.remove_duplicates(original_artists + featured_artists)

        if set(genres_from_titles) != set(original_genres) and len(genres_from_titles) > 0:
            self.tags["genre"] = utils.remove_duplicates(original_genres + genres_from_titles)

        if len(original_titles) > 0:
            pruned_title = utils.prune_title(original_titles[0])
            if original_titles[0] != pruned_title:
                self.tags["title"] = [pruned_title]

    def split_select_original_tags(self) -> None:
        """Split certain original tags on predefined separators.

        Split the genre and artist tag into a list if they contains
        pre-defined separators. New tags are only set if there is
        anything that differs from the old tags.
        """
        tags_to_split = ["genre", "artist"]

        for tag in tags_to_split:
            original_values = self.original_tags.get(tag)
            if original_values is not None and len(original_values) == 1:
                split_values = utils.split_tag(original_values[0])
                if split_values != original_values:
                    self.tags[tag] = split_values
