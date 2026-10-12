"""Module for identifying songs on MusicBrainz and turning them into tags."""
from typing import Final

from retag_opus import constants
from retag_opus.musicbrainz_client import JsonDict

Tags = dict[str, list[str]]

# MusicBrainz instrument names that differ from the names in the
# performer tags.
INSTRUMENT_ALIASES: Final[dict[str, str]] = {
    "drums (drum set)": "drums",
    "drum set": "drums",
    "synthesiser": "synthesizer",
    "electric bass guitar": "bass guitar",
    "tenor saxophone": "saxophone",
    "alto saxophone": "saxophone",
}

# Relationship types between a recording or a work and an artist, and
# the tag the artist is put in. Vocals and instruments are handled
# separately since they depend on the relationship attributes.
RELATION_TAGS: Final[dict[str, str]] = {
    "producer": "producer",
    "arranger": "arranger",
    "instrument arranger": "arranger",
    "vocal arranger": "arranger",
    "conductor": "conductor",
    "programming": "performer:programming",
    "composer": "composer",
    "lyricist": "lyricist",
    "writer": "lyricist",
}


def credited_names(artist_credit: list[JsonDict]) -> list[str]:
    """Get the names of all credited artists."""
    return [credit["name"] for credit in artist_credit]


def joined_credit(artist_credit: list[JsonDict]) -> str:
    """Get an artist credit the way it's printed, e.g. 'A feat. B'."""
    return "".join(credit["name"] + credit.get("joinphrase", "") for credit in artist_credit)


def artist_ids(artist_credit: list[JsonDict]) -> list[str]:
    """Get the MusicBrainz IDs of all credited artists."""
    return [credit["artist"]["id"] for credit in artist_credit]


def relation_tag_names(relation: JsonDict) -> list[str]:
    """Get the tags that the artist of a relationship should be put in.

    The tags are the ones Retag Opus already uses for credits parsed from
    YouTube descriptions, so that values from MusicBrainz and from
    YouTube end up in the same tag and can be compared. That's why some
    MusicBrainz names are translated, e.g. the instrument "drums (drum
    set)" to the tag "performer:drums", and why instruments without a
    performer tag in Retag Opus are left out.
    """
    relation_type = relation.get("type", "")
    attributes: list[str] = relation.get("attributes") or []
    if relation_type == "vocal":
        if "background vocals" in attributes:
            return ["performer:background vocals"]
        return ["performer:vocals"]
    if relation_type == "instrument":
        tag_names = []
        for instrument in attributes:
            tag_name = f"performer:{INSTRUMENT_ALIASES.get(instrument, instrument)}"
            if tag_name in constants.performer_tags:
                tag_names.append(tag_name)
        return tag_names
    if relation_type in RELATION_TAGS:
        return [RELATION_TAGS[relation_type]]
    return []


def credits_from_relations(relations: list[JsonDict], credits: Tags | None = None) -> Tags:
    """Turn artist relationships into credit tags like composer.

    Relationships of works, such as the composer of the song a
    recording is a performance of, are included. Relationships that have
    no corresponding tag are ignored.

    :param relations: Relationships of a recording or work.
    :param credits: Credits found so far, which are added to.

    :return: Credit tags with the names the artists are credited as.
    """
    credits = {} if credits is None else credits
    for relation in relations:
        if relation.get("target-type") == "work":
            # The work, i.e. the song itself, has e.g. the composers
            credits_from_relations(relation["work"].get("relations", []), credits)
        elif relation.get("target-type") == "artist":
            name = relation.get("target-credit") or relation["artist"]["name"]
            for tag_name in relation_tag_names(relation):
                if name not in credits.setdefault(tag_name, []):
                    credits[tag_name].append(name)
    return credits


def release_tracks(release: JsonDict) -> list[tuple[JsonDict, JsonDict]]:
    """Get all tracks on a release together with their medium, e.g. CD."""
    tracks = []
    for medium in release.get("media", []):
        for track in medium.get("tracks", []):
            tracks.append((medium, track))
    return tracks


def track_tags(release: JsonDict, medium: JsonDict, track: JsonDict) -> Tags:
    """Turn a track on a release into tags.

    MusicBrainz identifiers are stored in the same tags as MusicBrainz
    Picard uses, so that later runs and other tools can use them.
    """
    recording = track["recording"]
    artist_credit = track.get("artist-credit") or recording.get("artist-credit", [])
    album_credit = release.get("artist-credit", [])
    tags: Tags = {
        "title": [track.get("title") or recording["title"]],
        "artist": credited_names(artist_credit),
        "album": [release["title"]],
        "albumartist": [joined_credit(album_credit)] if album_credit else [],
        "date": [release["date"]] if release.get("date") else [],
        "tracknumber": [str(track["position"])],
        "totaltracks": [str(medium["track-count"])],
        "discnumber": [str(medium["position"])],
        "totaldiscs": [str(len(release["media"]))],
        "musicbrainz_trackid": [recording["id"]],
        "musicbrainz_artistid": artist_ids(artist_credit),
        "musicbrainz_albumid": [release["id"]],
        "musicbrainz_albumartistid": artist_ids(album_credit),
        "musicbrainz_releasegroupid": [release["release-group"]["id"]] if "release-group" in release else [],
    }
    tags.update(credits_from_relations(recording.get("relations", [])))
    # Leave out the tags that MusicBrainz has no value for
    return {tag_name: value for tag_name, value in tags.items() if value}
