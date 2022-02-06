#!/usr/bin/env python3
"""
Script to parse a "description" tag in a song, corresponding to the
youtube version of the song, and parse it to produce other tags.
"""

__author__ = "Simon Bengtsson"
__version__ = "0.1.0"
__license__ = "GPLv3"

import argparse
import re

from mutagen.oggopus import OggOpus
from colorama import Fore, init
from pathlib import Path
from typing import List, Dict, Optional, Tuple

INTERPUNCT = '\u00b7'
SPACE = '\u00b7'
SPACE = ' '
SEP = " | "

init(autoreset=True)


def remove_duplicates(duplicates: list) -> list:
    return list(dict.fromkeys(duplicates))


def prune_title(original_title):
    pruned = re.sub(r"\(Remastered.*\)", "", original_title)
    pruned = re.sub(r"\s*\([fFeat].*\)", "", original_title)
    return pruned


def split_tag(input: str) -> list:
    return re.split(", | and |; ", input)


def parse_artist_and_title(source_line):
    artist_and_title = source_line.split(" " + INTERPUNCT + " ")
    title = prune_title(artist_and_title[0]).strip()
    artist: List = artist_and_title[1:]

    if len(artist) < 2 and ", " in artist[0]:
        artist: List = re.split(", | and ", artist[0])

    return artist, title


