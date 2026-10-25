"""Tests for utils.py."""

import unittest

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
