"""Tests for utils.py."""
import unittest

from retag_opus.utils import Utils


class TestUtils(unittest.TestCase):
    """Test the Utils class."""

    def test_remove_duplicates(self):
        """Test that duplicates are removed."""
        duplicates = ["alpha", "beta", "alpha"]
        unduplicated = Utils.remove_duplicates(duplicates)
        self.assertEqual(2, len(unduplicated))
        self.assertListEqual(["alpha", "beta"], unduplicated)

    def test_prune_title_remove_whitespace(self):
        """Test that title has surrounding whitespace removed."""
        unpruned_title = " title of the song "
        pruned_title = Utils.prune_title(unpruned_title)
        self.assertEqual("title of the song", pruned_title)

    def test_prune_live_from_title(self):
        """Test that live version information is pruned from title."""
        unpruned_title_1 = "A song (live)"
        unpruned_title_2 = "A song [live]"
        unpruned_title_3 = "A song (Live)"
        unpruned_title_4 = "A song (LivE)"
        unpruned_title_5 = "A song (live 1998)"
        unpruned_title_6 = "A song (live cut)"
        unpruned_title_7 = "Spring (för livet)"
        self.assertEqual("A song", Utils.prune_title(unpruned_title_1))
        self.assertEqual("A song", Utils.prune_title(unpruned_title_2))
        self.assertEqual("A song", Utils.prune_title(unpruned_title_3))
        self.assertEqual("A song", Utils.prune_title(unpruned_title_4))
        self.assertEqual("A song", Utils.prune_title(unpruned_title_5))
        self.assertEqual("A song", Utils.prune_title(unpruned_title_6))
        self.assertEqual("Spring (för livet)", Utils.prune_title(unpruned_title_7))

    def test_prune_remix_from_title(self):
        """Test that remix version information is pruned from title."""
        unpruned_title_1 = "A song (person's remix)"
        unpruned_title_2 = "A song (person's Remix)"
        unpruned_title_3 = "A song (person's RemIx)"
        unpruned_title_4 = "A song - person's RemIx"
        unpruned_title_5 = "3 Gerald remix"
        unpruned_title_6 = "Summers Gonna Hurt You (Diplo 2010 Remix)"
        self.assertEqual("A song", Utils.prune_title(unpruned_title_1))
        self.assertEqual("A song", Utils.prune_title(unpruned_title_2))
        self.assertEqual("A song", Utils.prune_title(unpruned_title_3))
        self.assertEqual("A song", Utils.prune_title(unpruned_title_4))
        self.assertEqual("3 Gerald remix", Utils.prune_title(unpruned_title_5))
        self.assertEqual("Summers Gonna Hurt You", Utils.prune_title(unpruned_title_6))

    def test_prune_remaster_from_title(self):
        """Test that remix version information is pruned from title."""
        unpruned_title_1 = "A song (1934 remaster)"
        unpruned_title_2 = "A song (1934 remaster)"
        unpruned_title_3 = "A song (1934 Remaster)"
        unpruned_title_4 = "A song (remaster)"
        unpruned_title_5 = "A song (remastered)"
        unpruned_title_6 = "A song - 1992 digital remaster"
        unpruned_title_7 = "A song - 1992 remaster"
        unpruned_title_8 = "A song - 1992 remastered"
        unpruned_title_1 = "A song (remastered 1934)"
        unpruned_title_7 = "A song - remastered 1992"
        self.assertEqual("A song", Utils.prune_title(unpruned_title_1))
        self.assertEqual("A song", Utils.prune_title(unpruned_title_2))
        self.assertEqual("A song", Utils.prune_title(unpruned_title_3))
        self.assertEqual("A song", Utils.prune_title(unpruned_title_4))
        self.assertEqual("A song", Utils.prune_title(unpruned_title_5))
        self.assertEqual("A song", Utils.prune_title(unpruned_title_6))
        self.assertEqual("A song", Utils.prune_title(unpruned_title_7))
        self.assertEqual("A song", Utils.prune_title(unpruned_title_8))

    def test_prune_instrumental_from_title(self):
        """Test that remix version information is pruned from title."""
        unpruned_title_1 = "A song (instrumental)"
        unpruned_title_2 = "A song (Instrumental)"
        unpruned_title_3 = "A song (InstrumEntal)"
        unpruned_title_4 = "A song [instrumental]"
        self.assertEqual("A song", Utils.prune_title(unpruned_title_1))
        self.assertEqual("A song", Utils.prune_title(unpruned_title_2))
        self.assertEqual("A song", Utils.prune_title(unpruned_title_3))
        self.assertEqual("A song", Utils.prune_title(unpruned_title_4))
