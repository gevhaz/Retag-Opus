"""Tests for titles.py."""

import unittest

from retag_opus import titles


class TestTitles(unittest.TestCase):
    """Test the titles module."""

    def test_prune_title_remove_whitespace(self) -> None:
        """Test that title has surrounding whitespace removed."""
        unpruned_title = " title of the song "
        pruned_title = titles.prune_title(unpruned_title)
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
        self.assertEqual("A song", titles.prune_title(unpruned_title_1))
        self.assertEqual("A song", titles.prune_title(unpruned_title_2))
        self.assertEqual("A song", titles.prune_title(unpruned_title_3))
        self.assertEqual("A song", titles.prune_title(unpruned_title_4))
        self.assertEqual("A song", titles.prune_title(unpruned_title_5))
        self.assertEqual("A song", titles.prune_title(unpruned_title_6))
        self.assertEqual("Spring (för livet)", titles.prune_title(unpruned_title_7))

    def test_prune_albumversion_from_title(self) -> None:
        """Test that album version information is pruned from title."""
        unpruned_title_1 = "A song (album version)"
        unpruned_title_2 = "A song [album version]"
        unpruned_title_3 = "A song (alBUM VERSIon)"
        unpruned_title_4 = "A song [alBUM VERSIon]"
        self.assertEqual("A song", titles.prune_title(unpruned_title_1))
        self.assertEqual("A song", titles.prune_title(unpruned_title_2))
        self.assertEqual("A song", titles.prune_title(unpruned_title_3))
        self.assertEqual("A song", titles.prune_title(unpruned_title_4))

    def test_prune_remix_from_title(self) -> None:
        """Test that remix version information is pruned from title."""
        unpruned_title_1 = "A song (person's remix)"
        unpruned_title_2 = "A song (person's Remix)"
        unpruned_title_3 = "A song (person's RemIx)"
        unpruned_title_4 = "A song - person's RemIx"
        unpruned_title_5 = "3 Gerald remix"
        unpruned_title_6 = "Summers Gonna Hurt You (Diplo 2010 Remix)"
        self.assertEqual("A song", titles.prune_title(unpruned_title_1))
        self.assertEqual("A song", titles.prune_title(unpruned_title_2))
        self.assertEqual("A song", titles.prune_title(unpruned_title_3))
        self.assertEqual("A song", titles.prune_title(unpruned_title_4))
        self.assertEqual("3 Gerald remix", titles.prune_title(unpruned_title_5))
        self.assertEqual("Summers Gonna Hurt You", titles.prune_title(unpruned_title_6))

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
        self.assertEqual("A song", titles.prune_title(unpruned_title_1))
        self.assertEqual("A song", titles.prune_title(unpruned_title_2))
        self.assertEqual("A song", titles.prune_title(unpruned_title_3))
        self.assertEqual("A song", titles.prune_title(unpruned_title_4))
        self.assertEqual("A song", titles.prune_title(unpruned_title_5))
        self.assertEqual("A song", titles.prune_title(unpruned_title_6))
        self.assertEqual("A song", titles.prune_title(unpruned_title_7))
        self.assertEqual("A song", titles.prune_title(unpruned_title_8))

    def test_prune_instrumental_from_title(self) -> None:
        """Test that remix version information is pruned from title."""
        unpruned_title_1 = "A song (instrumental)"
        unpruned_title_2 = "A song (Instrumental)"
        unpruned_title_3 = "A song (InstrumEntal)"
        unpruned_title_4 = "A song [instrumental]"
        self.assertEqual("A song", titles.prune_title(unpruned_title_1))
        self.assertEqual("A song", titles.prune_title(unpruned_title_2))
        self.assertEqual("A song", titles.prune_title(unpruned_title_3))
        self.assertEqual("A song", titles.prune_title(unpruned_title_4))

    def test_prune_video_notes_from_title(self) -> None:
        """Test pruning notes about a YouTube video from a title."""
        video_titles = [
            "A song (Official Video)",
            "A song (official audio)",
            "A song [Official Music Video]",
            "A song (Official Lyric Video)",
            "A song (Official Lyrics Video)",
            "A song (Lyrics)",
            "A song [Audio]",
            "A song (Visualizer)",
            "A song (Official)",
            "A song #hiphop #india",
        ]
        for video_title in video_titles:
            self.assertEqual("A song", titles.prune_title(video_title))

        # Versions of the song and numbers in titles are kept
        self.assertEqual("A song (Video Edit)", titles.prune_title("A song (Video Edit)"))
        self.assertEqual("Revolution #9", titles.prune_title("Revolution #9"))

    def test_remove_video_notes(self) -> None:
        """Test that only video notes are removed from a video title."""
        self.assertEqual("Song (Live)", titles.remove_video_notes("Song (Live) (Official Video) #rock"))
        self.assertEqual("Song ft. Artist", titles.remove_video_notes("Song ft. Artist [Lyric Video]"))

    def test_split_artist_from_title(self) -> None:
        """Test splitting video titles where one side is the artist."""
        self.assertEqual(
            ("James Blunt", "James Blunt", "Bonfire Heart"),
            titles.split_artist_from_title("James Blunt - Bonfire Heart", ["James Blunt"]),
        )
        self.assertEqual(
            ("Annelie Lockneman", "Annelie Lockneman", "Änglasång"),
            titles.split_artist_from_title("Änglasång - Annelie Lockneman", ["Annelie Lockneman"]),
        )
        self.assertEqual(
            ("yeule", "yeule", "softscars"),
            titles.split_artist_from_title("yeule - 'softscars'", ["yeule"]),
        )
        self.assertEqual(
            ("Ellen Allien UFO", "Ellen Allien", "Love"),
            titles.split_artist_from_title("Ellen Allien - Love", ["Ellen Allien UFO"]),
        )
        self.assertEqual(
            ("Jay-Z", "Jay-Z", "Song (Song - 2021)"),
            titles.split_artist_from_title("Jay-Z – Song (Song - 2021)", ["Jay-Z"]),
        )

    def test_split_artist_from_title_without_artist(self) -> None:
        """Test not splitting video titles without an artist side."""
        # Lyricist and composer of a song that Annelie Lockneman sings
        self.assertIsNone(titles.split_artist_from_title("Lucia - Karlfeldt & Hazelius", ["Annelie Lockneman"]))
        self.assertIsNone(titles.split_artist_from_title("Naanum Rowdy Dhaan - Thangamey", ["Wunderbar Films"]))
        self.assertIsNone(titles.split_artist_from_title("Love - Live", ["Love Bites"]))
        self.assertIsNone(titles.split_artist_from_title("Song", ["Song"]))

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

        self.assertEqual("A song", titles.prune_title(unpruned_title_1))
        self.assertEqual("A song", titles.prune_title(unpruned_title_2))
        self.assertEqual("A song", titles.prune_title(unpruned_title_3))
        self.assertEqual("A song", titles.prune_title(unpruned_title_4))
        self.assertEqual("A song", titles.prune_title(unpruned_title_5))
        self.assertEqual("A song", titles.prune_title(unpruned_title_6))
        self.assertEqual("A song", titles.prune_title(unpruned_title_7))
        self.assertEqual("A song", titles.prune_title(unpruned_title_8))
        self.assertEqual("A song", titles.prune_title(unpruned_title_9))
        self.assertEqual("A song", titles.prune_title(unpruned_title_10))
        self.assertEqual("A song", titles.prune_title(unpruned_title_11))
        self.assertEqual("A song", titles.prune_title(unpruned_title_12))
        self.assertEqual("A song", titles.prune_title(unpruned_title_13))
        self.assertEqual("A song", titles.prune_title(unpruned_title_14))

    def test_featured_artists(self) -> None:
        """Test getting the featured artists named in a title."""
        self.assertEqual(["Singer", "Rapper"], titles.featured_artists("Song (feat. Singer & Rapper)"))
        self.assertEqual(["Singer"], titles.featured_artists("Song ft. Singer"))
        self.assertEqual([], titles.featured_artists("Song (Live)"))

    def test_text_before_featured_artists(self) -> None:
        """Test getting the text before the featured artists."""
        self.assertEqual("A & B", titles.text_before_featured_artists("A & B feat. C"))
        self.assertEqual("A", titles.text_before_featured_artists("A (featuring C)"))
        self.assertEqual("A & B", titles.text_before_featured_artists("A & B"))

    def test_versions(self) -> None:
        """Test getting the versions of a song named in its title."""
        self.assertEqual(["Live", "2007 Remaster"], titles.versions("Song (Live) - 2007 Remaster"))
        self.assertEqual(["Album Version"], titles.versions("Song [Album Version]"))
        self.assertEqual([], titles.versions("Song (feat. Singer)"))

    def test_is_instrumental(self) -> None:
        """Test checking whether a title says a song is instrumental."""
        self.assertTrue(titles.is_instrumental("Song (Instrumental)"))
        self.assertTrue(titles.is_instrumental("Song [instrumental version]"))
        self.assertFalse(titles.is_instrumental("Song (Live)"))
