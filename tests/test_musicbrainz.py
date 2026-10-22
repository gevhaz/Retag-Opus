"""Tests for musicbrainz.py."""

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from retag_opus import musicbrainz
from retag_opus.music_tags import ORIGINAL, YOUTUBE, MusicTags
from retag_opus.musicbrainz import MusicBrainzMatcher
from retag_opus.musicbrainz_client import MusicBrainzError

JsonDict = dict[str, Any]
Tags = dict[str, list[str]]


def credit(name: str, joinphrase: str = "") -> JsonDict:
    """Create an artist credit like the ones MusicBrainz returns."""
    return {"name": name, "joinphrase": joinphrase, "artist": {"id": f"id-{name}", "name": name}}


def artist_relation(relation_type: str, name: str, attributes: list[str] | None = None) -> JsonDict:
    """Create an artist relationship like the ones MusicBrainz returns."""
    return {
        "type": relation_type,
        "target-type": "artist",
        "target-credit": "",
        "attributes": attributes or [],
        "artist": {"id": f"id-{name}", "name": name},
    }


def track(position: int, title: str, length: int, relations: list[JsonDict] | None = None) -> JsonDict:
    """Create a track like the ones in a MusicBrainz release lookup."""
    return {
        "position": position,
        "title": title,
        "length": length,
        "recording": {"id": f"rec-{title}", "title": title, "length": length, "relations": relations or []},
    }


GOODBYES_RELATIONS: list[JsonDict] = [
    artist_relation("vocal", "Ben Ivor", ["lead vocals"]),
    artist_relation("vocal", "Ann Choir", ["background vocals"]),
    artist_relation("instrument", "Gus Tar", ["guitar", "theremin"]),
    artist_relation("instrument", "Drum Mer", ["drums (drum set)"]),
    artist_relation("producer", "Pro Ducer"),
    {**artist_relation("producer", "Pro Ducer"), "target-credit": "P. Ducer"},
    artist_relation("mix", "Mix Er"),
    {
        "type": "performance",
        "target-type": "work",
        "work": {"relations": [artist_relation("composer", "Com Poser"), artist_relation("writer", "Wri Ter")]},
    },
]

RELEASE: JsonDict = {
    "id": "rel-1",
    "title": "Goodbyes",
    "date": "2022-08-22",
    "artist-credit": [credit("The Global")],
    "release-group": {"id": "rg-1"},
    "media": [
        {
            "position": 1,
            "track-count": 2,
            "tracks": [
                {
                    **track(1, "Proper Goodbyes", 200_000, GOODBYES_RELATIONS),
                    "artist-credit": [credit("The Global", " feat. "), credit("Ben Ivor")],
                },
                track(2, "Hello Again", 180_000),
            ],
        },
        {"position": 2, "track-count": 1, "tracks": [track(1, "Bonus", 120_000)]},
    ],
}


def test_joined_credit() -> None:
    """Credits are joined the way they're printed."""
    assert musicbrainz.joined_credit([credit("A", " feat. "), credit("B")]) == "A feat. B"


def test_credits_from_relations() -> None:
    """Relationships, also of works, become credit tags."""
    assert musicbrainz.credits_from_relations(GOODBYES_RELATIONS) == {
        "performer:lead vocals": ["Ben Ivor"],
        "performer:background vocals": ["Ann Choir"],
        "performer:guitar": ["Gus Tar"],
        "performer:theremin": ["Gus Tar"],
        "performer:drums (drum set)": ["Drum Mer"],
        "producer": ["Pro Ducer", "P. Ducer"],
        "mixer": ["Mix Er"],
        "composer": ["Com Poser"],
        "writer": ["Wri Ter"],
    }


