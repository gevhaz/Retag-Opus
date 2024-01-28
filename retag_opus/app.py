"""An app to transfer YouTube data about a song to the song metadata.

This in ann app that parses a "description" tag in a song, corresponding
to the youtube version of the song, and parse it to produce other tags.
Existing tags are also used to produce new ones, e.g. moving strings
like "2020 Remix" from the title tag to the version tag.
"""

import os
import tomllib
from copy import deepcopy
from pathlib import Path
from typing import Sequence

from colorama import Fore, init
from mutagen.oggopus import OggOpus
from simple_term_menu import TerminalMenu

from retag_opus import colors
from retag_opus.cli import Cli
from retag_opus.description_parser import DescriptionParser
from retag_opus.exceptions import UserExitException
from retag_opus.music_tags import REMOVED_TAG, MusicTags
from retag_opus.tags_parser import TagsParser
from retag_opus.utils import Utils

init(autoreset=True)

Tags = dict[str, list[str]]

CONFIG_DIR = Path(os.environ.get("XDG_CONFIG_DIR", Path.home() / ".config"))
CONFIG_PATH = CONFIG_DIR / "retag.toml"


def run(argv: Sequence[str] | None = None) -> int:
    """Run all the functionality of the app."""
    args = Cli.parse_arguments(argv)
    music_dir = Path(args.dir).resolve()
    try:
        with open(CONFIG_PATH, "rb") as f:
            config = tomllib.load(f)
    except FileNotFoundError:
        config = {}
    if not music_dir.is_dir():
        print(Fore.RED + f"{args.dir} is not a directory!")
        return 1

    all_files = list(filter(Path.is_file, Path(music_dir).glob("*.opus")))
    if not all_files:
        print(Fore.YELLOW + f"There appears to be no .opus files in the provided directory {args.dir}")
        return 0

    for idx, file_path in enumerate(all_files):
        redo = True
        file_name = Utils().file_path_to_song_data(file_path)
        while redo:
            redo = False
            # Print info about file and progress
            print("\n" + Fore.BLUE + f"Song {idx + 1} of {len(all_files)}" + Fore.RESET)
            print(Fore.BLUE + f"----- Song: {file_name} -----" + Fore.RESET)

            # 1. Read the data and make basic improvements
            old_metadata: OggOpus = OggOpus(file_path)  # type: ignore
            old_tags: Tags = {}
            tag_source = {}
            for key, val in old_metadata.items():  # type: ignore
                old_tags[key] = val
            for key in old_tags.keys():
                tag_source[key] = colors.md_col
            tags = MusicTags(manual_album_set=args.manual_album is not None)

            tags.original = old_tags
            tags.discard_upload_date()
            if args.manual_album is not None:
                tags.switch_album_to_disc_subtitle(args.manual_album)

            tags.resolved = deepcopy(old_tags)

            old_tags_parser = TagsParser(tags.original)
            old_tags_parser.parse_tags()
            old_tags_parser.split_select_original_tags()
            tags.fromtags = old_tags_parser.tags

            # 1.1 Manually set album
            if args.manual_album is not None:
                tags.resolved["album"] = [args.manual_album]

            # 2. Get description
            description_lines: list[str] | None = old_tags.get("synopsis")
            if description_lines is None:
                description_lines = old_tags.get("description")

            # 3. If description exists, send it to be parsed
            if description_lines:
                desc_parser = DescriptionParser(manual_album_set=args.manual_album is not None)
                description = "\n".join(description_lines)
                desc_parser.parse(description)
                tags.youtube = desc_parser.tags
                tags.add_source_tag()

                new_tags_parser = TagsParser(tags.youtube)
                new_tags_parser.parse_tags()
                tags.fromdesc = new_tags_parser.tags

            # 4.5 Get rid of shady tags
            tags_to_delete = config.get("tags_to_delete", [])
            strings_to_delete_tags_based_on = config.get("strings_to_delete_tags_based_on", [])
            tags.prune_resolved_tags(tags_to_delete, strings_to_delete_tags_based_on)

            if not tags.check_any_new_data_exists() and not args.manual_album:
                print(Fore.YELLOW + "No new data exists. Skipping song." + Fore.RESET)
                break

            # 4. For each field, if there are conflicts, ask user input
            try:
                tags.resolve_metadata()
            except UserExitException as e:
                print(f"RetagOpus exited successfully: {e}")
                return 0

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
                        for tag, data in tags.resolved.items():
                            if data == REMOVED_TAG:
                                old_metadata.pop(tag, None)  # type: ignore
                            else:
                                old_metadata[tag] = data
                        old_metadata.save()
                        print(Fore.GREEN + f"Metadata saved for file: {file_name}")
                    case "[r] reset":
                        print(f"Trying to improve metadata again for file: {file_name}")
                        redo = True
                    case "[m] modify tag":
                        tags.modify_resolved_field()
                        print(Fore.BLUE + "Current metadata to save:")
                        tags.print_resolved()
                        reshow_choices = True
                    case "[d] delete item in tag":
                        tags.delete_tag_item()
                        reshow_choices = True
                    case "[p] pass":
                        print(Fore.YELLOW + f"Pass. Skipping song: {file_name}")
                    case "[y] youtube description":
                        if description_lines:
                            print(Fore.BLUE + "Original YouTube description:")
                            print(colors.yt_col + "\n".join(description_lines))
                        else:
                            print(Fore.RED + "No YouTube description tag for this song.")
                        reshow_choices = True
                    case "[a] all metadata":
                        print(Fore.BLUE + "All old and new metadata suggested for this file:")
                        tags.print_all()
                        reshow_choices = True
                    case "[e] resolved metadata":
                        print(Fore.BLUE + "Current metadata to save:")
                        tags.print_resolved()
                        reshow_choices = True
                    case _:
                        print(Fore.RED + "Something went wrong, starting over")
                        redo = True

    return 0
