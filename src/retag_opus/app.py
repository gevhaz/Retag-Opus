"""An app to transfer YouTube data about a song to the song metadata.

This in ann app that parses a "description" tag in a song, corresponding
to the youtube version of the song, and parse it to produce other tags.
Existing tags are also used to produce new ones, e.g. moving strings
like "2020 Remix" from the title tag to the version tag.
"""

import os
import re
import tomllib
from collections.abc import Sequence
from copy import deepcopy
from pathlib import Path

from mutagen.oggopus import OggOpus
from simple_term_menu import TerminalMenu

from retag_opus import cli, constants, description_parser, messages, styles, tags_parser
from retag_opus.exceptions import UserExitException
from retag_opus.musicbrainz import MusicBrainzMatcher
from retag_opus.tag_table import (
    MUSICBRAINZ,
    ORIGINAL,
    PARSED_FROM_ORIGINAL,
    PARSED_FROM_YOUTUBE,
    REMOVED_TAG,
    YOUTUBE,
    TagTable,
)
from retag_opus.tags import Tags


def get_config_path() -> Path:
    """Return the path to the configuration file."""
    config_dir = os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config"
    return Path(config_dir) / "retag.toml"


def file_path_to_song_name(file_path: Path) -> str:
    """Convert file name to readable string.

    Produce a string with song title and artist on a readable format
    from the name of the file being worked with.
    """
    text_to_print = str(file_path)
    basename_match = re.match(r"(.+/)*(.*).opus", text_to_print)
    if basename_match:
        text_to_print = basename_match.group(2)
        playlist_match = re.match(r"<(.*)> - <(.*?)(?: - Topic)*> - <(.*)> - <(.*)>", text_to_print)
        artist_title_match = re.match("<(.*?)(?: - Topic)*> - <(.*)>", text_to_print)
        title_only_match = re.match("<(.*)>", text_to_print)
        if playlist_match:
            text_to_print = playlist_match.group(2) + " - " + playlist_match.group(3)
        elif artist_title_match:
            text_to_print = artist_title_match.group(1) + " - " + artist_title_match.group(2)
        elif title_only_match:
            text_to_print = title_only_match.group(1)
    return text_to_print


def get_description(tags: Tags) -> list[str] | None:
    """Get the YouTube description from the tags, if there is one."""
    description_lines = tags.get("synopsis")
    if description_lines is None:
        description_lines = tags.get("description")
    return description_lines


def get_album(file_path: Path) -> str | None:
    """Get the album of a song from its YouTube description.

    :param file_path: The song to get the album for.

    :return: The album, or None if the description doesn't have one.
    """
    original_tags: Tags = dict(OggOpus(file_path).items())  # type: ignore
    description_lines = get_description(original_tags)
    if not description_lines:
        return None
    description_tags = description_parser.parse("\n".join(description_lines))
    album = description_tags.get("album", [""])[0].strip()
    return album or None


def group_by_album(files: list[Path]) -> dict[Path, str]:
    """Find out which songs are on the same album as another song.

    Songs with the same album name (ignoring case) in the YouTube
    description are considered to be from the same album.

    :param files: All songs to be retagged.

    :return: The album of each song that shares album with another,
        written as in the description of the first of its songs.
    """
    album_per_song: dict[Path, str] = {}
    for file_path in files:
        album = get_album(file_path)
        if album is not None:
            album_per_song[file_path] = album

    # Albums whose names only differ in case are the same album
    songs_per_album: dict[str, list[Path]] = {}
    for file_path, album in album_per_song.items():
        songs_per_album.setdefault(album.casefold(), []).append(file_path)

    shared_album_per_song: dict[Path, str] = {}
    for songs_on_album in songs_per_album.values():
        if len(songs_on_album) > 1:
            album = album_per_song[songs_on_album[0]]
            messages.info(
                f"{len(songs_on_album)} songs are from the album '{album}'. Album artist, date, genre "
                "and album saved for one of them will be saved for all of them."
            )
            for file_path in songs_on_album:
                shared_album_per_song[file_path] = album
    return shared_album_per_song


