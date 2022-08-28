"""Tests for music_tags.py."""
import sys
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
        tags.original = {"performer:vocals": ["artist 1"], "performer:violin": ["artist 1"]}
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

    def test_print_resolved_with_performers(self) -> None:
        """Test that resolved tags print, including performers.

        Test printing of resolved tags with the argument to print all
        set to false.
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
