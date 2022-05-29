import re
import sys
from pathlib import Path
from typing import List

from colorama import Fore
from simple_term_menu import TerminalMenu

from retag_opus import constants


class Utils:
    @staticmethod
    def remove_duplicates(duplicates: list[str]) -> list[str]:
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

    @staticmethod
    def select_single_tag(candidates: list[str]) -> list[str]:
        """
        Let's the user select one out of the candidate tags and returns a list with that as the only item. The user can
        also choose to skip with q, escape, or choosing the --No change-- item.

        :param candidates: The list of tags to choose between.

        :return: A list with the selected candidate or an empty list if none is selected.
        """
        candidates.append("--No change--")
        choose_one_tag_menu = TerminalMenu(candidates, title="Choose one tag to use")
        choice = choose_one_tag_menu.show()
        if choice is None:
            print(Fore.YELLOW + "No tag selected")
        elif isinstance(choice, int) and choice != len(candidates) - 1:
            print(Fore.BLUE + f"Using {candidates[choice]} as tag for this song")
            return [candidates[choice]]
        return []

    @staticmethod
    def exit_now() -> None:
        sys.exit(0)