def update_album_level_tags(files: list[Path], album_level_tags: Tags) -> None:
    """Set the album level tags of other songs on the same album.

    :param files: The songs to update.
    :param album_level_tags: The album level tags to set.
    """
    for file_path in files:
        opus_file: OggOpus = OggOpus(file_path)  # type: ignore
        any_tag_changed = False
        for tag_name, values in album_level_tags.items():
            if opus_file.get(tag_name) != values:  # type: ignore
                opus_file[tag_name] = values
                any_tag_changed = True
        if any_tag_changed:
            opus_file.save()
            messages.success(f"Album level tags saved for file: {file_path_to_song_name(file_path)}")


def read_song(file_path: Path) -> tuple[OggOpus, TagTable]:
    """Read the tags of a song and parse new tags from them.

    :param file_path: The song to read.

    :return: The song's file, for saving changes to it, and
        its tags from all sources.
    """
    # 1. Read the data and make basic improvements
    opus_file: OggOpus = OggOpus(file_path)  # type: ignore
    original_tags: Tags = dict(opus_file.items())  # type: ignore
    tags = TagTable()
    tags.length = getattr(getattr(opus_file, "info", None), "length", None)

    tags.set_tags(ORIGINAL, original_tags)
    tags.discard_upload_date()
    tags.resolved = deepcopy(original_tags)

    tags.set_tags(PARSED_FROM_ORIGINAL, tags_parser.alternatives(original_tags))

    # 2. Get description
    description_lines = get_description(original_tags)

    # 3. If description exists, send it to be parsed
    if description_lines:
        description = "\n".join(description_lines)
        youtube_tags = description_parser.parse(description)
        tags.set_tags(YOUTUBE, youtube_tags)
        tags.youtube_is_auto_generated = description_parser.is_auto_generated(description)
        tags.add_source_tag()

        tags.set_tags(PARSED_FROM_YOUTUBE, tags_parser.alternatives(youtube_tags))

    return opus_file, tags


def save_tags(opus_file: OggOpus, tags: Tags) -> None:
    """Write tags to a song's file, deleting those marked as removed."""
    for tag_name, values in tags.items():
        if values == REMOVED_TAG:
            opus_file.pop(tag_name, None)  # type: ignore
        else:
            opus_file[tag_name] = values
    opus_file.save()


def match_albums(matcher: MusicBrainzMatcher, shared_album_per_song: dict[Path, str]) -> dict[Path, Tags]:
    """Identify each album on MusicBrainz, with all its songs at once.

    :param matcher: Used for finding the albums on MusicBrainz.
    :param shared_album_per_song: The album of each song that shares
        album with another.

    :return: Tags from MusicBrainz for each song whose album was found.
    """
    songs_per_album: dict[str, dict[Path, TagTable]] = {}
    for file_path, album in shared_album_per_song.items():
        _, tags = read_song(file_path)
        songs_per_album.setdefault(album, {})[file_path] = tags

    musicbrainz_tags_per_song: dict[Path, Tags] = {}
    for album, songs in songs_per_album.items():
        musicbrainz_tags_per_song.update(matcher.match_album(album, songs))
    return musicbrainz_tags_per_song


