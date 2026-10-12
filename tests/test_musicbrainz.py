"""Tests for musicbrainz.py."""
from typing import Any

from retag_opus import musicbrainz

JsonDict = dict[str, Any]


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
        "performer:vocals": ["Ben Ivor"],
        "performer:background vocals": ["Ann Choir"],
        "performer:guitar": ["Gus Tar"],
        "performer:drums": ["Drum Mer"],
        "producer": ["Pro Ducer", "P. Ducer"],
        "composer": ["Com Poser"],
        "lyricist": ["Wri Ter"],
    }


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
        "performer:vocals": ["Ben Ivor"],
        "performer:background vocals": ["Ann Choir"],
        "performer:guitar": ["Gus Tar"],
        "performer:drums": ["Drum Mer"],
        "producer": ["Pro Ducer", "P. Ducer"],
        "composer": ["Com Poser"],
        "lyricist": ["Wri Ter"],
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
