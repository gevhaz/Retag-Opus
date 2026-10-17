"""Module for identifying songs on MusicBrainz and turning them into tags.

Songs from the same album are identified together as a release, when
there is a release that has all of them. Other songs are identified by
their MusicBrainz ID if the file has one, and otherwise by searching
for them. A search result is only used without asking when its title
is in what was searched for and its length is the song's.
"""
import re
from pathlib import Path
from typing import Final

from simple_term_menu import TerminalMenu

from retag_opus import constants, messages, styles, utils
from retag_opus.music_tags import MusicTags
from retag_opus.musicbrainz_client import JsonDict, MusicBrainzClient, MusicBrainzError

Tags = dict[str, list[str]]

MIN_RELEASE_SEARCH_SCORE: Final[int] = 90
MAX_DURATION_DIFFERENCE_SECONDS: Final[float] = 3.0
MAX_RELEASE_LOOKUPS: Final[int] = 3

# Tags that describe the release a song is on, rather than the song
ALBUM_AND_RELEASE_TAGS: Final[list[str]] = ["album", "albumartist"] + constants.release_tags

# Attributes of vocal and instrument relationships that say how the
# artist took part rather than in what role, e.g. "guest". Like Picard,
# they're left out of the role.
CREDIT_ATTRIBUTES: Final[set[str]] = {"guest", "additional", "minor", "solo"}

# Roles of vocal and instrument relationships whose attributes don't
# say which vocals or instruments, named as in Picard
DEFAULT_ROLES: Final[dict[str, str]] = {"vocal": "vocals", "instrument": "instruments"}