def parse(description_tag_full: str) -> Dict[str, List[str]]:
    new_metadata: Dict[str, List[str]] = {}
    lines_since_title_artist: int = 1000

    description_tag_lines: List[str] = description_tag_full.splitlines(False)

    for description_line in description_tag_lines:
        description_line = description_line.replace('\n', '')
        description_line = re.sub('\n', '', description_line)
        lines_since_title_artist = lines_since_title_artist + 1
        # Artist and title
        if INTERPUNCT in description_line:
            lines_since_title_artist = 0
            youtube_artist, youtube_title = parse_artist_and_title(description_line)
            if youtube_artist:
                new_metadata["artist"] = remove_duplicates(youtube_artist)
            new_metadata["title"] = [youtube_title]

        if lines_since_title_artist == 2:
            new_metadata["album"] = [description_line.strip()]

        def standard_pattern(field_name, regex):
            pattern = re.compile(regex)
            pattern_match = re.match(pattern, description_line)
            if pattern_match:
                field_value = pattern_match.groups()[len(pattern_match.groups())-1]
                field_value = field_value.strip()
                if new_metadata.get(field_name):
                    new_metadata[field_name].append(field_value)
                    new_metadata[field_name] = remove_duplicates(new_metadata[field_name])
                else:
                    new_metadata[field_name] = [field_value]

        # standard_pattern("artist", r"(.*, )?^(?!(Makeup)(Finishing)).*[aA]rtist.*:\s*(.+)\s*")
        # standard_pattern("artist", r"(.*, )?^(?!Makeup).*[aA]rtist.*:\s*(.+)\s*")
        # standard_pattern("artist", r".*[aA]rtist.*:\s*(.*)\s*")
        standard_pattern("album", r".*“.*” by .* from ‘(.*)’")
        standard_pattern("arranger", r".*?[aA]rranged\s+[bB]y.*:\s*(.+)\s*")
        standard_pattern("arranger", r".*?[aA]rranger.*:\s*(.+)\s*")
        standard_pattern("artist", r"(.*, )?[aA]rtist.*:\s*(.+)\s*")
        standard_pattern("artist", r".*\(feat. (.+?)\)")
        standard_pattern("artist", r".*“.*” by (.*) from ‘.*’")
        standard_pattern("author", r"(.*, )?[aA]uthor.*:\s*(.+)\s*")
        standard_pattern("composer", r".*?[cC]omposer.*:\s*(.+)\s*")
        standard_pattern("conductor", r".*[cC]onductor.*:\s*(.+)\s*")
        standard_pattern("copyright", r"\u2117 (.+)\s*")
        standard_pattern("copyright_date", r"\u2117 (\d\d\d\d)\s")
        standard_pattern("date", r"Released on:\s*(\d\d\d\d-\d\d-\d\d)")
        standard_pattern("lyricist", r"(.*, )?[wW]riter.*:\s*(.+)\s*")
        standard_pattern("lyricist", r"(.*, )?[wW]ritten\s+[bB]y.*:\s*(.+)\s*")
        standard_pattern("lyricist", r".*[lL]yricist.*:\s*(.+)\s*")
        standard_pattern("organization", r"Provided to YouTube by (.+)\s*")
        standard_pattern("performer", r".*[pP]erformer.*:\s*(.+)\s*")
        standard_pattern("performer:acoustic guitar", r".*[aA]coustic\s+[gG]uitar.*:\s*(.+)\s*")
        standard_pattern("performer:background vocals", r"(.*, )?[bB]ackground\s+[vV]ocal.*:\s*(.+)\s*")
        standard_pattern("performer:bass guitar", r".*[bB]ass\s+[gG]uitar.*:\s*(.+)\s*")
        standard_pattern("performer:cello", r"(.*, )?[cC]ello.*:\s*(.+)\s*")
        standard_pattern("performer:double bass", r".*[dD]ouble\s+[bB]ass.*:\s*(.+)\s*")
        standard_pattern("performer:drums", r"(.*, )?[dD]rum.*:\s*(.+)\s*")
        standard_pattern("performer:electric guitar", r".*[eE]lectric\s+[gG]uitar.*:\s*(.+)\s*")
        standard_pattern("performer:flute", r"(.*, )?[fF]lute.*:\s*(.+)\s*")
        standard_pattern("performer:guitar", r"(.*, )?[gG]uitar.*:\s*(.+)\s*")
        standard_pattern("performer:keyboard", r"(.*, )?[kK]eyboard.*:\s*(.+)\s*")
        standard_pattern("performer:percussion", r".*[pP]ercussion.*:\s*(.+)\s*")
        standard_pattern("performer:piano", r"(.*, )?[pP]iano.*:\s*(.+)\s*")
        standard_pattern("performer:programming", r"(.*, )?[pP]rogramm(er|ing).*:\s*(.+)\s*")
        standard_pattern("performer:saxophone", r"(.*, )?[sS]axophone.*:\s*(.+)\s*")
        standard_pattern("performer:synthesizer", r".*[sS]ynth.*:\s*(.+)\s*")
        standard_pattern("performer:ukulele", r".*[uU]kulele.*:\s*(.+)\s*")
        standard_pattern("performer:violin", r"(.*, )?[vV]iolin.*:\s*(.+)\s*")
        standard_pattern("performer:vocals", r"(.*, )?(Lead\s+)?[vV]ocal(?!.*[eE]ngineer).*:\s*(.+)\s*")
        standard_pattern("producer", r"(.*, )?[pP]roducer.*:\s*(.+)\s*")
        standard_pattern("publisher", r"(.*, )?[pP]ublisher.*:\s*(.+)\s*")
        standard_pattern("title", r".*“(.*)” by .* from ‘.*’")

    artist = new_metadata.get("artist")
    if artist:
        new_metadata["albumartist"] = [artist[0]]

    for key, value in new_metadata.items():
        if value == []:
            new_metadata.pop(key)
    # Basic pattern:
    # r".*[ ]   .*:\s*(.*)\s*"

    copyright_date = new_metadata.pop("copyright_date", None)
    date = new_metadata.get("date")
    if copyright_date and not date:
        new_metadata["date"] = copyright_date

    return new_metadata


def print_metadata_key(key_type, key, data):
    value = SEP.join(data.get(key, [Fore.BLACK + 'Not found'])).replace(' ', SPACE)
    print("  " + key_type + ": " + Fore.BLUE + value)


