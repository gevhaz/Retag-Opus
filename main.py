import re

from mutagen.oggopus import OggOpus
from os import listdir
from os.path import isfile, join
from pprint import pprint
from colorama import Fore, init
from typing import List, Dict, Tuple

init(autoreset=True)

# music_dir = "for-acid.csv"
music_dir = "pitchfork.csv"

verbose = True
fix_mismatches = True
debug = True
save = False

all_files = [join(music_dir, f) for f in listdir(music_dir) if isfile(join(music_dir, f))]

def remove_duplicates(l: list) -> list:
    return list(dict.fromkeys(l))

def prune_title(original_title):
    pruned = re.sub(r"\(Remastered.*\)", "", original_title)
    pruned = re.sub(r"\s*\([fFeat].*\)", "", original_title)
    return pruned

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
    lines_since_title_artist = 1000

    for desc_line in desc:
        lines_since_title_artist = lines_since_title_artist + 1
        # Artist and title
        if "\u00b7" in desc_line:
            lines_since_title_artist = 0
            youtube_artist, youtube_title = parse_artist_and_title(desc_line)
            if youtube_artist:
                new_data["artist"] = youtube_artist
            new_data["title"] = [youtube_title]

        if lines_since_title_artist == 2:
            new_data["album"] = [desc_line.strip()]

        def standard_pattern(field_name, regex):
            pattern = re.compile(regex)
            pattern_match = re.match(pattern, desc_line)
            if pattern_match:
                field_value = pattern_match.groups()[len(pattern_match.groups())-1]
                if new_data.get(field_name):
                    new_data[field_name].append(field_value)
                    new_data[field_name] = remove_duplicates(new_data[field_name])
                else:
                    new_data[field_name] = [field_value]

        standard_pattern("copyright", r"\u2117 (.+)\s*")
        standard_pattern("organization", r"Provided to YouTube by (.+)\s*")
        standard_pattern("date", r"Released on:\s*(\d\d\d\d-\d\d-\d\d)")
        standard_pattern("composer", r"(.*, )[cC]omposer.*:\s*(.+)\s*")
        standard_pattern("conductor", r"(.*, )[cC]onductor.*:\s*(.+)\s*")
        standard_pattern("performer", r"(.*, )[pP]erformer.*:\s*(.+)\s*")

        standard_pattern("performer:vocals", r"(.*, )[vV]ocal.*:\s*(.+)\s*")
        standard_pattern("performer:drums", r"(.*, )[dD]rum.*:\s*(.+)\s*")
        standard_pattern("performer:keyboard", r"(.*, )[pP]erformer.*:\s*(.+)\s*")
        standard_pattern("performer:programming", r"(.*, )[pP]erformer.*:\s*(.+)\s*")
        standard_pattern("performer:violin", r"(.*, )[pP]erformer.*:\s*(.+)\s*")
        standard_pattern("performer:saxophone", r"(.*, )[sS]axophone.*:\s*(.+)\s*")

        standard_pattern("author", r"(.*, )[aA]uthor.*:\s*(.+)\s*")
        standard_pattern("arranger", r"(.*, )[aA]rranger.*:\s*(.+)\s*")
        standard_pattern("lyricist", r"(.*, )[lL]yricist.*:\s*(.+)\s*")
        standard_pattern("lyricist", r"(.*, )[wW]riter.*:\s*(.+)\s*")
        standard_pattern("publisher", r"(.*, )[pP]ublisher.*:\s*(.+)\s*")
        standard_pattern("artist", r"(.*, )^(?!Makeup).*[aA]rtist.*:\s*(.+)\s*")
        standard_pattern("artist", r".*\(feat. (.+)\)")
        # standard_pattern("artist", r".*[aA]rtist.*:\s*(.*)\s*")

    artist = new_data.get("artist")
    if artist:
        print("Enetered if")
        new_data["albumartist"] = [artist[0]]

    for key, value in new_data.items():
        if value == []:
            new_data.pop(key)
    # Basic pattern:
    # r".*[ ]   .*:\s*(.*)\s*"

    return new_data

