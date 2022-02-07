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
yt_col = Fore.MAGENTA
md_col = Fore.CYAN
man_col = Fore.GREEN
auto_col = Fore.YELLOW

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


def print_metadata_key(key_type, key, key_col, data):
    value = SEP.join(data.get(key, [Fore.BLACK + 'Not found'])).replace(' ', SPACE)
    print("  " + key_type + ": " + key_col + value)


def print_metadata(data, tag_source, default_col):
    print_metadata_key("Title", "title", tag_source.get("title", default_col), data)
    print_metadata_key("Album", "album", tag_source.get("album", default_col), data)
    print_metadata_key("Album Artist", "albumartist", tag_source.get("albumartist", default_col), data)
    print_metadata_key("Artist(s)", "artist", tag_source.get("artist", default_col), data)
    print_metadata_key("Date", "date", tag_source.get("date", default_col), data)
    print_metadata_key("Genre", "genre", tag_source.get("genre", default_col), data)
    print_metadata_key("Performer", "performer", tag_source.get("performer", default_col), data)
    if "performer:" in ' '.join(data.keys()):
        print_metadata_key("- Vocals", "performer:vocals", tag_source.get("performer:vocals", default_col), data)
        print_metadata_key("- Background Vocals", "performer:background vocals",
                           tag_source.get("performer:background vocals", default_col), data)
        print_metadata_key("- Drums", "performer:drums", tag_source.get("performer:drums", default_col), data)
        print_metadata_key("- Percussion", "performer:percussion",
                           tag_source.get("performer:percussion", default_col), data)
        print_metadata_key("- Keyboard", "performer:keyboard", tag_source.get("performer:keyboard", default_col), data)
        print_metadata_key("- Piano", "performer:piano", tag_source.get("performer:piano", default_col), data)
        print_metadata_key("- Synthesizer", "performer:synthesizer",
                           tag_source.get("performer:synthesizer", default_col), data)
        print_metadata_key("- Guitar", "performer:guitar", tag_source.get("performer:guitar", default_col), data)
        print_metadata_key("- Electric guitar", "performer:electric guitar",
                           tag_source.get("performer:electric guitar", default_col), data)
        print_metadata_key("- Bass guitar", "performer:bass guitar",
                           tag_source.get("performer:bass guitar", default_col), data)
        print_metadata_key("- Ukulele", "performer:ukulele", tag_source.get("performer:ukulele", default_col), data)
        print_metadata_key("- Violin", "performer:violin", tag_source.get("performer:violin", default_col), data)
        print_metadata_key("- Double bass", "performer:double bass",
                           tag_source.get("performer:double bass", default_col), data)
        print_metadata_key("- Cello", "performer:cello", tag_source.get("performer:cello", default_col), data)
        print_metadata_key("- Programming", "performer:programming",
                           tag_source.get("performer:programming", default_col), data)
        print_metadata_key("- Saxophone", "performer:saxophone",
                           tag_source.get("performer:saxophone", default_col), data)
        print_metadata_key("- Flute", "performer:flute", tag_source.get("performer:flute", default_col), data)
    print_metadata_key("Organization", "organization", tag_source.get("organization", default_col), data)
    print_metadata_key("Copyright", "copyright", tag_source.get("copyright", default_col), data)
    print_metadata_key("Composer", "composer", tag_source.get("composer", default_col), data)
    print_metadata_key("Conductor", "conductor", tag_source.get("conductor", default_col), data)
    print_metadata_key("Arranger", "arranger", tag_source.get("arranger", default_col), data)
    print_metadata_key("Author", "author", tag_source.get("author", default_col), data)
    print_metadata_key("Producer", "producer", tag_source.get("producer", default_col), data)
    print_metadata_key("Publisher", "publisher", tag_source.get("publisher", default_col), data)
    print_metadata_key("Lyricist", "lyricist", tag_source.get("lyricist", default_col), data)
    print("")


def adjust_metadata(new_metadata: Dict[str, List[str]],
                    old_metadata: OggOpus,
                    tag_source: Dict[str, str]) -> Tuple[OggOpus, Dict[str, str]]:

    # Date should be safe to get from description
    date = new_metadata.get("date", None)
    if date and date != old_metadata.get("date"):
        old_metadata["date"] = date
        tag_source["date"] = yt_col

    # youtube-dl is default album, auto-change
    md_album = old_metadata.get("album")
    yt_album = new_metadata.get("album")
    if yt_album and md_album == ["youtube-dl"]:
        old_metadata["album"] = yt_album
        tag_source["album"] = yt_col

    md_artist = old_metadata.get("artist")
    yt_artist = new_metadata.get("artist")
    if md_artist is not None and len(md_artist) == 1 and split_tag(md_artist[0]) == yt_artist:
        old_metadata["artist"] = yt_artist
        tag_source["album"] = yt_col

    # Compare all fields
    for field, yt_value in new_metadata.items():
        if old_metadata.get(field) is None:
            print(Fore.YELLOW + f"{field.title()}: No value exists in metadata. Using parsed data.")
            old_metadata[field] = yt_value
            tag_source[field] = yt_col
        elif yt_value == old_metadata.get(field):
            print(Fore.GREEN + f"{field.title()}: Metadata matches YouTube description.")
            tag_source[field] = md_col
        else:
            print(Fore.RED + f"{field.title()}: Mismatch between values in description and metadata:")
            print("  1. Exisiting metadata:  " + md_col + f"{' | '.join(old_metadata.get(field, ['Not set']))}")
            print("  2. YouTube description: " + yt_col + f"{' | '.join(yt_value)}")
            print("  3. Manually fill in tag")
            choice = input("Choose the number you want to use. Empty leaves metadata unchanged: ")
            if choice == '2':
                old_metadata[field] = yt_value
                tag_source[field] = yt_col
            elif choice == '3':
                old_metadata[field] = input("Value: ")
                tag_source[field] = man_col
            else:
                tag_source[field] = md_col

    return old_metadata, tag_source