def run(argv: Sequence[str] | None = None) -> int:
    """Run all the functionality of the app."""
    args = cli.parse_arguments(argv)
    music_dir = Path(args.directory).resolve()
    try:
        with open(get_config_path(), "rb") as config_file:
            config = tomllib.load(config_file)
    except FileNotFoundError:
        config = {}
    if not music_dir.is_dir():
        messages.error(f"{args.directory} is not a directory!")
        return 1

    opus_files = list(filter(Path.is_file, music_dir.glob("*.opus")))
    if not opus_files:
        messages.warning(f"There appears to be no .opus files in the provided directory {args.directory}")
        return 0

    shared_album_per_song: dict[Path, str] = {}
    if not args.individual:
        shared_album_per_song = group_by_album(opus_files)
    # Album level tags saved for an earlier song on each album
    saved_album_level_tags: dict[str, Tags] = {}

    use_musicbrainz = args.musicbrainz if args.musicbrainz is not None else config.get("musicbrainz", False)
    # One matcher for all songs, so they share its cache and rate limit
    matcher = MusicBrainzMatcher() if use_musicbrainz else None
    musicbrainz_tags_per_song = match_albums(matcher, shared_album_per_song) if matcher is not None else {}
    tags_to_delete = config.get("tags_to_delete", [])
    strings_to_delete_tags_based_on = config.get("strings_to_delete_tags_based_on", [])

    for song_index, file_path in enumerate(opus_files):
        redo = True
        shared_album = shared_album_per_song.get(file_path)
        song_name = file_path_to_song_name(file_path)
        while redo:
            redo = False
            # Print info about file and progress
            print()
            messages.info(f"Song {song_index + 1} of {len(opus_files)}")
            messages.info(f"----- Song: {song_name} -----")

            opus_file, tags = read_song(file_path)
            description_lines = get_description(tags.tags_from(ORIGINAL))
            if matcher is not None:
                if file_path not in musicbrainz_tags_per_song:
                    musicbrainz_tags_per_song[file_path] = matcher.match_song(tags)
                tags.set_tags(MUSICBRAINZ, musicbrainz_tags_per_song[file_path])

            # 4.5 Get rid of shady tags
            tags.prune_resolved_tags(tags_to_delete, strings_to_delete_tags_based_on)

            if args.grouping is not None:
                tags.resolved["grouping"] = [args.grouping]

            # 4.6 Use the same album level tags as for earlier songs on
            # the same album
            if shared_album is not None and shared_album in saved_album_level_tags:
                tags.apply_album_level_tags(saved_album_level_tags[shared_album])

            if not tags.check_any_new_data_exists():
                messages.warning("No new data exists. Skipping song.")
                break

            # 4. For each field, if there are conflicts, ask user input
            try:
                tags.resolve_metadata()
            except UserExitException as e:
                print(f"RetagOpus exited successfully: {e}")
                return 0

            # 4.7 Don't ask about saving when nothing that the user can
            # check would change, but save new MusicBrainz IDs, which
            # the user can only check by the MusicBrainz match
            changed_tag_names = tags.changed_tags()
            if all(tag.startswith(constants.MUSICBRAINZ_ID_PREFIX) for tag in changed_tag_names):
                if changed_tag_names:
                    save_tags(opus_file, tags.resolved)
                    messages.success(f"MusicBrainz IDs saved for file: {song_name}")
                else:
                    messages.warning("Nothing to change. Skipping song.")
                break

            # 5. Show user final result and ask if it should be saved or
            # retried, or song skipped
            reshow_choices = True

            while reshow_choices:
                print("Final result:")
                tags.print_resolved()
                reshow_choices = False
                options = [
                    "[p] pass",
                    "[s] save",
                    "[r] reset",
                    "[m] modify tag",
                    "[d] delete item in tag",
                    "[y] youtube description",
                    "[a] all metadata",
                    "[e] resolved metadata",
                    "[q] quit",
                ]
                terminal_menu = TerminalMenu(options, title="What do you want to do?")
                choice = terminal_menu.show()
                print("-" * 40)

                action = "[q] quit"
                if choice is not None and not isinstance(choice, tuple):
                    action = options[choice]

                match action:
                    case "[q] quit":
                        print("RetagOpus exited successfully: Skipping this and all later songs")
                        return 0
                    case "[s] save":
                        save_tags(opus_file, tags.resolved)
                        messages.success(f"Metadata saved for file: {song_name}")
                        if shared_album is not None:
                            saved_album_level_tags[shared_album] = tags.get_album_level_tags()
                            other_songs = []
                            for other_file_path, other_album in shared_album_per_song.items():
                                if other_album == shared_album and other_file_path != file_path:
                                    other_songs.append(other_file_path)
                            update_album_level_tags(other_songs, saved_album_level_tags[shared_album])
                    case "[r] reset":
                        print(f"Trying to improve metadata again for file: {song_name}")
                        redo = True
                    case "[m] modify tag":
                        tags.modify_resolved_field()
                        messages.info("Current metadata to save:")
                        tags.print_resolved()
                        reshow_choices = True
                    case "[d] delete item in tag":
                        tags.delete_tag_item()
                        reshow_choices = True
                    case "[p] pass":
                        messages.warning(f"Pass. Skipping song: {song_name}")
                    case "[y] youtube description":
                        if description_lines:
                            messages.info("Original YouTube description:")
                            print(styles.youtube("\n".join(description_lines)))
                        else:
                            messages.error("No YouTube description tag for this song.")
                        reshow_choices = True
                    case "[a] all metadata":
                        messages.info("All old and new metadata suggested for this file:")
                        tags.print_all()
                        reshow_choices = True
                    case "[e] resolved metadata":
                        messages.info("Current metadata to save:")
                        tags.print_resolved()
                        reshow_choices = True
                    case _:
                        messages.error("Something went wrong, starting over")
                        redo = True

    return 0
