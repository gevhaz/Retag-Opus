import re

from mutagen.oggopus import OggOpus
from os import listdir
from os.path import isfile, join
from pprint import pprint
from colorama import Fore, init
from typing import List, Optional

init(autoreset=True)

music_dir = "for-acid.csv"

verbose = True
show_mismatches = True
save = False

all_files = [join(music_dir, f) for f in listdir(music_dir) if isfile(join(music_dir, f))]

def prune_title(original_title):
    return re.sub(r"\(Remastered.*\)", "", original_title)

def parse_artist_and_title(artist_and_title):
    title = prune_title(artist_and_title[0]).strip()
    artist: List = artist_and_title[1:]
    if verbose:
        print(f"Title: {title}")
        print(f"Artist(s): {', '.join(artist)}")

    if len(artist) < 2 and ", " in artist[0]:
        artist: List = re.split(", | and ", artist[0])

    return artist, title


for file in all_files:
    if verbose: print(f"\n----- File: {file} -----")

    metadata = OggOpus(file)

    artist = metadata.get("artist")
    title = metadata.get("title")
    if artist:
        artist = ' '.join(artist)
    if title:
        title = ' '.join(title)

    # if 'artist' in metadata and 'title' in metadata and 'description' in metadata:
    description = metadata.get("description")
    if description:
        # pprint(description)
        for desc_line in description:

            # Artist and title
            if "\u00b7" in desc_line:
                interpunct_line = desc_line.split(" \u00b7 ")
                youtube_artist, youtube_title = parse_artist_and_title(interpunct_line)
                metadata_artist: Optional[List] = metadata.get("artist")
                
                if youtube_artist != metadata["artist"] and metadata_artist is not None:
                    if show_mismatches: 
                        print(Fore.GREEN + "Artist mismatch:")
                        print(Fore.GREEN + f"\tYoutube description: {', '.join(youtube_artist)}")
                        print(Fore.GREEN + f"\tExisting metadata:   {', '.join(metadata['artist'])}")
                        print(Fore.RED + metadata_artist[0])
                elif metadata_artist is None:
                    if show_mismatches: print("No artist in existing metadata for song")
                if youtube_title != metadata["title"][0]:
                    if show_mismatches: 
                        print(Fore.GREEN + f"Title mismatch:")
                        print(Fore.GREEN + f"\tYoutube description: {youtube_title}")
                        print(Fore.GREEN + f"\tExisting metadata:   {metadata['title'][0]}")

            # Organization
            if "Provided" in desc_line:
                organization = re.sub("Provided to YouTube by ", "", desc_line)
                metadata["organization"] = organization
                if verbose: print(f"Organization: {organization}")

            # Copyright
            if "\u2117" in desc_line:
                copyright = re.sub("\u2117 ", "", desc_line)
                metadata["copyright"] = copyright
                if verbose: print(f"Copyright: {copyright}")

            # Date
            if "Released on:" in desc_line:
                date = re.sub("Released on: ", "", desc_line)
                date = date[0:4]
                metadata["date"] = date
                if verbose: print(f"Date: {date}")

        if verbose: print("")
        if save: metadata.save()

    else:
        print(f"Skipping '{title}' by {artist}")