def modify_field(old_metadata: OggOpus, tag_source: Dict[str, str]) -> Tuple[OggOpus, Dict[str, str]]:
    key = " "
    val = " "
    while key and val:
        print("Enter key and value (newline cancels):")
        key = input("  Key: ")
        val = input("  Value: ")
        if key and val:
            old_metadata[key] = [val]
            tag_source[key] = man_col
        else:
            break
    return old_metadata, tag_source


def adjust_existing_data(old_metadata: OggOpus, tag_source: Dict[str, str]) -> Tuple[OggOpus, Dict[str, str]]:
    old_metadata["comment"] = ["youtube-dl"]  # All youtube songs should have description tag

    old_metadata.pop("language", None)
    old_metadata.pop("compatible_brands", None)
    old_metadata.pop("minor_version", None)
    old_metadata.pop("major_brand", None)
    old_metadata.pop("vendor_id", None)

    # If the date is just the upload date, discard it
    if old_metadata.get("date") and re.match(r"\d\d\d\d\d\d\d\d", old_metadata["date"][0]):
        old_metadata.pop("date", None)

    tags_to_split = ['genre', 'artist']

    for tag in tags_to_split:
        original_tag = old_metadata.get(tag)
        if original_tag is not None and not len(original_tag) > 1:
            new_tag = split_tag(original_tag[0])
            if new_tag != original_tag:
                old_metadata[tag] = new_tag
                tag_source[tag] = auto_col

    return old_metadata, tag_source


def get_basename(file_path: Path) -> str:
    file_name = str(file_path)
    basename = re.match(".*/(.*)", file_name)
    if basename:
        match = basename.groups()[0]
        file_name = match
        name_playlist = re.match("<(.*)> - <(.*)> - <(.*)> - <(.*)>.opus", file_name)
        name_single = re.match("<(.*)> - <(.*)>.opus", file_name)
        if name_playlist:
            file_name = name_playlist.groups()[1] + " - " + name_playlist.groups()[2]
        elif name_single:
            file_name = name_single.groups()[0] + " - " + name_single.groups()[1]

    return file_name


def main(args):
    music_dir = Path(args.dir).resolve()
    all_files = list(filter(Path.is_file, Path(music_dir).glob('*.opus')))

    for idx, file_path in enumerate(all_files):
        stop = False
        redo = True
        file_name = get_basename(file_path)
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
                tag_source[key] = md_col
            old_metadata, tag_source = adjust_existing_data(old_metadata, tag_source)

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
            if new_metadata:
                old_metadata, tag_source = adjust_metadata(new_metadata, old_metadata, tag_source)

            # 5. Show user final result and ask if it should be saved or retried, or song skipped
            reshow_choices = True
            print("Final result:")
            print_metadata(old_metadata, tag_source, Fore.RED)
            if all(color == md_col for color in tag_source.values()):
                if args.fix_descriptionless:
                    reshow_choices = False if input("Only basic suggested, skip? (Y/n): ") == 'n' else True
                else:
                    reshow_choices = False
                    print(Fore.YELLOW + "No signficant changes suggested, therefore only auto-saving the basic changes")
                if not reshow_choices:
                    old_metadata.save()
                    print(Fore.YELLOW + f"Metadata saved for file: {file_name}")

            while reshow_choices:
                reshow_choices = False
                action_prompt = ("Action: (s)ave, (r)eset, (m)odify field, (p)ass, "
                                 "(y)outube description, (o)ld metadata, (c)urrent metadata, (d)escription metadata, "
                                 "(a)bort: ")
                action = input(action_prompt)
                print('-' * (len(action_prompt) + 1))
                if action == 's':
                    old_metadata.save()
                    print(Fore.GREEN + f"Metadata saved for file: {file_name}")
                elif action == "r":
                    print(f"Trying to improve metadata again for file: {file_name}")
                    redo = True
                elif action == "m":
                    old_metadata, tag_source = modify_field(old_metadata, tag_source)
                    print(Fore.BLUE + "Current metadata to save:")
                    print_metadata(old_metadata, tag_source, Fore.RED)
                    reshow_choices = True
                elif action == "p":
                    print(Fore.YELLOW + f"Pass. Skipping song: {file_name}")
                elif action == "y":
                    if description_lines:
                        print(Fore.BLUE + "Original YouTube description:")
                        print(yt_col + "\n".join(description_lines))
                    else:
                        print(Fore.RED + "No YouTube description tag for this song.")
                    reshow_choices = True
                elif action == "o":
                    print(Fore.BLUE + "The original metadata for this file:")
                    print_metadata(old_tags, {}, md_col)
                    reshow_choices = True
                elif action == "c":
                    print(Fore.BLUE + "Current metadata to save:")
                    print_metadata(old_metadata, tag_source, Fore.RED)
                    reshow_choices = True
                elif action == "d":
                    if new_metadata:
                        print(Fore.BLUE + "Metadata parsed from YouTube description:")
                        print_metadata(new_metadata, {}, yt_col)
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