# Relationship types between a recording or a work and an artist, and
# the tag the artist is put in, as in Picard. Vocals and instruments are
# handled separately since they depend on the relationship attributes.
RELATION_TAGS: Final[dict[str, str]] = {
    "producer": "producer",
    "arranger": "arranger",
    "instrument arranger": "arranger",
    "vocal arranger": "arranger",
    "orchestrator": "arranger",
    "conductor": "conductor",
    "mix": "mixer",
    "engineer": "engineer",
    "audio": "engineer",
    "sound": "engineer",
    "live sound": "engineer",
    "composer": "composer",
    "lyricist": "lyricist",
    "librettist": "lyricist",
    "writer": "writer",
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

    The tags are named as in MusicBrainz Picard. Vocals and instruments
    get one performer tag each, named after the vocals or instrument on
    MusicBrainz, e.g. "performer:drums (drum set)". Picard instead puts
    all instruments of a relationship in one tag, e.g. "performer:guitar
    and piano", but then they can't be compared with the performer tags
    from YouTube descriptions.
    """
    relation_type = relation.get("type", "")
    if relation_type in DEFAULT_ROLES:
        roles = []
        for attribute in relation.get("attributes") or []:
            if attribute not in CREDIT_ATTRIBUTES:
                roles.append(attribute)
        if not roles:
            roles = [DEFAULT_ROLES[relation_type]]
        tag_names = []
        for role in roles:
            tag_names.append(constants.PERFORMER_PREFIX + role)
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


def song_text(tags: MusicTags) -> str:
    """Get the words a song is known by, to search for it and match it.

    Those are the title and artists from the YouTube description, e.g.
    "Proper Goodbyes The Global Ben Ivor". Without a description, it's
    the existing title, which is then usually a YouTube video title that
    also names e.g. the artists and the movie the song is from, like
    "KAUN TUJHE Full Video | M.S. DHONI -THE UNTOLD STORY |Amaal Mallik".
    """
    # Tags are lists of values, but a song only has one title
    youtube_titles = tags.youtube.get("title", [])
    if youtube_titles:
        youtube_artists = tags.youtube.get("artist", [])
        return " ".join([youtube_titles[0]] + youtube_artists)
    existing_titles = tags.original.get("title", [])
    if existing_titles:
        return existing_titles[0]
    return ""


def words(text: str) -> set[str]:
    """Get the words in text, regardless of typography and case."""
    return set(re.findall(r"\w+", utils.normalize(text)))


def title_matches(title: str, text: str) -> bool:
    """Check whether a title from MusicBrainz is in the text.

    Only the main title, before any "(" or ":", has to be in the text.
    Parentheses usually describe the version, e.g. "Title (live)", and
    video titles often leave out what comes after a colon, e.g. "The
    Touch of Love" in "Nee Paartha Vizhigal: The Touch of Love". This
    also lets e.g. "Requiem: Lacrimosa" match a text with just
    "Requiem", but the length has to match too, and fit() prefers
    results whose whole title is in the text.
    """
    main_title = words(re.split(r"[(\[:]", title)[0])
    return bool(main_title) and main_title <= words(text)


def fit(recording: JsonDict, text: str) -> tuple[int, int]:
    """Rank how well a recording fits a song, lower being better.

    The recording whose title has fewest words that weren't searched
    for fits best, e.g. "Title" rather than "Title (5.1 mix)" if only
    "Title" was searched for. Of those, the one on the most releases
    does, since that's usually the original rather than e.g. a mix
    that was only released once.
    """
    unsearched_title_words = words(recording.get("title", "")) - words(text)
    release_count = len(recording.get("releases", []))
    return len(unsearched_title_words), -release_count


def format_length(milliseconds: int | None) -> str:
    """Format a length in milliseconds as e.g. "3:39".

    MusicBrainz doesn't know the length of every recording, and the
    length of a song file may be unknown too. Then "?:??" is shown.
    """
    if milliseconds is None:
        return "?:??"
    seconds = round(milliseconds / 1000)
    return f"{seconds // 60}:{seconds % 60:02d}"


def duration_matches(milliseconds: int | None, duration: float | None) -> bool:
    """Check whether a length from MusicBrainz is the song's duration."""
    if milliseconds is None or duration is None:
        return False
    return abs(milliseconds / 1000 - duration) <= MAX_DURATION_DIFFERENCE_SECONDS


def choose_release(releases: list[JsonDict], tags: MusicTags) -> JsonDict | None:
    """Choose which of the releases of a recording a song is from.

    The release whose ID is in the song's file is preferred, then
    releases with the album name in the song's tags, ignoring e.g.
    "(2011 Remaster)", then official releases, and of those the
    earliest.
    """
    if not releases:
        return None
    stored_release_ids = tags.original.get("musicbrainz_albumid", [])
    album_names_in_tags = set()
    for album_name in tags.youtube.get("album", []) + tags.original.get("album", []):
        album_names_in_tags.add(utils.normalize(utils.prune_title(album_name)))

    def preference(release: JsonDict) -> tuple[bool, bool, bool, str]:
        """Sort key that puts the preferred releases first."""
        is_stored = release["id"] in stored_release_ids
        has_album_name = utils.normalize(utils.prune_title(release.get("title", ""))) in album_names_in_tags
        is_official = release.get("status") == "Official"
        date = release.get("date") or "9999"  # Unknown dates last
        # False sorts before True, so releases with a property come first
        return not is_stored, not has_album_name, not is_official, date

    # Tuples are compared item by item, so this is the release that's
    # preferred by the first property where the releases differ
    return min(releases, key=preference)


def matching_track_index(tracks: list[tuple[JsonDict, JsonDict]], tags: MusicTags) -> int | None:
    """Find the track that a song is, by its title and, if known, length.

    :return: The index of the track in tracks, or None if no track is
        the song.
    """
    text = song_text(tags)
    for index, (_, track) in enumerate(tracks):
        same_title = title_matches(track["title"], text)
        same_length = tags.duration is None or duration_matches(track.get("length"), tags.duration)
        if same_title and same_length:
            return index
    return None


def match_tracks(release: JsonDict, songs: dict[Path, MusicTags]) -> dict[Path, Tags]:
    """Match each song to its own track on the release.

    :return: Tags for each song, or no tags if any song isn't on the
        release.
    """
    unmatched_tracks = release_tracks(release)
    tags_per_song: dict[Path, Tags] = {}
    for path, tags in songs.items():
        index = matching_track_index(unmatched_tracks, tags)
        if index is None:
            return {}
        # Each track can only be one of the songs
        medium, track = unmatched_tracks.pop(index)
        tags_per_song[path] = track_tags(release, medium, track)
    return tags_per_song


def stored_release_ids(songs: dict[Path, MusicTags]) -> list[str]:
    """Get the IDs of the MusicBrainz releases stored in the songs' files."""
    release_ids: list[str] = []
    for tags in songs.values():
        for release_id in tags.original.get("musicbrainz_albumid", []):
            if release_id not in release_ids:
                release_ids.append(release_id)
    return release_ids


def format_release(release: JsonDict) -> str:
    """Format a release with when and where it was released.

    E.g. "'A Night at the Opera' (1975-11-21, GB)", since a title alone
    doesn't say which of the many releases of an album it is.
    """
    details = []
    for detail in [release.get("date"), release.get("country")]:
        if detail:
            details.append(detail)
    if not details:
        return f"'{release['title']}'"
    return f"'{release['title']}' ({', '.join(details)})"


def match_message(track: JsonDict, release: JsonDict) -> str:
    """Get the message saying which track a song was matched to.

    E.g. "MusicBrainz: Found 'Love of My Life' (live, 1981-11-24:
    Montreal Forum) on 'Rock Montreal' (2007, CA)." The version of the
    recording and the release make a wrong match stand out.
    """
    version = track["recording"].get("disambiguation")
    title = f"'{track['title']}'"
    if version:
        title += f" ({version})"
    return f"MusicBrainz: Found {title} on {format_release(release)}."


def search_result_entry(recording: JsonDict) -> str:
    """Format a search result as a menu entry.

    E.g. "Love of My Life - Queen (3:39, on 'A Night at the Opera')".
    The menu treats "|" as the start of preview data, and "[" as the
    start of a shortcut key, so they're replaced.
    """
    recording_version = recording.get("disambiguation")
    releases_with_recording = recording.get("releases")
    entry = f"{recording.get('title', '')} - {joined_credit(recording.get('artist-credit', []))}"
    entry += f" ({format_length(recording.get('length'))}"
    if recording_version:
        entry += f", {recording_version}"
    if releases_with_recording:
        entry += f", on '{releases_with_recording[0].get('title', '')}'"
    return entry.replace("|", "/").replace("[", "(").replace("]", ")") + ")"


class MusicBrainzMatcher:
    """Find songs on MusicBrainz, asking the user when unsure."""

    def __init__(self, client: MusicBrainzClient | None = None) -> None:
        """Create matcher that uses the given client."""
        self.client = client if client is not None else MusicBrainzClient()
        self.disabled = False

    def disable(self, error: MusicBrainzError) -> None:
        """Stop using MusicBrainz, so that later songs don't wait for it."""
        messages.error(f"MusicBrainz: {error}. Not using MusicBrainz for the rest of this run.")
        self.disabled = True

    def match_song(self, tags: MusicTags) -> Tags:
        """Get tags for a song from MusicBrainz.

        When the album is set manually, the release found for the song
        isn't that album, so tags describing the release are left out.

        :return: Tags from MusicBrainz, or no tags if the song wasn't
            found, the user skipped it, or MusicBrainz can't be used.
        """
        if self.disabled:
            return {}
        messages.info("Looking up the song on MusicBrainz...")
        try:
            recording = self.find_recording(tags)
            release_summary = choose_release(recording.get("releases", []), tags) if recording else None
            release = self.client.lookup_release(release_summary["id"]) if release_summary else None
        except MusicBrainzError as e:
            self.disable(e)
            return {}
        if recording is None or release is None:
            return {}

        for medium, track in release_tracks(release):
            if track["recording"]["id"] == recording["id"]:
                print(styles.musicbrainz(match_message(track, release)))
                song_tags = track_tags(release, medium, track)
                if tags.manual_album_set:
                    # The release found for the song isn't the album the user set
                    for tag_name in ALBUM_AND_RELEASE_TAGS:
                        song_tags.pop(tag_name, None)
                return song_tags
        return {}

    def match_album(self, album: str, songs: dict[Path, MusicTags]) -> dict[Path, Tags]:
        """Get tags for songs from the same album from MusicBrainz.

        The songs are matched to the tracks of releases that may be the
        album, until a release has all of them: first the releases whose
        IDs are in the songs' files, and then a few releases found by
        searching. If no release has all of them, e.g. because the album
        is the user's own collection, the songs have to be looked up one
        by one.

        :return: Tags for each song, or no tags if no release has all of
            them.
        """
        if self.disabled:
            return {}
        messages.info(f"Looking up the album '{album}' on MusicBrainz...")
        try:
            for release_id in stored_release_ids(songs):
                tags_per_song = self.match_release(release_id, album, songs)
                if tags_per_song:
                    return tags_per_song
            # Looking up a release takes at least a second, so only the
            # likeliest ones are tried
            for release_id in self.search_album_releases(album, songs)[:MAX_RELEASE_LOOKUPS]:
                tags_per_song = self.match_release(release_id, album, songs)
                if tags_per_song:
                    return tags_per_song
        except MusicBrainzError as e:
            self.disable(e)
            return {}
        messages.warning(f"MusicBrainz: No release of '{album}' has all {len(songs)} songs.")
        return {}

    def match_release(self, release_id: str, album: str, songs: dict[Path, MusicTags]) -> dict[Path, Tags]:
        """Match the songs of an album to the tracks of a release.

        :return: Tags for each song, or no tags if any song isn't on the
            release.
        """
        release = self.client.lookup_release(release_id)
        if release is None:
            return {}
        tags_per_song = match_tracks(release, songs)
        if tags_per_song:
            found = f"MusicBrainz: Found all {len(songs)} songs from '{album}' on {format_release(release)}."
            print(styles.musicbrainz(found))
        return tags_per_song

    def search_album_releases(self, album: str, songs: dict[Path, MusicTags]) -> list[str]:
        """Search for releases that may be the album, likeliest first.

        Releases with the album's name, ignoring e.g. "(2011 Remaster)",
        by the songs' artist are searched for. Those that match the
        search well and have room for all the songs may be the album. Of
        them, those with fewest tracks, and of those the earliest, come
        first, so that the original standard edition is preferred over
        e.g. a deluxe edition or a later remaster that also has the songs.

        :return: IDs of the releases.
        """
        artist = None
        for tags in songs.values():
            youtube_artists = tags.youtube.get("artist")
            if youtube_artists:
                artist = youtube_artists[0]
                break

        candidates = []
        for release in self.client.search_releases(utils.prune_title(album), artist):
            matches_search = release.get("score", 0) >= MIN_RELEASE_SEARCH_SCORE
            has_room_for_songs = release.get("track-count", 0) >= len(songs)
            if matches_search and has_room_for_songs:
                candidates.append(release)

        def preference(release: JsonDict) -> tuple[int, str]:
            """Sort key that puts releases with fewest tracks first, earliest first."""
            return release.get("track-count", 0), release.get("date") or "9999"

        candidates.sort(key=preference)
        return [release["id"] for release in candidates]

    def find_recording(self, tags: MusicTags) -> JsonDict | None:
        """Find the recording of a song, with the releases it's on.

        A MusicBrainz ID in the file is used if there is one. Otherwise
        the song is searched for: by exact title and artist if they're
        in the YouTube description, and otherwise by the words in the
        title, since a video title mixes the song title with artists,
        movies, and other words. A result is used without asking if its
        main title is among the words searched for and it's as long as
        the song. Otherwise the user picks the result.

        :return: The recording, or None if the user skipped the song.
        """
        stored_recording_ids = tags.original.get("musicbrainz_trackid", [])
        if stored_recording_ids:
            recording = self.client.lookup_recording(stored_recording_ids[0])
            if recording is not None:
                return recording

        text = song_text(tags)
        youtube_titles = tags.youtube.get("title", [])
        youtube_artists = tags.youtube.get("artist", [])
        if youtube_titles and youtube_artists:
            results = self.client.search_recordings(utils.prune_title(youtube_titles[0]), youtube_artists[0])
        elif text:
            results = self.client.search_recordings_by_words(text)
        else:
            results = []
        while True:
            confident_results = [
                result
                for result in results
                if title_matches(result.get("title", ""), text)
                and duration_matches(result.get("length"), tags.duration)
            ]
            if confident_results:
                # The result that fits the song best, see fit()
                return min(confident_results, key=lambda result: fit(result, text))
            choice = self.ask_for_recording(results, text, tags.duration)
            if choice is not True:
                return choice or None
            text = input(f"Search MusicBrainz for [{text}]: ").strip() or text
            results = self.client.search_recordings_by_words(text) if text else []

    @staticmethod
    def ask_for_recording(results: list[JsonDict], text: str, duration: float | None) -> JsonDict | bool:
        """Let the user pick a recording from search results.

        :return: The chosen recording, True if the user wants to search
            for something else, or False if the user skips the song.
        """
        length = format_length(round(duration * 1000)) if duration is not None else "?:??"
        found = "Results" if results else "Nothing found"
        title = f"MusicBrainz: {found} for '{text}'. The song is {length} long."
        entries = [search_result_entry(recording) for recording in results]
        entries += ["[e] Edit search", "[s] Skip MusicBrainz for this song"]
        choice = TerminalMenu(entries, title=title).show()
        if not isinstance(choice, int) or choice == len(results) + 1:
            return False
        return True if choice == len(results) else results[choice]
