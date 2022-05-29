import re
from typing import Dict, List

from retag_opus import constants
from retag_opus.utils import Utils

INTERPUNCT = "\u00b7"


class TagsParser:
    def __init__(self, tags: Dict[str, List[str]]):
        self.tags: Dict[str, List[str]] = {}
        self.original_tags = tags

    def standard_pattern(self, field_name: str, regex: str, line: str) -> None:
        pattern = re.compile(regex)
        pattern_match = re.match(pattern, line)
        if pattern_match:
            field_value = pattern_match.groups()[len(pattern_match.groups()) - 1]
            field_value = field_value.strip()
            if self.tags.get(field_name):
                self.tags[field_name].append(field_value)
                self.tags[field_name] = Utils().remove_duplicates(self.tags[field_name])
            else:
                self.tags[field_name] = [field_value]

    def parse_tags(self) -> None:
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

            instrumental_regex = constants.tag_parse_patterns["instrumental"]
            instrumental_match = re.match(instrumental_regex, title)
            if instrumental_match:
                new_genre.append("Instrumental")

            remix_regex = constants.tag_parse_patterns["remix"]
            remix_match = re.match(remix_regex, title)
            if remix_match:
                new_version.append(remix_match.groups()[1].strip())

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

    def process_existing_tags(self) -> None:
        """
        Analyze existing tags for information that can be moved into new tags.
        """

        # If the date is just the upload date, discard it
        if self.original_tags.get("date") and re.match(r"\d\d\d\d\d\d\d\d", self.original_tags["date"][0]):
            self.original_tags.pop("date", None)

        tags_to_split = ["genre", "artist"]

        for tag in tags_to_split:
            tags_tag = self.original_tags.get(tag)
            if tags_tag is not None and not len(tags_tag) > 1:
                new_tag = Utils().split_tag(tags_tag[0])
                if new_tag != tags_tag:
                    self.tags[tag] = new_tag

    def get_tags(self) -> Dict[str, List[str]]:
        return self.tags
