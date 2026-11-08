"""Tests for tag_editor.py."""

import os
import sys
import unittest
from copy import deepcopy
from unittest.mock import MagicMock, patch

import pytest

from retag_opus import styles, tag_editor
from retag_opus.exceptions import UserExitException
from retag_opus.tag_table import MUSICBRAINZ, ORIGINAL, PARSED_FROM_ORIGINAL, PARSED_FROM_YOUTUBE, TagTable
from retag_opus.tags import Tags


class TestTagEditor(unittest.TestCase):
    """Test showing a song's tags and asking about them."""

    @pytest.fixture(autouse=True)
    def store_capsys(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Store capsys, since unittest methods can't take fixtures."""
        self.capsys = capsys

    def test_print_tag(self) -> None:
        """Test printing of a single metadata key."""
        tags: Tags = {"artist": ["artist 1", "artist 2"], "title": ["title 1", "title 2"]}
        tag_editor.print_tag(TagTable(), "Artist", "artist", styles.original, tags)
        captured = self.capsys.readouterr()
        self.assertEqual("  Artist: artist 1 | artist 2\n", captured.out)

    def test_print_tags(self) -> None:
        """Test printing of metadata."""
        tags: Tags = {"artist": ["artist 1", "artist 2"], "title": ["title 1", "title 2"]}
        tag_editor.print_tags(TagTable(), tags, styles.original)
        captured = self.capsys.readouterr()
        expected = (
            "  Title: title 1 | title 2\n"
            "  Album: Not found\n"
            "  Album Artist: Not found\n"
            "  Artist(s): artist 1 | artist 2\n"
            "  Date: Not found\n"
            "  Genre: Not found\n"
            "  Version: Not found\n"
            "  Performer: Not found\n"
            "  Organization: Not found\n"
            "  Copyright: Not found\n"
            "  Composer: Not found\n"
            "  Conductor: Not found\n"
            "  Arranger: Not found\n"
            "  Author: Not found\n"
            "  Producer: Not found\n"
            "  Publisher: Not found\n"
            "  Lyricist: Not found\n"
            "  Writer: Not found\n\n"
        )

        self.assertEqual(expected, captured.out)

    def test_print_tags_with_performers(self) -> None:
        """Test printing of metadata where there are performer tags."""
        tags: Tags = {"artist": ["artist 1", "artist 2"], "performer:lead vocals": ["bassist 1"]}
        tag_editor.print_tags(TagTable(), tags, styles.original)
        captured = self.capsys.readouterr()
        expected = (
            "  Performers:\n"
            "  - Lead vocals: bassist 1\n"
            "  Title: Not found\n"
            "  Album: Not found\n"
            "  Album Artist: Not found\n"
            "  Artist(s): artist 1 | artist 2\n"
            "  Date: Not found\n"
            "  Genre: Not found\n"
            "  Version: Not found\n"
            "  Performer: Not found\n"
            "  Organization: Not found\n"
            "  Copyright: Not found\n"
            "  Composer: Not found\n"
            "  Conductor: Not found\n"
            "  Arranger: Not found\n"
            "  Author: Not found\n"
            "  Producer: Not found\n"
            "  Publisher: Not found\n"
            "  Lyricist: Not found\n"
            "  Writer: Not found\n\n"
        )

        self.assertEqual(expected, captured.out)

    def test_print_tags_with_performer_tags_without_pattern(self) -> None:
        """Test printing performer tags without a description pattern.

        They're printed after the ones that can, in alphabetical order.
        """
        tags: Tags = {
            "artist": ["artist 1", "artist 2"],
            "performer:theremin": ["person 1"],
            "performer:accordion": ["person 2"],
            "performer:violin": ["person 3"],
        }
        tag_editor.print_tags(TagTable(), tags, styles.original)
        captured = self.capsys.readouterr()
        expected = (
            "  Performers:\n"
            "  - Violin: person 3\n"
            "  - Accordion: person 2\n"
            "  - Theremin: person 1\n"
            "  Title: Not found\n"
            "  Album: Not found\n"
            "  Album Artist: Not found\n"
            "  Artist(s): artist 1 | artist 2\n"
            "  Date: Not found\n"
            "  Genre: Not found\n"
            "  Version: Not found\n"
            "  Performer: Not found\n"
            "  Organization: Not found\n"
            "  Copyright: Not found\n"
            "  Composer: Not found\n"
            "  Conductor: Not found\n"
            "  Arranger: Not found\n"
            "  Author: Not found\n"
            "  Producer: Not found\n"
            "  Publisher: Not found\n"
            "  Lyricist: Not found\n"
            "  Writer: Not found\n\n"
        )

        self.assertEqual(expected, captured.out)

    def test_styled_values_from_all_sources_one_source(self) -> None:
        """Test getting tags from one source."""
        tags = TagTable()
        tags.set_tags(ORIGINAL, {"artist": ["artist 1"]})
        actual = tag_editor.styled_values_from_all_sources(tags, "artist")
        expected = ["artist 1"]
        self.assertListEqual(expected, actual)

    def test_styled_values_from_all_sources_two_sources(self) -> None:
        """Test getting tags from two source."""
        tags = TagTable()
        tags.set_tags(ORIGINAL, {"artist": ["artist 1"]})
        tags.set_youtube_tags({"artist": ["artist 2"]}, is_auto_generated=True)
        actual = tag_editor.styled_values_from_all_sources(tags, "artist")
        expected = ["artist 2", "artist 1"]
        self.assertListEqual(expected, actual)

    def test_styled_values_from_all_sources_two_overlapping_sources(self) -> None:
        """Test get tags from two sources where a value is in both."""
        tags = TagTable()
        tags.set_tags(ORIGINAL, {"artist": ["artist 1"]})
        tags.set_youtube_tags({"artist": ["artist 1", "artist 2"]}, is_auto_generated=True)
        actual = tag_editor.styled_values_from_all_sources(tags, "artist")
        expected = ["artist 1 | artist 2", "artist 1"]
        self.assertListEqual(expected, actual)

    def test_styled_values_from_all_sources_no_values(self) -> None:
        """Test getting tags from one source."""
        tags = TagTable()
        actual = tag_editor.styled_values_from_all_sources(tags, "artist")
        expected: list[str] = []
        self.assertListEqual(expected, actual)

    def test_styled_values_from_all_sources_all_sources(self) -> None:
        """Test getting tags from two source."""
        tags = TagTable()
        tags.set_tags(ORIGINAL, {"artist": ["artist 1"]})
        tags.set_youtube_tags({"artist": ["artist 2"]}, is_auto_generated=True)
        tags.set_tags(PARSED_FROM_ORIGINAL, {"artist": ["artist 3"]})
        tags.set_tags(PARSED_FROM_YOUTUBE, {"artist": ["artist 4"]})
        actual = tag_editor.styled_values_from_all_sources(tags, "artist")
        expected = [
            "artist 2",
            "artist 3",
            "artist 4",
            "artist 1",
        ]
        self.assertListEqual(expected, actual)

    def test_print_all_sources(self) -> None:
        """Test printing the combined metadata of all sources."""
        tags = TagTable()
        tags.set_tags(ORIGINAL, {"artist": ["artist 1"]})
        tags.set_youtube_tags({"artist": ["artist 2"]}, is_auto_generated=True)
        tags.set_tags(PARSED_FROM_ORIGINAL, {"artist": ["artist 3"]})
        tags.set_tags(PARSED_FROM_YOUTUBE, {"artist": ["artist 4"]})
        tag_editor.print_all_sources(tags)
        captured = self.capsys.readouterr()
        expected = (
            "Title: Not set\n"
            "Album: Not set\n"
            "Album Artist: Not set\n"
            "Artist(s): artist 2 | artist 3 | artist 4 | artist 1\n"
            "Date: Not set\n"
            "Genre: Not set\n"
            "Version: Not set\n"
            "Performer: Not set\n"
            "Organization: Not set\n"
            "Copyright: Not set\n"
            "Composer: Not set\n"
            "Conductor: Not set\n"
            "Arranger: Not set\n"
            "Author: Not set\n"
            "Producer: Not set\n"
            "Publisher: Not set\n"
            "Lyricist: Not set\n"
            "Writer: Not set\n\n"
        )
        self.assertEqual(expected, captured.out)

    def test_print_all_sources_with_performers(self) -> None:
        """Test printing combined data when there are performer tags."""
        tags = TagTable()
        tags.set_tags(ORIGINAL, {"artist": ["artist 1"]})
        tags.set_youtube_tags({"artist": ["artist 2"]}, is_auto_generated=True)
        tags.set_tags(PARSED_FROM_ORIGINAL, {"artist": ["artist 3"]})
        tags.set_tags(PARSED_FROM_YOUTUBE, {"performer:lead vocals": ["artist 4"]})
        tag_editor.print_all_sources(tags)
        captured = self.capsys.readouterr()
        expected = (
            "Performers:\n"
            "- Lead vocals: artist 4\n"
            "Title: Not set\n"
            "Album: Not set\n"
            "Album Artist: Not set\n"
            "Artist(s): artist 2 | artist 3 | artist 1\n"
            "Date: Not set\n"
            "Genre: Not set\n"
            "Version: Not set\n"
            "Performer: Not set\n"
            "Organization: Not set\n"
            "Copyright: Not set\n"
            "Composer: Not set\n"
            "Conductor: Not set\n"
            "Arranger: Not set\n"
            "Author: Not set\n"
            "Producer: Not set\n"
            "Publisher: Not set\n"
            "Lyricist: Not set\n"
            "Writer: Not set\n\n"
        )
        self.assertEqual(expected, captured.out)

    def test_print_all_sources_with_no_data(self) -> None:
        """Test printing the combined metadata of all sources."""
        tags = TagTable()
        tag_editor.print_all_sources(tags)
        captured = self.capsys.readouterr()
        expected = "There's no data to be printed\n"
        self.assertEqual(expected, captured.out)

    def test_print_youtube_tags(self) -> None:
        """Test printing data from youtube tags."""
        tags = TagTable()
        tags.set_tags(ORIGINAL, {"artist": ["artist 1"]})
        tags.set_youtube_tags({"artist": ["artist 2"], "performer:lead vocals": ["artist 5"]}, is_auto_generated=True)
        tags.set_tags(PARSED_FROM_ORIGINAL, {"artist": ["artist 3"]})
        tags.set_tags(PARSED_FROM_YOUTUBE, {"performer:lead vocals": ["artist 4"]})
        tag_editor.print_youtube_tags(tags)
        captured = self.capsys.readouterr()
        expected = (
            "  Performers:\n"
            "  - Lead vocals: artist 5\n"
            "  Title: Not found\n"
            "  Album: Not found\n"
            "  Album Artist: Not found\n"
            "  Artist(s): artist 2\n"
            "  Date: Not found\n"
            "  Genre: Not found\n"
            "  Version: Not found\n"
            "  Performer: Not found\n"
            "  Organization: Not found\n"
            "  Copyright: Not found\n"
            "  Composer: Not found\n"
            "  Conductor: Not found\n"
            "  Arranger: Not found\n"
            "  Author: Not found\n"
            "  Producer: Not found\n"
            "  Publisher: Not found\n"
            "  Lyricist: Not found\n"
            "  Writer: Not found\n\n"
        )
        self.assertEqual(expected, captured.out)

    def test_print_youtube_tags_no_data(self) -> None:
        """Test printing data from youtube tags when there are none."""
        tags = TagTable()
        tags.set_tags(ORIGINAL, {"artist": ["artist 1"]})
        tags.set_tags(PARSED_FROM_ORIGINAL, {"artist": ["artist 3"]})
        tags.set_tags(PARSED_FROM_YOUTUBE, {"performer:lead vocals": ["artist 4"]})
        tag_editor.print_youtube_tags(tags)
        captured = self.capsys.readouterr()
        expected = "No new data parsed from description\n"
        self.assertEqual(expected, captured.out)

    def test_print_resolved_tags(self) -> None:
        """Test that resolved tags can be printed."""
        tags = TagTable()
        tags.set_tags(ORIGINAL, {"artist": ["artist 1"], "title": ["title 1"], "producer": ["someone"]})
        tags.resolved = {"artist": ["artist 1"], "title": ["title 2"], "producer": ["[Removed]"]}
        tag_editor.print_resolved_tags(tags, with_all_sources=False)
        captured = self.capsys.readouterr()
        expected = (
            "  Title: title 2\n"
            "  Album: Not found\n"
            "  Album Artist: Not found\n"
            "  Artist(s): artist 1\n"
            "  Date: Not found\n"
            "  Genre: Not found\n"
            "  Version: Not found\n"
            "  Performer: Not found\n"
            "  Organization: Not found\n"
            "  Copyright: Not found\n"
            "  Composer: Not found\n"
            "  Conductor: Not found\n"
            "  Arranger: Not found\n"
            "  Author: Not found\n"
            "  Producer (Removed): someone\n"
            "  Publisher: Not found\n"
            "  Lyricist: Not found\n"
            "  Writer: Not found\n\n"
        )
        self.assertEqual(expected, captured.out)

    def test_print_resolved_tags_with_performers(self) -> None:
        """Test that resolved tags print, including performers."""
        tags = TagTable()
        tags.set_tags(
            ORIGINAL,
            {
                "performer:lead vocals": ["artist 1"],
                "performer:violin": ["artist 1"],
                "performer:keyboard": ["some guy"],
            },
        )
        tags.resolved = {
            "performer:lead vocals": ["artist 1"],
            "performer:violin": ["artist 2"],
            "performer:keyboard": ["[Removed]"],
        }
        tag_editor.print_resolved_tags(tags, with_all_sources=False)
        captured = self.capsys.readouterr()
        expected = (
            "  Performers:\n"
            "  - Lead vocals: artist 1\n"
            "  - Keyboard (Removed): some guy\n"
            "  - Violin: artist 2\n"
            "  Title: Not found\n"
            "  Album: Not found\n"
            "  Album Artist: Not found\n"
            "  Artist(s): Not found\n"
            "  Date: Not found\n"
            "  Genre: Not found\n"
            "  Version: Not found\n"
            "  Performer: Not found\n"
            "  Organization: Not found\n"
            "  Copyright: Not found\n"
            "  Composer: Not found\n"
            "  Conductor: Not found\n"
            "  Arranger: Not found\n"
            "  Author: Not found\n"
            "  Producer: Not found\n"
            "  Publisher: Not found\n"
            "  Lyricist: Not found\n"
            "  Writer: Not found\n\n"
        )
        sys.stdout.write(captured.out)
        self.assertEqual(expected, captured.out)

    def test_print_resolved_tags_with_performer_tags_without_pattern(self) -> None:
        """Test that all performer tags are printed as performers.

        Performer tags that can't be parsed from descriptions, e.g. from
        MusicBrainz or with names from older versions, are printed last.
        """
        tags = TagTable()
        tags.set_tags(ORIGINAL, {"performer:vocals": ["artist 1"]})
        tags.resolved = {"performer:vocals": ["artist 1"], "performer:theremin": ["artist 2"]}
        tag_editor.print_resolved_tags(tags, with_all_sources=False)
        captured = self.capsys.readouterr()
        self.assertNotIn("Other tags", captured.out)
        expected = "  Performers:\n  - Theremin: artist 2\n  - Vocals: artist 1\n  Title: Not found\n"
        self.assertIn(expected, captured.out)

    def test_print_resolved_tags_with_all_sources_and_performers(self) -> None:
        """Test that resolved tags print, including performers.

        Test printing of resolved tags with the argument to print all
        set to true.
        """
        tags = TagTable()
        tags.set_tags(
            ORIGINAL,
            {
                "performer:lead vocals": ["artist 1"],
                "performer:violin": ["artist 1"],
                "performer:guitar": ["artist 3"],
                "performer:keyboard": ["the keyboard master"],
            },
        )
        tags.set_youtube_tags(
            {
                "performer:guitar": ["artist 4"],
            },
            is_auto_generated=True,
        )
        tags.resolved = {
            "performer:lead vocals": ["artist 1"],
            "performer:violin": ["artist 2"],
            "performer:keyboard": ["[Removed]"],
        }
        tag_editor.print_resolved_tags(tags, with_all_sources=True)
        captured = self.capsys.readouterr()
        expected = (
            "  Performers:\n"
            "  - Lead vocals: artist 1\n"
            "  - Keyboard (Removed): the keyboard master\n"
            "  - Guitar: artist 4 | artist 3\n"
            "  - Violin: artist 2\n"
            "  Title: Not found\n"
            "  Album: Not found\n"
            "  Album Artist: Not found\n"
            "  Artist(s): Not found\n"
            "  Date: Not found\n"
            "  Genre: Not found\n"
            "  Version: Not found\n"
            "  Performer: Not found\n"
            "  Organization: Not found\n"
            "  Copyright: Not found\n"
            "  Composer: Not found\n"
            "  Conductor: Not found\n"
            "  Arranger: Not found\n"
            "  Author: Not found\n"
            "  Producer: Not found\n"
            "  Publisher: Not found\n"
            "  Lyricist: Not found\n"
            "  Writer: Not found\n\n"
        )
        self.assertEqual(expected, captured.out)

    def test_print_resolved_tags_with_performers_multiple_sources(self) -> None:
        """Test that resolved tags print, including performers.

        Test printing of resolved tags with the argument to print all
        set to false when there are several sources with relevant tags.
        """
        tags = TagTable()
        tags.set_tags(
            ORIGINAL,
            {
                "performer:lead vocals": ["artist 1"],
                "performer:violin": ["artist 1"],
                "performer:guitar": ["artist 3"],
                "performer:keyboard": ["artist 5"],
            },
        )
        tags.set_youtube_tags(
            {
                "performer:guitar": ["artist 4"],
                "performer:keyboard": ["artist 6"],
            },
            is_auto_generated=True,
        )
        tags.resolved = {
            "performer:lead vocals": ["artist 1"],
            "performer:violin": ["artist 2"],
            "performer:keyboard": ["[Removed]"],
        }
        tag_editor.print_resolved_tags(tags, with_all_sources=False)
        captured = self.capsys.readouterr()
        expected = (
            "  Performers:\n"
            "  - Lead vocals: artist 1\n"
            "  - Keyboard (Removed): artist 5\n"
            "  - Violin: artist 2\n"
            "  Title: Not found\n"
            "  Album: Not found\n"
            "  Album Artist: Not found\n"
            "  Artist(s): Not found\n"
            "  Date: Not found\n"
            "  Genre: Not found\n"
            "  Version: Not found\n"
            "  Performer: Not found\n"
            "  Organization: Not found\n"
            "  Copyright: Not found\n"
            "  Composer: Not found\n"
            "  Conductor: Not found\n"
            "  Arranger: Not found\n"
            "  Author: Not found\n"
            "  Producer: Not found\n"
            "  Publisher: Not found\n"
            "  Lyricist: Not found\n"
            "  Writer: Not found\n\n"
        )
        self.assertEqual(expected, captured.out)

    def test_print_resolved_tags_with_all_sources_without_performers(self) -> None:
        """Test that resolved tags print, not including performers.

        Test printing of resolved tags with the argument to print all
        set to true.
        """
        tags = TagTable()
        tags.set_tags(
            ORIGINAL,
            {
                "artist": ["artist 1", "artist 2"],
                "title": ["title 1"],
                "producer": ["person 1"],
                "arranger": ["artist 1"],
            },
        )
        tags.set_youtube_tags(
            {
                "arranger": ["artist 2"],
            },
            is_auto_generated=True,
        )
        tags.resolved = {
            "artist": ["artist 1", "artist 2"],
            "title": ["title 2"],
            "producer": ["[Removed]"],
        }
        tag_editor.print_resolved_tags(tags, with_all_sources=True)
        captured = self.capsys.readouterr()
        expected = (
            "  Title: title 2\n"
            "  Album: Not found\n"
            "  Album Artist: Not found\n"
            "  Artist(s): artist 1 | artist 2\n"
            "  Date: Not found\n"
            "  Genre: Not found\n"
            "  Version: Not found\n"
            "  Performer: Not found\n"
            "  Organization: Not found\n"
            "  Copyright: Not found\n"
            "  Composer: Not found\n"
            "  Conductor: Not found\n"
            "  Arranger: artist 2 | artist 1\n"
            "  Author: Not found\n"
            "  Producer (Removed): person 1\n"
            "  Publisher: Not found\n"
            "  Lyricist: Not found\n"
            "  Writer: Not found\n\n"
        )
        self.assertEqual(expected, captured.out)

    def test_print_resolved_tags_without_performers(self) -> None:
        """Test that resolved tags print, not including performers.

        Test printing of resolved tags with the argument to print all
        set to false.
        """
        tags = TagTable()
        tags.set_tags(
            ORIGINAL,
            {
                "artist": ["artist 1", "artist 2"],
                "title": ["title 1"],
                "producer": ["person 1"],
                "arranger": ["artist 1"],
            },
        )
        tags.set_youtube_tags(
            {
                "arranger": ["artist 2"],
            },
            is_auto_generated=True,
        )
        tags.resolved = {
            "artist": ["artist 1", "artist 2"],
            "title": ["title 2"],
            "producer": ["[Removed]"],
        }
        tag_editor.print_resolved_tags(tags, with_all_sources=False)
        captured = self.capsys.readouterr()
        expected = (
            "  Title: title 2\n"
            "  Album: Not found\n"
            "  Album Artist: Not found\n"
            "  Artist(s): artist 1 | artist 2\n"
            "  Date: Not found\n"
            "  Genre: Not found\n"
            "  Version: Not found\n"
            "  Performer: Not found\n"
            "  Organization: Not found\n"
            "  Copyright: Not found\n"
            "  Composer: Not found\n"
            "  Conductor: Not found\n"
            "  Arranger: Not found\n"
            "  Author: Not found\n"
            "  Producer (Removed): person 1\n"
            "  Publisher: Not found\n"
            "  Lyricist: Not found\n"
            "  Writer: Not found\n\n"
        )
        sys.stdout.write(captured.out)
        self.assertEqual(expected, captured.out)

    @patch("simple_term_menu.TerminalMenu.__init__")
    @patch("simple_term_menu.TerminalMenu.show")
    def test_remove_values_from_tag(self, mock_show: MagicMock, mock_menu: MagicMock) -> None:
        """Test deleting one value from a tag list."""
        mock_show.side_effect = [0, 1]  # Where a choice is returned from the menu
        mock_menu.return_value = None  # constructor requires terminal, not availabe in CI.

        tags = TagTable()
        tags.resolved = {"artist": ["artist 1", "artist 2"]}
        tag_editor.remove_values_from_tag(tags)
        self.assertEqual(["artist 1"], tags.resolved.get("artist"))

    @patch("simple_term_menu.TerminalMenu.__init__")
    @patch("simple_term_menu.TerminalMenu.show")
    def test_remove_values_from_tag_performer(self, mock_show: MagicMock, mock_menu: MagicMock) -> None:
        """Test deleting one value from a tag list."""
        mock_show.side_effect = [1, 1]  # Where a choice is returned from the menu
        mock_menu.return_value = None  # constructor requires terminal, not availabe in CI.

        tags = TagTable()
        tags.resolved = {"artist": ["artist 1"], "performer:lead vocals": ["artist 1", "artist 2"]}
        tag_editor.remove_values_from_tag(tags)
        self.assertEqual(["artist 1"], tags.resolved.get("performer:lead vocals"))

    @patch("simple_term_menu.TerminalMenu.__init__")
    @patch("simple_term_menu.TerminalMenu.show")
    def test_remove_values_from_tag_unknown_tag(self, mock_show: MagicMock, mock_menu: MagicMock) -> None:
        """Test deleting one value from a tag list."""
        mock_show.side_effect = [0, 0]  # Where a choice is returned from the menu
        mock_menu.return_value = None  # constructor requires terminal, not availabe in CI.

        tags = TagTable()
        tags.resolved = {"unknown_key": ["artist 1"]}
        tag_editor.remove_values_from_tag(tags)
        self.assertEqual(["artist 1"], tags.resolved.get("unknown_key"))

    @patch("simple_term_menu.TerminalMenu.__init__")
    @patch("simple_term_menu.TerminalMenu.show")
    def test_remove_values_from_tag_two_items(self, mock_show: MagicMock, mock_menu: MagicMock) -> None:
        """Test deleting two values from a tag list."""
        mock_show.side_effect = [0, [1, 2]]  # Where a choice is returned from the menu
        mock_menu.return_value = None  # constructor requires terminal, not availabe in CI.

        tags = TagTable()
        tags.resolved = {"artist": ["artist 1", "artist 2", "artist 3"]}
        tag_editor.remove_values_from_tag(tags)
        self.assertEqual(["artist 1"], tags.resolved.get("artist"))

    @patch("simple_term_menu.TerminalMenu.__init__")
    @patch("simple_term_menu.TerminalMenu.show")
    def test_remove_values_from_tag_zero_items(self, mock_show: MagicMock, mock_menu: MagicMock) -> None:
        """Test deleting zero values from a tag list."""
        mock_show.side_effect = [0, None]  # Where a choice is returned from the menu
        mock_menu.return_value = None  # constructor requires terminal, not availabe in CI.

        tags = TagTable()
        tags.resolved = {"artist": ["artist 1", "artist 2"]}
        tag_editor.remove_values_from_tag(tags)
        self.assertEqual(["artist 1", "artist 2"], tags.resolved.get("artist"))
        captured = self.capsys.readouterr()
        self.assertEqual("Returning without removing anything\n", captured.out)

    @patch("simple_term_menu.TerminalMenu.__init__")
    @patch("simple_term_menu.TerminalMenu.show")
    def test_remove_values_from_tag_all_items(self, mock_show: MagicMock, mock_menu: MagicMock) -> None:
        """Test deleting all values from a tag list.

        When all values are removed, the tag itself should also be
        removed (not kept with an empty list).
        """
        mock_show.side_effect = [0, [0, 1, 2]]  # Where a choice is returned from the menu
        mock_menu.return_value = None  # constructor requires terminal, not availabe in CI.

        tags = TagTable()
        tags.resolved = {"artist": ["artist 1", "artist 2", "artist 3"]}
        tag_editor.remove_values_from_tag(tags)
        self.assertEqual(tags.resolved["artist"], ["[Removed]"])

    @patch("simple_term_menu.TerminalMenu.__init__")
    @patch("simple_term_menu.TerminalMenu.show")
    def test_remove_values_from_tag_quit(self, mock_show: MagicMock, mock_menu: MagicMock) -> None:
        """Test quitting witout deleting tag.

        The function is for deleting values from a tag, but the user can
        also chose to quit witout deleting anyting. Test that nothing is
        deleted and that the quitting text is printed.
        """
        mock_show.side_effect = [1]  # Where a choice is returned from the menu (quit)
        mock_menu.return_value = None  # constructor requires terminal, not availabe in CI.

        tags = TagTable()
        tags.resolved = {"artist": ["artist 1", "artist 2"]}
        tag_editor.remove_values_from_tag(tags)
        self.assertEqual(["artist 1", "artist 2"], tags.resolved.get("artist"))
        captured = self.capsys.readouterr()
        self.assertEqual("Returning without removing anything\n", captured.out)

    @patch("simple_term_menu.TerminalMenu.__init__")
    @patch("simple_term_menu.TerminalMenu.show")
    def test_remove_values_from_tag_hide_already_removed(self, mock_show: MagicMock, mock_menu: MagicMock) -> None:
        """Test that a deleted tag isn't suggested for deletion.

        If a tag is already marked for deletion, there is no point in
        showing it in the list of tags offered for deletion to the user
        when they enter the tag deletion menu. So we test that these
        tags are not shown.

        It's hard to test directly, so the test is actually to verify
        that the menu has the right number of elements by verifying that
        the function returns without deleting anything if we moch the
        first return to be at the position where we expect the "Quit"
        option to be.
        """
        # 0 is artist tag, 1 is quit. there is no title
        mock_show.side_effect = [1]  # Where a choice is returned from the menu
        mock_menu.return_value = None  # constructor requires terminal, not availabe in CI.

        tags = TagTable()
        tags.resolved = {"artist": ["artist 1", "artist 2"], "title": ["[Removed]"]}
        tag_editor.remove_values_from_tag(tags)
        self.assertEqual(["artist 1", "artist 2"], tags.resolved.get("artist"))
        self.assertEqual(["[Removed]"], tags.resolved.get("title"))
        captured = self.capsys.readouterr()
        self.assertEqual("Returning without removing anything\n", captured.out)

    @patch("retag_opus.tag_editor.input")
    def test_enter_tags_by_hand(self, mock_input: MagicMock) -> None:
        """Test modifying a field.

        If the user gives a list of artists separated by ' | ', it
        should be split.
        """
        mock_input.side_effect = ["artist", "artist 3 | artist 4", "", ""]
        tags = TagTable()
        tags.resolved = {"artist": ["artist 1", "artist 2"]}
        tag_editor.enter_tags_by_hand(tags)
        self.assertEqual(["artist 3", "artist 4"], tags.resolved.get("artist"))

    @patch("retag_opus.tag_editor.input")
    def test_enter_tags_by_hand_exit_immediately(self, mock_input: MagicMock) -> None:
        """Test exiting without modifying a field."""
        mock_input.side_effect = ["", ""]
        tags = TagTable()
        tags.resolved = {"artist": ["artist 1", "artist 2"]}
        tag_editor.enter_tags_by_hand(tags)
        self.assertEqual(["artist 1", "artist 2"], tags.resolved.get("artist"))

    @patch("retag_opus.tag_editor.input")
    def test_enter_tags_by_hand_no_value(self, mock_input: MagicMock) -> None:
        """Test that nothing is changed if no value is given."""
        mock_input.side_effect = ["artist", ""]
        tags = TagTable()
        tags.resolved = {"artist": ["artist 1", "artist 2"]}
        tag_editor.enter_tags_by_hand(tags)
        self.assertEqual(["artist 1", "artist 2"], tags.resolved.get("artist"))

    @patch("retag_opus.tag_editor.input")
    def test_enter_tags_by_hand_no_key(self, mock_input: MagicMock) -> None:
        """Test that nothing is changed if no key is given."""
        mock_input.side_effect = ["", "artist 1"]
        tags = TagTable()
        tags.resolved = {"artist": ["artist 1", "artist 2"]}
        tag_editor.enter_tags_by_hand(tags)
        self.assertEqual(["artist 1", "artist 2"], tags.resolved.get("artist"))

    @patch("simple_term_menu.TerminalMenu.__init__")
    @patch("simple_term_menu.TerminalMenu.show")
    def test_ask_for_other_action_no_choice(self, mock_show: MagicMock, mock_menu: MagicMock) -> None:
        """Test no choice or multiple choice not allowed.

        The tested function shows a menu with options for making manual
        adjustments to a tag. It shouldn't be possible to make no
        choice or multiple choices, but we test it here for safety.
        Expectation is a return with value True.
        """
        tags = TagTable()

        mock_menu.return_value = None  # constructor requires terminal, not availabe in CI.
        mock_show.return_value = None  # Where a choice is returned from the menu

        expected = "Going back to previous menu\n"

        repeat = tag_editor.ask_for_other_action(tags, "artist")
        captured = self.capsys.readouterr()

        self.assertTrue(repeat)
        self.assertEqual(expected, captured.out)

        mock_show.return_value = (0, 1)  # Where a choice is returned from the menu

        repeat = tag_editor.ask_for_other_action(tags, "artist")
        captured = self.capsys.readouterr()

        self.assertTrue(repeat)

    @patch("simple_term_menu.TerminalMenu.__init__")
    @patch("simple_term_menu.TerminalMenu.show")
    def test_ask_for_other_action_go_back(self, mock_show: MagicMock, mock_menu: MagicMock) -> None:
        """Test going back to previous menu."""
        tags = TagTable()

        mock_menu.return_value = None  # constructor requires terminal, not availabe in CI.
        mock_show.return_value = None  # Where a choice is returned from the menu

        expected = "Going back to previous menu\n"

        repeat = tag_editor.ask_for_other_action(tags, "artist")
        captured = self.capsys.readouterr()

        self.assertTrue(repeat)
        self.assertEqual(expected, captured.out)

    @patch("simple_term_menu.TerminalMenu.__init__")
    @patch("simple_term_menu.TerminalMenu.show")
    @patch("builtins.input")
    def test_ask_for_other_action_manual(
        self,
        mock_input: MagicMock,
        mock_show: MagicMock,
        mock_menu: MagicMock,
    ) -> None:
        """Test manually adjusting tag, with and without input."""
        tags = TagTable()

        mock_menu.return_value = None  # constructor requires terminal, not availabe in CI.
        mock_show.return_value = 1  # Where a choice is returned from the menu
        mock_input.return_value = "artist 1"

        repeat = tag_editor.ask_for_other_action(tags, "artist")

        self.assertFalse(repeat)
        self.assertEqual(["artist 1"], tags.resolved.get("artist"))

        mock_input.return_value = "genre 1, genre 2"
        repeat = tag_editor.ask_for_other_action(tags, "genre")

        self.assertFalse(repeat)
        self.assertEqual(["genre 1", "genre 2"], tags.resolved.get("genre"))

        tags.resolved = {}
        mock_input.return_value = ""
        repeat = tag_editor.ask_for_other_action(tags, "artist")
        captured = self.capsys.readouterr()

        self.assertTrue(repeat)
        self.assertNotIn("artist", tags.resolved)
        self.assertEqual("No input, not changing tag\n", captured.out)

    @patch("simple_term_menu.TerminalMenu.__init__")
    @patch("simple_term_menu.TerminalMenu.show")
    @patch("retag_opus.tag_editor.print_youtube_tags")
    def test_ask_for_other_action_print_description_data(
        self,
        mock_print_youtube: MagicMock,
        mock_show: MagicMock,
        mock_menu: MagicMock,
    ) -> None:
        """Test that description printing function called when asked."""
        mock_menu.return_value = None  # constructor requires terminal, not availabe in CI.
        mock_show.return_value = 2  # Where a choice is returned from the menu
        mock_print_youtube.side_effect = "test"

        tags = TagTable()
        repeat = tag_editor.ask_for_other_action(tags, "artist")

        self.assertTrue(repeat)
        mock_print_youtube.assert_called_once()

    @patch("simple_term_menu.TerminalMenu.__init__")
    @patch("simple_term_menu.TerminalMenu.show")
    def test_ask_for_other_action_remove_tag(
        self,
        mock_show: MagicMock,
        mock_menu: MagicMock,
    ) -> None:
        """Test removing a tag."""
        mock_menu.return_value = None  # constructor requires terminal, not availabe in CI.
        mock_show.return_value = 3  # Where a choice is returned from the menu

        tags = TagTable()
        tags.set_tags(ORIGINAL, {"artist": ["artist 1", "artist 2"]})
        repeat = tag_editor.ask_for_other_action(tags, "artist")

        self.assertFalse(repeat)
        self.assertEqual(["[Removed]"], tags.resolved.get("artist"))
        self.assertEqual(["artist 1", "artist 2"], tags.values_from(ORIGINAL, "artist"))

    @patch("simple_term_menu.TerminalMenu.__init__")
    @patch("simple_term_menu.TerminalMenu.show")
    def test_ask_for_other_action_select(
        self,
        mock_show: MagicMock,
        mock_menu: MagicMock,
    ) -> None:
        """Test selecting tag from list."""
        mock_menu.return_value = None  # constructor requires terminal, not availabe in CI.

        tags = TagTable()
        tags.set_tags(ORIGINAL, {"artist": ["artist 1, artist 2"]})
        tags.set_youtube_tags({"artist": ["artist 1", "artist 2"]}, is_auto_generated=True)

        mock_show.side_effect = [0, 0]  # Second menu
        repeat = tag_editor.ask_for_other_action(tags, "artist")

        self.assertFalse(repeat)
        self.assertEqual(["artist 1"], tags.resolved.get("artist"))

        mock_show.side_effect = [0, 2]  # Second menu
        repeat = tag_editor.ask_for_other_action(tags, "artist")

        self.assertFalse(repeat)
        self.assertEqual(["artist 1, artist 2"], tags.resolved.get("artist"))

        mock_show.side_effect = [0, 1]  # Second menu
        repeat = tag_editor.ask_for_other_action(tags, "artist")

        self.assertFalse(repeat)
        self.assertEqual(["artist 2"], tags.resolved.get("artist"))

        mock_show.side_effect = [0, [0, 1]]  # Second menu
        repeat = tag_editor.ask_for_other_action(tags, "artist")

        self.assertFalse(repeat)
        self.assertEqual(["artist 1", "artist 2"], tags.resolved.get("artist"))

        mock_show.side_effect = [0, None]  # Second menu
        repeat = tag_editor.ask_for_other_action(tags, "artist")
        captured = self.capsys.readouterr()

        self.assertTrue(repeat)
        self.assertEqual(["artist 1", "artist 2"], tags.resolved.get("artist"))
        self.assertEqual("Invalid choice, try again\n", captured.out)

    def test_resolve_tags_defaults_positive(self) -> None:
        """Test defaults taken from any source when lacking other data.

        When there is no original data and there aren't multiple
        sources of new data, we can just use the one we found since
        there is no alternative. The user can manually change it later
        if they want.
        """
        # Parsed from description
        tags = TagTable()
        tags.set_youtube_tags({"artist": ["artist 1"]}, is_auto_generated=True)

        tag_editor.resolve_tags(tags)
        captured = self.capsys.readouterr()
        self.assertEqual(["artist 1"], tags.resolved.get("artist"))
        self.assertEqual(
            "Artist: No value exists in metadata. Using auto-generated YouTube description: ['artist 1'].\n",
            captured.out,
        )

        # Parsed from description tags
        tags = TagTable()
        tags.set_tags(PARSED_FROM_YOUTUBE, {"artist": ["artist 1"]})

        tag_editor.resolve_tags(tags)
        captured = self.capsys.readouterr()
        self.assertEqual(["artist 1"], tags.resolved.get("artist"))
        self.assertEqual(
            "Artist: No value exists in metadata. Using tags parsed from YouTube tags: ['artist 1'].\n",
            captured.out,
        )

    def test_resolve_tags_defaults_negative(self) -> None:
        """Test no defaults taken when no good data exists.

        There shouldn't be any tags parsed from original tags when there
        are no original tags. And if there just are no tags, nothing
        should happen.
        """
        # No tags at all
        tags = TagTable()

        tag_editor.resolve_tags(tags)
        self.assertEqual({}, tags.resolved)

        # Parsed from original tags
        tags = TagTable()

        tags.set_tags(PARSED_FROM_ORIGINAL, {"artist": ["artist 1"]})
        tag_editor.resolve_tags(tags)
        self.assertEqual({"artist": ["artist 1"]}, tags.resolved)

    def test_resolve_tags_keeps_pruned_tag_removed(self) -> None:
        """Test that a pruned tag isn't restored by a matching source.

        If the YouTube description has the same value as a tag that has
        been pruned, resolving shouldn't set the tag back to that value.
        """
        tags = TagTable()
        tags.set_tags(ORIGINAL, {"artist": ["Junk Artist"], "albumartist": ["Junk Artist"]})
        tags.resolved = {"artist": ["[Removed]"], "albumartist": ["[Removed]"]}
        tags.set_youtube_tags({"artist": ["Junk Artist"], "albumartist": ["Junk Artist"]}, is_auto_generated=True)

        tag_editor.resolve_tags(tags)
        self.assertEqual({"artist": ["[Removed]"], "albumartist": ["[Removed]"]}, tags.resolved)

    @patch("simple_term_menu.TerminalMenu.__init__")
    @patch("simple_term_menu.TerminalMenu.show")
    def test_resolve_tags_replaces_pruned_tag_with_new_value(self, mock_show: MagicMock, mock_init: MagicMock) -> None:
        """Test that a pruned tag can be replaced by a different value.

        Choosing the original value of a pruned tag, here for the album
        artist, should still result in the tag being removed.
        """
        mock_init.return_value = None
        # Choose "YouTube description" for artist, then "Junk Artist" as
        # album artist
        mock_show.side_effect = [0, 1]
        tags = TagTable()
        tags.set_tags(ORIGINAL, {"artist": ["Junk Artist"], "albumartist": ["Junk Artist"]})
        tags.resolved = {"artist": ["[Removed]"], "albumartist": ["[Removed]"]}
        tags.set_youtube_tags({"artist": ["Real Artist"]}, is_auto_generated=True)

        tag_editor.resolve_tags(tags)
        self.assertEqual(["Real Artist"], tags.resolved.get("artist"))
        self.assertEqual(["[Removed]"], tags.resolved.get("albumartist"))

    def test_resolve_tags_empty_tag(self) -> None:
        """Test that empty tags in original tags are skipped."""
        # Parsed from description
        tags = TagTable()
        tags.set_tags(ORIGINAL, {"artist": ["artist 1"], "title": []})

        tag_editor.resolve_tags(tags)
        captured = self.capsys.readouterr()
        print(tags.resolved)
        self.assertNotIn("artist", tags.resolved)  # No need to resolve
        self.assertEqual(["artist 1"], tags.values_from(ORIGINAL, "artist"))
        self.assertEqual(captured, ("", ""))

    def test_resolve_tags_equal_when_stripped(self) -> None:
        """Test that new metadata autoresolves when equal when stripped.

        If a new source differs from the original only in that one of
        them has some extra whitespace, remove the whitespace and use
        that value.
        """
        # Youtube
        tags = TagTable()
        tags.set_tags(ORIGINAL, {"artist": ["artist 1"]})
        tags.set_youtube_tags({"artist": ["artist 1 "]}, is_auto_generated=True)

        tag_editor.resolve_tags(tags)
        captured = self.capsys.readouterr()
        self.assertEqual(["artist 1"], tags.resolved.get("artist"))
        self.assertEqual(
            "Artist: Metadata matches auto-generated YouTube description.\n",
            captured.out,
        )

        # Parsed from description
        tags = TagTable()
        tags.set_tags(ORIGINAL, {"artist": ["artist 1"]})
        tags.set_tags(PARSED_FROM_YOUTUBE, {"artist": ["artist 1 "]})

        tag_editor.resolve_tags(tags)
        captured = self.capsys.readouterr()
        self.assertEqual(["artist 1"], tags.resolved.get("artist"))
        self.assertEqual(
            "Artist: Metadata matches tags parsed from YouTube tags.\n",
            captured.out,
        )

        # Parsed from original tags
        tags = TagTable()
        tags.set_tags(ORIGINAL, {"artist": ["artist 1"]})
        tags.set_tags(PARSED_FROM_ORIGINAL, {"artist": ["artist 1 "]})

        tag_editor.resolve_tags(tags)
        captured = self.capsys.readouterr()
        self.assertEqual(["artist 1"], tags.resolved.get("artist"))
        self.assertEqual(
            "Artist: Metadata matches tags parsed from original tags.\n",
            captured.out,
        )

    @patch("simple_term_menu.TerminalMenu.__init__")
    @patch("simple_term_menu.TerminalMenu.show")
    def test_resolve_tags_print_all_sources(self, mock_show: MagicMock, mock_menu: MagicMock) -> None:
        """Test printing available new metadata."""
        mock_show.return_value = 0  # Where a choice is returned from the menu
        mock_menu.return_value = None  # constructor requires terminal, not availabe in CI.

        tags = TagTable()
        tags.set_tags(ORIGINAL, {"artist": ["artist 1"]})
        tags.set_youtube_tags({"artist": ["artist 2"]}, is_auto_generated=True)
        tags.set_tags(PARSED_FROM_YOUTUBE, {"artist": ["artist 2"]})
        tags.set_tags(PARSED_FROM_ORIGINAL, {"artist": ["artist 2"]})

        tag_editor.resolve_tags(tags)
        captured = self.capsys.readouterr()
        self.assertEqual(
            (
                "-----------------------------------------------\n"
                "  Title: Not found\n"
                "  Album: Not found\n"
                "  Album Artist: Not found\n"
                "  Artist(s): artist 2 | artist 2 | artist 2 | artist 1\n"
                "  Date: Not found\n"
                "  Genre: Not found\n"
                "  Version: Not found\n"
                "  Performer: Not found\n"
                "  Organization: Not found\n"
                "  Copyright: Not found\n"
                "  Composer: Not found\n"
                "  Conductor: Not found\n"
                "  Arranger: Not found\n"
                "  Author: Not found\n"
                "  Producer: Not found\n"
                "  Publisher: Not found\n"
                "  Lyricist: Not found\n"
                "  Writer: Not found\n\n"
                "Artist: Mismatch between values in description and metadata:\n"
                "Auto-generated YouTube description: artist 2\n"
                "Tags parsed from original tags: artist 2\n"
                "Tags parsed from YouTube tags: artist 2\n"
                "Existing metadata: artist 1\n"
            ),
            captured.out,
        )

    @patch("simple_term_menu.TerminalMenu.__init__")
    @patch("simple_term_menu.TerminalMenu.show")
    def test_resolve_tags_do_not_print_lines_for_empty_source(self, mock_show: MagicMock, mock_menu: MagicMock) -> None:
        """Test that empty sources don't get printed."""
        mock_show.return_value = 0  # Where a choice is returned from the menu
        mock_menu.return_value = None  # constructor requires terminal, not availabe in CI.

        # With only youtube
        tags_only_youtube = TagTable()
        tags_only_youtube.set_tags(ORIGINAL, {"artist": ["artist 1"]})
        tags_only_youtube.set_youtube_tags({"artist": ["artist 2"]}, is_auto_generated=True)

        tag_editor.resolve_tags(tags_only_youtube)
        captured = self.capsys.readouterr()
        self.assertEqual(
            (
                "-----------------------------------------------\n"
                "  Title: Not found\n"
                "  Album: Not found\n"
                "  Album Artist: Not found\n"
                "  Artist(s): artist 2 | artist 1\n"
                "  Date: Not found\n"
                "  Genre: Not found\n"
                "  Version: Not found\n"
                "  Performer: Not found\n"
                "  Organization: Not found\n"
                "  Copyright: Not found\n"
                "  Composer: Not found\n"
                "  Conductor: Not found\n"
                "  Arranger: Not found\n"
                "  Author: Not found\n"
                "  Producer: Not found\n"
                "  Publisher: Not found\n"
                "  Lyricist: Not found\n"
                "  Writer: Not found\n\n"
                "Artist: Mismatch between values in description and metadata:\n"
                "Auto-generated YouTube description: artist 2\n"
                "Existing metadata: artist 1\n"
            ),
            captured.out,
        )

        # With only from youtube tags
        tags_only_parsed_from_youtube = TagTable()
        tags_only_parsed_from_youtube.set_tags(ORIGINAL, {"artist": ["artist 1"]})
        tags_only_parsed_from_youtube.set_tags(PARSED_FROM_YOUTUBE, {"artist": ["artist 2"]})

        tag_editor.resolve_tags(tags_only_parsed_from_youtube)
        captured = self.capsys.readouterr()
        self.assertEqual(
            (
                "-----------------------------------------------\n"
                "  Title: Not found\n"
                "  Album: Not found\n"
                "  Album Artist: Not found\n"
                "  Artist(s): artist 2 | artist 1\n"
                "  Date: Not found\n"
                "  Genre: Not found\n"
                "  Version: Not found\n"
                "  Performer: Not found\n"
                "  Organization: Not found\n"
                "  Copyright: Not found\n"
                "  Composer: Not found\n"
                "  Conductor: Not found\n"
                "  Arranger: Not found\n"
                "  Author: Not found\n"
                "  Producer: Not found\n"
                "  Publisher: Not found\n"
                "  Lyricist: Not found\n"
                "  Writer: Not found\n\n"
                "Artist: Mismatch between values in description and metadata:\n"
                "Tags parsed from YouTube tags: artist 2\n"
                "Existing metadata: artist 1\n"
            ),
            captured.out,
        )

    @patch("simple_term_menu.TerminalMenu.__init__")
    @patch("simple_term_menu.TerminalMenu.show")
    def test_resolve_tags_skip_song(self, mock_show: MagicMock, mock_menu: MagicMock) -> None:
        """Test skipping a song when resolving metadata.

        There are two ways. Either pressing escape, which returns None
        from the menu, or selecting 'Quit'
        """
        mock_show.return_value = None  # Where a choice is returned from the menu
        mock_menu.return_value = None  # constructor requires terminal, not availabe in CI.

        tags = TagTable()
        tags.set_tags(ORIGINAL, {"artist": ["artist 1"]})
        tags.set_youtube_tags({"artist": ["artist 2"]}, is_auto_generated=True)
        tags.set_tags(PARSED_FROM_YOUTUBE, {"artist": ["artist 2"]})
        tags.set_tags(PARSED_FROM_ORIGINAL, {"artist": ["artist 2"]})

        with self.assertRaisesRegex(UserExitException, "Skipping this and all later songs"):
            tag_editor.resolve_tags(tags)

        captured = self.capsys.readouterr()
        self.assertEqual(
            (
                "-----------------------------------------------\n"
                "  Title: Not found\n"
                "  Album: Not found\n"
                "  Album Artist: Not found\n"
                "  Artist(s): artist 2 | artist 2 | artist 2 | artist 1\n"
                "  Date: Not found\n"
                "  Genre: Not found\n"
                "  Version: Not found\n"
                "  Performer: Not found\n"
                "  Organization: Not found\n"
                "  Copyright: Not found\n"
                "  Composer: Not found\n"
                "  Conductor: Not found\n"
                "  Arranger: Not found\n"
                "  Author: Not found\n"
                "  Producer: Not found\n"
                "  Publisher: Not found\n"
                "  Lyricist: Not found\n"
                "  Writer: Not found\n\n"
                "Artist: Mismatch between values in description and metadata:\n"
                "Auto-generated YouTube description: artist 2\n"
                "Tags parsed from original tags: artist 2\n"
                "Tags parsed from YouTube tags: artist 2\n"
                "Existing metadata: artist 1\n"
            ),
            captured.out,
        )

        mock_show.return_value = 5  # Where a choice is returned from the menu
        with self.assertRaisesRegex(UserExitException, "Skipping this and all later songs"):
            tag_editor.resolve_tags(tags)

        captured = self.capsys.readouterr()
        self.assertEqual(
            (
                "-----------------------------------------------\n"
                "  Title: Not found\n"
                "  Album: Not found\n"
                "  Album Artist: Not found\n"
                "  Artist(s): artist 2 | artist 2 | artist 2 | artist 1\n"
                "  Date: Not found\n"
                "  Genre: Not found\n"
                "  Version: Not found\n"
                "  Performer: Not found\n"
                "  Organization: Not found\n"
                "  Copyright: Not found\n"
                "  Composer: Not found\n"
                "  Conductor: Not found\n"
                "  Arranger: Not found\n"
                "  Author: Not found\n"
                "  Producer: Not found\n"
                "  Publisher: Not found\n"
                "  Lyricist: Not found\n"
                "  Writer: Not found\n\n"
                "Artist: Mismatch between values in description and metadata:\n"
                "Auto-generated YouTube description: artist 2\n"
                "Tags parsed from original tags: artist 2\n"
                "Tags parsed from YouTube tags: artist 2\n"
                "Existing metadata: artist 1\n"
            ),
            captured.out,
        )

    @patch("retag_opus.tag_editor.ask_for_other_action")
    @patch("simple_term_menu.TerminalMenu.__init__")
    @patch("simple_term_menu.TerminalMenu.show")
    def test_resolve_tags_other_action(
        self, mock_show: MagicMock, mock_menu: MagicMock, mock_manual_adjust: MagicMock
    ) -> None:
        """Test the "other action" function is called when requested."""
        mock_menu.return_value = None  # constructor requires terminal, not availabe in CI.
        mock_show.return_value = 4  # Where a choice is returned from the menu

        # The "other action" function
        mock_manual_adjust.return_value = False

        tags = TagTable()
        tags.set_tags(ORIGINAL, {"artist": ["artist 1"]})
        tags.set_youtube_tags({"artist": ["artist 2"]}, is_auto_generated=True)
        tags.set_tags(PARSED_FROM_YOUTUBE, {"artist": ["artist 2"]})
        tags.set_tags(PARSED_FROM_ORIGINAL, {"artist": ["artist 2"]})

        tag_editor.resolve_tags(tags)

        mock_manual_adjust.assert_called_once()

    @patch("simple_term_menu.TerminalMenu.__init__")
    @patch("simple_term_menu.TerminalMenu.show")
    def test_resolve_tags_choosing_source(self, mock_show: MagicMock, mock_menu: MagicMock) -> None:
        """Test choosing the source to use when resolving."""
        mock_menu.return_value = None  # constructor requires terminal, not availabe in CI.

        tags_youtube = TagTable()
        tags_youtube.set_tags(ORIGINAL, {"artist": ["artist 1"]})
        tags_youtube.set_youtube_tags({"artist": ["artist 2"]}, is_auto_generated=True)
        tags_youtube.set_tags(PARSED_FROM_YOUTUBE, {"artist": ["artist 3"]})
        tags_youtube.set_tags(PARSED_FROM_ORIGINAL, {"artist": ["artist 4"]})

        mock_show.return_value = 0  # Youtube is first in list
        tag_editor.resolve_tags(tags_youtube)
        self.assertEqual(["artist 2"], tags_youtube.resolved.get("artist"))

        tags_fromtags = TagTable()
        tags_fromtags.set_tags(ORIGINAL, {"artist": ["artist 1"]})
        tags_fromtags.set_youtube_tags({"artist": ["artist 2"]}, is_auto_generated=True)
        tags_fromtags.set_tags(PARSED_FROM_YOUTUBE, {"artist": ["artist 3"]})
        tags_fromtags.set_tags(PARSED_FROM_ORIGINAL, {"artist": ["artist 4"]})

        mock_show.return_value = 1  # Parsed from original tags is second in list
        tag_editor.resolve_tags(tags_fromtags)
        self.assertEqual(["artist 4"], tags_fromtags.resolved.get("artist"))

        tags_original = TagTable()
        tags_original.set_tags(ORIGINAL, {"artist": ["artist 1"]})
        tags_original.set_youtube_tags({"artist": ["artist 2"]}, is_auto_generated=True)
        tags_original.set_tags(PARSED_FROM_YOUTUBE, {"artist": ["artist 3"]})
        tags_original.set_tags(PARSED_FROM_ORIGINAL, {"artist": ["artist 4"]})

        mock_show.return_value = 3  # Existing metadata is after the other sources
        tag_editor.resolve_tags(tags_original)
        self.assertEqual(["artist 1"], tags_original.resolved.get("artist"))

        tags_fromdesc = TagTable()
        tags_fromdesc.set_tags(ORIGINAL, {"artist": ["artist 1"]})
        tags_fromdesc.set_youtube_tags({"artist": ["artist 2"]}, is_auto_generated=True)
        tags_fromdesc.set_tags(PARSED_FROM_YOUTUBE, {"artist": ["artist 3"]})
        tags_fromdesc.set_tags(PARSED_FROM_ORIGINAL, {"artist": ["artist 4"]})

        mock_show.return_value = 2  # Parsed from YouTube tags is third in list
        tag_editor.resolve_tags(tags_fromdesc)
        self.assertEqual(["artist 3"], tags_fromdesc.resolved.get("artist"))

    @patch("simple_term_menu.TerminalMenu.__init__")
    @patch("simple_term_menu.TerminalMenu.show")
    def test_resolve_tags_keeps_album_artist_a_source_agrees_with(
        self,
        mock_show: MagicMock,
        mock_menu: MagicMock,
    ) -> None:
        """Test the album artist of a song with several artists.

        The album artist is resolved like other tags, so the existing
        one is kept when a source has the same, however many artists
        the song has.
        """
        mock_menu.return_value = None  # constructor requires terminal, not availabe in CI.

        tags = TagTable()
        tags.set_tags(ORIGINAL, {"artist": ["Singer", "Other Singer"], "albumartist": ["Singer"]})
        tags.set_youtube_tags({"artist": ["Singer", "Other Singer"], "albumartist": ["Singer"]}, is_auto_generated=True)

        tag_editor.resolve_tags(tags)

        mock_show.assert_not_called()
        self.assertEqual(["Singer"], tags.resolved.get("albumartist"))

    def test_resolve_tags_fills_album_artist(self) -> None:
        """Test that a missing album artist is taken from a source."""
        tags = TagTable()
        tags.set_tags(ORIGINAL, {"artist": ["Singer", "Other Singer"]})
        tags.set_youtube_tags({"artist": ["Singer", "Other Singer"], "albumartist": ["Singer"]}, is_auto_generated=True)

        tag_editor.resolve_tags(tags)

        self.assertEqual(["Singer"], tags.resolved.get("albumartist"))

    @patch("simple_term_menu.TerminalMenu.__init__")
    @patch("simple_term_menu.TerminalMenu.show")
    def test_resolve_tags_asks_about_album_artist_no_source_agrees_with(
        self,
        mock_show: MagicMock,
        mock_menu: MagicMock,
    ) -> None:
        """Test choosing an album artist when no source has the file's.

        E.g. the existing album artist has two values, which earlier
        versions could set, and the choices are the album artists of
        the sources, one value each.
        """
        mock_menu.return_value = None  # constructor requires terminal, not availabe in CI.
        mock_show.return_value = 0  # YouTube description

        tags = TagTable()
        tags.set_tags(ORIGINAL, {"artist": ["Singer", "Other Singer"], "albumartist": ["Singer", "Other Singer"]})
        tags.set_youtube_tags({"artist": ["Singer", "Other Singer"], "albumartist": ["Singer"]}, is_auto_generated=True)
        tags.set_tags(MUSICBRAINZ, {"albumartist": ["Singer & Other Singer"]})

        tag_editor.resolve_tags(tags)

        mock_show.assert_called_once()
        self.assertEqual(["Singer"], tags.resolved.get("albumartist"))

    @patch("simple_term_menu.TerminalMenu.__init__")
    @patch("simple_term_menu.TerminalMenu.show")
    def test_resolve_tags_album_tags(
        self,
        mock_show: MagicMock,
        mock_menu: MagicMock,
    ) -> None:
        """Test not asking about an earlier song's album level tags.

        Album level tags chosen for an earlier song on the same album
        should be used even if they differ from the sources, and only
        the other tags should be asked about.
        """
        mock_menu.return_value = None  # constructor requires terminal, not availabe in CI.
        mock_show.side_effect = [0]  # Youtube artist

        tags = TagTable()
        tags.set_tags(ORIGINAL, {"artist": ["artist 1"], "genre": ["genre 1"]})
        tags.set_youtube_tags(
            {
                "artist": ["artist 2", "artist 3"],
                "album": ["album 1"],
                "date": ["2020-01-01"],
            },
            is_auto_generated=True,
        )
        tags.set_tags(PARSED_FROM_ORIGINAL, {"genre": ["genre 1", "Instrumental"]})
        tags.resolved = deepcopy(tags.tags_from(ORIGINAL))
        tags.apply_album_level_tags(
            {"albumartist": ["artist 3"], "genre": ["genre 2"], "album": ["Album 1"], "date": ["2019-01-01"]}
        )

        tag_editor.resolve_tags(tags)

        mock_show.assert_called_once()
        self.assertEqual(["artist 2", "artist 3"], tags.resolved.get("artist"))
        self.assertEqual(["artist 3"], tags.resolved.get("albumartist"))
        self.assertEqual(["genre 2"], tags.resolved.get("genre"))
        self.assertEqual(["Album 1"], tags.resolved.get("album"))
        self.assertEqual(["2019-01-01"], tags.resolved.get("date"))

    @patch("retag_opus.tag_editor.ask_for_other_action")
    @patch("simple_term_menu.TerminalMenu.__init__")
    @patch("simple_term_menu.TerminalMenu.show")
    def test_resolve_tags_looping(
        self,
        mock_show: MagicMock,
        mock_menu: MagicMock,
        mock_manual_adjust: MagicMock,
    ) -> None:
        """Test that looping works when resolving.

        When first choosing other action, a loop should happen. This is
        tested by first mocking a choice of 'other action', and only
        after that an exit. Even though exit is not chosen the first
        time, we still exit because the menu is presented again.
        """
        mock_menu.return_value = None  # constructor requires terminal, not availabe in CI.
        mock_show.side_effect = [2, 3]  # Youtube artist in both cases

        # The "other action" function
        mock_manual_adjust.return_value = True

        tags = TagTable()
        tags.set_tags(ORIGINAL, {"artist": ["artist 1"]})
        tags.set_youtube_tags({"artist": ["artist 2"]}, is_auto_generated=True)

        with self.assertRaisesRegex(UserExitException, "Skipping this and all later songs"):
            tag_editor.resolve_tags(tags)


class TestMusicBrainzSource(unittest.TestCase):
    """Test showing and choosing MusicBrainz's tags."""

    @pytest.fixture(autouse=True)
    def store_capsys(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Store capsys, since unittest methods can't take fixtures."""
        self.capsys = capsys

    def test_styled_values_from_all_sources_includes_musicbrainz(self) -> None:
        """Test that MusicBrainz values are shown when they're new."""
        tags = TagTable()
        tags.set_tags(ORIGINAL, {"artist": ["artist 1"], "title": ["title 1"]})
        tags.set_tags(MUSICBRAINZ, {"artist": ["artist 2"], "title": ["title 1"]})
        self.assertEqual(
            ["artist 2", "artist 1"],
            tag_editor.styled_values_from_all_sources(tags, "artist"),
        )
        self.assertEqual(["title 1"], tag_editor.styled_values_from_all_sources(tags, "title"))

    def test_resolve_tags_uses_musicbrainz_last(self) -> None:
        """Test that MusicBrainz fills tags no other source has.

        Where the sources agree, the value from the YouTube description
        is used, as it's written there.
        """
        tags = TagTable()
        tags.set_youtube_tags({"title": ["title 1"]}, is_auto_generated=True)
        tags.set_tags(MUSICBRAINZ, {"title": ["Title 1"], "tracknumber": ["3"]})
        tag_editor.resolve_tags(tags)
        self.assertEqual({"title": ["title 1"], "tracknumber": ["3"]}, tags.resolved)

    @patch("simple_term_menu.TerminalMenu.__init__")
    @patch("simple_term_menu.TerminalMenu.show")
    def test_resolve_tags_asks_when_sources_disagree(self, mock_show: MagicMock, mock_menu: MagicMock) -> None:
        """Test choosing a missing value the sources disagree on."""
        mock_show.return_value = 1  # MusicBrainz
        mock_menu.return_value = None
        tags = TagTable()
        tags.set_youtube_tags({"albumartist": ["Jane Paknia"]}, is_auto_generated=True)
        tags.set_tags(MUSICBRAINZ, {"albumartist": ["Jane Paknia & Hagop Tchaparian"]})
        tag_editor.resolve_tags(tags)
        mock_show.assert_called_once()
        self.assertEqual(["Jane Paknia & Hagop Tchaparian"], tags.resolved["albumartist"])

    @patch("simple_term_menu.TerminalMenu.__init__")
    @patch("simple_term_menu.TerminalMenu.show")
    def test_resolve_tags_prefers_musicbrainz_to_uploader_description(
        self, mock_show: MagicMock, mock_menu: MagicMock
    ) -> None:
        """Test where MusicBrainz is in the order of preference.

        It comes after an auto-generated description, but before one
        that the uploader wrote.
        """
        mock_show.return_value = 0
        mock_menu.return_value = None
        tags = TagTable()
        youtube_tags = {"title": ["Song (Official Video)"], "album": ["Don't Go"]}
        tags.set_youtube_tags(youtube_tags, is_auto_generated=False)
        tags.set_tags(PARSED_FROM_YOUTUBE, {"title": ["Song (Official)"]})
        tags.set_tags(MUSICBRAINZ, {"title": ["Song"], "album": ["Don’t Go"]})

        tag_editor.resolve_tags(tags)

        self.assertEqual(
            [
                "MusicBrainz",
                "Uploader's YouTube description",
                "Tags parsed from YouTube tags",
                "Existing metadata",
                "Other action",
                "Quit",
            ],
            mock_menu.call_args.args[0],
        )
        self.assertEqual(["Song"], tags.resolved["title"])
        # Where the sources agree, MusicBrainz's value is used
        self.assertEqual(["Don’t Go"], tags.resolved["album"])

        tags.set_youtube_tags(youtube_tags, is_auto_generated=True)
        tag_editor.resolve_tags(tags)
        self.assertEqual(
            [
                "Auto-generated YouTube description",
                "Tags parsed from YouTube tags",
                "MusicBrainz",
                "Existing metadata",
                "Other action",
                "Quit",
            ],
            mock_menu.call_args.args[0],
        )
        self.assertEqual(["Song (Official Video)"], tags.resolved["title"])
        self.assertEqual(["Don't Go"], tags.resolved["album"])

    def test_resolve_tags_matches_musicbrainz_regardless_of_typography(self) -> None:
        """Test that MusicBrainz typography doesn't cause a conflict."""
        tags = TagTable()
        tags.set_tags(ORIGINAL, {"title": ["Don't Go"]})
        tags.set_tags(MUSICBRAINZ, {"title": ["Don’t Go"]})
        tag_editor.resolve_tags(tags)
        self.assertEqual(["Don't Go"], tags.resolved["title"])
        out = self.capsys.readouterr().out
        self.assertEqual("Title: Metadata matches MusicBrainz.\n", out)

    @patch("simple_term_menu.TerminalMenu.__init__")
    @patch("simple_term_menu.TerminalMenu.show")
    def test_resolve_tags_offers_musicbrainz(self, mock_show: MagicMock, mock_menu: MagicMock) -> None:
        """Test that MusicBrainz is a choice, in its own typography."""
        mock_show.return_value = 1  # MusicBrainz
        mock_menu.return_value = None
        tags = TagTable()
        tags.set_tags(ORIGINAL, {"title": ["Dont Go"]})
        tags.set_youtube_tags({"title": ["Don't Go"]}, is_auto_generated=True)
        tags.set_tags(MUSICBRAINZ, {"title": ["Don’t Go"]})

        tag_editor.resolve_tags(tags)

        out = self.capsys.readouterr().out
        self.assertIn("MusicBrainz: Don’t Go\n", out)
        self.assertEqual(
            ["Auto-generated YouTube description", "MusicBrainz", "Existing metadata", "Other action", "Quit"],
            mock_menu.call_args.args[0],
        )
        self.assertEqual(["Don’t Go"], tags.resolved["title"])

    def test_resolve_tags_sets_musicbrainz_ids_and_numbers_quietly(self) -> None:
        """Test that tags from the match are set without messages."""
        tags = TagTable()
        tags.set_tags(ORIGINAL, {"musicbrainz_trackid": ["old id"], "tracknumber": ["2"]})
        tags.set_tags(
            MUSICBRAINZ,
            {
                "musicbrainz_trackid": ["new id"],
                "musicbrainz_albumid": ["album id"],
                "tracknumber": ["2"],
                "totaltracks": ["12"],
            },
        )
        tag_editor.resolve_tags(tags)
        self.assertEqual(["new id"], tags.resolved["musicbrainz_trackid"])
        self.assertEqual(["album id"], tags.resolved["musicbrainz_albumid"])
        self.assertEqual(["12"], tags.resolved["totaltracks"])
        out = self.capsys.readouterr().out
        self.assertEqual("Tracknumber: Metadata matches MusicBrainz.\n", out)

    def test_print_resolved_tags_hides_musicbrainz_ids(self) -> None:
        """Test printing track numbers but not MusicBrainz IDs."""
        tags = TagTable()
        tags.resolved = {"musicbrainz_trackid": ["id"], "tracknumber": ["2"]}
        tag_editor.print_resolved_tags(tags)
        out = self.capsys.readouterr().out
        self.assertIn("tracknumber", out)
        self.assertNotIn("musicbrainz_trackid", out)

    @patch("simple_term_menu.TerminalMenu.__init__")
    @patch("simple_term_menu.TerminalMenu.show")
    def test_resolve_tags_asks_about_other_release(self, mock_show: MagicMock, mock_menu: MagicMock) -> None:
        """Test asking for the album when MusicBrainz differs."""
        mock_show.return_value = 1  # MusicBrainz
        mock_menu.return_value = None
        tags = TagTable()
        tags.set_tags(ORIGINAL, {"album": ["Single"]})
        tags.resolved = {"album": ["Single"]}
        tags.set_youtube_tags({"album": ["Single"]}, is_auto_generated=True)
        tags.set_tags(MUSICBRAINZ, {"album": ["Album"], "tracknumber": ["5"]})
        tag_editor.resolve_tags(tags)
        self.assertEqual(
            ["Auto-generated YouTube description", "MusicBrainz", "Existing metadata", "Other action", "Quit"],
            mock_menu.call_args.args[0],
        )
        self.assertEqual(["Album"], tags.resolved["album"])
        self.assertEqual(["5"], tags.resolved["tracknumber"])

        tags = TagTable()
        tags.set_youtube_tags({"album": ["Single"]}, is_auto_generated=True)
        tags.set_tags(MUSICBRAINZ, {"album": ["Album"]})
        tag_editor.resolve_tags(tags)
        self.assertEqual(["Album"], tags.resolved["album"])

    @patch("simple_term_menu.TerminalMenu.__init__")
    @patch("simple_term_menu.TerminalMenu.show")
    def test_resolve_tags_keeps_release_tags_consistent(self, mock_show: MagicMock, mock_menu: MagicMock) -> None:
        """Test that release tags aren't used for another release."""
        mock_show.return_value = 2  # Existing metadata
        mock_menu.return_value = None
        tags = TagTable()
        tags.set_tags(ORIGINAL, {"album": ["Single"], "totaltracks": ["1"]})
        tags.resolved = {"album": ["Single"], "totaltracks": ["1"]}
        tags.set_youtube_tags({"album": ["Single"]}, is_auto_generated=True)
        tags.set_tags(
            MUSICBRAINZ,
            {
                "album": ["Album"],
                "tracknumber": ["5"],
                "totaltracks": ["10"],
                "musicbrainz_albumid": ["album id"],
                "musicbrainz_trackid": ["track id"],
            },
        )
        tag_editor.resolve_tags(tags)
        self.assertEqual(["Single"], tags.resolved["album"])
        self.assertEqual(["1"], tags.resolved["totaltracks"])
        self.assertNotIn("tracknumber", tags.resolved)
        self.assertNotIn("musicbrainz_albumid", tags.resolved)
        self.assertEqual(["track id"], tags.resolved["musicbrainz_trackid"])

    @patch("simple_term_menu.TerminalMenu.__init__")
    @patch("simple_term_menu.TerminalMenu.show")
    def test_resolve_tags_keeps_release_tags_of_same_album(self, mock_show: MagicMock, mock_menu: MagicMock) -> None:
        """Test keeping release tags if the album is the release.

        That's so even if the album's name has a note like "Remastered".
        """
        mock_show.return_value = 0  # The album as written in the YouTube description
        mock_menu.return_value = None
        tags = TagTable()
        tags.set_youtube_tags({"album": ["Album (2011 Remaster)"]}, is_auto_generated=True)
        tags.set_tags(MUSICBRAINZ, {"album": ["album"], "tracknumber": ["5"]})
        tag_editor.resolve_tags(tags)
        self.assertEqual(["5"], tags.resolved["tracknumber"])


@patch.dict(os.environ, {"FORCE_COLOR": "1", "NO_COLOR": ""})
class TestTagEditorColors(unittest.TestCase):
    """Test that tags are printed in a style telling what they are."""

    @pytest.fixture(autouse=True)
    def store_capsys(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Store capsys, since unittest methods can't take fixtures."""
        self.capsys = capsys

    def test_styled_values_from_all_sources_styles_sources(self) -> None:
        """Test that each source of a tag has its own style."""
        tags = TagTable()
        tags.set_tags(ORIGINAL, {"artist": ["artist 1"]})
        tags.set_youtube_tags({"artist": ["artist 2"]}, is_auto_generated=True)
        tags.set_tags(PARSED_FROM_ORIGINAL, {"artist": ["artist 3"]})
        tags.set_tags(PARSED_FROM_YOUTUBE, {"artist": ["artist 4"]})
        tags.set_tags(MUSICBRAINZ, {"artist": ["artist 5"]})
        expected = [
            styles.youtube("artist 2"),
            styles.parsed_from_original("artist 3"),
            styles.parsed_from_youtube("artist 4"),
            styles.musicbrainz("artist 5"),
            styles.original("artist 1"),
        ]
        self.assertListEqual(expected, tag_editor.styled_values_from_all_sources(tags, "artist"))

    def test_print_resolved_tags_styles_changes(self) -> None:
        """Test styling changed, removed, unchanged and unset tags."""
        tags = TagTable()
        tags.set_tags(ORIGINAL, {"artist": ["artist 1"], "title": ["title 1"], "producer": ["someone"]})
        tags.resolved = {"artist": ["artist 1"], "title": ["title 2"], "producer": ["[Removed]"]}
        tag_editor.print_resolved_tags(tags, with_all_sources=False)
        lines = self.capsys.readouterr().out.split("\n")
        self.assertIn("  Title: " + styles.changed("title 2"), lines)
        self.assertIn("  Artist(s): " + styles.original("artist 1"), lines)
        self.assertIn("  Producer (Removed): " + styles.removed("someone"), lines)
        self.assertIn("  Album: " + styles.unset("Not found"), lines)

    def test_print_all_sources_styles_unset_tags(self) -> None:
        """Test that tags no source has a value for look unset."""
        tags = TagTable()
        tags.set_tags(ORIGINAL, {"artist": ["artist 1"]})
        tag_editor.print_all_sources(tags)
        lines = self.capsys.readouterr().out.split("\n")
        self.assertIn("Artist(s): " + styles.original("artist 1"), lines)
        self.assertIn("Title: " + styles.unset("Not set"), lines)
