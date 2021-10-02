import re

from mutagen.oggopus import OggOpus
from os import listdir
from os.path import isfile, join
from pprint import pprint
from colorama import Fore, init
from typing import List, Optional, Dict

init(autoreset=True)

music_dir = "for-acid.csv"

verbose = False
fix_mismatches = False
save = False

all_files = [join(music_dir, f) for f in listdir(music_dir) if isfile(join(music_dir, f))]

def prune_title(original_title):
    return re.sub(r"\(Remastered.*\)", "", original_title)

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
        # Artist and title
        if "\u00b7" in desc_line:
            youtube_artist, youtube_title = parse_artist_and_title(desc_line)
            new_data["artist"] = youtube_artist
            new_data["title"] = [youtube_title]

        # Organization
        if "Provided" in desc_line:
            organization = re.sub("Provided to YouTube by ", "", desc_line)
            new_data["organization"] = [organization]

        # Copyright
        if "\u2117" in desc_line:
            copyright = re.sub("\u2117 ", "", desc_line)
            new_data["copyright"] = [copyright]

        # Date
        if "Released on:" in desc_line:
            date = re.sub("Released on: ", "", desc_line)
            date = date[0:4]
            new_data["date"] = [date]

    return new_data

def print_new_metadata(data):
    print(f"  Artist: {', '.join(data.get('artist', ['Not found']))}")
    print(f"  Title: {', '.join(data.get('title', ['Not found']))}")
    print(f"  Date: {', '.join(data.get('date', ['Not found']))}")
    print(f"  Organization: {', '.join(data.get('organization', ['Not found']))}")
    print(f"  Copyright: {', '.join(data.get('copyright', ['Not found']))}")
    # print(f": {}")
    print("")

def adjust_metadata(new_data, metadata):
    if new_data:
        for field, value in new_data.items():
            if value is None:
                print(f"{field.title()}: No value found in YouTube description.")
            elif metadata.get(field) is None:
                print(Fore.CYAN + f"{field.title()}: No value exists in metadata. Using parsed data.")
                metadata[field] = value
            elif value == metadata.get(field):
                print(Fore.GREEN + f"{field.title()}: Metadata matches description.")
            else:
                print(Fore.RED + f"{field.title()}: Mismatch between values in description and metadata:")
                print(f"  1. Exisiting metadata:  {', '.join(metadata.get(field, ['Not set']))}")
                print(f"  2. YouTube description: {', '.join(value)}")
                choice = input("Choose the number you want to use. Empty skips this field for this song: ")
                if choice == 2:
                    metadata[field] = value
    else:
        print(f"No new data was found.")

    return metadata

for file in all_files:
    if verbose: print(Fore.BLUE + f"\n----- File: {file} -----")

    metadata = OggOpus(file)

    # if 'artist' in metadata and 'title' in metadata and 'description' in metadata:
    description = metadata.get("description")
    if description:
        pprint(description)
        new_data = parse(description)

        if verbose:
            print("Metadata parsed from YouTube description:")
            print_new_metadata(new_data)
            print("Existing metadata:")
            print_new_metadata(metadata)

        #Mismatches
        if fix_mismatches:
            metadata = adjust_metadata(new_data, metadata)

        if save: metadata.save()

    elif verbose:
        artist = metadata.get("artist")
        title = metadata.get("title")
        if artist and title:
            print(f"Skipping \'{', '.join(title)}\' by {', '.join(artist)}")
