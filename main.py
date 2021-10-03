import re

from mutagen.oggopus import OggOpus
from os import listdir
from os.path import isfile, join
from pprint import pprint
from colorama import Fore, init, Style
from typing import List, Dict, Tuple

init(autoreset=True)

music_dir = "for-acid.csv"

verbose = True
fix_mismatches = True
save = False

all_files = [join(music_dir, f) for f in listdir(music_dir) if isfile(join(music_dir, f))]

def prune_title(original_title):
    return re.sub(r"\(Remastered.*\)", "", original_title)

def split_tag(input: str) -> list:
    return re.split(", | and ", input)


def parse_artist_and_title(source_line):
    artist_and_title = source_line.split(" \u00b7 ")
    title = prune_title(artist_and_title[0]).strip()
    artist: List = artist_and_title[1:]

    if len(artist) < 2 and ", " in artist[0]:
        artist: List = re.split(", | and ", artist[0])

    return artist, title

def parse(desc):
    new_data: Dict = {}

    for desc_line in desc:
        # Album artist and title
        if "\u00b7" in desc_line:
            youtube_artist, youtube_title = parse_artist_and_title(desc_line)
            new_data["albumartist"] = youtube_artist
            new_data["title"] = [youtube_title]

        def standard_pattern(field_name, regex):
            pattern = re.compile(regex)
            pattern_match = re.match(pattern, desc_line)
            if pattern_match:
                field_value = pattern_match.groups()[0]
                if new_data.get(field_name):
                    new_data[field_name].append(field_value)
                else:
                    new_data[field_name] = [field_value]

        standard_pattern("copyright", r"\u2117 (.*)\s*")
        standard_pattern("organization", r"Provided to YouTube by (.*)\s*")
        standard_pattern("date", r"Released on:\s*(\d\d\d\d)")
        # TODO: Write tests. Check that date only has one value.
        standard_pattern("composer", r".*[cC]omposer.*:\s*(.*)\s*")
        standard_pattern("performer", r".*[pP]erformer.*:\s*(.*)\s*")
        standard_pattern("author", r".*[aA]uthor.*:\s*(.*)\s*")
        standard_pattern("lyricist", r".*[lL]yricist.*:\s*(.*)\s*")
        standard_pattern("publisher", r".*[pP]ublisher.*:\s*(.*)\s*")
        standard_pattern("artist", r"\s*([fF]eatured)*\s*[aA]rtist[s]*:*\s*(.*)\s*")

        # Basic pattern:
        # r".*[ ]   .*:\s*(.*)\s*"

    return new_data

def print_new_metadata(data):
    print("  Album Artist: " + Fore.BLUE + f"{', '.join(data.get('albumartist', [Fore.BLACK + 'Not found']))}")
    print("  Artist(s): " + Fore.BLUE + f"{', '.join(data.get('artist', [Fore.BLACK + 'Not found']))}")
    print("  Title: " + Fore.BLUE + f"{', '.join(data.get('title', [Fore.BLACK + 'Not found']))}")
    print("  Date: " + Fore.BLUE + f"{', '.join(data.get('date', [Fore.BLACK + 'Not found']))}")
    print("  Performer: " + Fore.BLUE + f"{', '.join(data.get('performer', [Fore.BLACK + 'Not found']))}")
    print("  Organization: " + Fore.BLUE + f"{', '.join(data.get('organization', [Fore.BLACK + 'Not found']))}")
    print("  Copyright: " + Fore.BLUE + f"{', '.join(data.get('copyright', [Fore.BLACK + 'Not found']))}")
    print("  Composer: " + Fore.BLUE + f"{', '.join(data.get('composer', [Fore.BLACK + 'Not found']))}")
    print("  Author: " + Fore.BLUE + f"{', '.join(data.get('author', [Fore.BLACK + 'Not found']))}")
    print("  Publisher: " + Fore.BLUE + f"{', '.join(data.get('publisher', [Fore.BLACK + 'Not found']))}")
    print("  Lyricist: " + Fore.BLUE + f"{', '.join(data.get('lyricist', [Fore.BLACK + 'Not found']))}")
    # print(f": {}")
    print("")

def adjust_metadata(new_data, metadata) -> Tuple[bool, OggOpus]:
    changes_made = False
    for field, value in new_data.items():
        if metadata.get(field) is None:
            print(Fore.CYAN + f"{field.title()}: No value exists in metadata. Using parsed data.")
            metadata[field] = value
            changes_made = True
        elif value == metadata.get(field):
            print(Fore.GREEN + f"{field.title()}: Metadata matches description.")
        else:
            print(Fore.RED + f"{field.title()}: Mismatch between values in description and metadata:")
            print(f"  1. Exisiting metadata:  {', '.join(metadata.get(field, ['Not set']))}")
            print(f"  2. YouTube description: {', '.join(value)}")
            print("  3. Manually fill in tag")
            choice = input("Choose the number you want to use. Empty skips this field for this song: ")
            if choice == '2':
                metadata[field] = value
                changes_made = True
            elif choice == '3':
                metadata[field] = input("Value: ")
                changes_made = True

    return changes_made, metadata

for file in all_files:
    # if "<10>" in file:
        if verbose: print(Fore.BLUE + f"\n----- File: {file} -----")

        metadata = OggOpus(file)

        # if 'artist' in metadata and 'title' in metadata and 'description' in metadata:
        description = metadata.get("description")
        if description:
            # pprint(description)
            new_data = parse(description)

            if verbose:
                print("Metadata parsed from YouTube description:")
                print_new_metadata(new_data)
                print("Existing metadata:")
                print_new_metadata(metadata)

            #Mismatches
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
                                metadata = OggOpus(file)
                                changed, metadata = adjust_metadata(new_data, metadata)
                else:
                    print(f"No new data was found.")

            if save: metadata.save()

        elif verbose:
            artist = metadata.get("artist")
            title = metadata.get("title")
            if artist and title:
                print(f"Skipping \'{', '.join(title)}\' by {', '.join(artist)}")
