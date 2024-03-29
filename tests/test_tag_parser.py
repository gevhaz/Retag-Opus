"""Tests for tags_parser.py."""
import unittest

import pytest

from retag_opus.tags_parser import TagsParser


class TestTagsParser(unittest.TestCase):
    """Test the TagsParser class."""

    @pytest.fixture(autouse=True)
    def capsys(self, capsys) -> None:  # type: ignore
        """Fixture for capturing system output."""
        self.capsys = capsys  # type: ignore

    def test_clean_original_tags_no_change(self) -> None:
        """Test basic case of cleaning original tags.

        There are tags to parse, but they are already okay so new
        "from tags" tags should be set.
        """
        original_tags = {
            "artist": ["artist 1", "artist 2"],
            "albumartist": ["artist 1"],
            "title": ["title of song"],
            "album": ["album name"],
            "genre": ["Rock", "Pop", "Alternative", "Jazz"],
        }
        tag_parser = TagsParser(original_tags)
        tag_parser.parse_tags()
        tag_parser.split_select_original_tags()
        self.assertEqual(0, len(tag_parser.tags))

    def test_clean_original_tags_split_tags(self) -> None:
        """Test that tags are split only when it's the right tags."""
        original_tags = {
            "artist": ["artist 1, artist 2"],
            "genre": ["genre 1; genre 2"],
            "album": ["album, with a comma in it"],
            "title": ["title, with a comma in it"],
        }

        tags_parser = TagsParser(original_tags)
        tags_parser.split_select_original_tags()
        self.assertEqual(["artist 1", "artist 2"], tags_parser.tags.get("artist"))
        self.assertEqual(["genre 1", "genre 2"], tags_parser.tags.get("genre"))
        self.assertNotIn("album", tags_parser.tags)
        self.assertNotIn("title", tags_parser.tags)

    def test_clean_original_tags_already_split(self) -> None:
        """Test not setting split tags when not needed.

        If the relevant tags are already split or if they don't need to
        be split, they should not be treated as new tags parsed from
        oringinal tags.
        """
        original_tags = {
            "artist": ["artist 1", "artist 2"],
            "genre": ["only genre"],
        }

        tags_parser = TagsParser(original_tags)
        tags_parser.split_select_original_tags()
        self.assertNotIn("artist", tags_parser.tags)
        self.assertNotIn("genre", tags_parser.tags)

    def test_parse_tags_featuring(self) -> None:
        """Test parsing featuring artists."""
        titles = [
            "title featuring artist name",
            "title feat artist name",
            "title feat. artist name",
            "title Ft. artist name",
            "title Featuring artist name",
            "title Feat artist name",
            "title FEAT. artist name",
            "title ft. artist name",
            "title (featuring artist name) more text",
            "title (feat artist name) more text",
            "title (feat. artist name) more text",
            "title (ft. artist name) more text",
            "title [featuring artist name] more text",
            "title [feat artist name] more text",
            "title [feat. artist name] more text",
            "title [ft. artist name] more text",
        ]

        for title in titles:
            tags_parser = TagsParser({"title": [title]})
            tags_parser.tags = {}  # Make sure no tags remain and ruin tests
            tags_parser.parse_tags()
            self.assertEqual(["artist name"], tags_parser.tags.get("artist"))

    def test_parse_tags_featuring_artist_in_addition_to_existing(self) -> None:
        """Test adding featuring artist to existing artist."""
        tags_parser = TagsParser(
            {
                "title": ["Song name (ft. Third Artist)"],
                "artist": ["First Artist, Second Artist"],
            },
        )
        tags_parser.tags = {}  # Make sure no tags remain and ruin tests
        tags_parser.parse_tags()
        self.assertEqual(["First Artist", "Second Artist", "Third Artist"], tags_parser.tags.get("artist"))
        self.assertEqual(["Song name"], tags_parser.tags.get("title"))

    def test_parse_tags_albumversion(self) -> None:
        """Test parsing "Album version" data."""
        titles = [
            "title of a Song (Album Version)",
            "title of a Song [Album Version]",
        ]

        for title in titles:
            tags_parser = TagsParser({"title": [title]})
            tags_parser.tags = {}  # Make sure no tags remain and ruin tests
            tags_parser.parse_tags()
            self.assertEqual(["Album Version"], tags_parser.tags.get("version"))
            self.assertEqual(["title of a Song"], tags_parser.tags.get("title"))

    def test_parse_tags_live(self) -> None:
        """Test parsing live version."""
        titles = [
            "title (live at the famous arena)",
            "title [live at the famous arena]",
        ]

        for title in titles:
            tags_parser = TagsParser({"title": [title]})
            tags_parser.tags = {}  # Make sure no tags remain and ruin tests
            tags_parser.parse_tags()
            self.assertEqual(["live at the famous arena"], tags_parser.tags.get("version"))

        tags_parser = TagsParser({"title": ["title (Live at the famous arena)"]})
        tags_parser.tags = {}  # Make sure no tags remain and ruin tests
        tags_parser.parse_tags()
        self.assertEqual(["Live at the famous arena"], tags_parser.tags.get("version"))

        tags_parser = TagsParser({"title": ["Song (Live)"]})
        tags_parser.tags = {}  # Make sure no tags remain and ruin tests
        tags_parser.parse_tags()
        self.assertEqual(["Live"], tags_parser.tags.get("version"))

        tags_parser = TagsParser({"title": ["Wing [Live: Paris, 2001]"]})
        tags_parser.tags = {}  # Make sure no tags remain and ruin tests
        tags_parser.parse_tags()
        self.assertEqual(["Live: Paris, 2001"], tags_parser.tags.get("version"))

    def test_parse_tags_remaster(self) -> None:
        """Test parsing remaster version."""
        test_cases = [
            {
                "original_title": "Song name (Remastered)",
                "expected_version": "Remastered",
            },
            {
                "original_title": "Song name [Remastered]",
                "expected_version": "Remastered",
            },
            {
                "original_title": "Song name (2007 Remaster)",
                "expected_version": "2007 Remaster",
            },
            {
                "original_title": "Song name (Remastered Version)",
                "expected_version": "Remastered Version",
            },
            {
                "original_title": "Song name (Remastered 2015)",
                "expected_version": "Remastered 2015",
            },
            {
                "original_title": "Song name - remastered 2005",
                "expected_version": "remastered 2005",
            },
            {
                "original_title": "Song name - Remastered 2005",
                "expected_version": "Remastered 2005",
            },
            {
                "original_title": "Song name - 1999 - Remaster",
                "expected_version": "1999 - Remaster",
            },
            {
                "original_title": "Song name - Remastered",
                "expected_version": "Remastered",
            },
        ]

        for test_case in test_cases:
            tags_parser = TagsParser({"title": [test_case["original_title"]]})
            tags_parser.tags = {}  # Make sure no tags remain and ruin tests
            tags_parser.parse_tags()
            self.assertEqual([test_case["expected_version"]], tags_parser.tags.get("version"))
            self.assertEqual(["Song name"], tags_parser.tags.get("title"))

        tags_parser = TagsParser({"title": ["Song name (With another paretheses) (1996 Remastered Version)"]})
        tags_parser.tags = {}  # Make sure no tags remain and ruin tests
        tags_parser.parse_tags()
        self.assertEqual(["1996 Remastered Version"], tags_parser.tags.get("version"))
        self.assertEqual(["Song name (With another paretheses)"], tags_parser.tags.get("title"))

    def test_parse_tags_instrumental(self) -> None:
        """Test parsing instrumental version."""
        tags_parser = TagsParser({"title": ["Song name (instrumental)"]})
        tags_parser.tags = {}  # Make sure no tags remain and ruin tests
        tags_parser.parse_tags()
        self.assertEqual(["Instrumental"], tags_parser.tags.get("genre"))
        self.assertEqual(["Song name"], tags_parser.tags.get("title"))

        tags_parser = TagsParser({"title": ["Song name (Instrumental)"]})
        tags_parser.tags = {}  # Make sure no tags remain and ruin tests
        tags_parser.parse_tags()
        self.assertEqual(["Instrumental"], tags_parser.tags.get("genre"))
        self.assertEqual(["Song name"], tags_parser.tags.get("title"))

        tags_parser = TagsParser({"title": ["Song name [Instrumental]"]})
        tags_parser.tags = {}  # Make sure no tags remain and ruin tests
        tags_parser.parse_tags()
        self.assertEqual(["Instrumental"], tags_parser.tags.get("genre"))
        self.assertEqual(["Song name"], tags_parser.tags.get("title"))

        tags_parser = TagsParser({"title": ["Song name (continued) [Extended Instrumental Version]"]})
        tags_parser.tags = {}  # Make sure no tags remain and ruin tests
        tags_parser.parse_tags()
        self.assertEqual(["Instrumental"], tags_parser.tags.get("genre"))
        self.assertEqual(["Song name (continued)"], tags_parser.tags.get("title"))

    def test_parse_tags_instrumental_and_keep_old_genre(self) -> None:
        """Test that old genres are kept when parsing instrumental."""
        tags_parser = TagsParser({"title": ["Song name (instrumental)"], "genre": ["Rock"]})
        tags_parser.tags = {}
        tags_parser.parse_tags()
        self.assertEqual(["Rock", "Instrumental"], tags_parser.tags.get("genre"))
        self.assertEqual(["Song name"], tags_parser.tags.get("title"))

    def test_parse_tags_remix(self) -> None:
        """Test parsing songs as remixed."""
        tags_parser = TagsParser({"title": ["Song name (Artist Remix)"]})
        tags_parser.tags = {}
        tags_parser.parse_tags()
        self.assertEqual(["Artist Remix"], tags_parser.tags.get("version"))
        self.assertEqual(["Song name"], tags_parser.tags.get("title"))

        tags_parser = TagsParser({"title": ["Song name (Remix) [feat. Second Artist]"]})
        tags_parser.tags = {}
        tags_parser.parse_tags()
        self.assertEqual(["Remix"], tags_parser.tags.get("version"))
        self.assertEqual(["Song name"], tags_parser.tags.get("title"))
        self.assertEqual(["Second Artist"], tags_parser.tags.get("artist"))

        tags_parser = TagsParser({"title": ["Song name - Second Artist Remix"]})
        tags_parser.tags = {}
        tags_parser.parse_tags()
        self.assertEqual(["Second Artist Remix"], tags_parser.tags.get("version"))
        self.assertEqual(["Song name"], tags_parser.tags.get("title"))

        tags_parser = TagsParser({"title": ["Song name Remix"]})
        tags_parser.tags = {}
        tags_parser.parse_tags()
        self.assertNotIn("version", tags_parser.tags)
        self.assertNotIn("title", tags_parser.tags)

        tags_parser = TagsParser({"title": ["Song name (Artist remix)"]})
        tags_parser.tags = {}
        tags_parser.parse_tags()
        self.assertEqual(["Artist remix"], tags_parser.tags.get("version"))
        self.assertEqual(["Song name"], tags_parser.tags.get("title"))

    def test_parse_tags_of_multiple_types(self) -> None:
        """Test parsing tags of multiple types.

        Test that when there is multiple sources of information in a
        song title, all the data is used to prune the title and append
        to the correct tag.
        """
        tags_parser = TagsParser({"title": ["Song name (Artist Remix) (instrumental)"]})
        tags_parser.tags = {}
        tags_parser.parse_tags()
        self.assertEqual(["Artist Remix"], tags_parser.tags.get("version"))
        self.assertEqual(["Song name"], tags_parser.tags.get("title"))
        self.assertEqual(["Instrumental"], tags_parser.tags.get("genre"))

        tags_parser = TagsParser({"title": ["Song name (instrumental) (Artist Remix) "]})
        tags_parser.tags = {}
        tags_parser.parse_tags()
        self.assertEqual(["Artist Remix"], tags_parser.tags.get("version"))
        self.assertEqual(["Song name"], tags_parser.tags.get("title"))
        self.assertEqual(["Instrumental"], tags_parser.tags.get("genre"))

        tags_parser = TagsParser({"title": ["Song name (instrumental) (Live at famous arena) "]})
        tags_parser.tags = {}
        tags_parser.parse_tags()
        self.assertEqual(["Live at famous arena"], tags_parser.tags.get("version"))
        self.assertEqual(["Song name"], tags_parser.tags.get("title"))
        self.assertEqual(["Instrumental"], tags_parser.tags.get("genre"))

        tags_parser = TagsParser({"title": ["Song name (Artist remix) (Live at famous arena) "]})
        tags_parser.tags = {}
        tags_parser.parse_tags()
        self.assertEqual(["Live at famous arena", "Artist remix"], tags_parser.tags.get("version"))
        self.assertEqual(["Song name"], tags_parser.tags.get("title"))

        tags_parser = TagsParser({"title": ["Song name (Artist remix) (Live at famous arena) ft. Second Artist"]})
        tags_parser.tags = {}
        tags_parser.parse_tags()
        self.assertEqual(["Live at famous arena", "Artist remix"], tags_parser.tags.get("version"))
        self.assertEqual(["Song name"], tags_parser.tags.get("title"))
        self.assertEqual(["Second Artist"], tags_parser.tags.get("artist"))

        tags_parser = TagsParser({"title": ["Song name ft. Second Artist (Artist remix) (Live at famous arena) "]})
        tags_parser.tags = {}
        tags_parser.parse_tags()
        self.assertEqual(["Live at famous arena", "Artist remix"], tags_parser.tags.get("version"))
        self.assertEqual(["Song name"], tags_parser.tags.get("title"))
        self.assertEqual(["Second Artist"], tags_parser.tags.get("artist"))

        tags_parser = TagsParser({"title": ["Song name (Artist remix) (Live at famous arena) (2022 remaster)"]})
        tags_parser.tags = {}
        tags_parser.parse_tags()
        self.assertEqual(["Live at famous arena", "Artist remix", "2022 remaster"], tags_parser.tags.get("version"))
        self.assertEqual(["Song name"], tags_parser.tags.get("title"))

    def test_parse_tags_no_title(self) -> None:
        """Test that everything works fine with no title."""
        tags_parser = TagsParser({"artist": ["artist 1, artist 2"]})
        tags_parser.parse_tags()
        self.assertNotIn("title", tags_parser.tags)
        self.assertNotIn("artist", tags_parser.tags)
