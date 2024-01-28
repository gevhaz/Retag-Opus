"""Module for storing tags from different sources and printing them."""
import re
from copy import deepcopy
from typing import Final

from colorama import Fore
from simple_term_menu import TerminalMenu

from retag_opus import colors, constants
from retag_opus.exceptions import UserExitException
from retag_opus.utils import Utils

Tags = dict[str, list[str]]

REMOVED_TAG: Final[list[str]] = ["[Removed]"]


class MusicTags:
    """Store tags from different sources for a song.

    Stores tags for one song as a dictionary on the same format as the
    one provided by the OggOpus object.
    """

    def __init__(self, manual_album_set: bool = False) -> None:
        """Create empty attributes for each source."""
        self.base_patterns = deepcopy(constants.all_tags)
        self.performer_patterns = deepcopy(constants.performer_tags)
        if manual_album_set:
            self.base_patterns["discsubtitle"] = self.base_patterns["album"].copy()
            self.base_patterns["discsubtitle"]["print"] = "Disc subtitle"
            self.base_patterns["album"]["pattern"] = []
        self.original: Tags = {}
        self.youtube: Tags = {}
        self.fromtags: Tags = {}
        self.fromdesc: Tags = {}
        self.resolved: Tags = {}

    def print_metadata_key(
        self,
        key_type: str,
        key: str,
        key_col: str,
        data: Tags,
    ) -> None:
        """Print a single metadata key in specified color.

        :param key_type: Printed name of key.
        :param key: What key to print.
        :param key_col: Color to print the data in.
        :param data: The tags from which to get the given key.
        """
        value = constants.SEP.join(data.get(key, ["Not found"])).replace(" ", constants.SPACE)
        if self.resolved.get(key) == ["[Removed]"]:
            key_type = f"{key_type} (Removed)"
        key_col = key_col if data.get(key) else Fore.BLACK
        print("  " + key_type + ": " + key_col + value + Fore.RESET)

    def print_metadata(self, metadata: Tags, col: str) -> None:
        """Print metadata of given set of tags in specifed color.

        :param metadata: The set of tags to print.
        :param col: The color to print the tags in.
        """
        if any(t in self.performer_patterns.keys() for t in metadata.keys()):
            print("  Performers:")
            for tag_id, tag_data in self.performer_patterns.items():
                if tag_id in metadata and metadata[tag_id] is not None:
                    self.print_metadata_key(tag_data["print"], tag_id, col, metadata)
        for tag_id, tag_data in self.base_patterns.items():
            self.print_metadata_key(tag_data["print"], tag_id, col, metadata)
        print("")

    def get_tag_data(self, tag_id: str) -> list[str]:
        """Get data from all sources for given tag.

        Returns a list of all values for a specific tag from various
        sources with color depending on source.

        :param tag_id: The tag name for which data should be returned

        :return: List with strings containing the value the given tag
        has in different sources with color codes that differ between
        sources. If no source contains the tag, an empty list is
        returned.
        """
        print_data: list[str] = []
        original = self.original.get(tag_id)
        youtube = self.youtube.get(tag_id)
        fromdesc = self.fromdesc.get(tag_id)
        fromtags = self.fromtags.get(tag_id)
        if fromtags and fromtags != original:
            print_data.append(Fore.YELLOW + " | ".join(fromtags) + Fore.RESET)
        if fromdesc and fromdesc != original:
            print_data.append(Fore.GREEN + " | ".join(fromdesc) + Fore.RESET)
        if original:
            print_data.append(colors.md_col + " | ".join(original) + Fore.RESET)
        if youtube and original != youtube:
            print_data.append(colors.yt_col + " | ".join(youtube) + Fore.RESET)
        return print_data

    def print_all(self) -> None:
        """Print all tags from all sources.

        Print a block of text with all data from all sources for a given
        tag name, differentiated by color.
        """
        performer_block = []
        there_are_tags = False
        for tag_id, tag_data in self.performer_patterns.items():
            tag_all_values = self.get_tag_data(tag_id)
            if len(tag_all_values) > 0:
                there_are_tags = True
                performer_block.append(tag_data["print"] + ": " + " | ".join(tag_all_values))

        main_block = []
        for tag_id, tag_data in self.base_patterns.items():
            tag_all_values = self.get_tag_data(tag_id)
            if len(tag_all_values) > 0:
                there_are_tags = True
                main_block.append(tag_data["print"] + ": " + " | ".join(tag_all_values))
            else:
                main_block.append(tag_data["print"] + ": " + Fore.BLACK + "Not set" + Fore.RESET)

        if there_are_tags:
            if len(performer_block) > 0:
                print("Performers:")
                print("\n".join(performer_block))
            print("\n".join(main_block) + "\n")
        else:
            print(Fore.RED + "There's no data to be printed" + Fore.RESET)

    def print_youtube(self) -> None:
        """Print all tags parsed from youtube description."""
        if self.youtube:
            self.print_metadata(self.youtube, colors.yt_col)
        else:
            print(Fore.RED + "No new data parsed from description" + Fore.RESET)

    def print_original(self) -> None:
        """Print tags from original file.

        Print tags from the original file, if they are in the predefined
        set of tags.
        """
        if self.original:
            self.print_metadata(self.original, colors.md_col)
        else:
            print(Fore.RED + "There were no pre-existing tags for this file" + Fore.RESET)

    def print_from_tags(self) -> None:
        """Print all tags parsed from original tags."""
        if self.fromtags:
            self.print_metadata(self.fromtags, Fore.YELLOW)
        else:
            print(Fore.RED + "No new data parsed from tags" + Fore.RESET)

    def print_from_desc(self) -> None:
        """Print all tags parsed from YouTube description tags."""
        if self.fromdesc:
            self.print_metadata(self.fromdesc, Fore.GREEN)
        else:
            print(Fore.RED + "No new data parsed from tags parsed from description" + Fore.RESET)

    def print_resolved(self, print_all: bool = False) -> None:
        """Print resolved tags.

        Print the tags in the "resolved" set, meaning that they have
        been assumed to be correct or that they have been manually
        selected to be right.

        :param print_all: Print tags even if they haven't been changed.
        """
        other_tags: list[str] = []
        for tag_id in self.resolved.keys():
            if tag_id not in self.base_patterns and tag_id not in self.performer_patterns:
                other_tags.append(tag_id)
        if other_tags:
            print("  Other tags:")
            for tag in other_tags:
                resolved_tag = self.resolved.get(tag, [])
                joined_tag_items = " | ".join(resolved_tag).replace("\n", " ")
                if resolved_tag == REMOVED_TAG:
                    self.print_metadata_key(f"- {tag}", tag, Fore.RED, self.original)
                elif resolved_tag != self.original.get(tag):
                    self.print_metadata_key(f"- {tag}", tag, Fore.GREEN, self.resolved)
                elif len(joined_tag_items) > 200:
                    print(f"  - {tag}: {colors.md_col}[{joined_tag_items[:65]}...]{Fore.RESET}")
                else:
                    self.print_metadata_key(f"- {tag}", tag, colors.md_col, self.resolved)

        if "performer:" in " ".join(self.resolved.keys()):
            print("  Performers:")
            for tag_id, tag_data in self.performer_patterns.items():
                resolved_tag = self.resolved.get(tag_id, [])
                all_sources_tag = self.get_tag_data(tag_id)
                # If the user chose to remove a tag that existed before
                if resolved_tag == REMOVED_TAG:
                    self.print_metadata_key(tag_data["print"], tag_id, Fore.RED, self.original)
                # If the resolved tag differs from the original tag
                elif resolved_tag != self.original.get(tag_id, []) and self.resolved.get(tag_id) is not None:
                    self.print_metadata_key(tag_data["print"], tag_id, Fore.GREEN, self.resolved)
                # original and resolved are equal, but other tags exist
                elif len(all_sources_tag) > 0 and print_all:
                    print("  " + tag_data["print"] + ": " + " | ".join(all_sources_tag))
                else:
                    self.print_metadata_key(tag_data["print"], tag_id, colors.md_col, self.resolved)
        for tag_id, tag_data in self.base_patterns.items():
            resolved_tag = self.resolved.get(tag_id, [])
            all_sources_tag = self.get_tag_data(tag_id)
            if resolved_tag == REMOVED_TAG:
                self.print_metadata_key(tag_data["print"], tag_id, Fore.RED, self.original)
            elif resolved_tag != self.original.get(tag_id, []) and self.resolved.get(tag_id) is not None:
                self.print_metadata_key(tag_data["print"], tag_id, Fore.GREEN, self.resolved)
            elif len(all_sources_tag) > 0 and print_all:
                print("  " + tag_data["print"] + ": " + " | ".join(all_sources_tag))
            else:
                self.print_metadata_key(tag_data["print"], tag_id, colors.md_col, self.resolved)

        print("")

    def switch_album_to_disc_subtitle(self, manual_album_name: str) -> None:
        """Move album tag to discsubtitle tag.

        Switches the original album tag to the discsubtitle tag so that
        it will be used in the comparison for that tag, rather than
        album, which is not used when the album is set manually.

        :param manual_album_name: What to use as the new album tag.
        """
        original_album = self.original.pop("album", None)
        if original_album is not None and original_album != [manual_album_name]:
            self.original["discsubtitle"] = original_album

    def discard_upload_date(self) -> None:
        """If the date is just the upload date, discard it."""
        if self.original.get("date") and re.match(r"\d\d\d\d\d\d\d\d", self.original["date"][0]):
            self.original.pop("date", None)

    def prune_resolved_tags(self, tags_to_delete: list[str], strings_to_delete_tags_based_on: list[str]) -> None:
        """Remove tags that the user wants removed by default."""
        for tag in tags_to_delete:
            if tag in self.original:
                self.resolved[tag] = REMOVED_TAG

        for tag_id, tag_data in self.original.items():
            for bad_word in strings_to_delete_tags_based_on:
                if any(re.fullmatch(bad_word, item) for item in tag_data):
                    self.resolved[tag_id] = REMOVED_TAG

    def add_source_tag(self) -> None:
        """Add a comment tag with the value 'youtube-dl'."""
        if any("youtube" in item for item in self.original.get("purl", [])):
            if "youtube-dl" not in self.original.get("comment", []):
                self.resolved["comment"] = self.original.get("comment", []) + ["youtube-dl"]

    def get_field(self, field: str, only_new: bool = False) -> list[str]:
        """Get values for field from all sources.

        :param field: Tag to get values for.
        :param only_new: Whether to include the value of the field in
            the original music file.
        """
        old_value = self.original.get(field, [])
        yt_value = self.youtube.get(field, [])
        from_desc_value = self.fromdesc.get(field, [])
        from_tags_value = self.fromtags.get(field, [])
        if only_new:
            return Utils().remove_duplicates(yt_value + from_desc_value + from_tags_value)
        else:
            return Utils().remove_duplicates(old_value + yt_value + from_desc_value + from_tags_value)

    def modify_resolved_field(self) -> None:
        """Manually add key-value pairs to the set of resolved tags."""
        key = " "
        val = " "
        while key and val:
            print("Enter key and value (newline cancels, sequence ' | ' splits tag):")
            key = input("  Key: ")
            val = input("  Value: ")
            if key and val:
                self.resolved[key] = val.split(" | ")

    def delete_tag_item(self) -> None:
        """Present a menu for removing tags and remove selected ones.

        Presents the user with a prompt to fill in a field name from
        which to remove keys. The user can then select what values to
        remove from the list of values from this key.
        """
        tags_in_resolved = []
        for tag in self.resolved.keys():
            if tag in self.base_patterns.keys() or tag in self.performer_patterns.keys():
                if self.resolved[tag] != REMOVED_TAG:
                    tags_in_resolved.append(tag)

        tags_in_resolved = sorted(tags_in_resolved)
        tags_in_resolved.append("Quit")
        removal_menu = TerminalMenu(tags_in_resolved, title="Which field do you want to delete items from?")
        tag_index = removal_menu.show()

        if tag_index is None or isinstance(tag_index, tuple) or tags_in_resolved[tag_index] == "Quit":
            print(Fore.YELLOW + "Returning without removing anything" + Fore.RESET)
        else:
            selected_tag = tags_in_resolved[tag_index]
            items_in_tag = self.resolved.get(selected_tag, []).copy()
            item_removal_menu = TerminalMenu(
                items_in_tag,
                title=f"Which field should be removed from the '{selected_tag}' tag?",
                multi_select=True,
                show_multi_select_hint=True,
                multi_select_empty_ok=True,
                multi_select_select_on_accept=False,
            )

            items_to_remove = item_removal_menu.show()
            if isinstance(items_to_remove, int):
                items_to_remove = [items_to_remove]
            elif items_to_remove is None or len(items_to_remove) == 0:
                print(Fore.YELLOW + "Returning without removing anything" + Fore.RESET)
                return

            for item in items_to_remove:
                self.resolved[selected_tag].remove(items_in_tag[item])
                if len(self.resolved[selected_tag]) == 0:
                    self.resolved[selected_tag] = REMOVED_TAG

    def check_any_new_data_exists(self) -> bool:
        """Check whether there are new tags in the sources.

        Check whether the parsing has produced any values for tags that
        weren't already in the metadata of the music file.

        :return: True if there are new values found, otherwise False.
        """
        new_content_exists = False
        all_new_fields = [key for key in self.youtube.keys()]
        all_new_fields += [key for key in self.fromdesc.keys()]
        all_new_fields += [key for key in self.fromtags.keys()]
        all_new_fields = Utils.remove_duplicates(all_new_fields)
        for tag in all_new_fields:
            all_sources = set(self.get_field(tag))
            original_tags = set(self.original.get(tag, []))
            if not original_tags.issuperset(all_sources):
                # If there are no new tags, the set of all tags should
                # not contain anything that is not already in the
                # original tags.
                new_content_exists = True

        for tag in self.resolved.keys():
            original_tags = set(self.original.get(tag, []))
            resolved_tags = set(self.resolved.get(tag, []))
            if not original_tags.issuperset(resolved_tags):
                # There may be some automatically added tags in
                # resolved. Check that resolved doesn't contain any tag
                # that doesn't already exist in the original tags.
                new_content_exists = True

        return new_content_exists

    def determine_album_artist(self) -> None:
        """Choose value to use for albumartist tag."""
        all_artists = self.get_field("artist")
        resolved_artist = self.resolved.get("artist")
        original_artist = self.original.get("artist")

        if len(all_artists) > 1:
            print("-----------------------------------------------")
            self.print_resolved(print_all=True)
            print(Fore.BLUE + "Select the album artist:")
            one_artist = Utils().select_single_tag(all_artists)
            if len(one_artist) > 0:
                self.resolved["albumartist"] = one_artist
        elif not self.original.get("albumartist"):
            if resolved_artist:
                self.resolved["albumartist"] = resolved_artist
            elif original_artist:
                self.resolved["albumartist"] = original_artist

    def default_to_youtube_date(self) -> None:
        """If youtube has date data, use that for resolved."""
        date = self.youtube.get("date")
        if date:
            self.resolved["date"] = date

    def set_artist_if_obvious(self) -> None:
        """Set the resolved artist if it's good for sure.

        If the original tag and the youtube tags are identical
        with regards to the artist tag, assume that it is correct.
        """
        md_artist = self.original.get("artist")
        yt_artist = self.youtube.get("artist")
        if md_artist is not None and yt_artist is not None:
            if (
                len(md_artist) == 1
                and Utils.split_tag(md_artist[0]) == yt_artist
                or Utils.is_equal_when_stripped(md_artist, yt_artist)
            ):
                self.resolved["artist"] = yt_artist

    def manually_adjust_tag_when_resolving(self, tag_name: str) -> bool:
        """Perform a manual action on a tag when no source is right.

        For the tag with the given name, manually fill choose its
        content. Either completely manually or with help from the
        found tags.

        When neither the original tag, nor any of the new ones has the
        right value, the user can remove the whole tag, one or more
        values in it, a specific value from the found ones, or just
        manually write the tag.
        """
        other_choices = [
            "[s] Select items from a list",
            "[m] Manually fill in tag",
            "[p] Print description metadata",
            "[r] Remove field",
            "[g] Go back",
        ]

        other_choice_menu = TerminalMenu(other_choices, title="Choose the source you want to use:")
        choice = other_choice_menu.show()

        action = ""
        if isinstance(choice, int):
            action = other_choices[choice]

        match action:
            case "[m] Manually fill in tag":
                manual_tag = input("Value: ")
                if manual_tag:
                    self.resolved[tag_name] = [manual_tag]
                else:
                    print("No input, not changing tag")
                    return True
                return False
            case "[p] Print description metadata":
                print("-----------------------------------------------")
                self.print_youtube()
                return True
            case "[s] Select items from a list":
                available_tags = self.get_field(tag_name)
                tag_selection_menu = TerminalMenu(
                    available_tags,
                    title="Select the items you want in this tag",
                    multi_select=True,
                    show_multi_select_hint=True,
                    multi_select_empty_ok=True,
                    multi_select_select_on_accept=False,
                )

                items = tag_selection_menu.show()
                if isinstance(items, int):
                    items = [items]
                elif items is None:
                    print(Fore.RED + "Invalid choice, try again")
                    return True

                self.resolved[tag_name] = []
                for item in items:
                    self.resolved[tag_name].append(available_tags[item])

                return False
            case "[r] Remove field":
                self.resolved[tag_name] = REMOVED_TAG
                return False
            case _:
                print("Going back to previous menu")
                return True

    def resolve_metadata(self) -> None:
        """Merge the metadata from the different sources.

        Use the acquired metadata from all sources to produce a set of
        "resolved" tags. A few tags will automatically be used, but most
        require user interaction to resolve. The user is presented with
        menus where the selection happens. It's also possible to make
        manual edits to the tags.

        :raises UserExitException: Raised when the user chooses to quit
            the app.
        """
        all_tags_with_new_data = [tag_name for tag_name in self.youtube.keys()]
        all_tags_with_new_data += [tag_name for tag_name in self.fromdesc.keys()]
        all_tags_with_new_data += [tag_name for tag_name in self.fromtags.keys()]
        all_tags_with_new_data = Utils.remove_duplicates(all_tags_with_new_data)

        for tag_name in all_tags_with_new_data:
            old_value = self.original.get(tag_name, [])
            yt_value = self.youtube.get(tag_name, [])
            from_desc_value = self.fromdesc.get(tag_name, [])
            from_tags_value = self.fromtags.get(tag_name, [])
            all_values = self.get_field(tag_name, only_new=True)

            if not old_value and len(all_values) > 0 and tag_name != "albumartist":
                if len(yt_value) > 0:
                    self.resolved[tag_name] = yt_value
                elif len(from_tags_value) > 0:
                    self.resolved[tag_name] = from_tags_value
                else:  # len(from_desc_value) > 0:
                    self.resolved[tag_name] = from_desc_value
                print(
                    Fore.YELLOW + f"{tag_name.title()}: No value exists in metadata. Using parsed data: "
                    f"{self.resolved[tag_name]}." + Fore.RESET
                )
            elif Utils.is_equal_when_stripped(yt_value, old_value) and len(old_value) > 0:
                print(Fore.GREEN + f"{tag_name.title()}: Metadata matches YouTube description tags." + Fore.RESET)
                self.resolved[tag_name] = [v.strip() for v in old_value]
                continue
            elif Utils.is_equal_when_stripped(from_desc_value, old_value) and len(old_value) > 0:
                print(Fore.GREEN + f"{tag_name.title()}: Metadata matches tags parsed from YouTube tags." + Fore.RESET)
                self.resolved[tag_name] = [v.strip() for v in old_value]
                continue
            elif Utils.is_equal_when_stripped(from_tags_value, old_value) and len(old_value) > 0:
                print(Fore.GREEN + f"{tag_name.title()}: Metadata matches tags parsed from original tags." + Fore.RESET)
                self.resolved[tag_name] = [v.strip() for v in old_value]
                continue
            else:
                redo = True
                print("-----------------------------------------------")
                self.print_resolved(print_all=True)
                while redo:
                    redo = False
                    candidates = []
                    print(
                        Fore.RED
                        + f"{tag_name.title()}: Mismatch between values in description and metadata:"
                        + Fore.RESET
                    )
                    if len(yt_value) > 0:
                        print("YouTube description: " + colors.yt_col + " | ".join(yt_value) + Fore.RESET)
                        candidates.append("YouTube description")
                    if len(from_tags_value) > 0:
                        print("Parsed from original tags: " + Fore.YELLOW + " | ".join(from_tags_value) + Fore.RESET)
                        candidates.append("Parsed from original tags")

                    print("Exisiting metadata:  " + colors.md_col + " | ".join(old_value) + Fore.RESET)
                    candidates.append("Existing metadata")

                    if len(from_desc_value) > 0:
                        print("Parsed from YouTube tags: " + Fore.GREEN + " | ".join(from_desc_value) + Fore.RESET)
                        candidates.append("Parsed from Youtube tags")

                    candidates.append("Other action")
                    candidates.append("Quit")

                    candidate_menu = TerminalMenu(candidates)
                    choice = candidate_menu.show()

                    if not isinstance(choice, int):
                        raise UserExitException("Skipping this and all later songs")

                    match candidates[choice]:
                        case "Other action":
                            redo = self.manually_adjust_tag_when_resolving(tag_name)

                        case "Existing metadata":
                            self.resolved[tag_name] = old_value

                        case "YouTube description":
                            self.resolved[tag_name] = yt_value

                        case "Parsed from original tags":
                            self.resolved[tag_name] = from_tags_value

                        case "Parsed from Youtube tags":
                            self.resolved[tag_name] = from_desc_value

                        case _:
                            raise UserExitException("Skipping this and all later songs")

        self.determine_album_artist()
