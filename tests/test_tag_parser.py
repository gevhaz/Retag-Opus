"""Tests for tags_parser.py."""

import unittest

import pytest

from retag_opus import tags_parser


class TestTagsParser(unittest.TestCase):
    """Test parsing tags for metadata that belongs in other tags."""

    @pytest.fixture(autouse=True)
    def store_capsys(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Store capsys, since unittest methods can't take fixtures."""
        self.capsys = capsys

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
        parsed_tags = tags_parser.alternatives(original_tags)
        self.assertEqual(0, len(parsed_tags))

    def test_clean_original_tags_split_tags(self) -> None:
        """Test that tags are split only when it's the right tags."""
        original_tags = {
            "artist": ["artist 1, artist 2"],
            "genre": ["genre 1; genre 2"],
            "album": ["album, with a comma in it"],
            "title": ["title, with a comma in it"],
        }

        parsed_tags = tags_parser.split_artists_and_genres(original_tags)
        self.assertEqual(["artist 1", "artist 2"], parsed_tags.get("artist"))
        self.assertEqual(["genre 1", "genre 2"], parsed_tags.get("genre"))
        self.assertNotIn("album", parsed_tags)
        self.assertNotIn("title", parsed_tags)

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

        parsed_tags = tags_parser.split_artists_and_genres(original_tags)
        self.assertNotIn("artist", parsed_tags)
        self.assertNotIn("genre", parsed_tags)

    def test_parse_titles_featuring(self) -> None:
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
            parsed_tags = tags_parser.parse_titles({"title": [title]})
            self.assertEqual(["artist name"], parsed_tags.get("artist"))

    def test_parse_titles_featuring_artist_in_addition_to_existing(self) -> None:
        """Test adding featuring artist to existing artist."""
        parsed_tags = tags_parser.parse_titles(
            {
                "title": ["Song name (ft. Third Artist)"],
                "artist": ["First Artist, Second Artist"],
            },
        )
        self.assertEqual(["First Artist", "Second Artist", "Third Artist"], parsed_tags.get("artist"))
        self.assertEqual(["Song name"], parsed_tags.get("title"))

    def test_parse_titles_artist_in_title(self) -> None:
        """Test splitting the artist from a video title."""
        parsed_tags = tags_parser.parse_titles(
            {"title": ["Ellen Allien - Love (Official Video)"], "artist": ["Ellen Allien UFO"]}
        )
        self.assertEqual(["Love"], parsed_tags.get("title"))
        self.assertEqual(["Ellen Allien"], parsed_tags.get("artist"))

        parsed_tags = tags_parser.parse_titles(
            {"title": ["B.o.B - Airplanes (feat. Hayley Williams) [Official Video]"], "artist": ["B.o.B"]}
        )
        self.assertEqual(["Airplanes"], parsed_tags.get("title"))
        self.assertEqual(["B.o.B", "Hayley Williams"], parsed_tags.get("artist"))

        parsed_tags = tags_parser.parse_titles(
            {"title": ["Lucia - Karlfeldt & Hazelius"], "artist": ["Annelie Lockneman"]}
        )
        self.assertEqual({}, parsed_tags)

    def test_parse_titles_albumversion(self) -> None:
        """Test parsing "Album version" data."""
        titles = [
            "title of a Song (Album Version)",
            "title of a Song [Album Version]",
        ]

        for title in titles:
            parsed_tags = tags_parser.parse_titles({"title": [title]})
            self.assertEqual(["Album Version"], parsed_tags.get("version"))
            self.assertEqual(["title of a Song"], parsed_tags.get("title"))

    def test_parse_titles_live(self) -> None:
        """Test parsing live version."""
        titles = [
            "title (live at the famous arena)",
            "title [live at the famous arena]",
        ]

        for title in titles:
            parsed_tags = tags_parser.parse_titles({"title": [title]})
            self.assertEqual(["live at the famous arena"], parsed_tags.get("version"))

        parsed_tags = tags_parser.parse_titles({"title": ["title (Live at the famous arena)"]})
        self.assertEqual(["Live at the famous arena"], parsed_tags.get("version"))

        parsed_tags = tags_parser.parse_titles({"title": ["Song (Live)"]})
        self.assertEqual(["Live"], parsed_tags.get("version"))

        parsed_tags = tags_parser.parse_titles({"title": ["Wing [Live: Paris, 2001]"]})
        self.assertEqual(["Live: Paris, 2001"], parsed_tags.get("version"))

    def test_parse_titles_remaster(self) -> None:
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
            parsed_tags = tags_parser.parse_titles({"title": [test_case["original_title"]]})
            self.assertEqual([test_case["expected_version"]], parsed_tags.get("version"))
            self.assertEqual(["Song name"], parsed_tags.get("title"))

        parsed_tags = tags_parser.parse_titles(
            {"title": ["Song name (With another paretheses) (1996 Remastered Version)"]}
        )
        self.assertEqual(["1996 Remastered Version"], parsed_tags.get("version"))
        self.assertEqual(["Song name (With another paretheses)"], parsed_tags.get("title"))

    def test_parse_titles_instrumental(self) -> None:
        """Test parsing instrumental version."""
        parsed_tags = tags_parser.parse_titles({"title": ["Song name (instrumental)"]})
        self.assertEqual(["Instrumental"], parsed_tags.get("genre"))
        self.assertEqual(["Song name"], parsed_tags.get("title"))

        parsed_tags = tags_parser.parse_titles({"title": ["Song name (Instrumental)"]})
        self.assertEqual(["Instrumental"], parsed_tags.get("genre"))
        self.assertEqual(["Song name"], parsed_tags.get("title"))

        parsed_tags = tags_parser.parse_titles({"title": ["Song name [Instrumental]"]})
        self.assertEqual(["Instrumental"], parsed_tags.get("genre"))
        self.assertEqual(["Song name"], parsed_tags.get("title"))

        parsed_tags = tags_parser.parse_titles({"title": ["Song name (continued) [Extended Instrumental Version]"]})
        self.assertEqual(["Instrumental"], parsed_tags.get("genre"))
        self.assertEqual(["Song name (continued)"], parsed_tags.get("title"))

    def test_parse_titles_instrumental_and_keep_old_genre(self) -> None:
        """Test that old genres are kept when parsing instrumental."""
        parsed_tags = tags_parser.parse_titles({"title": ["Song name (instrumental)"], "genre": ["Rock"]})
        self.assertEqual(["Rock", "Instrumental"], parsed_tags.get("genre"))
        self.assertEqual(["Song name"], parsed_tags.get("title"))

    def test_parse_titles_remix(self) -> None:
        """Test parsing songs as remixed."""
        parsed_tags = tags_parser.parse_titles({"title": ["Song name (Artist Remix)"]})
        self.assertEqual(["Artist Remix"], parsed_tags.get("version"))
        self.assertEqual(["Song name"], parsed_tags.get("title"))

        parsed_tags = tags_parser.parse_titles({"title": ["Song name (Remix) [feat. Second Artist]"]})
        self.assertEqual(["Remix"], parsed_tags.get("version"))
        self.assertEqual(["Song name"], parsed_tags.get("title"))
        self.assertEqual(["Second Artist"], parsed_tags.get("artist"))

        parsed_tags = tags_parser.parse_titles({"title": ["Song name - Second Artist Remix"]})
        self.assertEqual(["Second Artist Remix"], parsed_tags.get("version"))
        self.assertEqual(["Song name"], parsed_tags.get("title"))

        parsed_tags = tags_parser.parse_titles({"title": ["Song name Remix"]})
        self.assertNotIn("version", parsed_tags)
        self.assertNotIn("title", parsed_tags)

        parsed_tags = tags_parser.parse_titles({"title": ["Song name (Artist remix)"]})
        self.assertEqual(["Artist remix"], parsed_tags.get("version"))
        self.assertEqual(["Song name"], parsed_tags.get("title"))

    def test_parse_titles_of_multiple_types(self) -> None:
        """Test parsing tags of multiple types.

        Test that when there is multiple sources of information in a
        song title, all the data is used to prune the title and append
        to the correct tag.
        """
        parsed_tags = tags_parser.parse_titles({"title": ["Song name (Artist Remix) (instrumental)"]})
        self.assertEqual(["Artist Remix"], parsed_tags.get("version"))
        self.assertEqual(["Song name"], parsed_tags.get("title"))
        self.assertEqual(["Instrumental"], parsed_tags.get("genre"))

        parsed_tags = tags_parser.parse_titles({"title": ["Song name (instrumental) (Artist Remix) "]})
        self.assertEqual(["Artist Remix"], parsed_tags.get("version"))
        self.assertEqual(["Song name"], parsed_tags.get("title"))
        self.assertEqual(["Instrumental"], parsed_tags.get("genre"))

        parsed_tags = tags_parser.parse_titles({"title": ["Song name (instrumental) (Live at famous arena) "]})
        self.assertEqual(["Live at famous arena"], parsed_tags.get("version"))
        self.assertEqual(["Song name"], parsed_tags.get("title"))
        self.assertEqual(["Instrumental"], parsed_tags.get("genre"))

        parsed_tags = tags_parser.parse_titles({"title": ["Song name (Artist remix) (Live at famous arena) "]})
        self.assertEqual(["Live at famous arena", "Artist remix"], parsed_tags.get("version"))
        self.assertEqual(["Song name"], parsed_tags.get("title"))

        parsed_tags = tags_parser.parse_titles(
            {"title": ["Song name (Artist remix) (Live at famous arena) ft. Second Artist"]}
        )
        self.assertEqual(["Live at famous arena", "Artist remix"], parsed_tags.get("version"))
        self.assertEqual(["Song name"], parsed_tags.get("title"))
        self.assertEqual(["Second Artist"], parsed_tags.get("artist"))

        parsed_tags = tags_parser.parse_titles(
            {"title": ["Song name ft. Second Artist (Artist remix) (Live at famous arena) "]}
        )
        self.assertEqual(["Live at famous arena", "Artist remix"], parsed_tags.get("version"))
        self.assertEqual(["Song name"], parsed_tags.get("title"))
        self.assertEqual(["Second Artist"], parsed_tags.get("artist"))

        parsed_tags = tags_parser.parse_titles(
            {"title": ["Song name (Artist remix) (Live at famous arena) (2022 remaster)"]}
        )
        self.assertEqual(["Live at famous arena", "Artist remix", "2022 remaster"], parsed_tags.get("version"))
        self.assertEqual(["Song name"], parsed_tags.get("title"))

    def test_parse_titles_no_title(self) -> None:
        """Test that everything works fine with no title."""
        parsed_tags = tags_parser.parse_titles({"artist": ["artist 1, artist 2"]})
        self.assertNotIn("title", parsed_tags)
        self.assertNotIn("artist", parsed_tags)
