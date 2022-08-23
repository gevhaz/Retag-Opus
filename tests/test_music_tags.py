"""Tests for music_tags.py."""
import unittest

import pytest
from colorama import Fore

from retag_opus.music_tags import MusicTags

Tags = dict[str, list[str]]


class TestUtils(unittest.TestCase):
    """Test the MusicTags class."""

    @pytest.fixture(autouse=True)
    def capsys(self, capsys) -> None:  # type: ignore
        """Fixture for capturing system output."""
        self.capsys = capsys  # type: ignore

    def test_print_metadata_key(self) -> None:
        """Test printing of a single metadata key."""
        tags: Tags = {"artist": ["artist 1", "artist 2"], "title": ["title 1", "title 2"]}
        MusicTags.print_metadata_key("Artist", "artist", Fore.RED, tags)
        captured = self.capsys.readouterr()  # type: ignore
        self.assertEqual(f"  Artist: {Fore.RED}artist 1 | artist 2{Fore.RESET}\n", captured.out)

    def test_print_metadata(self) -> None:
        """Test printing of metadata."""
        tags: Tags = {"artist": ["artist 1", "artist 2"], "title": ["title 1", "title 2"]}
        MusicTags.print_metadata(tags, Fore.RED)
        captured = self.capsys.readouterr()  # type: ignore
        expected = (
            f"  Title: {Fore.RED}title 1 | title 2{Fore.RESET}\n"
            f"  Album: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  Album Artist: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  Artist(s): {Fore.RED}artist 1 | artist 2{Fore.RESET}\n"
            f"  Date: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  Genre: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  Version: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  Performer: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  Organization: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  Copyright: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  Composer: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  Conductor: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  Arranger: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  Author: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  Producer: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  Publisher: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  Lyricist: {Fore.BLACK}Not found{Fore.RESET}\n\n"
        )

        self.assertEqual(expected, captured.out)