def print_metadata(data):
    print_metadata_key("Title", "title", data)
    print_metadata_key("Album", "album", data)
    print_metadata_key("Album Artist", "albumartist", data)
    print_metadata_key("Artist(s)", "artist", data)
    print_metadata_key("Date", "date", data)
    print_metadata_key("Performer", "performer", data)
    if "performer:" in ' '.join(data.keys()):
        print_metadata_key("- Vocals", "performer:vocals", data)
        print_metadata_key("- Background Vocals", "performer:background vocals", data)
        print_metadata_key("- Drums", "performer:drums", data)
        print_metadata_key("- Percussion", "performer:percussion", data)
        print_metadata_key("- Keyboard", "performer:keyboard", data)
        print_metadata_key("- Piano", "performer:piano", data)
        print_metadata_key("- Synthesizer", "performer:synthesizer", data)
        print_metadata_key("- Guitar", "performer:guitar", data)
        print_metadata_key("- Electric guitar", "performer:electric guitar", data)
        print_metadata_key("- Bass guitar", "performer:bass guitar", data)
        print_metadata_key("- Ukulele", "performer:ukulele", data)
        print_metadata_key("- Violin", "performer:violin", data)
        print_metadata_key("- Double bass", "performer:double bass", data)
        print_metadata_key("- Cello", "performer:cello", data)
        print_metadata_key("- Programming", "performer:programming", data)
        print_metadata_key("- Saxophone", "performer:saxophone", data)
        print_metadata_key("- Flute", "performer:flute", data)
    print_metadata_key("Organization", "organization", data)
    print_metadata_key("Copyright", "copyright", data)
    print_metadata_key("Composer", "composer", data)
    print_metadata_key("Conductor", "conductor", data)
    print_metadata_key("Arranger", "arranger", data)
    print_metadata_key("Author", "author", data)
    print_metadata_key("Producer", "producer", data)
    print_metadata_key("Publisher", "publisher", data)
    print_metadata_key("Lyricist", "lyricist", data)
    print("")


def adjust_metadata(new_metadata: Dict[str, List[str]], old_metadata: OggOpus) -> Tuple[bool, OggOpus]:
    changes_made = False

    # Date should be safe to get from description
    date = new_metadata.pop("date", None)
    if date:
        old_metadata["date"] = date
        changes_made = True

    # youtube-dl is default album, auto-change
    md_album = old_metadata.get("album")
    yt_album = new_metadata.get("album")
    if yt_album and md_album == ["youtube-dl"]:
        old_metadata["album"] = yt_album
        changes_made = True

    md_artist = old_metadata.get("artist")
    yt_artist = new_metadata.get("artist")
    if md_artist is not None and len(md_artist) == 1 and split_tag(md_artist[0]) == yt_artist:
        old_metadata["artist"] = yt_artist

    # Compare all fields
    for field, yt_value in new_metadata.items():
        if old_metadata.get(field) is None:
            print(Fore.CYAN + f"{field.title()}: No value exists in metadata. Using parsed data.")
            old_metadata[field] = yt_value
            changes_made = True
        elif yt_value == old_metadata.get(field):
            print(Fore.GREEN + f"{field.title()}: Metadata matches YouTube description.")
        else:
            print(Fore.RED + f"{field.title()}: Mismatch between values in description and metadata:")
            print("  1. Exisiting metadata:  " + Fore.CYAN + f"{' | '.join(old_metadata.get(field, ['Not set']))}")
            print("  2. YouTube description: " + Fore.MAGENTA + f"{' | '.join(yt_value)}")
            print("  3. Manually fill in tag")
            choice = input("Choose the number you want to use. Empty skips this field for this song: ")
            if choice == '2':
                old_metadata[field] = yt_value
                changes_made = True
            elif choice == '3':
                old_metadata[field] = input("Value: ")
                changes_made = True

    return changes_made, old_metadata


def modify_field(old_metadata: OggOpus) -> OggOpus:
    key = " "
    val = " "
    while key and val:
        print("Enter key and value (newline cancels):")
        key = input("  Key: ")
        val = input("  Value: ")
        if key and val:
            old_metadata[key] = [val]
        else:
            break
    return old_metadata


def adjust_existing_data(old_metadata: OggOpus) -> OggOpus:
    old_metadata["comment"] = ["youtube-dl"]  # All youtube songs should have description tag

    old_metadata.pop("language", None)

    # If the date is just the upload date, discard it
    if old_metadata.get("date") and re.match(r"\d\d\d\d\d\d\d\d", old_metadata["date"][0]):
        old_metadata.pop("date", None)

    new_artist = old_metadata.get('artist')
    if new_artist is not None and not len(new_artist) > 1:
        old_metadata['artist'] = split_tag(new_artist[0])

    return old_metadata


