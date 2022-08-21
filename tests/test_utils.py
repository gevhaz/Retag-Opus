"""Tests for utils.py."""
import unittest
from pathlib import Path

from retag_opus.utils import Utils


class TestUtils(unittest.TestCase):
    """Test the Utils class."""

    def test_remove_duplicates(self) -> None:
        """Test that duplicates are removed."""
        duplicates = ["alpha", "beta", "alpha"]
        unduplicated = Utils.remove_duplicates(duplicates)
        self.assertEqual(2, len(unduplicated))
        self.assertListEqual(["alpha", "beta"], unduplicated)

    def test_prune_title_remove_whitespace(self) -> None:
        """Test that title has surrounding whitespace removed."""
        unpruned_title = " title of the song "
        pruned_title = Utils.prune_title(unpruned_title)
        self.assertEqual("title of the song", pruned_title)

    def test_prune_live_from_title(self) -> None:
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

    def test_prune_remix_from_title(self) -> None:
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

    def test_prune_remaster_from_title(self) -> None:
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

    def test_prune_instrumental_from_title(self) -> None:
        """Test that remix version information is pruned from title."""
        unpruned_title_1 = "A song (instrumental)"
        unpruned_title_2 = "A song (Instrumental)"
        unpruned_title_3 = "A song (InstrumEntal)"
        unpruned_title_4 = "A song [instrumental]"
        self.assertEqual("A song", Utils.prune_title(unpruned_title_1))
        self.assertEqual("A song", Utils.prune_title(unpruned_title_2))
        self.assertEqual("A song", Utils.prune_title(unpruned_title_3))
        self.assertEqual("A song", Utils.prune_title(unpruned_title_4))

    def test_prune_featuring_from_title(self) -> None:
        """Test that remix version information is pruned from title."""
        unpruned_title_1 = "A song (featuring artist)"
        unpruned_title_2 = "A song (Featuring artist)"
        unpruned_title_3 = "A song (FeatUring artist)"
        unpruned_title_4 = "A song [featuring artist]"
        unpruned_title_5 = "A song (feat. artist)"
        unpruned_title_6 = "A song (ft. artist)"
        unpruned_title_7 = "A song feat. artist"
        unpruned_title_8 = "A song ft. artist"
        unpruned_title_9 = "A song feat. artist and second artist"
        unpruned_title_10 = "A song ft. artist"
        unpruned_title_11 = "A song (ft. another artist & a, third)"
        unpruned_title_12 = "A song ft. an artist, another artist"
        unpruned_title_13 = "A song Ft an artist"
        unpruned_title_14 = "A song(ft. an artist)"

        self.assertEqual("A song", Utils.prune_title(unpruned_title_1))
        self.assertEqual("A song", Utils.prune_title(unpruned_title_2))
        self.assertEqual("A song", Utils.prune_title(unpruned_title_3))
        self.assertEqual("A song", Utils.prune_title(unpruned_title_4))
        self.assertEqual("A song", Utils.prune_title(unpruned_title_5))
        self.assertEqual("A song", Utils.prune_title(unpruned_title_6))
        self.assertEqual("A song", Utils.prune_title(unpruned_title_7))
        self.assertEqual("A song", Utils.prune_title(unpruned_title_8))
        self.assertEqual("A song", Utils.prune_title(unpruned_title_9))
        self.assertEqual("A song", Utils.prune_title(unpruned_title_10))
        self.assertEqual("A song", Utils.prune_title(unpruned_title_11))
        self.assertEqual("A song", Utils.prune_title(unpruned_title_12))
        self.assertEqual("A song", Utils.prune_title(unpruned_title_13))
        self.assertEqual("A song", Utils.prune_title(unpruned_title_14))

    def test_split_tags(self) -> None:
        """Test that tags are split at given characters and pruned."""
        unsplit_tag_1 = "an artist and another artist"
        unsplit_tag_2 = "an artist, another artist & a third artist"
        unsplit_tag_3 = "an artist, another artist and a third artist"
        unsplit_tag_4 = "an artist and  another artist and a third artist"
        unsplit_tag_5 = "an artist; another artist"
        unsplit_tag_6 = "an artist ; another artist"

        self.assertEqual(["an artist", "another artist"], Utils.split_tag(unsplit_tag_1))
        self.assertEqual(["an artist", "another artist", "a third artist"], Utils.split_tag(unsplit_tag_2))
        self.assertEqual(["an artist", "another artist", "a third artist"], Utils.split_tag(unsplit_tag_3))
        self.assertEqual(["an artist", "another artist", "a third artist"], Utils.split_tag(unsplit_tag_4))
        self.assertEqual(["an artist", "another artist"], Utils.split_tag(unsplit_tag_5))
        self.assertEqual(["an artist", "another artist"], Utils.split_tag(unsplit_tag_6))

    def test_file_path_to_song_title(self) -> None:
        """Test that a file path can be converted to a song title."""
        song = Path("<artist> - <title>.opus")
        song_nested = Path("path/to/<artist> - <title>.opus")
        song_topic = Path("<artist - Topic> - <title>.opus")
        playlist = Path("<01> - <Artist - Topic> - <Title of Song> - <zTByLCLu6NI>.opus")
        playlist_nested = Path("path/to/<01> - <Artist - Topic> - <Title of Song> - <zTByLCLu6NI>.opus")
        only_title = Path("<a song title>.opus")
        no_angle_brackets = Path("a song title.opus")

        self.assertEqual("artist - title", Utils.file_path_to_song_data(song))
        self.assertEqual("artist - title", Utils.file_path_to_song_data(song_nested))
        self.assertEqual("artist - title", Utils.file_path_to_song_data(song_topic))
        self.assertEqual("Artist - Title of Song", Utils.file_path_to_song_data(playlist))
        self.assertEqual("Artist - Title of Song", Utils.file_path_to_song_data(playlist_nested))
        self.assertEqual("a song title", Utils.file_path_to_song_data(only_title))
        self.assertEqual("a song title", Utils.file_path_to_song_data(no_angle_brackets))
