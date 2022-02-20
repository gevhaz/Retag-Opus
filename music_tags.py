import re

from mutagen.oggopus import OggOpus  # type: ignore
from colorama import Fore  # type: ignore

import colors
import constants

from utils import Utils

Tags = dict[str, list[str]]


class MusicTags:
    """
    Stores tags for one song as a dictionary on the same format as the one provided by the OggOpus object.
    """

    def __init__(self):
        self.original: Tags = {}
        self.youtube: Tags = {}
        self.fromtags: Tags = {}
        self.fromdesc: Tags = {}
        self.resolved: Tags = {}

    def print_metadata_key(self, key_type, key, key_col, data):
        value = constants.SEP.join(data.get(key, [Fore.BLACK + 'Not found'])).replace(' ', constants.SPACE)
        print("  " + key_type + ": " + key_col + value)

    def print_metadata(self, data, col):
        if "performer:" in ' '.join(data.keys()):
            print("  Performers:")
            for tag_id, tag_data in constants.performer_tags.items():
                if tag_id in data and data[tag_id] is not None:
                    self.print_metadata_key(tag_data["print"], tag_id, col, data)
        for tag_id, tag_data in constants.all_tags.items():
            self.print_metadata_key(tag_data["print"], tag_id, col, data)
        print("")

    def print_all(self):

        performer_block = []
        for tag_id, tag_data in constants.performer_tags.items():
            performer_line = []
            original = self.original.get(tag_id)
            youtube = self.youtube.get(tag_id)
            fromdesc = self.fromdesc.get(tag_id)
            fromtags = self.fromtags.get(tag_id)
            if original:
                performer_line.append(colors.md_col + " | ".join(original))
            if youtube and youtube != original:
                performer_line.append(colors.yt_col + " | ".join(youtube))
            if fromtags and fromtags != original:
                performer_line.append(Fore.YELLOW + " | ".join(fromtags))
            if fromdesc and fromdesc != original:
                performer_line.append(Fore.GREEN + " | ".join(fromdesc))
            if len(performer_line) > 0:
                performer_block.append(Fore.WHITE + tag_data['print'] + ": " + f"{Fore.WHITE} | ".join(performer_line))

        main_block = []
        for tag_id, tag_data in constants.all_tags.items():
            main_line = []
            original = self.original.get(tag_id)
            youtube = self.youtube.get(tag_id)
            fromdesc = self.fromdesc.get(tag_id)
            fromtags = self.fromtags.get(tag_id)
            if original:
                main_line.append(colors.md_col + " | ".join(original))
            if youtube and original != youtube:
                main_line.append(colors.yt_col + " | ".join(youtube))
            if fromtags and fromtags != original:
                main_line.append(Fore.YELLOW + " | ".join(fromtags))
            if fromdesc and fromdesc != original:
                main_line.append(Fore.GREEN + " | ".join(fromdesc))
            if len(main_line) > 0:
                main_block.append(Fore.WHITE + tag_data['print'] + ": " + f"{Fore.WHITE} | ".join(main_line))

        if len(performer_block + main_block) > 0:
            if len(performer_block) > 0:
                print(Fore.BLUE + "Performers:")
                print("\n".join(performer_block))
            print("\n".join(main_block))
        else:
            print(Fore.RED + "There's no data to be printed")

    def print_youtube(self):
        if self.youtube:
            self.print_metadata(self.youtube, colors.yt_col)
        else:
            print(Fore.RED + "No new data parsed from description")

    def print_original(self):
        if self.original:
            self.print_metadata(self.original, colors.md_col)
        else:
            print(Fore.RED + "There were no pre-existing tags for this file")

    def print_from_tags(self):
        if self.fromtags:
            self.print_metadata(self.fromtags, Fore.YELLOW)
        else:
            print(Fore.RED + "No new data parsed from tags")

    def print_from_desc(self):
        if self.fromdesc:
            self.print_metadata(self.fromdesc, Fore.GREEN)
        else:
            print(Fore.RED + "No new data parsed from tags parsed from description")

    def print_resolved(self):
        if "performer:" in ' '.join(self.resolved.keys()):
            print("  Performers:")
            for tag_id, tag_data in constants.performer_tags.items():
                tag = self.resolved.get(tag_id)
                if tag:
                    col = Fore.GREEN if tag != self.original.get(tag_id) else colors.md_col
                    self.print_metadata_key(tag_data["print"], tag_id, col, self.resolved)
        for tag_id, tag_data in constants.all_tags.items():
            tag = self.resolved.get(tag_id)
            col = Fore.GREEN if tag != self.original.get(tag_id) else colors.md_col
            self.print_metadata_key(tag_data["print"], tag_id, col, self.resolved)
        print("")

    def cleanup_orignal(self):
        self.original["comment"] = ["youtube-dl"]  # All youtube songs should have description tag

        self.original.pop("language", None)
        self.original.pop("compatible_brands", None)
        self.original.pop("minor_version", None)
        self.original.pop("major_brand", None)
        self.original.pop("vendor_id", None)

        # If the date is just the upload date, discard it
        if self.original.get("date") and re.match(r"\d\d\d\d\d\d\d\d", self.original["date"][0]):
            self.original.pop("date", None)

    def merge_original_metadata(self, original_metadata: OggOpus):
        for key, value in original_metadata.values():
            self.original[key] = value

    def set_youtube_tags(self, youtube_tags: Tags):
        self.youtube = youtube_tags

    def set_original_tags(self, original_tags: Tags):
        self.original = original_tags

    def set_tags_from_description(self, from_desc_tags: Tags):
        self.fromdesc = from_desc_tags

    def set_tags_from_old_tags(self, tags_from_old_tags: Tags):
        self.fromtags = tags_from_old_tags

    def set_resolved_tags(self, resolved: Tags):
        self.resolved = resolved

    def prune_final_metadata(self):
        self.resolved.pop("language", None)
        self.resolved.pop("compatible_brands", None)
        self.resolved.pop("minor_version", None)
        self.resolved.pop("major_brand", None)
        self.resolved.pop("vendor_id", None)

    def add_source_tag(self):
        self.resolved["comment"] = ["youtube-dl"]

    def adjust_metadata(self):

        # Date should be safe to get from description
        date = self.youtube.get("date", None)
        if date and date != self.original.get("date"):
            self.resolved["date"] = date

        md_artist = self.original.get("artist")
        yt_artist = self.youtube.get("artist")
        if md_artist is not None and len(md_artist) == 1 and Utils().split_tag(md_artist[0]) == yt_artist:
            if yt_artist is not None:
                self.resolved["artist"] = yt_artist

        # Compare all fields
        all_new_fields = [key for key in self.youtube.keys()]
        all_new_fields += [key for key in self.fromdesc.keys()]
        all_new_fields += [key for key in self.fromtags.keys()]
        for field in all_new_fields:
            old_value = self.original.get(field)
            yt_value = self.youtube.get(field)
            from_desc_value = self.fromdesc.get(field)
            from_tags_value = self.fromtags.get(field)
            if (old_value is None and len([x for x in [yt_value, from_desc_value, from_tags_value] if x is not None])
                    and field != "albumartist"):
                print(Fore.YELLOW + f"{field.title()}: No value exists in metadata. Using parsed data.")
                if yt_value:
                    self.resolved[field] = yt_value
                if from_tags_value:
                    self.resolved[field] = from_tags_value
                if from_desc_value:
                    self.resolved[field] = from_desc_value
            elif yt_value == old_value:
                print(Fore.GREEN + f"{field.title()}: Metadata matches YouTube description.")
            elif from_desc_value == old_value:
                print(Fore.GREEN + f"{field.title()}: Metadata matches parsed YouTube tags.")
            else:
                redo = True
                print("-----------------------------------------------")
                self.print_all()
                while redo:
                    redo = False
                    print(Fore.RED + f"{field.title()}: Mismatch between values in description and metadata:")
                    if old_value:
                        print("  1. Exisiting metadata:  " + colors.md_col + ' | '.join(old_value))
                    if yt_value:
                        print("  2. YouTube description: " + colors.yt_col + ' | '.join(yt_value))
                    if from_tags_value:
                        print("  3. Parsed from original tags: " + Fore.YELLOW + ' | '.join(from_tags_value))
                    if from_desc_value:
                        print("  4. Parsed from YouTube tags: " + Fore.GREEN + ' | '.join(from_desc_value))
                    print("  5. Manually fill in tag")
                    print("  6. Print description metadata")
                    print("  7. Remove field")
                    choice = input("Choose the number you want to use. Empty leaves metadata unchanged: ")
                    if choice == '1':
                        self.resolved[field] = self.original[field]
                    elif choice == '2' and yt_value is not None:
                        self.resolved[field] = yt_value
                    elif choice == '3' and from_tags_value is not None:
                        self.resolved[field] = from_tags_value
                    elif choice == '4' and from_desc_value is not None:
                        self.resolved[field] = from_desc_value
                    elif choice == '5':
                        self.resolved[field] = [input("Value: ")]
                    elif choice == '6':
                        print("-----------------------------------------------")
                        self.print_youtube()
                        redo = True
                    elif choice == '7':
                        self.resolved.pop(field, None)
                    else:
                        print(Fore.RED + "Invalid choice, try again")
                        redo = True

    def modify_resolved_field(self):
        key = " "
        val = " "
        while key and val:
            print("Enter key and value (newline cancels):")
            key = input("  Key: ")
            val = input("  Value: ")
            if key and val:
                self.resolved[key] = [val]
            else:
                break
