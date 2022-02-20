import re

from pathlib import Path
from typing import List

import constants


class Utils:

    @staticmethod
    def remove_duplicates(duplicates: list) -> list:
        return list(dict.fromkeys(duplicates))

    @staticmethod
    def prune_title(original_title: str) -> str:
        pruned = original_title
        for pattern in constants.tag_parse_patterns.values():
            pruned = re.sub(pattern, r"\1 \3", pruned)
        return pruned.strip()

    @staticmethod
    def split_tag(input: str) -> List[str]:
        return re.split(", | and | & |; ", input)

    @staticmethod
    def file_path_to_song_data(file_path: Path) -> str:
        file_name = str(file_path)
        basename = re.match(".*/(.*)", file_name)
        if basename:
            match = basename.groups()[0]
            file_name = match
            name_playlist = re.match("<(.*)> - <(.*)> - <(.*)> - <(.*)>.opus", file_name)
            name_single = re.match("<(.*)> - <(.*)>.opus", file_name)
            if name_playlist:
                file_name = name_playlist.groups()[1] + " - " + name_playlist.groups()[2]
            elif name_single:
                file_name = name_single.groups()[0] + " - " + name_single.groups()[1]

        return file_name
