"""Tests for utils.py."""
import unittest
from pathlib import Path
from types import SimpleNamespace

from mock import patch
from mock.mock import MagicMock

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

    def test_playlist_file_path_to_song_title(self) -> None:
        """Test paths on playlist format can be converted to a title."""
        playlist = Path("<01> - <Artist - Topic> - <Title of Song> - <zTByLCLu6NI>.opus")
        playlist_nested = Path("path/to/<01> - <Artist - Topic> - <Title of Song> - <zTByLCLu6NI>.opus")

        self.assertEqual("Artist - Title of Song", Utils.file_path_to_song_data(playlist))
        self.assertEqual("Artist - Title of Song", Utils.file_path_to_song_data(playlist_nested))

    def test_title_only_file_path_to_song_title(self) -> None:
        """Test paths on title only format can be converted to title."""
        only_title = Path("<a song title>.opus")
        no_angle_brackets = Path("a song title.opus")

        self.assertEqual("a song title", Utils.file_path_to_song_data(only_title))
        self.assertEqual("a song title", Utils.file_path_to_song_data(no_angle_brackets))

    def test_artist_title_file_path_to_song_title(self) -> None:
        """Test paths on artist-title format converts to a title."""
        song = Path("<artist> - <title>.opus")
        song_nested = Path("path/to/<artist> - <title>.opus")
        song_topic = Path("<artist - Topic> - <title>.opus")

        self.assertEqual("artist - title", Utils.file_path_to_song_data(song))
        self.assertEqual("artist - title", Utils.file_path_to_song_data(song_nested))
        self.assertEqual("artist - title", Utils.file_path_to_song_data(song_topic))

    def test_basename_not_found(self) -> None:
        """Test that path is returned when no basename can be found."""
        song = Path("test/<artist> - <title>.mp3")

        self.assertEqual("test/<artist> - <title>.mp3", Utils.file_path_to_song_data(song))

    @patch("retag_opus.utils.TerminalMenu")
    def test_select_single_tag(self, mock_menu: MagicMock) -> None:
        """Test that a candidate from a list can be selected."""
        candidates = ["candidate 1", "candidate 2", "candidate 3"]
        menu = SimpleNamespace(show=(lambda: 1))  # second option
        mock_menu.return_value = menu
        actual_outcome = Utils.select_single_tag(candidates)
        self.assertListEqual(["candidate 2"], actual_outcome)

    @patch("retag_opus.utils.TerminalMenu")
    def test_select_single_tag_no_choice(self, mock_menu: MagicMock) -> None:
        """Test that selection of no choice results in empty list."""
        candidates = ["candidate 1", "candidate 2", "candidate 3"]
        menu = SimpleNamespace(show=(lambda: None))  # no option selected
        mock_menu.return_value = menu
        actual_outcome = Utils.select_single_tag(candidates)
        self.assertEqual(0, len(actual_outcome))

    @patch("retag_opus.utils.TerminalMenu")
    def test_select_single_tag_multiple_choices(self, mock_menu: MagicMock) -> None:
        """Test that multiple selection is not allowed."""
        candidates = ["candidate 1", "candidate 2", "candidate 3"]
        menu = SimpleNamespace(show=(lambda: [1, 2]))  # second and third option
        mock_menu.return_value = menu
        actual_outcome = Utils.select_single_tag(candidates)
        self.assertEqual(0, len(actual_outcome))

    @patch("retag_opus.utils.TerminalMenu")
    def test_select_single_tag_no_change(self, mock_menu: MagicMock) -> None:
        """Test that it's possible to use the 'no choice' option."""
        candidates = ["candidate 1", "candidate 2", "candidate 3"]
        menu = SimpleNamespace(show=(lambda: 3))  # "no choice" option
        mock_menu.return_value = menu
        actual_outcome = Utils.select_single_tag(candidates)
        self.assertEqual(0, len(actual_outcome))

    def test_exit_now(self) -> None:
        """Test that the exit_now function raises exception."""
        with self.assertRaises(SystemExit):
            Utils.exit_now()

    def test_equal_when_stripped(self) -> None:
        """Test that lists with different whitespace/order are equal."""
        self.assertTrue(
            Utils.is_equal_when_stripped(
                ["value 1", "value 2  ", "value 3"],
                ["value 1", "value 2", "value 3"],
            )
        )
        self.assertTrue(
            Utils.is_equal_when_stripped(
                ["value 1", "value 2", "value 3"],
                ["value 1", "value 3", "value 2"],
            )
        )
        self.assertTrue(
            Utils.is_equal_when_stripped(
                ["value 1", "value 2  ", "value 3"],
                ["value 1", "value 3", "value 2  "],
            )
        )

    def test_equal_when_stripped_different(self) -> None:
        """Test that lists with different whitespace/order are equal."""
        self.assertFalse(
            Utils.is_equal_when_stripped(
                ["value 1", "value 2  ", "value  3"],
                ["value 1", "value 2", "value 3"],
            )
        )
