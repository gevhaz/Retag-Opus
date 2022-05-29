#!/usr/bin/env python3
"""
Script to parse a "description" tag in a song, corresponding to the youtube version of the song, and parse it to produce
other tags. Existing tags are also used to produce new ones, e.g. moving strings like "2020 Remix" from the title tag to
the version tag.
"""

from pathlib import Path

from colorama import Fore, init
from mutagen.oggopus import OggOpus
from simple_term_menu import TerminalMenu

from retag_opus import colors, constants
from retag_opus.cli import Cli
from retag_opus.description_parser import DescriptionParser
from retag_opus.music_tags import MusicTags
from retag_opus.tags_parser import TagsParser
from retag_opus.utils import Utils

init(autoreset=True)


def run() -> int:
    args = Cli.parse_arguments()
    music_dir = Path(args.dir).resolve()
    all_files = list(filter(Path.is_file, Path(music_dir).glob("*.opus")))

    if args.manual_album is not None:
        constants.all_tags["discsubtitle"] = constants.all_tags["album"].copy()
        constants.all_tags["discsubtitle"]["print"] = "Disc subtitle"
        constants.all_tags["album"]["pattern"] = []

    for idx, file_path in enumerate(all_files):
        redo = True
        file_name = Utils().file_path_to_song_data(file_path)
        while redo:
            redo = False
            # Print info about file and progress
            print(Fore.BLUE + f"\nSong {idx + 1} of {len(all_files)}")
            print(Fore.BLUE + f"----- File: {file_name} -----")

            # 1. Read the data and make basic improvements
            old_metadata: OggOpus = OggOpus(file_path)
            old_tags = {}
            tag_source = {}
            for key, val in old_metadata.items():
                old_tags[key] = val
            for key in old_tags.keys():
                tag_source[key] = colors.md_col
            tags = MusicTags()

            tags.set_original_tags(old_tags)
            tags.discard_upload_date()
            if args.manual_album is not None:
                tags.switch_album_to_disc_subtitle(args.manual_album)

            prepare_resolved = old_tags.copy()
            tags.set_resolved_tags(prepare_resolved)

            old_tags_parser = TagsParser(tags.original)
            old_tags_parser.parse_tags()
            old_tags_parser.process_existing_tags()
            tags.set_tags_from_old_tags(old_tags_parser.get_tags())

            # 2. Get description
            description_lines: list[str] | None = old_metadata.get("synopsis")
            if description_lines is None:
                description_lines = old_metadata.get("description")

            # 3. If description exists, send it to be parsed
            if description_lines is not None:
                desc_parser = DescriptionParser()
                description = "\n".join(description_lines)
                desc_parser.parse(description)
                tags.set_youtube_tags(desc_parser.get_tags())
                tags.add_source_tag()

                new_tags_parser = TagsParser(tags.youtube)
                new_tags_parser.parse_tags()
                tags.set_tags_from_description(new_tags_parser.get_tags())

            if not tags.check_any_new_data_exists():
                print(Fore.YELLOW + "No new data exists. Skipping song")
                break

            # 4. For each field, if there are conflicts, ask user input
            tags.adjust_metadata()

            # 4.5 Get rid of shady tags
            tags.prune_final_metadata()

            # 4.5.1 Manually set album
            if args.manual_album is not None:
                tags.resolved["album"] = [args.manual_album]

            # 5. Show user final result and ask if it should be saved or retried, or song skipped
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
                        print(Fore.YELLOW + "Skipping this and all later songs")
                        Utils().exit_now()
                    case "[s] save":
                        for tag, data in tags.resolved.items():
                            if data == ["[Removed]"]:
                                old_metadata.pop(tag, None)
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
