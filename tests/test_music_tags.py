"""Tests for music_tags.py."""

import os
import sys
import unittest
from copy import deepcopy
from unittest.mock import MagicMock, patch

import pytest

from retag_opus import styles
from retag_opus.exceptions import UserExitException
from retag_opus.music_tags import MUSICBRAINZ, ORIGINAL, PARSED_FROM_ORIGINAL, PARSED_FROM_YOUTUBE, YOUTUBE, MusicTags

Tags = dict[str, list[str]]


class TestMusicTags(unittest.TestCase):
    """Test the MusicTags class."""

    @pytest.fixture(autouse=True)
    def capsys(self, capsys) -> None:  # type: ignore
        """Fixture for capturing system output."""
        self.capsys = capsys  # type: ignore

    def test_print_metadata_key(self) -> None:
        """Test printing of a single metadata key."""
        tags: Tags = {"artist": ["artist 1", "artist 2"], "title": ["title 1", "title 2"]}
        MusicTags().print_metadata_key("Artist", "artist", styles.original, tags)
        captured = self.capsys.readouterr()  # type: ignore
        self.assertEqual("  Artist: artist 1 | artist 2\n", captured.out)

    def test_print_metadata(self) -> None:
        """Test printing of metadata."""
        tags: Tags = {"artist": ["artist 1", "artist 2"], "title": ["title 1", "title 2"]}
        MusicTags().print_metadata(tags, styles.original)
        captured = self.capsys.readouterr()  # type: ignore
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

    def test_print_metadata_with_performers(self) -> None:
        """Test printing of metadata where there are performer tags."""
        tags: Tags = {"artist": ["artist 1", "artist 2"], "performer:lead vocals": ["bassist 1"]}
        MusicTags().print_metadata(tags, styles.original)
        captured = self.capsys.readouterr()  # type: ignore
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

    def test_print_metadata_with_performer_tags_without_pattern(self) -> None:
        """Test printing of performer tags that can't be parsed from descriptions.

        They're printed after the ones that can, in alphabetical order.
        """
        tags: Tags = {
            "artist": ["artist 1", "artist 2"],
            "performer:theremin": ["person 1"],
            "performer:accordion": ["person 2"],
            "performer:violin": ["person 3"],
        }
        MusicTags().print_metadata(tags, styles.original)
        captured = self.capsys.readouterr()  # type: ignore
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

    def test_get_colored_values_from_all_sources_one_source(self) -> None:
        """Test getting tags from one source."""
        tags = MusicTags()
        tags.set_tags(ORIGINAL, {"artist": ["artist 1"]})
        actual = tags.get_colored_values_from_all_sources("artist")
        expected = ["artist 1"]
        self.assertListEqual(expected, actual)

    def test_get_colored_values_from_all_sources_two_sources(self) -> None:
        """Test getting tags from two source."""
        tags = MusicTags()
        tags.set_tags(ORIGINAL, {"artist": ["artist 1"]})
        tags.set_tags(YOUTUBE, {"artist": ["artist 2"]})
        actual = tags.get_colored_values_from_all_sources("artist")
        expected = ["artist 2", "artist 1"]
        self.assertListEqual(expected, actual)

    def test_get_colored_values_from_all_sources_two_overlapping_sources(self) -> None:
        """Test get tags from two sources where a value is in both."""
        tags = MusicTags()
        tags.set_tags(ORIGINAL, {"artist": ["artist 1"]})
        tags.set_tags(YOUTUBE, {"artist": ["artist 1", "artist 2"]})
        actual = tags.get_colored_values_from_all_sources("artist")
        expected = ["artist 1 | artist 2", "artist 1"]
        self.assertListEqual(expected, actual)

    def test_get_colored_values_from_all_sources_no_values(self) -> None:
        """Test getting tags from one source."""
        tags = MusicTags()
        actual = tags.get_colored_values_from_all_sources("artist")
        expected: list[str] = []
        self.assertListEqual(expected, actual)

    def test_get_colored_values_from_all_sources_all_sources(self) -> None:
        """Test getting tags from two source."""
        tags = MusicTags()
        tags.set_tags(ORIGINAL, {"artist": ["artist 1"]})
        tags.set_tags(YOUTUBE, {"artist": ["artist 2"]})
        tags.set_tags(PARSED_FROM_ORIGINAL, {"artist": ["artist 3"]})
        tags.set_tags(PARSED_FROM_YOUTUBE, {"artist": ["artist 4"]})
        actual = tags.get_colored_values_from_all_sources("artist")
        expected = [
            "artist 2",
            "artist 3",
            "artist 4",
            "artist 1",
        ]
        self.assertListEqual(expected, actual)

    def test_print_all(self) -> None:
        """Test printing the combined metadata of all sources."""
        tags = MusicTags()
        tags.set_tags(ORIGINAL, {"artist": ["artist 1"]})
        tags.set_tags(YOUTUBE, {"artist": ["artist 2"]})
        tags.set_tags(PARSED_FROM_ORIGINAL, {"artist": ["artist 3"]})
        tags.set_tags(PARSED_FROM_YOUTUBE, {"artist": ["artist 4"]})
        tags.print_all()
        captured = self.capsys.readouterr()  # type: ignore
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

    def test_print_all_with_performers(self) -> None:
        """Test printing combined data when there are performer tags."""
        tags = MusicTags()
        tags.set_tags(ORIGINAL, {"artist": ["artist 1"]})
        tags.set_tags(YOUTUBE, {"artist": ["artist 2"]})
        tags.set_tags(PARSED_FROM_ORIGINAL, {"artist": ["artist 3"]})
        tags.set_tags(PARSED_FROM_YOUTUBE, {"performer:lead vocals": ["artist 4"]})
        tags.print_all()
        captured = self.capsys.readouterr()  # type: ignore
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

    def test_print_all_with_no_data(self) -> None:
        """Test printing the combined metadata of all sources."""
        tags = MusicTags()
        tags.print_all()
        captured = self.capsys.readouterr()  # type: ignore
        expected = "There's no data to be printed\n"
        self.assertEqual(expected, captured.out)

    def test_print_youtube(self) -> None:
        """Test printing data from youtube tags."""
        tags = MusicTags()
        tags.set_tags(ORIGINAL, {"artist": ["artist 1"]})
        tags.set_tags(YOUTUBE, {"artist": ["artist 2"], "performer:lead vocals": ["artist 5"]})
        tags.set_tags(PARSED_FROM_ORIGINAL, {"artist": ["artist 3"]})
        tags.set_tags(PARSED_FROM_YOUTUBE, {"performer:lead vocals": ["artist 4"]})
        tags.print_youtube()
        captured = self.capsys.readouterr()  # type: ignore
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

    def test_print_youtube_no_data(self) -> None:
        """Test printing data from youtube tags when there are none."""
        tags = MusicTags()
        tags.set_tags(ORIGINAL, {"artist": ["artist 1"]})
        tags.set_tags(PARSED_FROM_ORIGINAL, {"artist": ["artist 3"]})
        tags.set_tags(PARSED_FROM_YOUTUBE, {"performer:lead vocals": ["artist 4"]})
        tags.print_youtube()
        captured = self.capsys.readouterr()  # type: ignore
        expected = "No new data parsed from description\n"
        self.assertEqual(expected, captured.out)

    def test_print_resolved(self) -> None:
        """Test that resolved tags can be printed."""
        tags = MusicTags()
        tags.set_tags(ORIGINAL, {"artist": ["artist 1"], "title": ["title 1"], "producer": ["someone"]})
        tags.resolved = {"artist": ["artist 1"], "title": ["title 2"], "producer": ["[Removed]"]}
        tags.print_resolved(print_all=False)
        captured = self.capsys.readouterr()  # type: ignore
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

    def test_print_resolved_with_performers(self) -> None:
        """Test that resolved tags print, including performers."""
        tags = MusicTags()
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
        tags.print_resolved(print_all=False)
        captured = self.capsys.readouterr()  # type: ignore
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

    def test_print_resolved_with_performer_tags_without_pattern(self) -> None:
        """Test that all performer tags are printed as performers.

        Performer tags that can't be parsed from descriptions, e.g. from
        MusicBrainz or with names from older versions, are printed last.
        """
        tags = MusicTags()
        tags.set_tags(ORIGINAL, {"performer:vocals": ["artist 1"]})
        tags.resolved = {"performer:vocals": ["artist 1"], "performer:theremin": ["artist 2"]}
        tags.print_resolved(print_all=False)
        captured = self.capsys.readouterr()  # type: ignore
        self.assertNotIn("Other tags", captured.out)
        expected = "  Performers:\n  - Theremin: artist 2\n  - Vocals: artist 1\n  Title: Not found\n"
        self.assertIn(expected, captured.out)

    def test_print_all_resolved_with_performers(self) -> None:
        """Test that resolved tags print, including performers.

        Test printing of resolved tags with the argument to print all
        set to true.
        """
        tags = MusicTags()
        tags.set_tags(
            ORIGINAL,
            {
                "performer:lead vocals": ["artist 1"],
                "performer:violin": ["artist 1"],
                "performer:guitar": ["artist 3"],
                "performer:keyboard": ["the keyboard master"],
            },
        )
        tags.set_tags(
            YOUTUBE,
            {
                "performer:guitar": ["artist 4"],
            },
        )
        tags.resolved = {
            "performer:lead vocals": ["artist 1"],
            "performer:violin": ["artist 2"],
            "performer:keyboard": ["[Removed]"],
        }
        tags.print_resolved(print_all=True)
        captured = self.capsys.readouterr()  # type: ignore
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

    def test_print_resolved_with_performers_multiple_sources(self) -> None:
        """Test that resolved tags print, including performers.

        Test printing of resolved tags with the argument to print all
        set to false when there are several sources with relevant tags.
        """
        tags = MusicTags()
        tags.set_tags(
            ORIGINAL,
            {
                "performer:lead vocals": ["artist 1"],
                "performer:violin": ["artist 1"],
                "performer:guitar": ["artist 3"],
                "performer:keyboard": ["artist 5"],
            },
        )
        tags.set_tags(
            YOUTUBE,
            {
                "performer:guitar": ["artist 4"],
                "performer:keyboard": ["artist 6"],
            },
        )
        tags.resolved = {
            "performer:lead vocals": ["artist 1"],
            "performer:violin": ["artist 2"],
            "performer:keyboard": ["[Removed]"],
        }
        tags.print_resolved(print_all=False)
        captured = self.capsys.readouterr()  # type: ignore
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

    def test_print_all_resolved_without_performers(self) -> None:
        """Test that resolved tags print, not including performers.

        Test printing of resolved tags with the argument to print all
        set to true.
        """
        tags = MusicTags()
        tags.set_tags(
            ORIGINAL,
            {
                "artist": ["artist 1", "artist 2"],
                "title": ["title 1"],
                "producer": ["person 1"],
                "arranger": ["artist 1"],
            },
        )
        tags.set_tags(
            YOUTUBE,
            {
                "arranger": ["artist 2"],
            },
        )
        tags.resolved = {
            "artist": ["artist 1", "artist 2"],
            "title": ["title 2"],
            "producer": ["[Removed]"],
        }
        tags.print_resolved(print_all=True)
        captured = self.capsys.readouterr()  # type: ignore
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

    def test_print_resolved_without_performers(self) -> None:
        """Test that resolved tags print, not including performers.

        Test printing of resolved tags with the argument to print all
        set to false.
        """
        tags = MusicTags()
        tags.set_tags(
            ORIGINAL,
            {
                "artist": ["artist 1", "artist 2"],
                "title": ["title 1"],
                "producer": ["person 1"],
                "arranger": ["artist 1"],
            },
        )
        tags.set_tags(
            YOUTUBE,
            {
                "arranger": ["artist 2"],
            },
        )
        tags.resolved = {
            "artist": ["artist 1", "artist 2"],
            "title": ["title 2"],
            "producer": ["[Removed]"],
        }
        tags.print_resolved(print_all=False)
        captured = self.capsys.readouterr()  # type: ignore
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

    def test_discard_upload_date_bad_date(self) -> None:
        """Test that bad upload dates are removed."""
        tags = MusicTags()
        tags.set_tags(ORIGINAL, {"date": ["20220202"]})
        tags.discard_upload_date()
        self.assertNotIn("date", tags.tags_from(ORIGINAL))

    def test_discard_upload_date_good_date(self) -> None:
        """Test that good upload dates are not removed."""
        tags = MusicTags()
        tags.set_tags(ORIGINAL, {"date": ["2022-02-02"]})
        tags.discard_upload_date()
        actual_date = tags.tags_from(ORIGINAL).get("date")
        assert actual_date is not None
        self.assertListEqual(["2022-02-02"], actual_date)

    def test_prune_resolved_tags(self) -> None:
        """Test that useless tags are removed."""
        tags_to_delete = [
            "language",
            "compatible_brands",
            "minor_version",
            "major_brand",
            "vendor_id",
        ]
        tags = MusicTags()
        tags.set_tags(
            ORIGINAL,
            {
                "language": ["eng"],
                "compatible_brands": ["a brand"],
                "minor_version": ["The minor version"],
                "major_brand": ["brand"],
                "vendor_id": ["id of the vendor"],
                "date": ["2022-02-02"],
            },
        )
        tags.resolved = {
            "language": ["eng"],
            "compatible_brands": ["a brand"],
            "minor_version": ["The minor version"],
            "major_brand": ["brand"],
            "vendor_id": ["id of the vendor"],
            "date": ["2022-02-02"],
        }
        tags.prune_resolved_tags(tags_to_delete=tags_to_delete, strings_to_delete_tags_based_on=[])
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
        tags.set_tags(ORIGINAL, {"purl": ["youtube.com"]})
        tags.resolved = {"date": ["2022-02-02"]}
        tags.add_source_tag()
        self.assertEqual(2, len(tags.resolved))
        self.assertEqual(["youtube-dl"], tags.resolved.get("comment"))

    def test_preserve_original_comment_when_adding_source(self) -> None:
        """Test that source tag doesn't overwrite."""
        tags = MusicTags()
        tags.set_tags(ORIGINAL, {"comment": ["test"], "purl": ["youtube.com"]})
        tags.resolved = {"date": ["2022-02-02"]}
        tags.add_source_tag()
        self.assertEqual(2, len(tags.resolved))
        self.assertEqual(["test", "youtube-dl"], tags.resolved.get("comment"))

    def test_get_values_from_all_sources_only_new(self) -> None:
        """Test getting data from all new sources for a given tag."""
        tags = MusicTags()
        tags.set_tags(ORIGINAL, {"artist": ["artist 1"]})
        tags.set_tags(YOUTUBE, {"artist": ["artist 2"]})
        tags.set_tags(PARSED_FROM_ORIGINAL, {"artist": ["artist 3"]})
        tags.set_tags(PARSED_FROM_YOUTUBE, {"artist": ["artist 2"]})
        actual_tags = tags.get_values_from_all_sources("artist", only_new=True)
        self.assertEqual(2, len(actual_tags))
        self.assertNotIn("artist 1", actual_tags)
        self.assertIn("artist 2", actual_tags)
        self.assertIn("artist 3", actual_tags)

    def test_get_values_from_all_sources_include_original(self) -> None:
        """Test getting data from all sources for a given tag."""
        tags = MusicTags()
        tags.set_tags(ORIGINAL, {"artist": ["artist 1"]})
        tags.set_tags(YOUTUBE, {"artist": ["artist 2"]})
        tags.set_tags(PARSED_FROM_ORIGINAL, {"artist": ["artist 3"]})
        tags.set_tags(PARSED_FROM_YOUTUBE, {"artist": ["artist 2"]})
        actual_tags = tags.get_values_from_all_sources("artist", only_new=False)
        self.assertEqual(3, len(actual_tags))
        self.assertIn("artist 1", actual_tags)
        self.assertIn("artist 2", actual_tags)
        self.assertIn("artist 3", actual_tags)

    def test_get_values_from_all_sources_that_does_not_exist(self) -> None:
        """Test getting data from all sources for a non-existent tag."""
        tags = MusicTags()
        tags.set_tags(ORIGINAL, {"artist": ["artist 1"]})
        tags.set_tags(YOUTUBE, {"artist": ["artist 2"]})
        tags.set_tags(PARSED_FROM_ORIGINAL, {"artist": ["artist 3"]})
        tags.set_tags(PARSED_FROM_YOUTUBE, {"artist": ["artist 2"]})
        actual_tags = tags.get_values_from_all_sources("title", only_new=False)
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
        tags.set_tags(ORIGINAL, {"artist": ["artist 1"]})
        self.assertFalse(tags.check_any_new_data_exists())

        # Other sources have same value for tag as original
        tags.set_tags(YOUTUBE, {"artist": ["artist 1"]})
        tags.set_tags(PARSED_FROM_ORIGINAL, {"artist": ["artist 1"]})
        tags.set_tags(PARSED_FROM_YOUTUBE, {"artist": ["artist 1"]})
        self.assertFalse(tags.check_any_new_data_exists())

        # There actually are new values for the tag
        tags.set_tags(YOUTUBE, {"artist": ["artist 2"]})
        self.assertTrue(tags.check_any_new_data_exists())
        tags.set_tags(PARSED_FROM_ORIGINAL, {"artist": ["artist 3"]})
        self.assertTrue(tags.check_any_new_data_exists())
        tags.set_tags(PARSED_FROM_YOUTUBE, {"artist": ["artist 2"]})
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
        tags.set_tags(ORIGINAL, {"artist": ["artist 1"]})
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
        tags.resolved = {"artist": ["artist 1"], "performer:lead vocals": ["artist 1", "artist 2"]}
        tags.delete_tag_item()
        self.assertEqual(["artist 1"], tags.resolved.get("performer:lead vocals"))

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
        self.assertEqual("Returning without removing anything\n", captured.out)

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
        self.assertEqual(tags.resolved["artist"], ["[Removed]"])

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
        self.assertEqual("Returning without removing anything\n", captured.out)

    @patch("retag_opus.utils.TerminalMenu.__init__")
    @patch("retag_opus.utils.TerminalMenu.show")
    def test_delete_tag_item_hide_already_removed(self, mock_show: MagicMock, mock_menu: MagicMock) -> None:
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

        tags = MusicTags()
        tags.resolved = {"artist": ["artist 1", "artist 2"], "title": ["[Removed]"]}
        tags.delete_tag_item()
        self.assertEqual(["artist 1", "artist 2"], tags.resolved.get("artist"))
        self.assertEqual(["[Removed]"], tags.resolved.get("title"))
        captured = self.capsys.readouterr()  # type: ignore
        self.assertEqual("Returning without removing anything\n", captured.out)

    @patch("retag_opus.music_tags.input")
    def test_modify_resolved_field(self, mock_input: MagicMock) -> None:
        """Test modifying a field.

        If the user gives a list of artists separated by ' | ', it
        should be split.
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

    @patch("retag_opus.utils.select_single_value")
    def test_determine_album_artist_select_one(self, select_single_value: MagicMock) -> None:
        """Test that album artist can be picked up normally."""
        expected_artist = ["artist 4"]
        select_single_value.return_value = expected_artist
        tags = MusicTags()

        tags.set_tags(ORIGINAL, {"artist": ["artist 1"]})
        tags.set_tags(YOUTUBE, {"artist": ["artist 2"]})
        tags.set_tags(PARSED_FROM_ORIGINAL, {"artist": ["artist 3"]})
        tags.set_tags(PARSED_FROM_YOUTUBE, {"artist": ["artist 4"]})
        tags.determine_album_artist()
        self.assertEqual(expected_artist, tags.resolved.get("albumartist"))

    @patch("retag_opus.utils.select_single_value")
    def test_determine_album_artist_select_two(self, select_single_value: MagicMock) -> None:
        """Test that two album artists can be selected."""
        expected_artist = ["artist 2", "artist 4"]
        select_single_value.return_value = expected_artist
        tags = MusicTags()

        tags.set_tags(ORIGINAL, {"artist": ["artist 1"]})
        tags.set_tags(YOUTUBE, {"artist": ["artist 2"]})
        tags.set_tags(PARSED_FROM_ORIGINAL, {"artist": ["artist 3"]})
        tags.set_tags(PARSED_FROM_YOUTUBE, {"artist": ["artist 4"]})
        tags.determine_album_artist()
        self.assertEqual(expected_artist, tags.resolved.get("albumartist"))

    @patch("retag_opus.utils.select_single_value")
    def test_determine_album_artist_select_zero(self, select_single_value: MagicMock) -> None:
        """Test that no tag is added when nothing is selected."""
        select_single_value.return_value = []
        tags = MusicTags()

        tags.set_tags(ORIGINAL, {"artist": ["artist 1"]})
        tags.set_tags(YOUTUBE, {"artist": ["artist 2"]})
        tags.set_tags(PARSED_FROM_ORIGINAL, {"artist": ["artist 3"]})
        tags.set_tags(PARSED_FROM_YOUTUBE, {"artist": ["artist 4"]})
        tags.determine_album_artist()
        self.assertNotIn("albumartist", tags.resolved)

    @patch("retag_opus.utils.select_single_value")
    def test_determine_album_artist_unsplit_is_candidate(self, select_single_value: MagicMock) -> None:
        """Test that the unsplit album artist is offered with split artists."""
        select_single_value.return_value = ["artist 1 & artist 2"]
        tags = MusicTags()

        tags.set_tags(YOUTUBE, {"artist": ["artist 1", "artist 2"], "albumartist": ["artist 1 & artist 2"]})
        tags.determine_album_artist()
        select_single_value.assert_called_once_with(["artist 1 & artist 2", "artist 1", "artist 2"])
        self.assertEqual(["artist 1 & artist 2"], tags.resolved.get("albumartist"))

    def test_determine_album_artist_only_old_exist(self) -> None:
        """Test that two album artists can be selected.

        When only the original tags have an artist, use that one as
        albumartist without asking.
        """
        tags = MusicTags()

        tags.set_tags(ORIGINAL, {"artist": ["artist 1"]})
        tags.determine_album_artist()
        self.assertEqual(["artist 1"], tags.resolved.get("albumartist"))

    def test_determine_album_artist_old_and_resolved_exist(self) -> None:
        """Test that resolved artist is preferred.

        When resolved artist is found, that should be used.
        """
        tags = MusicTags()

        tags.set_tags(ORIGINAL, {"artist": ["artist 1"]})
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

        tags.set_tags(PARSED_FROM_ORIGINAL, {"artist": ["artist 1"]})
        tags.set_tags(ORIGINAL, {"albumartist": ["artist 2"]})
        tags.determine_album_artist()
        self.assertEqual(None, tags.resolved.get("albumartist"))

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

        mock_input.return_value = "genre 1, genre 2"
        repeat = tags.manually_adjust_tag_when_resolving("genre")

        self.assertFalse(repeat)
        self.assertEqual(["genre 1", "genre 2"], tags.resolved.get("genre"))

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
        tags.set_tags(ORIGINAL, {"artist": ["artist 1", "artist 2"]})
        repeat = tags.manually_adjust_tag_when_resolving("artist")

        self.assertFalse(repeat)
        self.assertEqual(["[Removed]"], tags.resolved.get("artist"))
        self.assertEqual(["artist 1", "artist 2"], tags.values_from(ORIGINAL, "artist"))

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
        tags.set_tags(ORIGINAL, {"artist": ["artist 1, artist 2"]})
        tags.set_tags(YOUTUBE, {"artist": ["artist 1", "artist 2"]})

        mock_show.side_effect = [0, 0]  # Second menu
        repeat = tags.manually_adjust_tag_when_resolving("artist")

        self.assertFalse(repeat)
        self.assertEqual(["artist 1"], tags.resolved.get("artist"))

        mock_show.side_effect = [0, 2]  # Second menu
        repeat = tags.manually_adjust_tag_when_resolving("artist")

        self.assertFalse(repeat)
        self.assertEqual(["artist 1, artist 2"], tags.resolved.get("artist"))

        mock_show.side_effect = [0, 1]  # Second menu
        repeat = tags.manually_adjust_tag_when_resolving("artist")

        self.assertFalse(repeat)
        self.assertEqual(["artist 2"], tags.resolved.get("artist"))

        mock_show.side_effect = [0, [0, 1]]  # Second menu
        repeat = tags.manually_adjust_tag_when_resolving("artist")

        self.assertFalse(repeat)
        self.assertEqual(["artist 1", "artist 2"], tags.resolved.get("artist"))

        mock_show.side_effect = [0, None]  # Second menu
        repeat = tags.manually_adjust_tag_when_resolving("artist")
        captured = self.capsys.readouterr()  # type: ignore

        self.assertTrue(repeat)
        self.assertEqual(["artist 1", "artist 2"], tags.resolved.get("artist"))
        self.assertEqual("Invalid choice, try again\n", captured.out)

    def test_resolve_metadata_defaults_positive(self) -> None:
        """Test defaults taken from any source when lacking other data.

        When there is no original data and there aren't multiple
        sources of new data, we can just use the one we found since
        there is no alternative. The user can manually change it later
        if they want.
        """
        # Parsed from description
        tags = MusicTags()
        tags.set_tags(YOUTUBE, {"artist": ["artist 1"]})

        tags.resolve_metadata()
        captured = self.capsys.readouterr()  # type: ignore
        self.assertEqual(["artist 1"], tags.resolved.get("artist"))
        self.assertEqual(
            "Artist: No value exists in metadata. Using YouTube description: ['artist 1'].\n",
            captured.out,
        )

        # Parsed from description tags
        tags = MusicTags()
        tags.set_tags(PARSED_FROM_YOUTUBE, {"artist": ["artist 1"]})

        tags.resolve_metadata()
        captured = self.capsys.readouterr()  # type: ignore
        self.assertEqual(["artist 1"], tags.resolved.get("artist"))
        self.assertEqual(
            "Artist: No value exists in metadata. Using tags parsed from YouTube tags: ['artist 1'].\n",
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

        tags.set_tags(PARSED_FROM_ORIGINAL, {"artist": ["artist 1"]})
        tags.resolve_metadata()
        self.assertEqual({"artist": ["artist 1"], "albumartist": ["artist 1"]}, tags.resolved)

    def test_resolve_metadata_keeps_pruned_tag_removed(self) -> None:
        """Test that a pruned tag isn't restored by a matching source.

        If the YouTube description has the same value as a tag that has
        been pruned, resolving shouldn't set the tag back to that value.
        """
        tags = MusicTags()
        tags.set_tags(ORIGINAL, {"artist": ["Junk Artist"], "albumartist": ["Junk Artist"]})
        tags.resolved = {"artist": ["[Removed]"], "albumartist": ["[Removed]"]}
        tags.set_tags(YOUTUBE, {"artist": ["Junk Artist"], "albumartist": ["Junk Artist"]})

        tags.resolve_metadata()
        self.assertEqual({"artist": ["[Removed]"], "albumartist": ["[Removed]"]}, tags.resolved)

    @patch("retag_opus.utils.TerminalMenu.__init__")
    @patch("retag_opus.utils.TerminalMenu.show")
    def test_resolve_metadata_replaces_pruned_tag_with_new_value(
        self, mock_show: MagicMock, mock_init: MagicMock
    ) -> None:
        """Test that a pruned tag can be replaced by a different value.

        Choosing the original value of a pruned tag, here for the album
        artist, should still result in the tag being removed.
        """
        mock_init.return_value = None
        # Choose "YouTube description" for artist, then "Junk Artist" as
        # album artist
        mock_show.side_effect = [0, 1]
        tags = MusicTags()
        tags.set_tags(ORIGINAL, {"artist": ["Junk Artist"], "albumartist": ["Junk Artist"]})
        tags.resolved = {"artist": ["[Removed]"], "albumartist": ["[Removed]"]}
        tags.set_tags(YOUTUBE, {"artist": ["Real Artist"]})

        tags.resolve_metadata()
        self.assertEqual(["Real Artist"], tags.resolved.get("artist"))
        self.assertEqual(["[Removed]"], tags.resolved.get("albumartist"))

    def test_resolve_metadata_empty_tag(self) -> None:
        """Test that empty tags in original tags are skipped."""
        # Parsed from description
        tags = MusicTags()
        tags.set_tags(ORIGINAL, {"artist": ["artist 1"], "title": []})

        tags.resolve_metadata()
        captured = self.capsys.readouterr()  # type: ignore
        print(tags.resolved)
        self.assertNotIn("artist", tags.resolved)  # No need to resolve
        self.assertEqual(["artist 1"], tags.values_from(ORIGINAL, "artist"))
        self.assertEqual(captured, ("", ""))

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
        tags.set_tags(ORIGINAL, {"artist": ["artist 1"]})
        tags.set_tags(YOUTUBE, {"artist": ["artist 1 "]})

        tags.resolve_metadata()
        captured = self.capsys.readouterr()  # type: ignore
        self.assertEqual(["artist 1"], tags.resolved.get("artist"))
        self.assertEqual(
            "Artist: Metadata matches YouTube description.\n",
            captured.out,
        )

        # Parsed from description
        tags = MusicTags()
        tags.set_tags(ORIGINAL, {"artist": ["artist 1"]})
        tags.set_tags(PARSED_FROM_YOUTUBE, {"artist": ["artist 1 "]})

        tags.resolve_metadata()
        captured = self.capsys.readouterr()  # type: ignore
        self.assertEqual(["artist 1"], tags.resolved.get("artist"))
        self.assertEqual(
            "Artist: Metadata matches tags parsed from YouTube tags.\n",
            captured.out,
        )

        # Parsed from original tags
        tags = MusicTags()
        tags.set_tags(ORIGINAL, {"artist": ["artist 1"]})
        tags.set_tags(PARSED_FROM_ORIGINAL, {"artist": ["artist 1 "]})

        tags.resolve_metadata()
        captured = self.capsys.readouterr()  # type: ignore
        self.assertEqual(["artist 1"], tags.resolved.get("artist"))
        self.assertEqual(
            "Artist: Metadata matches tags parsed from original tags.\n",
            captured.out,
        )

    @patch("retag_opus.music_tags.MusicTags.determine_album_artist")
    @patch("retag_opus.utils.TerminalMenu.__init__")
    @patch("retag_opus.utils.TerminalMenu.show")
    def test_resolve_metadata_print_all_sources(
        self,
        mock_show: MagicMock,
        mock_menu: MagicMock,
        mock_album_artist: MagicMock,
    ) -> None:
        """Test printing available new metadata."""
        mock_album_artist.return_value = None
        mock_show.return_value = 0  # Where a choice is returned from the menu
        mock_menu.return_value = None  # constructor requires terminal, not availabe in CI.

        tags = MusicTags()
        tags.set_tags(ORIGINAL, {"artist": ["artist 1"]})
        tags.set_tags(YOUTUBE, {"artist": ["artist 2"]})
        tags.set_tags(PARSED_FROM_YOUTUBE, {"artist": ["artist 2"]})
        tags.set_tags(PARSED_FROM_ORIGINAL, {"artist": ["artist 2"]})

        tags.resolve_metadata()
        captured = self.capsys.readouterr()  # type: ignore
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
                "YouTube description: artist 2\n"
                "Tags parsed from original tags: artist 2\n"
                "Tags parsed from YouTube tags: artist 2\n"
                "Existing metadata: artist 1\n"
            ),
            captured.out,
        )

    @patch("retag_opus.music_tags.MusicTags.determine_album_artist")
    @patch("retag_opus.utils.TerminalMenu.__init__")
    @patch("retag_opus.utils.TerminalMenu.show")
    def test_resolve_metadata_do_not_print_lines_for_empty_source(
        self,
        mock_show: MagicMock,
        mock_menu: MagicMock,
        mock_album_artist: MagicMock,
    ) -> None:
        """Test that empty sources don't get printed."""
        mock_album_artist.return_value = None
        mock_show.return_value = 0  # Where a choice is returned from the menu
        mock_menu.return_value = None  # constructor requires terminal, not availabe in CI.

        # With only youtube
        tags_only_youtube = MusicTags()
        tags_only_youtube.set_tags(ORIGINAL, {"artist": ["artist 1"]})
        tags_only_youtube.set_tags(YOUTUBE, {"artist": ["artist 2"]})

        tags_only_youtube.resolve_metadata()
        captured = self.capsys.readouterr()  # type: ignore
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
                "YouTube description: artist 2\n"
                "Existing metadata: artist 1\n"
            ),
            captured.out,
        )

        # With only from youtube tags
        tags_only_parsed_from_youtube = MusicTags()
        tags_only_parsed_from_youtube.set_tags(ORIGINAL, {"artist": ["artist 1"]})
        tags_only_parsed_from_youtube.set_tags(PARSED_FROM_YOUTUBE, {"artist": ["artist 2"]})

        tags_only_parsed_from_youtube.resolve_metadata()
        captured = self.capsys.readouterr()  # type: ignore
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

    @patch("retag_opus.music_tags.MusicTags.determine_album_artist")
    @patch("retag_opus.utils.TerminalMenu.__init__")
    @patch("retag_opus.utils.TerminalMenu.show")
    def test_resolve_metadata_skip_song(
        self,
        mock_show: MagicMock,
        mock_menu: MagicMock,
        mock_album_artist: MagicMock,
    ) -> None:
        """Test skipping a song when resolving metadata.

        There are two ways. Either pressing escape, which returns None
        from the menu, or selecting 'Quit'
        """
        mock_album_artist.return_value = None
        mock_show.return_value = None  # Where a choice is returned from the menu
        mock_menu.return_value = None  # constructor requires terminal, not availabe in CI.

        tags = MusicTags()
        tags.set_tags(ORIGINAL, {"artist": ["artist 1"]})
        tags.set_tags(YOUTUBE, {"artist": ["artist 2"]})
        tags.set_tags(PARSED_FROM_YOUTUBE, {"artist": ["artist 2"]})
        tags.set_tags(PARSED_FROM_ORIGINAL, {"artist": ["artist 2"]})

        with self.assertRaisesRegex(UserExitException, "Skipping this and all later songs"):
            tags.resolve_metadata()

        captured = self.capsys.readouterr()  # type: ignore
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
                "YouTube description: artist 2\n"
                "Tags parsed from original tags: artist 2\n"
                "Tags parsed from YouTube tags: artist 2\n"
                "Existing metadata: artist 1\n"
            ),
            captured.out,
        )

        mock_show.return_value = 5  # Where a choice is returned from the menu
        with self.assertRaisesRegex(UserExitException, "Skipping this and all later songs"):
            tags.resolve_metadata()

        captured = self.capsys.readouterr()  # type: ignore
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
                "YouTube description: artist 2\n"
                "Tags parsed from original tags: artist 2\n"
                "Tags parsed from YouTube tags: artist 2\n"
                "Existing metadata: artist 1\n"
            ),
            captured.out,
        )

    @patch("retag_opus.music_tags.MusicTags.manually_adjust_tag_when_resolving")
    @patch("retag_opus.music_tags.MusicTags.determine_album_artist")
    @patch("retag_opus.utils.TerminalMenu.__init__")
    @patch("retag_opus.utils.TerminalMenu.show")
    def test_resolve_metadata_other_action(
        self,
        mock_show: MagicMock,
        mock_menu: MagicMock,
        mock_album_artist: MagicMock,
        mock_manual_adjust: MagicMock,
    ) -> None:
        """Test the "other action" function is called when requested."""
        mock_album_artist.return_value = None
        mock_menu.return_value = None  # constructor requires terminal, not availabe in CI.
        mock_show.return_value = 4  # Where a choice is returned from the menu

        # The "other action" function
        mock_manual_adjust.return_value = False

        tags = MusicTags()
        tags.set_tags(ORIGINAL, {"artist": ["artist 1"]})
        tags.set_tags(YOUTUBE, {"artist": ["artist 2"]})
        tags.set_tags(PARSED_FROM_YOUTUBE, {"artist": ["artist 2"]})
        tags.set_tags(PARSED_FROM_ORIGINAL, {"artist": ["artist 2"]})

        tags.resolve_metadata()

        mock_manual_adjust.assert_called_once()

    @patch("retag_opus.music_tags.MusicTags.determine_album_artist")
    @patch("retag_opus.utils.TerminalMenu.__init__")
    @patch("retag_opus.utils.TerminalMenu.show")
    def test_resolve_metadata_choosing_source(
        self,
        mock_show: MagicMock,
        mock_menu: MagicMock,
        mock_album_artist: MagicMock,
    ) -> None:
        """Test choosing the source to use when resolving."""
        mock_album_artist.return_value = None
        mock_menu.return_value = None  # constructor requires terminal, not availabe in CI.

        tags_youtube = MusicTags()
        tags_youtube.set_tags(ORIGINAL, {"artist": ["artist 1"]})
        tags_youtube.set_tags(YOUTUBE, {"artist": ["artist 2"]})
        tags_youtube.set_tags(PARSED_FROM_YOUTUBE, {"artist": ["artist 3"]})
        tags_youtube.set_tags(PARSED_FROM_ORIGINAL, {"artist": ["artist 4"]})

        mock_show.return_value = 0  # Youtube is first in list
        tags_youtube.resolve_metadata()
        self.assertEqual(["artist 2"], tags_youtube.resolved.get("artist"))

        tags_fromtags = MusicTags()
        tags_fromtags.set_tags(ORIGINAL, {"artist": ["artist 1"]})
        tags_fromtags.set_tags(YOUTUBE, {"artist": ["artist 2"]})
        tags_fromtags.set_tags(PARSED_FROM_YOUTUBE, {"artist": ["artist 3"]})
        tags_fromtags.set_tags(PARSED_FROM_ORIGINAL, {"artist": ["artist 4"]})

        mock_show.return_value = 1  # Parsed from original tags is second in list
        tags_fromtags.resolve_metadata()
        self.assertEqual(["artist 4"], tags_fromtags.resolved.get("artist"))

        tags_original = MusicTags()
        tags_original.set_tags(ORIGINAL, {"artist": ["artist 1"]})
        tags_original.set_tags(YOUTUBE, {"artist": ["artist 2"]})
        tags_original.set_tags(PARSED_FROM_YOUTUBE, {"artist": ["artist 3"]})
        tags_original.set_tags(PARSED_FROM_ORIGINAL, {"artist": ["artist 4"]})

        mock_show.return_value = 3  # Existing metadata is after the other sources
        tags_original.resolve_metadata()
        self.assertEqual(["artist 1"], tags_original.resolved.get("artist"))

        tags_fromdesc = MusicTags()
        tags_fromdesc.set_tags(ORIGINAL, {"artist": ["artist 1"]})
        tags_fromdesc.set_tags(YOUTUBE, {"artist": ["artist 2"]})
        tags_fromdesc.set_tags(PARSED_FROM_YOUTUBE, {"artist": ["artist 3"]})
        tags_fromdesc.set_tags(PARSED_FROM_ORIGINAL, {"artist": ["artist 4"]})

        mock_show.return_value = 2  # Parsed from YouTube tags is third in list
        tags_fromdesc.resolve_metadata()
        self.assertEqual(["artist 3"], tags_fromdesc.resolved.get("artist"))

    @patch("retag_opus.utils.TerminalMenu.__init__")
    @patch("retag_opus.utils.TerminalMenu.show")
    def test_resolve_metadata_choosing_source_and_album_artist(
        self,
        mock_show: MagicMock,
        mock_menu: MagicMock,
    ) -> None:
        """Test that choosing an artist and then album artist works.

        The album artist should be one of the values for the artist tags
        of the available sources. Test That those show up as
        alternatives when selecting the album artist, and that both tags
        are correct in the end.
        """
        mock_menu.return_value = None  # constructor requires terminal, not availabe in CI.
        mock_show.side_effect = [0, 0]  # Youtube artist in both cases

        tags = MusicTags()
        tags.set_tags(ORIGINAL, {"artist": ["artist 1"]})
        tags.set_tags(YOUTUBE, {"artist": ["artist 2"]})
        tags.set_tags(PARSED_FROM_YOUTUBE, {"artist": ["artist 3"]})

        tags.resolve_metadata()

        self.assertEqual(["artist 2"], tags.resolved.get("artist"))
        self.assertEqual(["artist 2"], tags.resolved.get("albumartist"))

    @patch("retag_opus.utils.TerminalMenu.__init__")
    @patch("retag_opus.utils.TerminalMenu.show")
    def test_resolve_metadata_album_tags(
        self,
        mock_show: MagicMock,
        mock_menu: MagicMock,
    ) -> None:
        """Test that album level tags from an earlier song are not asked about.

        Album level tags chosen for an earlier song on the same album should
        be used even if they differ from the sources, and only the other
        tags should be asked about.
        """
        mock_menu.return_value = None  # constructor requires terminal, not availabe in CI.
        mock_show.side_effect = [0]  # Youtube artist

        tags = MusicTags()
        tags.set_tags(ORIGINAL, {"artist": ["artist 1"], "genre": ["genre 1"]})
        tags.set_tags(
            YOUTUBE,
            {
                "artist": ["artist 2", "artist 3"],
                "album": ["album 1"],
                "date": ["2020-01-01"],
            },
        )
        tags.set_tags(PARSED_FROM_ORIGINAL, {"genre": ["genre 1", "Instrumental"]})
        tags.resolved = deepcopy(tags.tags_from(ORIGINAL))
        tags.apply_album_level_tags(
            {"albumartist": ["artist 3"], "genre": ["genre 2"], "album": ["Album 1"], "date": ["2019-01-01"]}
        )

        tags.resolve_metadata()

        mock_show.assert_called_once()
        self.assertEqual(["artist 2", "artist 3"], tags.resolved.get("artist"))
        self.assertEqual(["artist 3"], tags.resolved.get("albumartist"))
        self.assertEqual(["genre 2"], tags.resolved.get("genre"))
        self.assertEqual(["Album 1"], tags.resolved.get("album"))
        self.assertEqual(["2019-01-01"], tags.resolved.get("date"))

    def test_get_album_level_tags(self) -> None:
        """Test that only set and not removed album level tags are returned."""
        tags = MusicTags()
        tags.resolved = {
            "title": ["title 1"],
            "album": ["album 1"],
            "albumartist": ["artist 1"],
            "genre": ["[Removed]"],
        }
        self.assertEqual({"album": ["album 1"], "albumartist": ["artist 1"]}, tags.get_album_level_tags())

    @patch("retag_opus.music_tags.MusicTags.manually_adjust_tag_when_resolving")
    @patch("retag_opus.utils.TerminalMenu.__init__")
    @patch("retag_opus.utils.TerminalMenu.show")
    def test_resolve_metadata_looping(
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

        tags = MusicTags()
        tags.set_tags(ORIGINAL, {"artist": ["artist 1"]})
        tags.set_tags(YOUTUBE, {"artist": ["artist 2"]})

        with self.assertRaisesRegex(UserExitException, "Skipping this and all later songs"):
            tags.resolve_metadata()

    def test_deleting_specified_tags(self) -> None:
        """Test deleting named tags."""
        delete_these = ["producer"]
        tags = MusicTags()
        tags.set_tags(
            ORIGINAL,
            {
                "artist": ["artist 1"],
                "title": ["title 2"],
                "producer": ["producer 1"],
            },
        )
        tags.resolved = {
            "artist": ["artist 1"],
            "title": ["title 2"],
            "producer": ["producer 1"],
        }
        tags.prune_resolved_tags(tags_to_delete=delete_these, strings_to_delete_tags_based_on=[])
        assert tags.resolved == {
            "artist": ["artist 1"],
            "title": ["title 2"],
            "producer": ["[Removed]"],
        }

    def test_deleting_tags_matching_specified_strings(self) -> None:
        """Test deleting tags matching specified strings."""
        delete_these = ["producer 1"]
        tags = MusicTags()
        tags.set_tags(
            ORIGINAL,
            {
                "artist": ["artist 1"],
                "title": ["title 2"],
                "producer": ["producer 1"],
            },
        )
        tags.resolved = {
            "artist": ["artist 1"],
            "title": ["title 2"],
            "producer": ["producer 1"],
        }
        tags.prune_resolved_tags(tags_to_delete=[], strings_to_delete_tags_based_on=delete_these)
        assert tags.resolved == {
            "artist": ["artist 1"],
            "title": ["title 2"],
            "producer": ["[Removed]"],
        }

    def test_deleting_tags_matching_specified_strings_regex(self) -> None:
        """Test deleting tags matching specified strings."""
        full_match_1 = "pro.*"
        full_match_2 = ".*cer 1"
        tags = MusicTags()
        tags.set_tags(
            ORIGINAL,
            {
                "artist": ["artist 1"],
                "title": ["title 2"],
                "producer": ["producer 1"],
            },
        )
        tags.resolved = {
            "artist": ["artist 1"],
            "title": ["title 2"],
            "producer": ["producer 1"],
        }
        tags.prune_resolved_tags(tags_to_delete=[], strings_to_delete_tags_based_on=[full_match_1])
        assert tags.resolved["producer"] == ["[Removed]"]
        tags.resolved["producer"] = ["producer 1"]
        tags.prune_resolved_tags(tags_to_delete=[], strings_to_delete_tags_based_on=[full_match_2])
        assert tags.resolved["producer"] == ["[Removed]"]

    def test_not_deleting_tags_half_matching_specified_strings(self) -> None:
        """Test deleting tags matching specified strings."""
        half_match_1 = "prod"
        half_match_2 = "ucer 1"
        tags = MusicTags()
        tags.set_tags(
            ORIGINAL,
            {
                "artist": ["artist 1"],
                "title": ["title 2"],
                "producer": ["producer 1"],
            },
        )
        tags.resolved = {
            "artist": ["artist 1"],
            "title": ["title 2"],
            "producer": ["producer 1"],
        }

        tags.prune_resolved_tags(tags_to_delete=[], strings_to_delete_tags_based_on=[half_match_1])
        assert tags.resolved["producer"] == ["producer 1"]

        tags.prune_resolved_tags(tags_to_delete=[], strings_to_delete_tags_based_on=[half_match_2])
        assert tags.resolved["producer"] == ["producer 1"]

    def test_not_deleting_tags_not_in_original(self) -> None:
        """Test deleting tags matching specified strings."""
        no_delete_this_tag = "producer"
        no_delete_this_string = "title 2"
        tags = MusicTags()
        tags.set_tags(
            ORIGINAL,
            {
                "artist": ["artist 1"],
            },
        )
        tags.resolved = {
            "artist": ["artist 1"],
            "title": ["title 2"],
            "producer": ["producer 1"],
        }

        tags.prune_resolved_tags(
            tags_to_delete=[no_delete_this_tag],
            strings_to_delete_tags_based_on=[no_delete_this_string],
        )
        assert tags.resolved == {
            "artist": ["artist 1"],
            "title": ["title 2"],
            "producer": ["producer 1"],
        }

    def test_deleting_tags_despite_not_in_resolved(self) -> None:
        """Test deleting tags that are not among the resolved."""
        delete_this_string = "producer 1"
        delete_this_tag = "title"
        tags = MusicTags()
        tags.set_tags(
            ORIGINAL,
            {
                "artist": ["artist 1"],
                "title": ["title 2"],
                "producer": ["producer 1"],
            },
        )
        tags.resolved = {
            "artist": ["artist 1"],
        }

        tags.prune_resolved_tags(tags_to_delete=[delete_this_tag], strings_to_delete_tags_based_on=[delete_this_string])

        assert tags.resolved == {
            "artist": ["artist 1"],
            "title": ["[Removed]"],
            "producer": ["[Removed]"],
        }


class TestMusicBrainzSource(unittest.TestCase):
    """Test MusicBrainz as a source of tags."""

    @pytest.fixture(autouse=True)
    def capsys(self, capsys) -> None:  # type: ignore
        """Fixture for capturing system output."""
        self.capsys = capsys  # type: ignore

    def test_get_colored_values_from_all_sources_includes_musicbrainz(self) -> None:
        """Test that MusicBrainz values are shown when they're new."""
        tags = MusicTags()
        tags.set_tags(ORIGINAL, {"artist": ["artist 1"], "title": ["title 1"]})
        tags.set_tags(MUSICBRAINZ, {"artist": ["artist 2"], "title": ["title 1"]})
        self.assertEqual(
            ["artist 2", "artist 1"],
            tags.get_colored_values_from_all_sources("artist"),
        )
        self.assertEqual(["title 1"], tags.get_colored_values_from_all_sources("title"))

    def test_get_values_from_all_sources_includes_musicbrainz(self) -> None:
        """Test that MusicBrainz values can be selected."""
        tags = MusicTags()
        tags.set_tags(ORIGINAL, {"artist": ["artist 1"]})
        tags.set_tags(MUSICBRAINZ, {"artist": ["artist 2"]})
        self.assertEqual(["artist 2", "artist 1"], tags.get_values_from_all_sources("artist"))
        self.assertEqual(["artist 2"], tags.get_values_from_all_sources("artist", only_new=True))

    def test_check_any_new_data_exists_in_musicbrainz(self) -> None:
        """Test that tags only MusicBrainz has are new data."""
        tags = MusicTags()
        tags.set_tags(ORIGINAL, {"title": ["title 1"]})
        tags.set_tags(MUSICBRAINZ, {"title": ["title 1"]})
        self.assertFalse(tags.check_any_new_data_exists())
        tags.tags_from(MUSICBRAINZ)["musicbrainz_trackid"] = ["id 1"]
        self.assertTrue(tags.check_any_new_data_exists())

    @patch("retag_opus.music_tags.MusicTags.determine_album_artist")
    def test_resolve_metadata_uses_musicbrainz_last(self, _: MagicMock) -> None:
        """Test that MusicBrainz fills tags no other source has."""
        tags = MusicTags()
        tags.set_tags(YOUTUBE, {"title": ["title 1"]})
        tags.set_tags(MUSICBRAINZ, {"title": ["title 2"], "tracknumber": ["3"]})
        tags.resolve_metadata()
        self.assertEqual({"title": ["title 1"], "tracknumber": ["3"]}, tags.resolved)

    @patch("retag_opus.music_tags.MusicTags.determine_album_artist")
    def test_resolve_metadata_matches_musicbrainz_regardless_of_typography(self, _: MagicMock) -> None:
        """Test that MusicBrainz typography doesn't cause a conflict."""
        tags = MusicTags()
        tags.set_tags(ORIGINAL, {"title": ["Don't Go"]})
        tags.set_tags(MUSICBRAINZ, {"title": ["Don’t Go"]})
        tags.resolve_metadata()
        self.assertEqual(["Don't Go"], tags.resolved["title"])
        out = self.capsys.readouterr().out  # type: ignore
        self.assertEqual("Title: Metadata matches MusicBrainz.\n", out)

    @patch("retag_opus.music_tags.MusicTags.determine_album_artist")
    @patch("retag_opus.utils.TerminalMenu.__init__")
    @patch("retag_opus.utils.TerminalMenu.show")
    def test_resolve_metadata_starts_on_value_musicbrainz_agrees_with(
        self, mock_show: MagicMock, mock_menu: MagicMock, _: MagicMock
    ) -> None:
        """Test that MusicBrainz is an option and hints at the right one."""
        mock_show.return_value = 1  # MusicBrainz
        mock_menu.return_value = None
        tags = MusicTags()
        tags.set_tags(ORIGINAL, {"title": ["Dont Go"]})
        tags.set_tags(YOUTUBE, {"title": ["Don't Go"]})
        tags.set_tags(MUSICBRAINZ, {"title": ["Don’t Go"]})

        tags.resolve_metadata()

        out = self.capsys.readouterr().out  # type: ignore
        self.assertIn("MusicBrainz: Don’t Go\n", out)
        self.assertEqual(
            ["YouTube description", "MusicBrainz", "Existing metadata", "Other action", "Quit"],
            mock_menu.call_args.args[0],
        )
        self.assertEqual(0, mock_menu.call_args.kwargs["cursor_index"])
        self.assertEqual(["Don’t Go"], tags.resolved["title"])

        tags.set_tags(YOUTUBE, {"title": ["Do Go"]})
        tags.set_tags(PARSED_FROM_YOUTUBE, {"title": ["Don't Go"]})
        tags.resolve_metadata()
        self.assertEqual(1, mock_menu.call_args.kwargs["cursor_index"])

        tags.set_tags(MUSICBRAINZ, {"title": ["Something Else"]})
        tags.resolve_metadata()
        self.assertEqual("MusicBrainz", mock_menu.call_args.args[0][mock_menu.call_args.kwargs["cursor_index"]])

    @patch("retag_opus.music_tags.MusicTags.determine_album_artist")
    def test_resolve_metadata_sets_musicbrainz_ids_and_numbers_quietly(self, _: MagicMock) -> None:
        """Test that tags that depend on the match are set without messages."""
        tags = MusicTags()
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
        tags.resolve_metadata()
        self.assertEqual(["new id"], tags.resolved["musicbrainz_trackid"])
        self.assertEqual(["album id"], tags.resolved["musicbrainz_albumid"])
        self.assertEqual(["12"], tags.resolved["totaltracks"])
        out = self.capsys.readouterr().out  # type: ignore
        self.assertEqual("Tracknumber: Metadata matches MusicBrainz.\n", out)

    def test_print_resolved_hides_musicbrainz_ids(self) -> None:
        """Test that MusicBrainz IDs aren't printed, but track numbers are."""
        tags = MusicTags()
        tags.resolved = {"musicbrainz_trackid": ["id"], "tracknumber": ["2"]}
        tags.print_resolved()
        out = self.capsys.readouterr().out  # type: ignore
        self.assertIn("tracknumber", out)
        self.assertNotIn("musicbrainz_trackid", out)

    @patch("retag_opus.music_tags.MusicTags.determine_album_artist")
    @patch("retag_opus.utils.TerminalMenu.__init__")
    @patch("retag_opus.utils.TerminalMenu.show")
    def test_resolve_metadata_asks_about_other_release(
        self, mock_show: MagicMock, mock_menu: MagicMock, _: MagicMock
    ) -> None:
        """Test that the user chooses the album if MusicBrainz found another release."""
        mock_show.return_value = 1  # MusicBrainz
        mock_menu.return_value = None
        tags = MusicTags()
        tags.set_tags(ORIGINAL, {"album": ["Single"]})
        tags.resolved = {"album": ["Single"]}
        tags.set_tags(YOUTUBE, {"album": ["Single"]})
        tags.set_tags(MUSICBRAINZ, {"album": ["Album"], "tracknumber": ["5"]})
        tags.resolve_metadata()
        self.assertEqual(
            ["YouTube description", "MusicBrainz", "Existing metadata", "Other action", "Quit"],
            mock_menu.call_args.args[0],
        )
        self.assertEqual(1, mock_menu.call_args.kwargs["cursor_index"])
        self.assertEqual(["Album"], tags.resolved["album"])
        self.assertEqual(["5"], tags.resolved["tracknumber"])

        tags = MusicTags()
        tags.set_tags(YOUTUBE, {"album": ["Single"]})
        tags.set_tags(MUSICBRAINZ, {"album": ["Album"]})
        tags.resolve_metadata()
        self.assertEqual(["Album"], tags.resolved["album"])

    @patch("retag_opus.music_tags.MusicTags.determine_album_artist")
    @patch("retag_opus.utils.TerminalMenu.__init__")
    @patch("retag_opus.utils.TerminalMenu.show")
    def test_resolve_metadata_keeps_release_tags_consistent(
        self, mock_show: MagicMock, mock_menu: MagicMock, _: MagicMock
    ) -> None:
        """Test that release tags aren't used if the album is another release."""
        mock_show.return_value = 2  # Existing metadata
        mock_menu.return_value = None
        tags = MusicTags()
        tags.set_tags(ORIGINAL, {"album": ["Single"], "totaltracks": ["1"]})
        tags.resolved = {"album": ["Single"], "totaltracks": ["1"]}
        tags.set_tags(YOUTUBE, {"album": ["Single"]})
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
        tags.resolve_metadata()
        self.assertEqual(["Single"], tags.resolved["album"])
        self.assertEqual(["1"], tags.resolved["totaltracks"])
        self.assertNotIn("tracknumber", tags.resolved)
        self.assertNotIn("musicbrainz_albumid", tags.resolved)
        self.assertEqual(["track id"], tags.resolved["musicbrainz_trackid"])

    @patch("retag_opus.music_tags.MusicTags.determine_album_artist")
    def test_resolve_metadata_keeps_release_tags_of_same_album(self, _: MagicMock) -> None:
        """Test that release tags are kept if the album is the release, e.g. remastered."""
        tags = MusicTags()
        tags.set_tags(YOUTUBE, {"album": ["Album (2011 Remaster)"]})
        tags.set_tags(MUSICBRAINZ, {"album": ["album"], "tracknumber": ["5"]})
        tags.resolve_metadata()
        self.assertEqual(["5"], tags.resolved["tracknumber"])


@patch.dict(os.environ, {"FORCE_COLOR": "1", "NO_COLOR": ""})
class TestMusicTagsColors(unittest.TestCase):
    """Test that tags are printed in the style that tells what they are."""

    @pytest.fixture(autouse=True)
    def capsys(self, capsys) -> None:  # type: ignore
        """Fixture for capturing system output."""
        self.capsys = capsys  # type: ignore

    def test_get_colored_values_from_all_sources_styles_sources(self) -> None:
        """Test that each source of a tag has its own style."""
        tags = MusicTags()
        tags.set_tags(ORIGINAL, {"artist": ["artist 1"]})
        tags.set_tags(YOUTUBE, {"artist": ["artist 2"]})
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
        self.assertListEqual(expected, tags.get_colored_values_from_all_sources("artist"))

    def test_print_resolved_styles_changes(self) -> None:
        """Test that changed, removed, unchanged and unset tags are styled."""
        tags = MusicTags()
        tags.set_tags(ORIGINAL, {"artist": ["artist 1"], "title": ["title 1"], "producer": ["someone"]})
        tags.resolved = {"artist": ["artist 1"], "title": ["title 2"], "producer": ["[Removed]"]}
        tags.print_resolved(print_all=False)
        lines = self.capsys.readouterr().out.split("\n")  # type: ignore
        self.assertIn("  Title: " + styles.changed("title 2"), lines)
        self.assertIn("  Artist(s): " + styles.original("artist 1"), lines)
        self.assertIn("  Producer (Removed): " + styles.removed("someone"), lines)
        self.assertIn("  Album: " + styles.unset("Not found"), lines)

    def test_print_all_styles_unset_tags(self) -> None:
        """Test that tags without a value in any source are styled as unset."""
        tags = MusicTags()
        tags.set_tags(ORIGINAL, {"artist": ["artist 1"]})
        tags.print_all()
        lines = self.capsys.readouterr().out.split("\n")  # type: ignore
        self.assertIn("Artist(s): " + styles.original("artist 1"), lines)
        self.assertIn("Title: " + styles.unset("Not set"), lines)
