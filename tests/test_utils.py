"""Tests for utils.py."""

import unittest
from pathlib import Path

from retag_opus import utils


class TestUtils(unittest.TestCase):
    """Test the utils module."""

    def test_remove_duplicates(self) -> None:
        """Test that duplicates are removed."""
        duplicates = ["alpha", "beta", "alpha"]
        unduplicated = utils.remove_duplicates(duplicates)
        self.assertEqual(2, len(unduplicated))
        self.assertListEqual(["alpha", "beta"], unduplicated)

    def test_split_manual_value(self) -> None:
        """Test splitting manually entered values."""
        self.assertEqual(["genre 1", "genre 2"], utils.split_manual_value("genre", "genre 1, genre 2"))
        self.assertEqual(["genre 1", "genre 2"], utils.split_manual_value("genre", "genre 1;genre 2"))
        self.assertEqual(["genre 1", "genre 2"], utils.split_manual_value("genre", "genre 1 | genre 2 |"))
        self.assertEqual(["Drum & Bass"], utils.split_manual_value("genre", "Drum & Bass"))
        self.assertEqual(["Tyler, The Creator"], utils.split_manual_value("artist", "Tyler, The Creator"))
        self.assertEqual(["artist 1", "artist 2"], utils.split_manual_value("artist", "artist 1 | artist 2"))

    def test_split_tags(self) -> None:
        """Test that tags are split at given characters and pruned."""
        unsplit_tag_1 = "an artist and another artist"
        unsplit_tag_2 = "an artist, another artist & a third artist"
        unsplit_tag_3 = "an artist, another artist and a third artist"
        unsplit_tag_4 = "an artist and  another artist and a third artist"
        unsplit_tag_5 = "an artist; another artist"
        unsplit_tag_6 = "an artist ; another artist"

        self.assertEqual(["an artist", "another artist"], utils.split_tag(unsplit_tag_1))
        self.assertEqual(["an artist", "another artist", "a third artist"], utils.split_tag(unsplit_tag_2))
        self.assertEqual(["an artist", "another artist", "a third artist"], utils.split_tag(unsplit_tag_3))
        self.assertEqual(["an artist", "another artist", "a third artist"], utils.split_tag(unsplit_tag_4))
        self.assertEqual(["an artist", "another artist"], utils.split_tag(unsplit_tag_5))
        self.assertEqual(["an artist", "another artist"], utils.split_tag(unsplit_tag_6))

    def test_playlist_file_path_to_song_title(self) -> None:
        """Test paths on playlist format can be converted to a title."""
        playlist = Path("<01> - <Artist - Topic> - <Title of Song> - <zTByLCLu6NI>.opus")
        playlist_nested = Path("path/to/<01> - <Artist - Topic> - <Title of Song> - <zTByLCLu6NI>.opus")

        self.assertEqual("Artist - Title of Song", utils.file_path_to_song_name(playlist))
        self.assertEqual("Artist - Title of Song", utils.file_path_to_song_name(playlist_nested))

    def test_title_only_file_path_to_song_title(self) -> None:
        """Test paths on title only format can be converted to title."""
        only_title = Path("<a song title>.opus")
        no_angle_brackets = Path("a song title.opus")

        self.assertEqual("a song title", utils.file_path_to_song_name(only_title))
        self.assertEqual("a song title", utils.file_path_to_song_name(no_angle_brackets))

    def test_artist_title_file_path_to_song_title(self) -> None:
        """Test paths on artist-title format converts to a title."""
        song = Path("<artist> - <title>.opus")
        song_nested = Path("path/to/<artist> - <title>.opus")
        song_topic = Path("<artist - Topic> - <title>.opus")

        self.assertEqual("artist - title", utils.file_path_to_song_name(song))
        self.assertEqual("artist - title", utils.file_path_to_song_name(song_nested))
        self.assertEqual("artist - title", utils.file_path_to_song_name(song_topic))

    def test_basename_not_found(self) -> None:
        """Test that path is returned when no basename can be found."""
        song = Path("test/<artist> - <title>.mp3")

        self.assertEqual("test/<artist> - <title>.mp3", utils.file_path_to_song_name(song))

    def test_equal_when_stripped(self) -> None:
        """Test that lists with different whitespace/order are equal."""
        self.assertTrue(
            utils.is_equal_when_stripped(
                ["value 1", "value 2  ", "value 3"],
                ["value 1", "value 2", "value 3"],
            )
        )
        self.assertTrue(
            utils.is_equal_when_stripped(
                ["value 1", "value 2", "value 3"],
                ["value 1", "value 3", "value 2"],
            )
        )
        self.assertTrue(
            utils.is_equal_when_stripped(
                ["value 1", "value 2  ", "value 3"],
                ["value 1", "value 3", "value 2  "],
            )
        )

    def test_equal_when_stripped_different(self) -> None:
        """Test that lists with different whitespace/order are equal."""
        self.assertFalse(
            utils.is_equal_when_stripped(
                ["value 1", "value 2  ", "value  3"],
                ["value 1", "value 2", "value 3"],
            )
        )

    def test_normalize(self) -> None:
        """Test that typography, case, and whitespace are evened out."""
        self.assertEqual("don't stop", utils.normalize("Don’t  Stop"))
        self.assertEqual('"hi" - there', utils.normalize("“Hi” – There"))
        self.assertEqual("abc", utils.normalize("ＡBC"))

    def test_is_equal_when_normalized(self) -> None:
        """Test comparing lists regardless of typography and order."""
        self.assertTrue(utils.is_equal_when_normalized(["B", "Don't"], ["don’t", "b"]))
        self.assertFalse(utils.is_equal_when_normalized(["A"], ["A", "B"]))