def get_basename(file_path: Path) -> str:
    file_name = str(file_path)
    basename = re.match(".*/(.*)", file_name)
    if basename:
        match = basename.groups()[0]
        file_name = match
        pruned_name = re.match("<(.*)>.opus", file_name)
        if pruned_name:
            file_name = pruned_name.groups()[0]

    return file_name


def main(args):
    music_dir = Path(args.dir).resolve()
    all_files = list(filter(Path.is_file, Path(music_dir).glob('*.opus')))

    for idx, file_path in enumerate(all_files):
        stop = False
        redo = True
        file_name = get_basename(file_path)
        while redo:
            # Print info about file and progress
            print(Fore.BLUE + f"\nSong {idx + 1} of {len(all_files)}")
            print(Fore.BLUE + f"----- File: {file_name} -----")

            # 1. Read the data and make basic improvements
            old_raw_metadata: OggOpus = OggOpus(file_path)
            old_metadata: OggOpus = adjust_existing_data(old_raw_metadata)

            # 2. Get description
            description_lines: List | None = old_metadata.get("description")

            # 3. If description exists, send it to be parsed
            new_metadata: Optional[Dict[str, List[str]]] = None
            if description_lines is not None:
                description = '\n'.join(description_lines)
                if args.verbose:
                    print("The raw YouTube description is the following:")
                    print(description)

                new_metadata = parse(description)

            # 4. For each field, if there are conflicts, ask user input
            changed = False
            if new_metadata:
                changed, old_metadata = adjust_metadata(new_metadata, old_metadata)

            # 5. Show user final result and ask if it should be saved or retried, or song skipped
            print("Final result:")
            print_metadata(old_metadata)
            reshow_choices = True
            while reshow_choices:
                reshow_choices = False
                redo = False
                action_prompt = ("Action: (s)ave, (r)eset, (m)odify field, (p)ass, "
                                 "(y)outube description, (c)urrent metadata, (d)escription metadata, (a)bort: ")
                action = input(action_prompt)
                print('-' * (len(action_prompt) + 1))
                if action == 's':
                    old_metadata.save()
                    print(Fore.GREEN + f"Metadata saved for file: {file_name}")
                elif action == "r":
                    print(f"Trying to improve metadata again for file: {file_name}")
                    redo = True
                elif action == "m":
                    old_metadata = modify_field(old_metadata)
                    print(Fore.CYAN + "Current metadata to save:")
                    print_metadata(old_metadata)
                    reshow_choices = True
                elif action == "p":
                    print(Fore.YELLOW + f"Pass. Skipping song: {file_name}")
                elif action == "y":
                    if description_lines:
                        print(Fore.BLUE + "Original YouTube description:")
                        print(Fore.MAGENTA + "\n".join(description_lines))
                    else:
                        print(Fore.RED + "No YouTube description tag for this song.")
                    reshow_choices = True
                elif action == "c":
                    print(Fore.BLUE + "Current metadata to save:")
                    print_metadata(old_metadata)
                    reshow_choices = True
                elif action == "d":
                    if new_metadata:
                        print(Fore.MAGENTA + "Metadata parsed from YouTube description:")
                        print_metadata(new_metadata)
                    else:
                        print(Fore.RED + "This song has no YouTube description tag to parse metadata from.")
                    reshow_choices = True
                elif action == "a":
                    print(Fore.YELLOW + "Skipping this and all later songs")
                    stop = True
                else:
                    print(Fore.RED + "Invalid choice. Try again:")
                    reshow_choices = True

        if stop:
            break
            # At any step with user input, user can choose:
            # * Show conflicting fields
            # * Show fields that will be changed


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("-a",
                        "--all",
                        action="store_true",
                        default=False,
                        dest="fix_descriptionless",
                        help="Even if there is no YouTube description, suggest improving existing tags")

    parser.add_argument("-d",
                        "--directory",
                        action="store",
                        dest="dir",
                        help="directory in which the files to be retagged are located")

    parser.add_argument("-v",
                        "--verbose",
                        action="store_true",
                        default=False,
                        dest="verbose",
                        help="show verbose output")

    parser.add_argument("-V",
                        "--version",
                        action="version",
                        version="%(prog)s (version {version})".format(version=__version__))

    args = parser.parse_args()
    main(args)