def print_new_metadata(data):
    print("  Title: " + Fore.BLUE + f"{' | '.join(data.get('title', [Fore.BLACK + 'Not found']))}")
    print("  Album: " + Fore.BLUE + f"{' | '.join(data.get('album', [Fore.BLACK + 'Not found']))}")
    print("  Album Artist: " + Fore.BLUE + f"{' | '.join(data.get('albumartist', [Fore.BLACK + 'Not found']))}")
    print("  Artist(s): " + Fore.BLUE + f"{' | '.join(data.get('artist', [Fore.BLACK + 'Not found']))}")
    print("  Date: " + Fore.BLUE + f"{' | '.join(data.get('date', [Fore.BLACK + 'Not found']))}")
    print("  Performer: " + Fore.BLUE + f"{' | '.join(data.get('performer', [Fore.BLACK + 'Not found']))}")
    if "performer:" in data:
        print("  \tVocals: " + Fore.BLUE + f"{' | '.join(data.get('performer:vocals', [Fore.BLACK + 'Not found']))}" +
              Fore.WHITE + ", Keyboard: " +
              Fore.BLUE + f"{' | '.join(data.get('performer:keyboard', [Fore.BLACK + 'Not found']))}" +
              Fore.WHITE + ", Drums: " +
              Fore.BLUE + f"{' | '.join(data.get('performer:drums', [Fore.BLACK + 'Not found']))}" +
              Fore.WHITE + ", Programmer: " +
              Fore.BLUE + f"{' | '.join(data.get('performer:programming', [Fore.BLACK + 'Not found']))}" +
              Fore.WHITE + ", Violin: " +
              Fore.BLUE + f"{' | '.join(data.get('performer:violin', [Fore.BLACK + 'Not found']))}" +
              Fore.WHITE + ", Saxophone: " +
              Fore.BLUE + f"{' | '.join(data.get('performer:saxophone', [Fore.BLACK + 'Not found']))}"
              )
    print("  Organization: " + Fore.BLUE + f"{' | '.join(data.get('organization', [Fore.BLACK + 'Not found']))}")
    print("  Copyright: " + Fore.BLUE + f"{' | '.join(data.get('copyright', [Fore.BLACK + 'Not found']))}")
    print("  Composer: " + Fore.BLUE + f"{' | '.join(data.get('composer', [Fore.BLACK + 'Not found']))}")
    print("  Conductor: " + Fore.BLUE + f"{' | '.join(data.get('conductor', [Fore.BLACK + 'Not found']))}")
    print("  Arranger: " + Fore.BLUE + f"{' | '.join(data.get('arranger', [Fore.BLACK + 'Not found']))}")
    print("  Author: " + Fore.BLUE + f"{' | '.join(data.get('author', [Fore.BLACK + 'Not found']))}")
    print("  Publisher: " + Fore.BLUE + f"{' | '.join(data.get('publisher', [Fore.BLACK + 'Not found']))}")
    print("  Lyricist: " + Fore.BLUE + f"{' | '.join(data.get('lyricist', [Fore.BLACK + 'Not found']))}")
    # print(f": {}")
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

    if re.match(r"\d\d\d\d\d\d\d\d", metadata["date"][0]):
        metadata.pop("date", None)

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
    # if "<175>" in file:
        if verbose: 
            print(Fore.BLUE + f"\nSong {index} of {len(all_files)}")
            print(Fore.BLUE + f"----- File: {file} -----")

        metadata = OggOpus(file)


        # if 'artist' in metadata and 'title' in metadata and 'description' in metadata:
        description = metadata.get("description")
        if description:
            if debug: pprint(description)
            new_data = parse(description)

            if verbose:
                print("Metadata parsed from YouTube description:")
                print_new_metadata(new_data)
                print("Existing metadata:")
                print_new_metadata(metadata)

            metadata["comment"] = ["youtube-dl"] # All youtube songs should have description tag

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
                                metadata.save()


                else:
                    print(f"No new data was found.")


        elif verbose:
            artist = metadata.get("artist")
            title = metadata.get("title")
            if artist and title:
                print(f"Skipping \'{', '.join(title)}\' by {', '.join(artist)}")