def test_relation_tag_names() -> None:
    """Vocals and instruments get a performer tag each, named as on MusicBrainz."""
    assert musicbrainz.relation_tag_names(artist_relation("instrument", "A", ["guest", "electric bass guitar"])) == [
        "performer:electric bass guitar"
    ]
    assert musicbrainz.relation_tag_names(artist_relation("vocal", "A", ["choir vocals", "alto vocals"])) == [
        "performer:choir vocals",
        "performer:alto vocals",
    ]
    assert musicbrainz.relation_tag_names(artist_relation("vocal", "A", ["solo"])) == ["performer:vocals"]
    assert musicbrainz.relation_tag_names(artist_relation("instrument", "A")) == ["performer:instruments"]
    assert musicbrainz.relation_tag_names(artist_relation("mix", "A")) == ["mixer"]
    assert musicbrainz.relation_tag_names(artist_relation("photography", "A")) == []
    # Programming isn't an instrument, and Picard has no tag for it
    assert musicbrainz.relation_tag_names(artist_relation("programming", "A")) == []


def test_release_tracks() -> None:
    """Tracks on all media are found."""
    titles = [(medium["position"], track["title"]) for medium, track in musicbrainz.release_tracks(RELEASE)]
    assert titles == [(1, "Proper Goodbyes"), (1, "Hello Again"), (2, "Bonus")]
    assert musicbrainz.release_tracks({}) == []


def test_track_tags() -> None:
    """A track becomes tags with credits and MusicBrainz IDs."""
    medium, first_track = musicbrainz.release_tracks(RELEASE)[0]
    assert musicbrainz.track_tags(RELEASE, medium, first_track) == {
        "title": ["Proper Goodbyes"],
        "artist": ["The Global", "Ben Ivor"],
        "album": ["Goodbyes"],
        "albumartist": ["The Global"],
        "date": ["2022-08-22"],
        "tracknumber": ["1"],
        "totaltracks": ["2"],
        "discnumber": ["1"],
        "totaldiscs": ["2"],
        "musicbrainz_trackid": ["rec-Proper Goodbyes"],
        "musicbrainz_artistid": ["id-The Global", "id-Ben Ivor"],
        "musicbrainz_albumid": ["rel-1"],
        "musicbrainz_albumartistid": ["id-The Global"],
        "musicbrainz_releasegroupid": ["rg-1"],
        "performer:lead vocals": ["Ben Ivor"],
        "performer:background vocals": ["Ann Choir"],
        "performer:guitar": ["Gus Tar"],
        "performer:theremin": ["Gus Tar"],
        "performer:drums (drum set)": ["Drum Mer"],
        "producer": ["Pro Ducer", "P. Ducer"],
        "mixer": ["Mix Er"],
        "composer": ["Com Poser"],
        "writer": ["Wri Ter"],
    }


def test_track_tags_with_little_data() -> None:
    """Missing data is left out, and the recording artist is used."""
    release: JsonDict = {"id": "rel-2", "title": "Bare", "media": [{"position": 1, "track-count": 1}]}
    bare_track = track(1, "Song", 1000)
    bare_track["recording"]["artist-credit"] = [credit("A")]
    assert musicbrainz.track_tags(release, release["media"][0], bare_track) == {
        "title": ["Song"],
        "artist": ["A"],
        "album": ["Bare"],
        "tracknumber": ["1"],
        "totaltracks": ["1"],
        "discnumber": ["1"],
        "totaldiscs": ["1"],
        "musicbrainz_trackid": ["rec-Song"],
        "musicbrainz_artistid": ["id-A"],
        "musicbrainz_albumid": ["rel-2"],
    }


SEARCH_RESULT: JsonDict = {
    "id": "rec-Proper Goodbyes",
    "title": "Proper Goodbyes",
    "length": 200_000,
    "artist-credit": [credit("The Global", " feat. "), credit("Ben Ivor")],
    "releases": [
        {"id": "bootleg", "title": "Live Bootleg", "status": "Bootleg", "date": "2020"},
        {"id": "single", "title": "Proper Goodbyes", "status": "Official", "date": "2022-01-01"},
        {"id": "rel-1", "title": "Goodbyes", "status": "Official", "date": "2022-08-22"},
    ],
}

