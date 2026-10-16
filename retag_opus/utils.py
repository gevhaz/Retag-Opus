"""Module with helper functions for the rest of the app."""
import re
import sys
import unicodedata
from pathlib import Path
from typing import List

from simple_term_menu import TerminalMenu

from retag_opus import constants, messages


class Utils:
    """Class containing static utility functions."""

    @staticmethod
    def remove_duplicates(duplicates: list[str]) -> list[str]:
        """Remove duplicate elemets from given list."""
        return list(dict.fromkeys(duplicates))

    @staticmethod
    def prune_title(original_title: str) -> str:
        """Clean up title tag value.

        Remove things such as live version specification and featured
        artist information from the title of a song, and remove leading
        and trailing whitespace.
        """
        pruned = original_title
        for pattern in constants.tag_parse_patterns.values():
            pruned = re.sub(pattern, r"\1 \3", pruned)
        return pruned.strip()

    @staticmethod
    def split_tag(input: str) -> List[str]:
        """Split the provided tag by pre-defined delimeters."""
        split_tags = re.split(", | and | & |; ", input)
        split_pruned_tags = [t.strip() for t in split_tags]
        return split_pruned_tags

    @staticmethod
    def split_manual_value(tag_name: str, value: str) -> list[str]:
        """Split a manually entered value into the values of a tag.

        The sequence ' | ' separates values in all tags, like when tags
        are printed. Genres can also be separated by commas and
        semicolons, since genres, unlike e.g. artists and titles, don't
        contain them.

        :param tag_name: The tag the value is entered for.
        :param value: The value entered by the user.

        :return: The values of the tag.
        """
        if tag_name == "genre":
            values = re.split(r"\s*[,;|]\s*", value)
        else:
            values = value.split(" | ")
        return [v.strip() for v in values if v.strip()]

    @staticmethod
    def file_path_to_song_data(file_path: Path) -> str:
        """Convert file name to readable string.

        Produce a string with song title and artist on a readable format
        from the name of the file being worked with.
        """
        text_to_print = str(file_path)
        basename_match = re.match(r"(.+/)*(.*).opus", text_to_print)
        if basename_match:
            basename = basename_match.groups()[1]
            text_to_print = basename
            playlist_match = re.match(r"<(.*)> - <(.*?)(?: - Topic)*> - <(.*)> - <(.*)>", text_to_print)
            artist_title_match = re.match("<(.*?)(?: - Topic)*> - <(.*)>", text_to_print)
            title_only_match = re.match("<(.*)>", text_to_print)
            if playlist_match:
                text_to_print = playlist_match.groups()[1] + " - " + playlist_match.groups()[2]
            elif artist_title_match:
                text_to_print = artist_title_match.groups()[0] + " - " + artist_title_match.groups()[1]
            elif title_only_match:
                text_to_print = title_only_match.groups()[0]
        return text_to_print

    @staticmethod
    def select_single_tag(candidates: list[str]) -> list[str]:
        """Select a single value to keep for a tag from a menu.

        Let's the user select one out of the candidate tags and returns
        a list with that as the only item. The user can also choose to
        skip with q, escape, or choosing the --No change-- item.

        :param candidates: The list of tags to choose between.

        :return: A list with the selected candidate or an empty list if
        none is selected.
        """
        candidates.append("--No change--")
        choose_one_tag_menu = TerminalMenu(candidates, title="Choose one tag to use")
        choice = choose_one_tag_menu.show()
        if choice is None:
            messages.warning("No tag selected")
        elif isinstance(choice, int) and choice != len(candidates) - 1:
            messages.info(f"Using {candidates[choice]} as tag for this song")
            return [candidates[choice]]
        return []

    @staticmethod
    def exit_now() -> None:
        """Immediately exit the program."""
        sys.exit(0)

    @staticmethod
    def is_equal_when_stripped(values_1: list[str], values_2: list[str]) -> bool:
        """Compare lists disregarding whitespace.

        Check if content of lists of strings are the same after strings
        have been stripped.
        """
        cleaned_values_1 = [v.strip() for v in values_1]
        cleaned_values_2 = [v.strip() for v in values_2]
        return sorted(cleaned_values_1) == sorted(cleaned_values_2)

    @staticmethod
    def normalize(text: str) -> str:
        """Make text comparable regardless of typography and case.

        MusicBrainz uses typographic apostrophes, quotes, and dashes,
        while YouTube and existing tags often don't.
        """
        text = unicodedata.normalize("NFKC", text)
        text = re.sub("[‘’‛´`]", "'", text)
        text = re.sub("[“”‟]", '"', text)
        text = re.sub("[‐-―]", "-", text)
        return " ".join(text.casefold().split())

    @staticmethod
    def is_equal_when_normalized(values_1: list[str], values_2: list[str]) -> bool:
        """Compare lists disregarding typography, case, and order.

        Order is disregarded since tags with several values, like
        artists, may list them in different orders in different sources,
        just like in is_equal_when_stripped.
        """
        return sorted(map(Utils.normalize, values_1)) == sorted(map(Utils.normalize, values_2))
