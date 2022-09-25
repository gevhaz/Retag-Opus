"""Tests for music_tags.py."""
import sys
import unittest

import pytest
from colorama import Fore
from mock import patch
from mock.mock import MagicMock

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

    def test_print_metadata_with_performers(self) -> None:
        """Test printing of metadata where there are performer tags."""
        tags: Tags = {"artist": ["artist 1", "artist 2"], "performer:vocals": ["bassist 1"]}
        MusicTags.print_metadata(tags, Fore.RED)
        captured = self.capsys.readouterr()  # type: ignore
        expected = (
            "  Performers:\n"
            f"  - Vocals: {Fore.RED}bassist 1{Fore.RESET}\n"
            f"  Title: {Fore.BLACK}Not found{Fore.RESET}\n"
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

    def test_print_metadata_with_unknown_performer_tag(self) -> None:
        """Test printing of metadata with unknown performer tag."""
        tags: Tags = {"artist": ["artist 1", "artist 2"], "performer:unknown": ["person 1"]}
        MusicTags.print_metadata(tags, Fore.RED)
        captured = self.capsys.readouterr()  # type: ignore
        expected = (
            f"  Title: {Fore.BLACK}Not found{Fore.RESET}\n"
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

    def test_get_tag_data_one_source(self) -> None:
        """Test getting tags from one source."""
        tags = MusicTags()
        tags.original = {"artist": ["artist 1"]}
        actual = tags.get_tag_data("artist")
        expected = [f"{Fore.CYAN}artist 1{Fore.RESET}"]
        self.assertListEqual(expected, actual)

    def test_get_tag_data_two_sources(self) -> None:
        """Test getting tags from two source."""
        tags = MusicTags()
        tags.original = {"artist": ["artist 1"]}
        tags.youtube = {"artist": ["artist 2"]}
        actual = tags.get_tag_data("artist")
        expected = [f"{Fore.CYAN}artist 1{Fore.RESET}", f"{Fore.MAGENTA}artist 2{Fore.RESET}"]
        self.assertListEqual(expected, actual)

    def test_get_tag_data_two_overlapping_sources(self) -> None:
        """Test get tags from two sources where a value is in both."""
        tags = MusicTags()
        tags.original = {"artist": ["artist 1"]}
        tags.youtube = {"artist": ["artist 1", "artist 2"]}
        actual = tags.get_tag_data("artist")
        expected = [f"{Fore.CYAN}artist 1{Fore.RESET}", f"{Fore.MAGENTA}artist 1 | artist 2{Fore.RESET}"]
        self.assertListEqual(expected, actual)

    def test_get_tag_data_no_values(self) -> None:
        """Test getting tags from one source."""
        tags = MusicTags()
        actual = tags.get_tag_data("artist")
        expected: list[str] = []
        self.assertListEqual(expected, actual)

    def test_get_tag_data_all_sources(self) -> None:
        """Test getting tags from two source."""
        tags = MusicTags()
        tags.original = {"artist": ["artist 1"]}
        tags.youtube = {"artist": ["artist 2"]}
        tags.fromtags = {"artist": ["artist 3"]}
        tags.fromdesc = {"artist": ["artist 4"]}
        actual = tags.get_tag_data("artist")
        expected = [
            f"{Fore.CYAN}artist 1{Fore.RESET}",
            f"{Fore.MAGENTA}artist 2{Fore.RESET}",
            f"{Fore.YELLOW}artist 3{Fore.RESET}",
            f"{Fore.GREEN}artist 4{Fore.RESET}",
        ]
        self.assertListEqual(expected, actual)

    def test_print_all(self) -> None:
        """Test printing the combined metadata of all sources."""
        tags = MusicTags()
        tags.original = {"artist": ["artist 1"]}
        tags.youtube = {"artist": ["artist 2"]}
        tags.fromtags = {"artist": ["artist 3"]}
        tags.fromdesc = {"artist": ["artist 4"]}
        tags.print_all()
        captured = self.capsys.readouterr()  # type: ignore
        expected = (
            f"Title: {Fore.BLACK}Not set{Fore.RESET}\n"
            f"Album: {Fore.BLACK}Not set{Fore.RESET}\n"
            f"Album Artist: {Fore.BLACK}Not set{Fore.RESET}\n"
            "Artist(s): "
            f"{Fore.CYAN}artist 1{Fore.RESET} | "
            f"{Fore.MAGENTA}artist 2{Fore.RESET} | "
            f"{Fore.YELLOW}artist 3{Fore.RESET} | "
            f"{Fore.GREEN}artist 4{Fore.RESET}\n"
            f"Date: {Fore.BLACK}Not set{Fore.RESET}\n"
            f"Genre: {Fore.BLACK}Not set{Fore.RESET}\n"
            f"Version: {Fore.BLACK}Not set{Fore.RESET}\n"
            f"Performer: {Fore.BLACK}Not set{Fore.RESET}\n"
            f"Organization: {Fore.BLACK}Not set{Fore.RESET}\n"
            f"Copyright: {Fore.BLACK}Not set{Fore.RESET}\n"
            f"Composer: {Fore.BLACK}Not set{Fore.RESET}\n"
            f"Conductor: {Fore.BLACK}Not set{Fore.RESET}\n"
            f"Arranger: {Fore.BLACK}Not set{Fore.RESET}\n"
            f"Author: {Fore.BLACK}Not set{Fore.RESET}\n"
            f"Producer: {Fore.BLACK}Not set{Fore.RESET}\n"
            f"Publisher: {Fore.BLACK}Not set{Fore.RESET}\n"
            f"Lyricist: {Fore.BLACK}Not set{Fore.RESET}\n\n"
        )
        self.assertEqual(expected, captured.out)

    def test_print_all_with_performers(self) -> None:
        """Test printing combined data when there are performer tags."""
        tags = MusicTags()
        tags.original = {"artist": ["artist 1"]}
        tags.youtube = {"artist": ["artist 2"]}
        tags.fromtags = {"artist": ["artist 3"]}
        tags.fromdesc = {"performer:vocals": ["artist 4"]}
        tags.print_all()
        captured = self.capsys.readouterr()  # type: ignore
        expected = (
            "Performers:\n"
            f"- Vocals: {Fore.GREEN}artist 4{Fore.RESET}\n"
            f"Title: {Fore.BLACK}Not set{Fore.RESET}\n"
            f"Album: {Fore.BLACK}Not set{Fore.RESET}\n"
            f"Album Artist: {Fore.BLACK}Not set{Fore.RESET}\n"
            "Artist(s): "
            f"{Fore.CYAN}artist 1{Fore.RESET} | "
            f"{Fore.MAGENTA}artist 2{Fore.RESET} | "
            f"{Fore.YELLOW}artist 3{Fore.RESET}\n"
            f"Date: {Fore.BLACK}Not set{Fore.RESET}\n"
            f"Genre: {Fore.BLACK}Not set{Fore.RESET}\n"
            f"Version: {Fore.BLACK}Not set{Fore.RESET}\n"
            f"Performer: {Fore.BLACK}Not set{Fore.RESET}\n"
            f"Organization: {Fore.BLACK}Not set{Fore.RESET}\n"
            f"Copyright: {Fore.BLACK}Not set{Fore.RESET}\n"
            f"Composer: {Fore.BLACK}Not set{Fore.RESET}\n"
            f"Conductor: {Fore.BLACK}Not set{Fore.RESET}\n"
            f"Arranger: {Fore.BLACK}Not set{Fore.RESET}\n"
            f"Author: {Fore.BLACK}Not set{Fore.RESET}\n"
            f"Producer: {Fore.BLACK}Not set{Fore.RESET}\n"
            f"Publisher: {Fore.BLACK}Not set{Fore.RESET}\n"
            f"Lyricist: {Fore.BLACK}Not set{Fore.RESET}\n\n"
        )
        self.assertEqual(expected, captured.out)

    def test_print_all_with_no_data(self) -> None:
        """Test printing the combined metadata of all sources."""
        tags = MusicTags()
        tags.print_all()
        captured = self.capsys.readouterr()  # type: ignore
        expected = f"{Fore.RED}There's no data to be printed{Fore.RESET}\n"
        self.assertEqual(expected, captured.out)

    def test_print_youtube(self) -> None:
        """Test printing data from youtube tags."""
        tags = MusicTags()
        tags.original = {"artist": ["artist 1"]}
        tags.youtube = {"artist": ["artist 2"], "performer:vocals": ["artist 5"]}
        tags.fromtags = {"artist": ["artist 3"]}
        tags.fromdesc = {"performer:vocals": ["artist 4"]}
        tags.print_youtube()
        captured = self.capsys.readouterr()  # type: ignore
        expected = (
            "  Performers:\n"
            f"  - Vocals: {Fore.MAGENTA}artist 5{Fore.RESET}\n"
            f"  Title: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  Album: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  Album Artist: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  Artist(s): {Fore.MAGENTA}artist 2{Fore.RESET}\n"
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

    def test_print_youtube_no_data(self) -> None:
        """Test printing data from youtube tags when there are none."""
        tags = MusicTags()
        tags.original = {"artist": ["artist 1"]}
        tags.fromtags = {"artist": ["artist 3"]}
        tags.fromdesc = {"performer:vocals": ["artist 4"]}
        tags.print_youtube()
        captured = self.capsys.readouterr()  # type: ignore
        expected = f"{Fore.RED}No new data parsed from description{Fore.RESET}\n"
        self.assertEqual(expected, captured.out)

    def test_print_original_tags(self) -> None:
        """Test printing original tags, including performer tags."""
        tags = MusicTags()
        tags.original = {"artist": ["artist 2"], "performer:vocals": ["artist 5"]}
        tags.youtube = {"artist": ["artist 1"]}
        tags.fromtags = {"artist": ["artist 3"]}
        tags.fromdesc = {"performer:vocals": ["artist 4"]}
        tags.print_original()
        captured = self.capsys.readouterr()  # type: ignore
        expected = (
            "  Performers:\n"
            f"  - Vocals: {Fore.CYAN}artist 5{Fore.RESET}\n"
            f"  Title: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  Album: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  Album Artist: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  Artist(s): {Fore.CYAN}artist 2{Fore.RESET}\n"
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

    def test_print_original_tags_no_data(self) -> None:
        """Test printing original tags when there are none."""
        tags = MusicTags()
        tags.youtube = {"artist": ["artist 1"]}
        tags.fromtags = {"artist": ["artist 3"]}
        tags.fromdesc = {"performer:vocals": ["artist 4"]}
        tags.print_original()
        captured = self.capsys.readouterr()  # type: ignore
        expected = f"{Fore.RED}There were no pre-existing tags for this file{Fore.RESET}\n"
        self.assertEqual(expected, captured.out)

    def test_print_from_tags(self) -> None:
        """Test printing tags parsed from original tags."""
        tags = MusicTags()
        tags.original = {"artist": ["artist 3"]}
        tags.youtube = {"artist": ["artist 1"]}
        tags.fromtags = {"artist": ["artist 2"], "performer:vocals": ["artist 5"]}
        tags.fromdesc = {"performer:vocals": ["artist 4"]}
        tags.print_from_tags()
        captured = self.capsys.readouterr()  # type: ignore
        expected = (
            "  Performers:\n"
            f"  - Vocals: {Fore.YELLOW}artist 5{Fore.RESET}\n"
            f"  Title: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  Album: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  Album Artist: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  Artist(s): {Fore.YELLOW}artist 2{Fore.RESET}\n"
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

    def test_print_from_tags_no_data(self) -> None:
        """Test print tags parsed from original tags when none exist."""
        tags = MusicTags()
        tags.original = {"artist": ["artist 3"]}
        tags.youtube = {"artist": ["artist 1"]}
        tags.fromdesc = {"performer:vocals": ["artist 4"]}
        tags.print_from_tags()
        captured = self.capsys.readouterr()  # type: ignore
        expected = f"{Fore.RED}No new data parsed from tags{Fore.RESET}\n"
        self.assertEqual(expected, captured.out)

    def test_print_from_descripton(self) -> None:
        """Test print tags parsed from description, with performers."""
        tags = MusicTags()
        tags.original = {"artist": ["artist 3"]}
        tags.youtube = {"artist": ["artist 1"]}
        tags.fromtags = {"performer:vocals": ["artist 4"]}
        tags.fromdesc = {"artist": ["artist 2"], "performer:vocals": ["artist 5"]}
        tags.print_from_desc()
        captured = self.capsys.readouterr()  # type: ignore
        expected = (
            "  Performers:\n"
            f"  - Vocals: {Fore.GREEN}artist 5{Fore.RESET}\n"
            f"  Title: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  Album: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  Album Artist: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  Artist(s): {Fore.GREEN}artist 2{Fore.RESET}\n"
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

    def test_print_from_descripton_from_tags(self) -> None:
        """Test print tags parsed from description, with no data."""
        tags = MusicTags()
        tags.original = {"artist": ["artist 3"]}
        tags.youtube = {"artist": ["artist 1"]}
        tags.fromtags = {"performer:vocals": ["artist 4"]}
        tags.print_from_desc()
        captured = self.capsys.readouterr()  # type: ignore
        expected = f"{Fore.RED}No new data parsed from tags parsed from description{Fore.RESET}\n"
        self.assertEqual(expected, captured.out)

    def test_print_resolved(self) -> None:
        """Test that resolved tags can be printed."""
        tags = MusicTags()
        tags.original = {"artist": ["artist 1"], "title": ["title 1"]}
        tags.resolved = {"artist": ["artist 1"], "title": ["title 2"], "producer": ["[Removed]"]}
        tags.print_resolved(print_all=False)
        captured = self.capsys.readouterr()  # type: ignore
        expected = (
            f"  Title: {Fore.GREEN}title 2{Fore.RESET}\n"
            f"  Album: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  Album Artist: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  Artist(s): {Fore.CYAN}artist 1{Fore.RESET}\n"
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
            f"  Producer: {Fore.RED}[Removed]{Fore.RESET}\n"
            f"  Publisher: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  Lyricist: {Fore.BLACK}Not found{Fore.RESET}\n\n"
        )
        self.assertEqual(expected, captured.out)

    def test_print_resolved_with_performers(self) -> None:
        """Test that resolved tags print, including performers."""
        tags = MusicTags()
        tags.original = {
            "performer:vocals": ["artist 1"],
            "performer:violin": ["artist 1"],
        }
        tags.resolved = {
            "performer:vocals": ["artist 1"],
            "performer:violin": ["artist 2"],
            "performer:keyboard": ["[Removed]"],
        }
        tags.print_resolved(print_all=False)
        captured = self.capsys.readouterr()  # type: ignore
        expected = (
            "  Performers:\n"
            f"  - Vocals: {Fore.CYAN}artist 1{Fore.RESET}\n"
            f"  - Background Vocals: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  - Drums: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  - Percussion: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  - Keyboard: {Fore.RED}[Removed]{Fore.RESET}\n"
            f"  - Piano: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  - Synthesizer: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  - Guitar: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  - Electric guitar: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  - Bass guitar: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  - Acoustic guitar: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  - Ukulele: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  - Violin: {Fore.GREEN}artist 2{Fore.RESET}\n"
            f"  - Double bass: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  - Cello: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  - Programming: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  - Saxophone: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  - Flute: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  Title: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  Album: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  Album Artist: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  Artist(s): {Fore.BLACK}Not found{Fore.RESET}\n"
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
        sys.stdout.write(captured.out)
        self.assertEqual(expected, captured.out)

    def test_print_all_resolved_with_performers(self) -> None:
        """Test that resolved tags print, including performers.

        Test printing of resolved tags with the argument to print all
        set to true.
        """
        tags = MusicTags()
        tags.original = {
            "performer:vocals": ["artist 1"],
            "performer:violin": ["artist 1"],
            "performer:guitar": ["artist 3"],
        }
        tags.youtube = {
            "performer:guitar": ["artist 4"],
        }
        tags.resolved = {
            "performer:vocals": ["artist 1"],
            "performer:violin": ["artist 2"],
            "performer:keyboard": ["[Removed]"],
        }
        tags.print_resolved(print_all=True)
        captured = self.capsys.readouterr()  # type: ignore
        expected = (
            "  Performers:\n"
            f"  - Vocals: {Fore.CYAN}artist 1{Fore.RESET}\n"
            f"  - Background Vocals: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  - Drums: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  - Percussion: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  - Keyboard: {Fore.RED}[Removed]{Fore.RESET}\n"
            f"  - Piano: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  - Synthesizer: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  - Guitar: {Fore.CYAN}artist 3{Fore.RESET} | {Fore.MAGENTA}artist 4{Fore.RESET}\n"
            f"  - Electric guitar: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  - Bass guitar: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  - Acoustic guitar: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  - Ukulele: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  - Violin: {Fore.GREEN}artist 2{Fore.RESET}\n"
            f"  - Double bass: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  - Cello: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  - Programming: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  - Saxophone: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  - Flute: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  Title: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  Album: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  Album Artist: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  Artist(s): {Fore.BLACK}Not found{Fore.RESET}\n"
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

    def test_print_resolved_with_performers_multiple_sources(self) -> None:
        """Test that resolved tags print, including performers.

        Test printing of resolved tags with the argument to print all
        set to false when there are several sources with relevant tags.
        """
        tags = MusicTags()
        tags.original = {
            "performer:vocals": ["artist 1"],
            "performer:violin": ["artist 1"],
            "performer:guitar": ["artist 3"],
        }
        tags.youtube = {
            "performer:guitar": ["artist 4"],
        }
        tags.resolved = {
            "performer:vocals": ["artist 1"],
            "performer:violin": ["artist 2"],
            "performer:keyboard": ["[Removed]"],
        }
        tags.print_resolved(print_all=False)
        captured = self.capsys.readouterr()  # type: ignore
        expected = (
            "  Performers:\n"
            f"  - Vocals: {Fore.CYAN}artist 1{Fore.RESET}\n"
            f"  - Background Vocals: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  - Drums: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  - Percussion: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  - Keyboard: {Fore.RED}[Removed]{Fore.RESET}\n"
            f"  - Piano: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  - Synthesizer: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  - Guitar: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  - Electric guitar: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  - Bass guitar: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  - Acoustic guitar: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  - Ukulele: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  - Violin: {Fore.GREEN}artist 2{Fore.RESET}\n"
            f"  - Double bass: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  - Cello: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  - Programming: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  - Saxophone: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  - Flute: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  Title: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  Album: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  Album Artist: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  Artist(s): {Fore.BLACK}Not found{Fore.RESET}\n"
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

    def test_print_all_resolved_without_performers(self) -> None:
        """Test that resolved tags print, not including performers.

        Test printing of resolved tags with the argument to print all
        set to true.
        """
        tags = MusicTags()
        tags.original = {
            "artist": ["artist 1", "artist 2"],
            "title": ["title 1"],
            "producer": ["person 1"],
            "arranger": ["artist 1"],
        }
        tags.youtube = {
            "arranger": ["artist 2"],
        }
        tags.resolved = {
            "artist": ["artist 1", "artist 2"],
            "title": ["title 2"],
            "producer": ["[Removed]"],
        }
        tags.print_resolved(print_all=True)
        captured = self.capsys.readouterr()  # type: ignore
        expected = (
            f"  Title: {Fore.GREEN}title 2{Fore.RESET}\n"
            f"  Album: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  Album Artist: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  Artist(s): {Fore.CYAN}artist 1 | artist 2{Fore.RESET}\n"
            f"  Date: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  Genre: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  Version: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  Performer: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  Organization: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  Copyright: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  Composer: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  Conductor: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  Arranger: {Fore.CYAN}artist 1{Fore.RESET} | {Fore.MAGENTA}artist 2{Fore.RESET}\n"
            f"  Author: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  Producer: {Fore.RED}[Removed]{Fore.RESET}\n"
            f"  Publisher: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  Lyricist: {Fore.BLACK}Not found{Fore.RESET}\n\n"
        )
        self.assertEqual(expected, captured.out)

    def test_print_resolved_without_performers(self) -> None:
        """Test that resolved tags print, not including performers.

        Test printing of resolved tags with the argument to print all
        set to false.
        """
        tags = MusicTags()
        tags.original = {
            "artist": ["artist 1", "artist 2"],
            "title": ["title 1"],
            "producer": ["person 1"],
            "arranger": ["artist 1"],
        }
        tags.youtube = {
            "arranger": ["artist 2"],
        }
        tags.resolved = {
            "artist": ["artist 1", "artist 2"],
            "title": ["title 2"],
            "producer": ["[Removed]"],
        }
        tags.print_resolved(print_all=False)
        captured = self.capsys.readouterr()  # type: ignore
        expected = (
            f"  Title: {Fore.GREEN}title 2{Fore.RESET}\n"
            f"  Album: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  Album Artist: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  Artist(s): {Fore.CYAN}artist 1 | artist 2{Fore.RESET}\n"
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
            f"  Producer: {Fore.RED}[Removed]{Fore.RESET}\n"
            f"  Publisher: {Fore.BLACK}Not found{Fore.RESET}\n"
            f"  Lyricist: {Fore.BLACK}Not found{Fore.RESET}\n\n"
        )
        sys.stdout.write(captured.out)
        self.assertEqual(expected, captured.out)

    def test_switch_album_to_disc_subtitle(self) -> None:
        """Test the album and discsubtitle switching function.

        The function is used when the user want to set a specific album
        for all songs being retagged, so that they are in a compilation
        of songs, while preserving data about which album the song was
        originally on in the discsubtitle tag.
        """
        tags = MusicTags()
        tags.original = {"album": ["album 1"]}
        tags.switch_album_to_disc_subtitle("album 2")
        actual_album = tags.original.get("album")
        actual_discsubtitle = tags.original.get("discsubtitle")
        self.assertIsNone(actual_album)
        assert actual_discsubtitle is not None
        self.assertListEqual(["album 1"], actual_discsubtitle)

    def test_switch_album_to_disc_subtitle_no_album(self) -> None:
        """Test that the function works when no album tag."""
        tags = MusicTags()
        tags.switch_album_to_disc_subtitle("album 2")
        self.assertNotIn("album", tags.original)
        self.assertNotIn("discsubtitle", tags.original)

    def test_switch_album_to_disc_subtitle_identical_tags(self) -> None:
        """Test that discsubtitle tag is not added when duplicated."""
        tags = MusicTags()
        tags.original = {"album": ["album 1"]}
        tags.switch_album_to_disc_subtitle("album 1")
        self.assertNotIn("album", tags.original)
        self.assertNotIn("discsubtitle", tags.original)

    def test_discard_upload_date_bad_date(self) -> None:
        """Test that bad upload dates are removed."""
        tags = MusicTags()
        tags.original = {"date": ["20220202"]}
        tags.discard_upload_date()
        self.assertNotIn("date", tags.original)

    def test_discard_upload_date_good_date(self) -> None:
        """Test that good upload dates are not removed."""
        tags = MusicTags()
        tags.original = {"date": ["2022-02-02"]}
        tags.discard_upload_date()
        actual_date = tags.original.get("date")
        assert actual_date is not None
        self.assertListEqual(["2022-02-02"], actual_date)

    def test_prune_resolved_tags(self) -> None:
        """Test that useless tags are removed."""
        tags = MusicTags()
        tags.resolved = {
            "language": ["eng"],
            "compatible_brands": ["a brand"],
            "minor_version": ["The minor version"],
            "major_brand": ["brand"],
            "vendor_id": ["id of the vendor"],
            "date": ["2022-02-02"],
        }
        tags.prune_resolved_tags()
        self.assertEqual(6, len(tags.resolved))
        self.assertEqual(["2022-02-02"], tags.resolved.get("date"))
        self.assertEqual(["[Removed]"], tags.resolved.get("language"))
        self.assertEqual(["[Removed]"], tags.resolved.get("compatible_brands"))
        self.assertEqual(["[Removed]"], tags.resolved.get("minor_version"))
        self.assertEqual(["[Removed]"], tags.resolved.get("major_brand"))
        self.assertEqual(["[Removed]"], tags.resolved.get("vendor_id"))

    def test_add_source_tag(self) -> None:
        """Test that the "youtube-dl" source tag is added."""
        tags = MusicTags()
        tags.resolved = {"date": ["2022-02-02"]}
        tags.add_source_tag()
        self.assertEqual(2, len(tags.resolved))
        self.assertEqual(["youtube-dl"], tags.resolved.get("comment"))

    def test_preserve_original_comment_when_adding_source(self) -> None:
        """Test that source tag doesn't overwrite."""
        tags = MusicTags()
        tags.original = {"comment": ["test"]}
        tags.resolved = {"date": ["2022-02-02"]}
        tags.add_source_tag()
        self.assertEqual(2, len(tags.resolved))
        self.assertEqual(["test", "youtube-dl"], tags.resolved.get("comment"))

    def test_get_field_only_new(self) -> None:
        """Test getting data from all new sources for a given tag."""
        tags = MusicTags()
        tags.original = {"artist": ["artist 1"]}
        tags.youtube = {"artist": ["artist 2"]}
        tags.fromtags = {"artist": ["artist 3"]}
        tags.fromdesc = {"artist": ["artist 2"]}
        actual_tags = tags.get_field("artist", only_new=True)
        self.assertEqual(2, len(actual_tags))
        self.assertNotIn("artist 1", actual_tags)
        self.assertIn("artist 2", actual_tags)
        self.assertIn("artist 3", actual_tags)

    def test_get_field_include_original(self) -> None:
        """Test getting data from all sources for a given tag."""
        tags = MusicTags()
        tags.original = {"artist": ["artist 1"]}
        tags.youtube = {"artist": ["artist 2"]}
        tags.fromtags = {"artist": ["artist 3"]}
        tags.fromdesc = {"artist": ["artist 2"]}
        actual_tags = tags.get_field("artist", only_new=False)
        self.assertEqual(3, len(actual_tags))
        self.assertIn("artist 1", actual_tags)
        self.assertIn("artist 2", actual_tags)
        self.assertIn("artist 3", actual_tags)

    def test_get_field_that_does_not_exist(self) -> None:
        """Test getting data from all sources for a non-existent tag."""
        tags = MusicTags()
        tags.original = {"artist": ["artist 1"]}
        tags.youtube = {"artist": ["artist 2"]}
        tags.fromtags = {"artist": ["artist 3"]}
        tags.fromdesc = {"artist": ["artist 2"]}
        actual_tags = tags.get_field("title", only_new=False)
        self.assertEqual(0, len(actual_tags))
        self.assertNotIn("artist 1", actual_tags)
        self.assertNotIn("artist 2", actual_tags)
        self.assertNotIn("artist 3", actual_tags)

    def test_check_any_new_data_exists(self) -> None:
        """Test checking for new data."""
        tags = MusicTags()

        # No tags at all
        self.assertFalse(tags.check_any_new_data_exists())

        # Only original tags
        tags.original = {"artist": ["artist 1"]}
        self.assertFalse(tags.check_any_new_data_exists())

        # Other sources have same value for tag as original
        tags.youtube = {"artist": ["artist 1"]}
        tags.fromtags = {"artist": ["artist 1"]}
        tags.fromdesc = {"artist": ["artist 1"]}
        self.assertFalse(tags.check_any_new_data_exists())

        # There actually are new values for the tag
        tags.youtube = {"artist": ["artist 2"]}
        self.assertTrue(tags.check_any_new_data_exists())
        tags.fromtags = {"artist": ["artist 3"]}
        self.assertTrue(tags.check_any_new_data_exists())
        tags.fromdesc = {"artist": ["artist 2"]}
        self.assertTrue(tags.check_any_new_data_exists())

    def test_check_any_new_data_exists_resolved(self) -> None:
        """Check that there are no new values in the resolved tags.

        Tags may be automaticall added to the resolved tags so we need
        to check that set also.
        """
        tags = MusicTags()

        # Only resolved has tags
        tags.resolved = {"artist": ["artist 1"]}
        self.assertTrue(tags.check_any_new_data_exists())

        # Identical tag in resolved
        tags.original = {"artist": ["artist 1"]}
        self.assertFalse(tags.check_any_new_data_exists())

        # New tag in resolved
        tags.resolved = {"artist": ["artist 2"]}
        self.assertTrue(tags.check_any_new_data_exists())

    @patch("retag_opus.utils.TerminalMenu.__init__")
    @patch("retag_opus.utils.TerminalMenu.show")
    def test_delete_tag_item(self, mock_show: MagicMock, mock_menu: MagicMock) -> None:
        """Test deleting one value from a tag list."""
        mock_show.side_effect = [0, 1]  # Where a choice is returned from the menu
        mock_menu.return_value = None  # constructor requires terminal, not availabe in CI.

        tags = MusicTags()
        tags.resolved = {"artist": ["artist 1", "artist 2"]}
        tags.delete_tag_item()
        self.assertEqual(["artist 1"], tags.resolved.get("artist"))

    @patch("retag_opus.utils.TerminalMenu.__init__")
    @patch("retag_opus.utils.TerminalMenu.show")
    def test_delete_tag_item_performer(self, mock_show: MagicMock, mock_menu: MagicMock) -> None:
        """Test deleting one value from a tag list."""
        mock_show.side_effect = [1, 1]  # Where a choice is returned from the menu
        mock_menu.return_value = None  # constructor requires terminal, not availabe in CI.

        tags = MusicTags()
        tags.resolved = {"artist": ["artist 1"], "performer:vocals": ["artist 1", "artist 2"]}
        tags.delete_tag_item()
        self.assertEqual(["artist 1"], tags.resolved.get("performer:vocals"))

    @patch("retag_opus.utils.TerminalMenu.__init__")
    @patch("retag_opus.utils.TerminalMenu.show")
    def test_delete_tag_item_unknown_tag(self, mock_show: MagicMock, mock_menu: MagicMock) -> None:
        """Test deleting one value from a tag list."""
        mock_show.side_effect = [0, 0]  # Where a choice is returned from the menu
        mock_menu.return_value = None  # constructor requires terminal, not availabe in CI.

        tags = MusicTags()
        tags.resolved = {"unknown_key": ["artist 1"]}
        tags.delete_tag_item()
        self.assertEqual(["artist 1"], tags.resolved.get("unknown_key"))

    @patch("retag_opus.utils.TerminalMenu.__init__")
    @patch("retag_opus.utils.TerminalMenu.show")
    def test_delete_tag_item_two_items(self, mock_show: MagicMock, mock_menu: MagicMock) -> None:
        """Test deleting two values from a tag list."""
        mock_show.side_effect = [0, [1, 2]]  # Where a choice is returned from the menu
        mock_menu.return_value = None  # constructor requires terminal, not availabe in CI.

        tags = MusicTags()
        tags.resolved = {"artist": ["artist 1", "artist 2", "artist 3"]}
        tags.delete_tag_item()
        self.assertEqual(["artist 1"], tags.resolved.get("artist"))

    @patch("retag_opus.utils.TerminalMenu.__init__")
    @patch("retag_opus.utils.TerminalMenu.show")
    def test_delete_tag_item_zero_items(self, mock_show: MagicMock, mock_menu: MagicMock) -> None:
        """Test deleting zero values from a tag list."""
        mock_show.side_effect = [0, None]  # Where a choice is returned from the menu
        mock_menu.return_value = None  # constructor requires terminal, not availabe in CI.

        tags = MusicTags()
        tags.resolved = {"artist": ["artist 1", "artist 2"]}
        tags.delete_tag_item()
        self.assertEqual(["artist 1", "artist 2"], tags.resolved.get("artist"))
        captured = self.capsys.readouterr()  # type: ignore
        self.assertEqual(f"{Fore.YELLOW}Returning without removing anything{Fore.RESET}\n", captured.out)

    @patch("retag_opus.utils.TerminalMenu.__init__")
    @patch("retag_opus.utils.TerminalMenu.show")
    def test_delete_tag_item_all_items(self, mock_show: MagicMock, mock_menu: MagicMock) -> None:
        """Test deleting all values from a tag list.

        When all values are removed, the tag itself should also be
        removed (not kept with an empty list).
        """
        mock_show.side_effect = [0, [0, 1, 2]]  # Where a choice is returned from the menu
        mock_menu.return_value = None  # constructor requires terminal, not availabe in CI.

        tags = MusicTags()
        tags.resolved = {"artist": ["artist 1", "artist 2", "artist 3"]}
        tags.delete_tag_item()
        self.assertNotIn("artist", tags.resolved)

    @patch("retag_opus.utils.TerminalMenu.__init__")
    @patch("retag_opus.utils.TerminalMenu.show")
    def test_delete_tag_item_quit(self, mock_show: MagicMock, mock_menu: MagicMock) -> None:
        """Test quitting witout deleting tag.

        The function is for deleting values from a tag, but the user can
        also chose to quit witout deleting anyting. Test that nothing is
        deleted and that the quitting text is printed.
        """
        mock_show.side_effect = [1]  # Where a choice is returned from the menu (quit)
        mock_menu.return_value = None  # constructor requires terminal, not availabe in CI.

        tags = MusicTags()
        tags.resolved = {"artist": ["artist 1", "artist 2"]}
        tags.delete_tag_item()
        self.assertEqual(["artist 1", "artist 2"], tags.resolved.get("artist"))
        captured = self.capsys.readouterr()  # type: ignore
        self.assertEqual(f"{Fore.YELLOW}Returning without removing anything{Fore.RESET}\n", captured.out)

    @patch("retag_opus.music_tags.input")
    def test_modify_resolved_field(self, mock_input: MagicMock) -> None:
        """Test modifying a field.

        If the user gives a comma-seperated list of artists, it should
        be split.
        """
        mock_input.side_effect = ["artist", "artist 3 | artist 4", "", ""]
        tags = MusicTags()
        tags.resolved = {"artist": ["artist 1", "artist 2"]}
        tags.modify_resolved_field()
        self.assertEqual(["artist 3", "artist 4"], tags.resolved.get("artist"))

    @patch("retag_opus.music_tags.input")
    def test_modify_resolved_field_exit_immediately(self, mock_input: MagicMock) -> None:
        """Test exiting without modifying a field."""
        mock_input.side_effect = ["", ""]
        tags = MusicTags()
        tags.resolved = {"artist": ["artist 1", "artist 2"]}
        tags.modify_resolved_field()
        self.assertEqual(["artist 1", "artist 2"], tags.resolved.get("artist"))

    @patch("retag_opus.music_tags.input")
    def test_modify_resolved_field_no_value(self, mock_input: MagicMock) -> None:
        """Test that nothing is changed if no value is given."""
        mock_input.side_effect = ["artist", ""]
        tags = MusicTags()
        tags.resolved = {"artist": ["artist 1", "artist 2"]}
        tags.modify_resolved_field()
        self.assertEqual(["artist 1", "artist 2"], tags.resolved.get("artist"))

    @patch("retag_opus.music_tags.input")
    def test_modify_resolved_field_no_key(self, mock_input: MagicMock) -> None:
        """Test that nothing is changed if no key is given."""
        mock_input.side_effect = ["", "artist 1"]
        tags = MusicTags()
        tags.resolved = {"artist": ["artist 1", "artist 2"]}
        tags.modify_resolved_field()
        self.assertEqual(["artist 1", "artist 2"], tags.resolved.get("artist"))

    @patch("retag_opus.utils.Utils.select_single_tag")
    def test_determine_album_artist_select_one(self, select_single_tag: MagicMock) -> None:
        """Test that album artist can be picked up normally."""
        expected_artist = ["artist 4"]
        select_single_tag.return_value = expected_artist
        tags = MusicTags()

        tags.original = {"artist": ["artist 1"]}
        tags.youtube = {"artist": ["artist 2"]}
        tags.fromtags = {"artist": ["artist 3"]}
        tags.fromdesc = {"artist": ["artist 4"]}
        tags.determine_album_artist()
        self.assertEqual(expected_artist, tags.resolved.get("albumartist"))

    @patch("retag_opus.utils.Utils.select_single_tag")
    def test_determine_album_artist_select_two(self, select_single_tag: MagicMock) -> None:
        """Test that two album artists can be selected."""
        expected_artist = ["artist 2", "artist 4"]
        select_single_tag.return_value = expected_artist
        tags = MusicTags()

        tags.original = {"artist": ["artist 1"]}
        tags.youtube = {"artist": ["artist 2"]}
        tags.fromtags = {"artist": ["artist 3"]}
        tags.fromdesc = {"artist": ["artist 4"]}
        tags.determine_album_artist()
        self.assertEqual(expected_artist, tags.resolved.get("albumartist"))

    @patch("retag_opus.utils.Utils.select_single_tag")
    def test_determine_album_artist_select_zero(self, select_single_tag: MagicMock) -> None:
        """Test that no tag is added when nothing is selected."""
        select_single_tag.return_value = []
        tags = MusicTags()

        tags.original = {"artist": ["artist 1"]}
        tags.youtube = {"artist": ["artist 2"]}
        tags.fromtags = {"artist": ["artist 3"]}
        tags.fromdesc = {"artist": ["artist 4"]}
        tags.determine_album_artist()
        self.assertNotIn("albumartist", tags.resolved)

    def test_determine_album_artist_only_old_exist(self) -> None:
        """Test that two album artists can be selected.

        When only the original tags have an artist, use that one as
        albumartist without asking.
        """
        tags = MusicTags()

        tags.original = {"artist": ["artist 1"]}
        tags.determine_album_artist()
        self.assertEqual(["artist 1"], tags.resolved.get("albumartist"))

    def test_determine_album_artist_old_and_resolved_exist(self) -> None:
        """Test that resolved artist is preferred.

        When resolved artist is found, that should be used.
        """
        tags = MusicTags()

        tags.original = {"artist": ["artist 1"]}
        tags.resolved = {"artist": ["artist 2"]}
        tags.determine_album_artist()
        self.assertEqual(["artist 2"], tags.resolved.get("albumartist"))

    def test_determine_album_artist_no_artist_or_albumartist(self) -> None:
        """Test nothing is added when nothing to choose from."""
        tags = MusicTags()

        tags.determine_album_artist()
        self.assertNotIn("albumartist", tags.resolved)

    def test_determine_album_artist_one_exists(self) -> None:
        """Test that no change is made when album artist is good.

        When there is only one artist in all sources, and there already
        is an albumartist in the original tags, there is no need to make
        any changes to the album artist because there is only one to
        choose from.
        """
        tags = MusicTags()

        tags.fromtags = {"artist": ["artist 1"]}
        tags.original = {"albumartist": ["artist 2"]}
        tags.determine_album_artist()
        self.assertEqual(None, tags.resolved.get("albumartist"))

    def test_default_to_youtube_date_protect_original(self) -> None:
        """Test that youtube date not overwrites original."""
        tags = MusicTags()
        tags.youtube = {"date": ["1991-01-01"]}
        tags.original = {"date": ["2022-09-03"]}
        tags.default_to_youtube_date()
        self.assertEqual(["1991-01-01"], tags.resolved.get("date"))

    def test_default_to_youtube_date_use_when_appropriate(self) -> None:
        """Test that youtube date is used."""
        tags = MusicTags()
        tags.youtube = {"date": ["1991-01-01"]}
        tags.default_to_youtube_date()
        self.assertEqual(["1991-01-01"], tags.resolved.get("date"))

    def test_default_to_youtube_date_no_change_with_no_youtube(self) -> None:
        """Test that no data is changed when no youtube date exists."""
        tags = MusicTags()
        tags.default_to_youtube_date()
        self.assertNotIn("date", tags.resolved)

    def test_set_artist_if_obvious_when_obvious(self) -> None:
        """Test that when artist is identical, it is auto-resolved."""
        tags = MusicTags()
        tags.youtube = {"artist": ["artist 1"]}
        tags.original = {"artist": ["artist 1"]}
        tags.set_artist_if_obvious()
        self.assertEqual(["artist 1"], tags.resolved.get("artist"))

    def test_set_artist_if_obvious_when_not_obvious(self) -> None:
        """Test resolved not set when youtube and original differ."""
        tags = MusicTags()
        tags.youtube = {"artist": ["artist 1"]}
        tags.original = {"artist": ["artist 2"]}
        tags.set_artist_if_obvious()
        self.assertNotIn("artist", tags.resolved)

    def test_set_artist_if_obvious_when_no_youtube_artist(self) -> None:
        """Test don't change anything when either artist is missing."""
        tags1 = MusicTags()
        tags1.original = {"artist": ["artist 2"]}
        tags1.set_artist_if_obvious()
        self.assertNotIn("artist", tags1.resolved)

        tags2 = MusicTags()
        tags2.original = {"artist": ["artist 2"]}
        tags2.set_artist_if_obvious()
        self.assertNotIn("artist", tags2.resolved)

    def test_set_artist_if_obvious_when_not_split_in_original(self) -> None:
        """Test setting obvious artist."""
        tags = MusicTags()
        tags.youtube = {"artist": ["artist 1", "artist 2"]}
        tags.original = {"artist": ["artist 1, artist 2"]}
        tags.set_artist_if_obvious()
        self.assertEqual(["artist 1", "artist 2"], tags.resolved.get("artist"))

    def test_set_artist_if_obvious_when_list_in_original_tags(self) -> None:
        """Test setting obvious artist."""
        tags = MusicTags()
        tags.youtube = {"artist": ["artist 1", "artist 2"]}
        tags.original = {"artist": ["artist 1", "artist 2"]}
        tags.set_artist_if_obvious()
        self.assertEqual(["artist 1", "artist 2"], tags.resolved.get("artist"))

    @patch("retag_opus.utils.TerminalMenu.__init__")
    @patch("retag_opus.utils.TerminalMenu.show")
    def test_manually_adjust_tag_when_resolving_no_choice(self, mock_show: MagicMock, mock_menu: MagicMock) -> None:
        """Test no choice or multiple choice not allowed.

        The tested function shows a menu with options for making manual
        adjustments to a tag. It shouldn't be possible to make no
        choice or multiple choices, but we test it here for safety.
        Expectation is a return with value True.
        """
        tags = MusicTags()

        mock_menu.return_value = None  # constructor requires terminal, not availabe in CI.
        mock_show.return_value = None  # Where a choice is returned from the menu

        expected = "Going back to previous menu\n"

        repeat = tags.manually_adjust_tag_when_resolving("artist")
        captured = self.capsys.readouterr()  # type: ignore

        self.assertTrue(repeat)
        self.assertEqual(expected, captured.out)

        mock_show.return_value = (0, 1)  # Where a choice is returned from the menu

        repeat = tags.manually_adjust_tag_when_resolving("artist")
        captured = self.capsys.readouterr()  # type: ignore

        self.assertTrue(repeat)

    @patch("retag_opus.utils.TerminalMenu.__init__")
    @patch("retag_opus.utils.TerminalMenu.show")
    def test_manually_adjust_tag_when_resolving_go_back(self, mock_show: MagicMock, mock_menu: MagicMock) -> None:
        """Test going back to previous menu."""
        tags = MusicTags()

        mock_menu.return_value = None  # constructor requires terminal, not availabe in CI.
        mock_show.return_value = None  # Where a choice is returned from the menu

        expected = "Going back to previous menu\n"

        repeat = tags.manually_adjust_tag_when_resolving("artist")
        captured = self.capsys.readouterr()  # type: ignore

        self.assertTrue(repeat)
        self.assertEqual(expected, captured.out)

    @patch("retag_opus.utils.TerminalMenu.__init__")
    @patch("retag_opus.utils.TerminalMenu.show")
    @patch("builtins.input")
    def test_manually_adjust_tag_when_resolving_manual(
        self,
        mock_input: MagicMock,
        mock_show: MagicMock,
        mock_menu: MagicMock,
    ) -> None:
        """Test manually adjusting tag, with and without input."""
        tags = MusicTags()

        mock_menu.return_value = None  # constructor requires terminal, not availabe in CI.
        mock_show.return_value = 1  # Where a choice is returned from the menu
        mock_input.return_value = "artist 1"

        repeat = tags.manually_adjust_tag_when_resolving("artist")

        self.assertFalse(repeat)
        self.assertEqual(["artist 1"], tags.resolved.get("artist"))

        tags.resolved = {}
        mock_input.return_value = ""
        repeat = tags.manually_adjust_tag_when_resolving("artist")
        captured = self.capsys.readouterr()  # type: ignore

        self.assertTrue(repeat)
        self.assertNotIn("artist", tags.resolved)
        self.assertEqual("No input, not changing tag\n", captured.out)

    @patch("retag_opus.utils.TerminalMenu.__init__")
    @patch("retag_opus.utils.TerminalMenu.show")
    @patch("retag_opus.music_tags.MusicTags.print_youtube")
    def test_manually_adjust_tag_when_resolving_print_description_data(
        self,
        mock_print_youtube: MagicMock,
        mock_show: MagicMock,
        mock_menu: MagicMock,
    ) -> None:
        """Test that description printing function called when asked."""
        mock_menu.return_value = None  # constructor requires terminal, not availabe in CI.
        mock_show.return_value = 2  # Where a choice is returned from the menu
        mock_print_youtube.side_effect = "test"

        tags = MusicTags()
        repeat = tags.manually_adjust_tag_when_resolving("artist")

        self.assertTrue(repeat)
        mock_print_youtube.assert_called_once()

    @patch("retag_opus.utils.TerminalMenu.__init__")
    @patch("retag_opus.utils.TerminalMenu.show")
    def test_manually_adjust_tag_when_resolving_remove_tag(
        self,
        mock_show: MagicMock,
        mock_menu: MagicMock,
    ) -> None:
        """Test removing a tag."""
        mock_menu.return_value = None  # constructor requires terminal, not availabe in CI.
        mock_show.return_value = 3  # Where a choice is returned from the menu

        tags = MusicTags()
        tags.original = {"artist": ["artist 1", "artist 2"]}
        repeat = tags.manually_adjust_tag_when_resolving("artist")

        self.assertFalse(repeat)
        self.assertEqual(["[Removed]"], tags.resolved.get("artist"))
        self.assertEqual(["artist 1", "artist 2"], tags.original.get("artist"))

    @patch("retag_opus.utils.TerminalMenu.__init__")
    @patch("retag_opus.utils.TerminalMenu.show")
    def test_manually_adjust_tag_when_resolving_select(
        self,
        mock_show: MagicMock,
        mock_menu: MagicMock,
    ) -> None:
        """Test selecting tag from list."""
        mock_menu.return_value = None  # constructor requires terminal, not availabe in CI.

        tags = MusicTags()
        tags.original = {"artist": ["artist 1, artist 2"]}
        tags.youtube = {"artist": ["artist 1", "artist 2"]}

        mock_show.side_effect = [0, 1]  # Second menu
        repeat = tags.manually_adjust_tag_when_resolving("artist")

        self.assertFalse(repeat)
        self.assertEqual(["artist 1"], tags.resolved.get("artist"))

        mock_show.side_effect = [0, 0]  # Second menu
        repeat = tags.manually_adjust_tag_when_resolving("artist")

        self.assertFalse(repeat)
        self.assertEqual(["artist 1, artist 2"], tags.resolved.get("artist"))

        mock_show.side_effect = [0, 2]  # Second menu
        repeat = tags.manually_adjust_tag_when_resolving("artist")

        self.assertFalse(repeat)
        self.assertEqual(["artist 2"], tags.resolved.get("artist"))

        mock_show.side_effect = [0, [1, 2]]  # Second menu
        repeat = tags.manually_adjust_tag_when_resolving("artist")

        self.assertFalse(repeat)
        self.assertEqual(["artist 1", "artist 2"], tags.resolved.get("artist"))

        mock_show.side_effect = [0, None]  # Second menu
        repeat = tags.manually_adjust_tag_when_resolving("artist")
        captured = self.capsys.readouterr()  # type: ignore

        self.assertTrue(repeat)
        self.assertEqual(["artist 1", "artist 2"], tags.resolved.get("artist"))
        self.assertEqual(Fore.RED + "Invalid choice, try again\n", captured.out)

    def test_resolve_metadata_defaults_positive(self) -> None:
        """Test defaults taken from any source when lacking other data.

        When there is no original data and there aren't multiple
        sources of new data, we can just use the one we found since
        there is no alternative. The user can manually change it later
        if they want.
        """
        # Parsed from description
        tags = MusicTags()
        tags.youtube = {"artist": ["artist 1"]}

        tags.resolve_metadata()
        captured = self.capsys.readouterr()  # type: ignore
        self.assertEqual(["artist 1"], tags.resolved.get("artist"))
        self.assertEqual(
            Fore.YELLOW + "Artist: No value exists in metadata. Using parsed data: ['artist 1']." + Fore.RESET + "\n",
            captured.out,
        )

        # Parsed from description tags
        tags = MusicTags()
        tags.fromdesc = {"artist": ["artist 1"]}

        tags.resolve_metadata()
        captured = self.capsys.readouterr()  # type: ignore
        self.assertEqual(["artist 1"], tags.resolved.get("artist"))
        self.assertEqual(
            Fore.YELLOW + "Artist: No value exists in metadata. Using parsed data: ['artist 1']." + Fore.RESET + "\n",
            captured.out,
        )

    def test_resolve_metadata_defaults_negative(self) -> None:
        """Test no defaults taken when no good data exists.

        There shouldn't be any tags parsed from original tags when there
        are no original tags. And if there just are no tags, nothing
        should happen.
        """
        # No tags at all
        tags = MusicTags()

        tags.resolve_metadata()
        self.assertEqual({}, tags.resolved)

        # Parsed from original tags
        tags = MusicTags()

        tags.fromtags = {"artist": ["artist 1"]}
        tags.resolve_metadata()
        self.assertEqual({}, tags.resolved)

    @patch("retag_opus.music_tags.MusicTags.determine_album_artist")
    def test_resolve_metadata_equal_when_stripped(self, mock_album_artist: MagicMock) -> None:
        """Test that new metadata autoresolves when equal when stripped.

        If a new source differs from the original only in that one of
        them has some extra whitespace, remove the whitespace and use
        that value.
        """
        mock_album_artist.return_value = None

        # Youtube
        tags = MusicTags()
        tags.original = {"artist": ["artist 1"]}
        tags.youtube = {"artist": ["artist 1 "]}

        tags.resolve_metadata()
        captured = self.capsys.readouterr()  # type: ignore
        self.assertEqual(["artist 1"], tags.resolved.get("artist"))
        self.assertEqual(
            Fore.GREEN + "Artist: Metadata matches YouTube description tags." + Fore.RESET + "\n",
            captured.out,
        )

        # Parsed from description
        tags = MusicTags()
        tags.original = {"artist": ["artist 1"]}
        tags.fromdesc = {"artist": ["artist 1 "]}

        tags.resolve_metadata()
        captured = self.capsys.readouterr()  # type: ignore
        self.assertEqual(["artist 1"], tags.resolved.get("artist"))
        self.assertEqual(
            Fore.GREEN + "Artist: Metadata matches tags parsed from YouTube tags." + Fore.RESET + "\n",
            captured.out,
        )

        # Parsed from original tags
        tags = MusicTags()
        tags.original = {"artist": ["artist 1"]}
        tags.fromtags = {"artist": ["artist 1 "]}

        tags.resolve_metadata()
        captured = self.capsys.readouterr()  # type: ignore
        self.assertEqual(["artist 1"], tags.resolved.get("artist"))
        self.assertEqual(
            Fore.GREEN + "Artist: Metadata matches tags parsed from original tags." + Fore.RESET + "\n",
            captured.out,
        )