VIDEO_TITLE = "PROPER GOODBYES Full  Video | The Global -THE MOVIE |Ben Ivor|Some Actor"


def song(
    original: Tags | None = None,
    youtube: Tags | None = None,
    length: float | None = 201.0,
) -> MusicTags:
    """Create tags for a song from the given sources."""
    tags = MusicTags()
    tags.set_tags(ORIGINAL, original or {})
    tags.set_tags(YOUTUBE, youtube or {})
    tags.length = length
    return tags


def fake_client() -> MagicMock:
    """Create a client that finds the test recording and release."""
    client = MagicMock()
    client.search_recordings.return_value = [SEARCH_RESULT]
    client.search_recordings_by_words.return_value = [SEARCH_RESULT]
    client.lookup_recording.return_value = SEARCH_RESULT
    client.lookup_release.return_value = RELEASE
    return client


@pytest.fixture
def menu(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    """Replace the terminal menu with a mock."""
    mock = MagicMock()
    monkeypatch.setattr(musicbrainz, "TerminalMenu", mock)
    return mock


@pytest.fixture
def typed(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Replace input with answers taken from the returned list."""
    answers: list[str] = []
    monkeypatch.setattr("builtins.input", lambda _: answers.pop(0))
    return answers


def test_song_text() -> None:
    """Describe songs by the description, or else the existing title."""
    youtube = {"title": ["Song"], "artist": ["A", "B"]}
    assert musicbrainz.song_text(song(original={"title": ["Video"]}, youtube=youtube)) == "Song A B"
    assert musicbrainz.song_text(song(original={"title": ["Video"], "artist": ["Channel"]})) == "Video"
    assert musicbrainz.song_text(song(original={"title": ["Artist - Song (Live) (Official Video)"]})) == (
        "Artist - Song (Live)"
    )
    assert musicbrainz.song_text(song()) == ""


@pytest.mark.parametrize(
    ("title", "text", "expected"),
    [
        ("Kaun Tujhe", "KAUN TUJHE Full  Video | M.S. DHONI -THE UNTOLD STORY |Amaal Mallik Palak", True),
        ("Nee Paartha Vizhigal: The Touch of Love", "Nee Paartha Vizhigal 8D - 3 (Moonu) Dhanush", True),
        ("Bhaja Govindam", "Bhaja Govindam song By M.S. Subbulakshmi | Carnatic Classical Music", True),
        ("Bohemian Rhapsody (Queen)", "Bohemian Rhapsody Queen", True),
        ("Don\u2019t Go", "Don't Go", True),
        ("Don\u2019t Go", "Dont Go", False),
        ("Kaun Tujhe Unplugged", "KAUN TUJHE Full Video", False),
        ("(Untitled)", "Untitled", False),
    ],
)
def test_title_matches(title: str, text: str, expected: bool) -> None:
    """Only the main title from MusicBrainz has to be in the text."""
    assert musicbrainz.title_matches(title, text) is expected


def test_format_length() -> None:
    """Show length as minutes and seconds."""
    assert musicbrainz.format_length(200_400) == "3:20"
    assert musicbrainz.format_length(None) == "?:??"


def test_length_matches() -> None:
    """Lengths match within three seconds."""
    assert musicbrainz.length_matches(200_000, 202.5)
    assert not musicbrainz.length_matches(200_000, 204.0)
    assert not musicbrainz.length_matches(200_000, None)
    assert not musicbrainz.length_matches(None, 200.0)


def test_choose_release() -> None:
    """Prefer the stored release, the named album, then the earliest official release."""
    releases = SEARCH_RESULT["releases"]
    stored = song(original={"musicbrainz_albumid": ["bootleg"], "album": ["Goodbyes"]})
    assert musicbrainz.choose_release(releases, stored)["id"] == "bootleg"  # type: ignore[index]
    named = song(youtube={"album": ["goodbyes"]})
    assert musicbrainz.choose_release(releases, named)["id"] == "rel-1"  # type: ignore[index]
    assert musicbrainz.choose_release(releases, song())["id"] == "single"  # type: ignore[index]
    assert musicbrainz.choose_release(releases[:1], song())["id"] == "bootleg"  # type: ignore[index]
    editions = [
        {"id": "remaster", "title": "Goodbyes (2011 Remaster)", "status": "Official", "date": "2011"},
        {"id": "dvd", "title": "Goodbyes", "status": "Official", "date": "2001"},
        {"id": "original", "title": "Goodbyes", "status": "Official", "date": "1975"},
    ]
    remaster = song(youtube={"album": ["Goodbyes (2011 Remaster)"]})
    assert musicbrainz.choose_release(editions, remaster)["id"] == "original"  # type: ignore[index]
    assert musicbrainz.choose_release([], song()) is None


def test_match_message() -> None:
    """Describe a match with the version and release."""
    live = track(1, "Song", 1000)
    live["recording"]["disambiguation"] = "live, 1981"
    release = {"title": "Album", "date": "2007", "country": "CA"}
    assert musicbrainz.match_message(live, release) == "MusicBrainz: Found 'Song' (live, 1981) on 'Album' (2007, CA)."
    assert musicbrainz.match_message(track(1, "Song", 1000), {"title": "Album"}) == (
        "MusicBrainz: Found 'Song' on 'Album'."
    )


def test_search_result_entry() -> None:
    """Describe search results with length, version, and release."""
    assert musicbrainz.search_result_entry({**SEARCH_RESULT, "title": "A [B] | C", "disambiguation": "live"}) == (
        "A (B) / C - The Global feat. Ben Ivor (3:20, live, on 'Live Bootleg')"
    )
    assert musicbrainz.search_result_entry({"title": "X"}) == "X -  (?:??)"


def test_match_song_from_description(capsys: pytest.CaptureFixture[str]) -> None:
    """Search for the exact title and artist from the description."""
    client = fake_client()
    youtube = {"title": ["Proper Goodbyes (feat. Ben Ivor)"], "artist": ["The Global"], "album": ["Goodbyes"]}
    tags = MusicBrainzMatcher(client).match_song(song(youtube=youtube))
    assert tags["album"] == ["Goodbyes"]
    assert tags["composer"] == ["Com Poser"]
    client.search_recordings.assert_called_once_with("Proper Goodbyes", "The Global")
    client.lookup_release.assert_called_once_with("rel-1")
    out = capsys.readouterr().out
    assert "Looking up the song on MusicBrainz..." in out
    assert "MusicBrainz: Found 'Proper Goodbyes' on 'Goodbyes' (2022-08-22)." in out


def test_match_song_from_video_title() -> None:
    """Search for the words of a video title."""
    client = fake_client()
    tags = MusicBrainzMatcher(client).match_song(song(original={"title": [VIDEO_TITLE], "artist": ["Channel"]}))
    assert tags["title"] == ["Proper Goodbyes"]
    client.search_recordings_by_words.assert_called_once_with(VIDEO_TITLE)
    client.lookup_release.assert_called_once_with("single")


def test_match_song_prefers_title_that_was_searched_for() -> None:
    """Among results as long as the song, use the one with the searched title."""
    client = fake_client()
    mix = {**SEARCH_RESULT, "id": "mix", "title": "Proper Goodbyes (5.1 mix)"}
    client.search_recordings_by_words.return_value = [{**SEARCH_RESULT, "length": 100}, mix, SEARCH_RESULT]
    tags = MusicBrainzMatcher(client).match_song(song(original={"title": [VIDEO_TITLE]}))
    assert tags["title"] == ["Proper Goodbyes"]


def test_fit() -> None:
    """Fewest unsearched words fit best, then most releases."""
    assert musicbrainz.fit({"title": "Song (5.1 mix)"}, "Song") == (3, 0)
    assert musicbrainz.fit({"title": "Song", "releases": [{}, {}]}, "Song Artist") == (0, -2)


def test_match_song_by_stored_id() -> None:
    """Use the MusicBrainz IDs in the file instead of searching."""
    client = fake_client()
    original = {"musicbrainz_trackid": ["rec-Proper Goodbyes"], "musicbrainz_albumid": ["rel-1"]}
    tags = MusicBrainzMatcher(client).match_song(song(original=original))
    assert tags["album"] == ["Goodbyes"]
    client.lookup_recording.assert_called_once_with("rec-Proper Goodbyes")
    client.search_recordings_by_words.assert_not_called()


def test_match_song_stored_id_not_found() -> None:
    """Search if the MusicBrainz ID in the file isn't found."""
    client = fake_client()
    client.lookup_recording.return_value = None
    original = {"musicbrainz_trackid": ["gone"], "title": [VIDEO_TITLE]}
    assert MusicBrainzMatcher(client).match_song(song(original=original))
    client.search_recordings_by_words.assert_called_once()


def test_match_song_not_on_release() -> None:
    """Without the recording on the release there are no tags."""
    client = fake_client()
    client.lookup_release.return_value = {"media": []}
    assert MusicBrainzMatcher(client).match_song(song(original={"title": [VIDEO_TITLE]})) == {}
    client.lookup_release.return_value = None
    assert MusicBrainzMatcher(client).match_song(song(original={"title": [VIDEO_TITLE]})) == {}
    client.search_recordings_by_words.return_value = [{**SEARCH_RESULT, "releases": []}]
    assert MusicBrainzMatcher(client).match_song(song(original={"title": [VIDEO_TITLE]})) == {}


def test_match_song_asks_when_not_confident(menu: MagicMock) -> None:
    """Let the user pick a result when the length doesn't match."""
    menu.return_value.show.return_value = 0
    tags = MusicBrainzMatcher(fake_client()).match_song(song(original={"title": [VIDEO_TITLE]}, length=150))
    assert tags["title"] == ["Proper Goodbyes"]
    assert menu.call_args.args[0][-2:] == ["[e] Edit search", "[s] Skip MusicBrainz for this song"]
    assert menu.call_args.kwargs["title"] == f"MusicBrainz: Results for '{VIDEO_TITLE}'. The song is 2:30 long."


def test_artist_matches() -> None:
    """One of the credited artists has to be in the text."""
    assert musicbrainz.artist_matches(SEARCH_RESULT, "Proper Goodbyes Ben Ivor")
    assert not musicbrainz.artist_matches(SEARCH_RESULT, "Proper Goodbyes Ben")
    assert not musicbrainz.artist_matches({"title": "X"}, "X")


def test_match_song_by_channel() -> None:
    """The YouTube channel counts as an artist in the video title."""
    client = fake_client()
    tags = MusicBrainzMatcher(client).match_song(song(original={"title": ["Proper Goodbyes"], "artist": ["Ben Ivor"]}))
    assert tags["title"] == ["Proper Goodbyes"]


def test_match_song_asks_when_artist_not_in_text(menu: MagicMock) -> None:
    """Let the user pick a result by another artist with the searched title."""
    menu.return_value.show.return_value = 0
    MusicBrainzMatcher(fake_client()).match_song(song(original={"title": ["Proper Goodbyes - Someone"]}))
    menu.assert_called_once()


def test_match_song_asks_when_title_not_in_text(menu: MagicMock) -> None:
    """Let the user pick a result when its title isn't what was searched for."""
    menu.return_value.show.return_value = 0
    MusicBrainzMatcher(fake_client()).match_song(song(original={"title": ["Something Else"]}))
    menu.assert_called_once()


@pytest.mark.parametrize("choice", [2, None])
def test_match_song_user_skips(menu: MagicMock, choice: int | None) -> None:
    """Skipping or escaping the results menu gives no tags."""
    menu.return_value.show.return_value = choice
    client = fake_client()
    assert MusicBrainzMatcher(client).match_song(song(original={"title": ["X"]}, length=None)) == {}
    client.lookup_release.assert_not_called()


def test_match_song_edit_search(menu: MagicMock, typed: list[str]) -> None:
    """Let the user search for something else."""
    menu.return_value.show.side_effect = [0, 0]
    typed += ["Proper Goodbyes Ben Ivor", ""]
    client = fake_client()
    client.search_recordings_by_words.side_effect = [[], [SEARCH_RESULT]]
    tags = MusicBrainzMatcher(client).match_song(song(original={"title": ["Wrong"]}))
    assert tags["title"] == ["Proper Goodbyes"]
    assert menu.call_args.kwargs["title"] == "MusicBrainz: Nothing found for 'Wrong'. The song is 3:21 long."
    client.search_recordings_by_words.assert_called_with("Proper Goodbyes Ben Ivor")


def test_match_song_without_title(menu: MagicMock, typed: list[str]) -> None:
    """Without a title, nothing is searched for until the user says what."""
    menu.return_value.show.side_effect = [0, 1]
    typed += [""]
    client = fake_client()
    assert MusicBrainzMatcher(client).match_song(song()) == {}
    assert menu.call_args.kwargs["title"] == "MusicBrainz: Nothing found for ''. The song is 3:21 long."
    client.search_recordings_by_words.assert_not_called()


def test_match_song_disabled_after_error(capsys: pytest.CaptureFixture[str]) -> None:
    """When MusicBrainz can't be reached, don't try again."""
    client = fake_client()
    client.search_recordings_by_words.side_effect = MusicBrainzError("Could not get data from MusicBrainz: offline")
    matcher = MusicBrainzMatcher(client)
    assert matcher.match_song(song(original={"title": ["A"]})) == {}
    assert matcher.match_song(song(original={"title": ["A"]})) == {}
    assert client.search_recordings_by_words.call_count == 1
    assert "Not using MusicBrainz for the rest of this run." in capsys.readouterr().out


def test_matcher_creates_client() -> None:
    """Create a real client when none is given."""
    assert MusicBrainzMatcher().client is not None


RELEASE_RESULTS: list[JsonDict] = [
    {"id": "deluxe", "score": 100, "track-count": 3},
    {"id": "other", "score": 60, "track-count": 2},
    {"id": "rel-1", "score": 100, "track-count": 2},
    {"id": "single", "score": 100, "track-count": 1},
    {"id": "unknown size", "score": 100},
]


def album_songs(goodbyes_length: float | None = 201.0, hello_length: float | None = 180.0) -> dict[Path, MusicTags]:
    """Create two songs from the test release."""
    return {
        Path("2.opus"): song(original={"title": ["Hello Again (Official Audio)"]}, length=hello_length),
        Path("1.opus"): song(youtube={"title": ["Proper Goodbyes"], "artist": ["The Global"]}, length=goodbyes_length),
    }


def test_match_tracks() -> None:
    """Match each song to a track by title and length."""
    matched = musicbrainz.match_tracks(RELEASE, album_songs())
    assert {path: tags["tracknumber"] for path, tags in matched.items()} == {
        Path("1.opus"): ["1"],
        Path("2.opus"): ["2"],
    }
    assert musicbrainz.match_tracks(RELEASE, album_songs(None, None)) == matched


def test_match_tracks_needs_every_song() -> None:
    """A release without all songs matches none of them."""
    assert musicbrainz.match_tracks(RELEASE, {**album_songs(), Path("3.opus"): song(original={"title": ["X"]})}) == {}
    assert musicbrainz.match_tracks(RELEASE, album_songs(goodbyes_length=100)) == {}
    same_song_twice = {Path(name): song(original={"title": ["Bonus"]}, length=None) for name in ["a", "b"]}
    assert musicbrainz.match_tracks(RELEASE, same_song_twice) == {}


def test_match_album(capsys: pytest.CaptureFixture[str]) -> None:
    """Use the smallest release with all songs, without asking."""
    client = fake_client()
    client.search_releases.return_value = RELEASE_RESULTS
    client.lookup_release.side_effect = lambda mbid: RELEASE if mbid == "rel-1" else None
    matched = MusicBrainzMatcher(client).match_album("Goodbyes (2011 Remaster)", album_songs())
    assert set(matched) == {Path("1.opus"), Path("2.opus")}
    client.search_releases.assert_called_once_with("Goodbyes", "The Global")
    assert [c.args[0] for c in client.lookup_release.call_args_list] == ["rel-1"]
    out = capsys.readouterr().out
    assert "Looking up the album 'Goodbyes (2011 Remaster)' on MusicBrainz..." in out
    assert "MusicBrainz: Found all 2 songs from 'Goodbyes (2011 Remaster)' on 'Goodbyes' (2022-08-22)." in out


def test_match_album_no_release(capsys: pytest.CaptureFixture[str]) -> None:
    """Look up at most a few releases, and give up if none has all songs."""
    client = fake_client()
    client.search_releases.return_value = [{"id": str(n), "score": 100, "track-count": 9} for n in range(5)]
    client.lookup_release.return_value = None
    assert MusicBrainzMatcher(client).match_album("My Favourites", album_songs()) == {}
    assert client.lookup_release.call_count == musicbrainz.MAX_RELEASE_LOOKUPS
    assert "MusicBrainz: No release of 'My Favourites' has all 2 songs." in capsys.readouterr().out


def test_match_album_disabled_after_error() -> None:
    """When MusicBrainz can't be reached, don't try again."""
    client = fake_client()
    client.search_releases.side_effect = MusicBrainzError("offline")
    matcher = MusicBrainzMatcher(client)
    assert matcher.match_album("Goodbyes", album_songs()) == {}
    assert matcher.match_album("Goodbyes", album_songs()) == {}
    client.search_releases.assert_called_once()


def test_search_album_releases() -> None:
    """Search for releases that may be the album, smallest and earliest first."""
    client = fake_client()
    client.search_releases.return_value = [
        {"id": "remaster", "score": 100, "track-count": 2, "date": "2011"},
        {"id": "undated", "score": 100, "track-count": 2},
        {"id": "original", "score": 100, "track-count": 2, "date": "1975"},
        *RELEASE_RESULTS,
    ]
    releases = MusicBrainzMatcher(client).search_album_releases("Goodbyes", album_songs())
    assert releases == ["original", "remaster", "undated", "rel-1", "deluxe"]


def test_stored_release_ids() -> None:
    """Get each release stored in the songs' files once."""
    songs = album_songs()
    for tags in songs.values():
        tags.tags_from(ORIGINAL)["musicbrainz_albumid"] = ["stored"]
    assert musicbrainz.stored_release_ids(songs) == ["stored"]
    assert musicbrainz.stored_release_ids(album_songs()) == []


def test_match_album_tries_stored_release_first() -> None:
    """Search for releases when the stored release doesn't have all songs."""
    client = fake_client()
    client.search_releases.return_value = RELEASE_RESULTS
    client.lookup_release.side_effect = lambda mbid: RELEASE if mbid == "rel-1" else None
    songs = album_songs()
    songs[Path("2.opus")].tags_from(ORIGINAL)["musicbrainz_albumid"] = ["stored"]
    assert MusicBrainzMatcher(client).match_album("Goodbyes", songs)
    assert [c.args[0] for c in client.lookup_release.call_args_list] == ["stored", "rel-1"]


def test_match_album_searches_only_when_needed() -> None:
    """Don't search when a stored release has all songs."""
    client = fake_client()
    songs = album_songs()
    songs[Path("1.opus")].tags_from(ORIGINAL)["musicbrainz_albumid"] = ["rel-1"]
    assert MusicBrainzMatcher(client).match_album("Goodbyes", songs)
    client.search_releases.assert_not_called()
