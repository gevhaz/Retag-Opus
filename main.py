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
from typing import List, Dict, Tuple


def main(args):
    init(autoreset=True)

    music_dir = Path(args.dir).resolve()

    INTERPUNCT = '\u00b7'
    SPACE = '\u00b7'
    SPACE = ' '
    SEP = " | "

    fix_mismatches = True

    all_files = list(filter(Path.is_file, Path(music_dir).glob('*.opus')))

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

    def parse(joined_desc: str) -> Dict[str, List[str]]:
        new_data: Dict[str, List[str]] = {}
        lines_since_title_artist: int = 1000

        desc: List[str] = joined_desc.splitlines(False)

        for desc_line in desc:
            desc_line = desc_line.replace('\n', '')
            desc_line = re.sub('\n', '', desc_line)
            lines_since_title_artist = lines_since_title_artist + 1
            # Artist and title
            if INTERPUNCT in desc_line:
                lines_since_title_artist = 0
                youtube_artist, youtube_title = parse_artist_and_title(desc_line)
                if youtube_artist:
                    new_data["artist"] = remove_duplicates(youtube_artist)
                new_data["title"] = [youtube_title]

            if lines_since_title_artist == 2:
                new_data["album"] = [desc_line.strip()]

            def standard_pattern(field_name, regex):
                pattern = re.compile(regex)
                pattern_match = re.match(pattern, desc_line)
                if pattern_match:
                    field_value = pattern_match.groups()[len(pattern_match.groups())-1]
                    field_value = field_value.strip()
                    if new_data.get(field_name):
                        new_data[field_name].append(field_value)
                        new_data[field_name] = remove_duplicates(new_data[field_name])
                    else:
                        new_data[field_name] = [field_value]

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

        artist = new_data.get("artist")
        if artist:
            new_data["albumartist"] = [artist[0]]

        for key, value in new_data.items():
            if value == []:
                new_data.pop(key)
        # Basic pattern:
        # r".*[ ]   .*:\s*(.*)\s*"

        copyright_date = new_data.pop("copyright_date", None)
        date = new_data.get("date")
        if copyright_date and not date:
            new_data["date"] = copyright_date

        return new_data

    def print_metadata_key(key_type, key, data):
        value = SEP.join(data.get(key, [Fore.BLACK + 'Not found'])).replace(' ', SPACE)
        print("  " + key_type + ": " + Fore.BLUE + value)

    def print_new_metadata(data):
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

    def adjust_metadata(new_data, metadata) -> Tuple[bool, OggOpus]:
        changes_made = False

        # Date should be safe to get from description
        date = new_data.pop("date", None)
        if date:
            metadata["date"] = date
            changes_made = True

        # youtube-dl is default album, auto-change
        md_album = metadata.get("album")
        yt_album = new_data.get("album")
        if yt_album and md_album == ["youtube-dl"]:
            metadata["album"] = yt_album
            changes_made = True

        md_artist = metadata.get("artist")
        yt_artist = new_data.get("artist")
        if len(md_artist) == 1 and split_tag(md_artist[0]) == yt_artist:
            metadata["artist"] = yt_artist

        # Compare all fields
        for field, yt_value in new_data.items():
            if metadata.get(field) is None:
                print(Fore.CYAN + f"{field.title()}: No value exists in metadata. Using parsed data.")
                metadata[field] = yt_value
                changes_made = True
            elif yt_value == metadata.get(field):
                print(Fore.GREEN + f"{field.title()}: Metadata matches YouTube description.")
            else:
                print(Fore.RED + f"{field.title()}: Mismatch between values in description and metadata:")
                print(f"  1. Exisiting metadata:  {' | '.join(metadata.get(field, ['Not set']))}")
                print(f"  2. YouTube description: {' | '.join(yt_value)}")
                print("  3. Manually fill in tag")
                choice = input("Choose the number you want to use. Empty skips this field for this song: ")
                if choice == '2':
                    metadata[field] = yt_value
                    changes_made = True
                elif choice == '3':
                    metadata[field] = input("Value: ")
                    changes_made = True

        return changes_made, metadata

    for index, file in enumerate(all_files):
        print(Fore.BLUE + f"\nSong {index} of {len(all_files)}")
        print(Fore.BLUE + f"----- File: {file} -----")

        metadata = OggOpus(file)

        description_lines: List | None = metadata.get("description")
        if description_lines:
            description = '\n'.join(description_lines)
            if args.verbose:
                print("The raw YouTube description is the following:")
                print(description)
            new_data = parse(description)

            if args.verbose:
                print("Metadata parsed from YouTube description:")
                print_new_metadata(new_data)
                print("Existing metadata:")
                print_new_metadata(metadata)

            metadata["comment"] = ["youtube-dl"]  # All youtube songs should have description tag

            if metadata.get("date") and re.match(r"\d\d\d\d\d\d\d\d", metadata["date"][0]):
                metadata.pop("date", None)

            # Mismatches
            if fix_mismatches:
                if new_data:
                    changed, metadata = adjust_metadata(new_data, metadata)

                    redo = True
                    if changed:
                        while redo:
                            print(Fore.CYAN + "\nNew metadata:")
                            print_new_metadata(metadata)
                            redo = False if input("Does this look right? (y/n) ") == 'y' else True
                            if redo:
                                print(Fore.RED + "Resetting metadata to original state")
                                new_data = parse(description)
                                metadata = OggOpus(file)
                                changed, metadata = adjust_metadata(new_data, metadata)
                                modify_field = input("Modify specific field? (y/n) ")
                                field = " "
                                key = " "
                                while field and key:
                                    if modify_field == 'y':
                                        print("Enter field and key (enter cancels):")
                                        field = input("  Field: ")
                                        key = input("  Key: ")
                                        if field and key:
                                            metadata[field] = [key]
                                    else:
                                        break
                            else:
                                metadata.save()
                                print(Fore.GREEN + "Metadata saved")
                else:
                    print("No new data was found.")
        elif args.verbose:
            artist = metadata.get("artist")
            title = metadata.get("title")
            if artist and title:
                print(f"Skipping \'{', '.join(title)}\' by {', '.join(artist)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

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
