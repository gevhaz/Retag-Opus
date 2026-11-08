"""Tests for tag_table.py."""

import unittest

import pytest

from retag_opus.tag_table import MUSICBRAINZ, ORIGINAL, PARSED_FROM_ORIGINAL, PARSED_FROM_YOUTUBE, YOUTUBE, TagTable


class TestTagTable(unittest.TestCase):
    """Test the TagTable class."""

    @pytest.fixture(autouse=True)
    def store_capsys(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Store capsys, since unittest methods can't take fixtures."""
        self.capsys = capsys

    def test_discard_upload_date_bad_date(self) -> None:
        """Test that bad upload dates are removed."""
        tags = TagTable()
        tags.set_tags(ORIGINAL, {"date": ["20220202"]})
        tags.discard_upload_date()
        self.assertNotIn("date", tags.tags_from(ORIGINAL))

    def test_discard_upload_date_good_date(self) -> None:
        """Test that good upload dates are not removed."""
        tags = TagTable()
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
        tags = TagTable()
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
        tags = TagTable()
        tags.set_tags(ORIGINAL, {"purl": ["youtube.com"]})
        tags.resolved = {"date": ["2022-02-02"]}
        tags.add_source_tag()
        self.assertEqual(2, len(tags.resolved))
        self.assertEqual(["youtube-dl"], tags.resolved.get("comment"))

    def test_preserve_original_comment_when_adding_source(self) -> None:
        """Test that source tag doesn't overwrite."""
        tags = TagTable()
        tags.set_tags(ORIGINAL, {"comment": ["test"], "purl": ["youtube.com"]})
        tags.resolved = {"date": ["2022-02-02"]}
        tags.add_source_tag()
        self.assertEqual(2, len(tags.resolved))
        self.assertEqual(["test", "youtube-dl"], tags.resolved.get("comment"))

    def test_get_values_from_all_sources_include_original(self) -> None:
        """Test getting data from all sources for a given tag."""
        tags = TagTable()
        tags.set_tags(ORIGINAL, {"artist": ["artist 1"]})
        tags.set_youtube_tags({"artist": ["artist 2"]}, is_auto_generated=True)
        tags.set_tags(PARSED_FROM_ORIGINAL, {"artist": ["artist 3"]})
        tags.set_tags(PARSED_FROM_YOUTUBE, {"artist": ["artist 2"]})
        actual_tags = tags.get_values_from_all_sources("artist")
        self.assertEqual(3, len(actual_tags))
        self.assertIn("artist 1", actual_tags)
        self.assertIn("artist 2", actual_tags)
        self.assertIn("artist 3", actual_tags)

    def test_get_values_from_all_sources_that_does_not_exist(self) -> None:
        """Test getting data from all sources for a non-existent tag."""
        tags = TagTable()
        tags.set_tags(ORIGINAL, {"artist": ["artist 1"]})
        tags.set_youtube_tags({"artist": ["artist 2"]}, is_auto_generated=True)
        tags.set_tags(PARSED_FROM_ORIGINAL, {"artist": ["artist 3"]})
        tags.set_tags(PARSED_FROM_YOUTUBE, {"artist": ["artist 2"]})
        actual_tags = tags.get_values_from_all_sources("title")
        self.assertEqual(0, len(actual_tags))
        self.assertNotIn("artist 1", actual_tags)
        self.assertNotIn("artist 2", actual_tags)
        self.assertNotIn("artist 3", actual_tags)

    def test_check_any_new_data_exists(self) -> None:
        """Test checking for new data."""
        tags = TagTable()

        # No tags at all
        self.assertFalse(tags.check_any_new_data_exists())

        # Only original tags
        tags.set_tags(ORIGINAL, {"artist": ["artist 1"]})
        self.assertFalse(tags.check_any_new_data_exists())

        # Other sources have same value for tag as original
        tags.set_youtube_tags({"artist": ["artist 1"]}, is_auto_generated=True)
        tags.set_tags(PARSED_FROM_ORIGINAL, {"artist": ["artist 1"]})
        tags.set_tags(PARSED_FROM_YOUTUBE, {"artist": ["artist 1"]})
        self.assertFalse(tags.check_any_new_data_exists())

        # There actually are new values for the tag
        tags.set_youtube_tags({"artist": ["artist 2"]}, is_auto_generated=True)
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
        tags = TagTable()

        # Only resolved has tags
        tags.resolved = {"artist": ["artist 1"]}
        self.assertTrue(tags.check_any_new_data_exists())

        # Identical tag in resolved
        tags.set_tags(ORIGINAL, {"artist": ["artist 1"]})
        self.assertFalse(tags.check_any_new_data_exists())

        # New tag in resolved
        tags.resolved = {"artist": ["artist 2"]}
        self.assertTrue(tags.check_any_new_data_exists())

    def test_get_album_level_tags(self) -> None:
        """Test that album level tags are returned unless removed."""
        tags = TagTable()
        tags.resolved = {
            "title": ["title 1"],
            "album": ["album 1"],
            "albumartist": ["artist 1"],
            "genre": ["[Removed]"],
        }
        self.assertEqual({"album": ["album 1"], "albumartist": ["artist 1"]}, tags.get_album_level_tags())

    def test_deleting_specified_tags(self) -> None:
        """Test deleting named tags."""
        delete_these = ["producer"]
        tags = TagTable()
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
        tags = TagTable()
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
        tags = TagTable()
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
        tags = TagTable()
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
        tags = TagTable()
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
        tags = TagTable()
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
    def store_capsys(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Store capsys, since unittest methods can't take fixtures."""
        self.capsys = capsys

    def test_get_values_from_all_sources_includes_musicbrainz(self) -> None:
        """Test that MusicBrainz values can be selected."""
        tags = TagTable()
        tags.set_tags(ORIGINAL, {"artist": ["artist 1"]})
        tags.set_tags(MUSICBRAINZ, {"artist": ["artist 2"]})
        self.assertEqual(["artist 2", "artist 1"], tags.get_values_from_all_sources("artist"))

    def test_check_any_new_data_exists_in_musicbrainz(self) -> None:
        """Test that tags only MusicBrainz has are new data."""
        tags = TagTable()
        tags.set_tags(ORIGINAL, {"title": ["title 1"]})
        tags.set_tags(MUSICBRAINZ, {"title": ["title 1"]})
        self.assertFalse(tags.check_any_new_data_exists())
        tags.tags_from(MUSICBRAINZ)["musicbrainz_trackid"] = ["id 1"]
        self.assertTrue(tags.check_any_new_data_exists())

    def test_youtube_description_is_not_trusted_until_set(self) -> None:
        """Test that MusicBrainz comes first without a description."""
        tags = TagTable()
        self.assertFalse(tags.youtube_is_auto_generated)
        self.assertEqual(
            [PARSED_FROM_ORIGINAL, MUSICBRAINZ, YOUTUBE, PARSED_FROM_YOUTUBE],
            tags.sources_in_order_of_preference(),
        )

    def test_set_tags_refuses_youtube(self) -> None:
        """Test that the YouTube tags need to say who wrote them."""
        tags = TagTable()
        with self.assertRaises(ValueError):
            tags.set_tags(YOUTUBE, {"title": ["Song"]})
        self.assertEqual({}, tags.tags_from(YOUTUBE))

    def test_sources_agree_regardless_of_typography(self) -> None:
        """Test that typography and case don't make sources disagree."""
        tags = TagTable()
        tags.set_youtube_tags({"title": ["Don't Go"]}, is_auto_generated=True)
        tags.set_tags(MUSICBRAINZ, {"title": ["Don’t go"]})
        self.assertTrue(tags.sources_agree("title"))
        tags.set_tags(MUSICBRAINZ, {"title": ["Don’t Go (Live)"]})
        self.assertFalse(tags.sources_agree("title"))

    def test_agreeing_source_is_the_most_preferred(self) -> None:
        """Test that each source compares with the file in its own way.

        MusicBrainz ignores typography, the others only whitespace.
        """
        tags = TagTable()
        tags.set_tags(ORIGINAL, {"title": ["Don't Go"]})
        tags.set_tags(PARSED_FROM_ORIGINAL, {"title": ["Dont Go"]})
        tags.set_tags(MUSICBRAINZ, {"title": ["Don’t Go"]})
        self.assertEqual(MUSICBRAINZ, tags.agreeing_source("title"))
        tags.set_youtube_tags({"title": [" Don't Go "]}, is_auto_generated=True)
        self.assertEqual(YOUTUBE, tags.agreeing_source("title"))

    def test_agreeing_source_needs_a_value_in_the_file(self) -> None:
        """Test that no source agrees with a missing or other value."""
        tags = TagTable()
        tags.set_tags(MUSICBRAINZ, {"title": ["Song"]})
        self.assertIsNone(tags.agreeing_source("title"))
        tags.set_tags(ORIGINAL, {"title": ["Song (Live)"]})
        self.assertIsNone(tags.agreeing_source("title"))

    def test_agreeing_source_ignores_album_unlike_musicbrainz(self) -> None:
        """Test keeping the album only if MusicBrainz agrees."""
        tags = TagTable()
        tags.set_tags(ORIGINAL, {"album": ["Single"]})
        tags.set_youtube_tags({"album": ["Single"]}, is_auto_generated=True)
        self.assertEqual(YOUTUBE, tags.agreeing_source("album"))
        tags.set_tags(MUSICBRAINZ, {"album": ["Album"]})
        self.assertIsNone(tags.agreeing_source("album"))

    def test_should_resolve_release_tags_of_the_release(self) -> None:
        """Test that track numbers are only taken for the same album."""
        tags = TagTable()
        tags.set_tags(MUSICBRAINZ, {"album": ["Album"], "tracknumber": ["5"]})
        tags.resolved = {"album": ["Single"]}
        self.assertTrue(tags.should_resolve("title"))
        self.assertFalse(tags.should_resolve("tracknumber"))
        tags.resolved["album"] = ["Album (2011 Remaster)"]
        self.assertTrue(tags.should_resolve("tracknumber"))

    def test_should_resolve_skips_album_level_tags(self) -> None:
        """Test that tags chosen for an earlier song are left alone."""
        tags = TagTable()
        tags.apply_album_level_tags({"genre": ["Pop"]})
        self.assertFalse(tags.should_resolve("genre"))
        self.assertTrue(tags.should_resolve("title"))
