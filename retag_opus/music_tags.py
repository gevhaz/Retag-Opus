"""Module for storing tags from different sources and printing them."""
import re
from copy import deepcopy
from typing import Final

from simple_term_menu import TerminalMenu

from retag_opus import constants, messages, styles
from retag_opus.exceptions import UserExitException
from retag_opus.utils import Utils

Tags = dict[str, list[str]]

REMOVED_TAG: Final[list[str]] = ["[Removed]"]

# Tags that should have the same value for all songs on an album
ALBUM_LEVEL_TAGS: Final[list[str]] = ["album", "albumartist", "date", "genre"]


class MusicTags:
    """Store tags from different sources for a song.

    Stores tags for one song as a dictionary on the same format as the
    one provided by the OggOpus object.
    """

    def __init__(self, manual_album_set: bool = False) -> None:
        """Create empty attributes for each source."""
        self.base_patterns = deepcopy(constants.all_tags)
        self.performer_patterns = deepcopy(constants.performer_tags)
        self.manual_album_set = manual_album_set
        if manual_album_set:
            self.base_patterns["discsubtitle"] = self.base_patterns["album"].copy()
            self.base_patterns["discsubtitle"]["print"] = "Disc subtitle"
            self.base_patterns["album"]["pattern"] = []
        self.original: Tags = {}
        self.youtube: Tags = {}
        self.fromtags: Tags = {}
        self.fromdesc: Tags = {}
        self.resolved: Tags = {}
        self.musicbrainz: Tags = {}
        self.album_level_tags: Tags = {}
        # Length of the song in seconds, used to identify it
        self.duration: float | None = None

    @staticmethod
    def is_performer_tag(tag_id: str) -> bool:
        """Check if a tag is a performer's role, e.g. "performer:violin"."""
        return tag_id.startswith(constants.PERFORMER_PREFIX)

    def performer_tags_in_print_order(self, *sources: Tags) -> list[str]:
        """Get the performer tags in the sources, in the order to print them.

        First come the performer tags that can be parsed from YouTube
        descriptions, in the order of constants.performer_tags. Then come
        the ones that can't, e.g. "performer:theremin" from MusicBrainz,
        in alphabetical order.

        :param sources: The tags to look for performer tags in.

        :return: Performer tag names, e.g. "performer:violin".
        """
        performer_tags_in_sources = []
        for source in sources:
            for tag_id in source.keys():
                if self.is_performer_tag(tag_id) and tag_id not in performer_tags_in_sources:
                    performer_tags_in_sources.append(tag_id)

        performer_tags_with_pattern = []
        for tag_id in self.performer_patterns.keys():
            if tag_id in performer_tags_in_sources:
                performer_tags_with_pattern.append(tag_id)

        performer_tags_without_pattern = []
        for tag_id in performer_tags_in_sources:
            if tag_id not in self.performer_patterns:
                performer_tags_without_pattern.append(tag_id)

        return performer_tags_with_pattern + sorted(performer_tags_without_pattern)

    def performer_print_name(self, tag_id: str) -> str:
        """Get the name to print before the values of a performer tag.

        Performers are printed as a list, e.g.:

          Performers:
          - Lead vocals: Freddie Mercury
          - Timpani: Roger Taylor

        :param tag_id: A performer tag, e.g. "performer:timpani".

        :return: The name to print, e.g. "- Timpani".
        """
        # Tags that can be parsed from YouTube descriptions have a name
        if tag_id in self.performer_patterns:
            return self.performer_patterns[tag_id]["print"]
        role = tag_id.removeprefix(constants.PERFORMER_PREFIX)
        role_with_capital = role[:1].upper() + role[1:]
        return "- " + role_with_capital

    def print_metadata_key(
        self,
        key_type: str,
        key: str,
        style: styles.Style,
        data: Tags,
    ) -> None:
        """Print a single metadata key in specified color.

        :param key_type: Printed name of key.
        :param key: What key to print.
        :param style: Style to print the data in.
        :param data: The tags from which to get the given key.
        """
        value = constants.SEP.join(data.get(key, ["Not found"])).replace(" ", constants.SPACE)
        if self.resolved.get(key) == REMOVED_TAG:
            key_type = f"{key_type} (Removed)"
        style = style if data.get(key) else styles.unset
        print("  " + key_type + ": " + style(value))

    def print_metadata(self, metadata: Tags, style: styles.Style) -> None:
        """Print metadata of given set of tags in specifed color.

        :param metadata: The set of tags to print.
        :param style: The style to print the tags in.
        """
        if any(self.is_performer_tag(t) for t in metadata.keys()):
            print("  Performers:")
            for tag_id in self.performer_tags_in_print_order(metadata):
                if tag_id in metadata and metadata[tag_id] is not None:
                    self.print_metadata_key(self.performer_print_name(tag_id), tag_id, style, metadata)
        for tag_id, tag_data in self.base_patterns.items():
            self.print_metadata_key(tag_data["print"], tag_id, style, metadata)
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
        musicbrainz = self.musicbrainz.get(tag_id)
        if fromtags and fromtags != original:
            print_data.append(styles.from_tags(" | ".join(fromtags)))
        if fromdesc and fromdesc != original:
            print_data.append(styles.from_desc(" | ".join(fromdesc)))
        if original:
            print_data.append(styles.metadata(" | ".join(original)))
        if youtube and original != youtube:
            print_data.append(styles.youtube(" | ".join(youtube)))
        if musicbrainz and original != musicbrainz:
            print_data.append(styles.musicbrainz(" | ".join(musicbrainz)))
        return print_data

    def print_all(self) -> None:
        """Print all tags from all sources.

        Print a block of text with all data from all sources for a given
        tag name, differentiated by color.
        """
        performer_block = []
        there_are_tags = False
        sources = [self.original, self.youtube, self.fromdesc, self.fromtags, self.musicbrainz]
        for tag_id in self.performer_tags_in_print_order(*sources):
            tag_all_values = self.get_tag_data(tag_id)
            if len(tag_all_values) > 0:
                there_are_tags = True
                performer_block.append(self.performer_print_name(tag_id) + ": " + " | ".join(tag_all_values))

        main_block = []
        for tag_id, tag_data in self.base_patterns.items():
            tag_all_values = self.get_tag_data(tag_id)
            if len(tag_all_values) > 0:
                there_are_tags = True
                main_block.append(tag_data["print"] + ": " + " | ".join(tag_all_values))
            else:
                main_block.append(tag_data["print"] + ": " + styles.unset("Not set"))

        if there_are_tags:
            if len(performer_block) > 0:
                print("Performers:")
                print("\n".join(performer_block))
            print("\n".join(main_block) + "\n")
        else:
            messages.error("There's no data to be printed")

    def print_youtube(self) -> None:
        """Print all tags parsed from youtube description."""
        if self.youtube:
            self.print_metadata(self.youtube, styles.youtube)
        else:
            messages.error("No new data parsed from description")

    def print_original(self) -> None:
        """Print tags from original file.

        Print tags from the original file, if they are in the predefined
        set of tags.
        """
        if self.original:
            self.print_metadata(self.original, styles.metadata)
        else:
            messages.error("There were no pre-existing tags for this file")

    def print_from_tags(self) -> None:
        """Print all tags parsed from original tags."""
        if self.fromtags:
            self.print_metadata(self.fromtags, styles.from_tags)
        else:
            messages.error("No new data parsed from tags")

    def print_from_desc(self) -> None:
        """Print all tags parsed from YouTube description tags."""
        if self.fromdesc:
            self.print_metadata(self.fromdesc, styles.from_desc)
        else:
            messages.error("No new data parsed from tags parsed from description")

    def print_resolved(self, print_all: bool = False) -> None:
        """Print resolved tags.

        Print the tags in the "resolved" set, meaning that they have
        been assumed to be correct or that they have been manually
        selected to be right.

        :param print_all: Print tags even if they haven't been changed.
        """
        other_tags: list[str] = []
        for tag_id in self.resolved.keys():
            if tag_id.startswith(constants.MUSICBRAINZ_ID_PREFIX):
                continue
            if tag_id not in self.base_patterns and not self.is_performer_tag(tag_id):
                other_tags.append(tag_id)
        if other_tags:
            print("  Other tags:")
            for tag in other_tags:
                resolved_tag = self.resolved.get(tag, [])
                joined_tag_items = " | ".join(resolved_tag).replace("\n", " ")
                if resolved_tag == REMOVED_TAG:
                    self.print_metadata_key(f"- {tag}", tag, styles.removed, self.original)
                elif resolved_tag != self.original.get(tag):
                    self.print_metadata_key(f"- {tag}", tag, styles.changed, self.resolved)
                elif len(joined_tag_items) > 200:
                    print(f"  - {tag}: " + styles.metadata(f"[{joined_tag_items[:65]}...]"))
                else:
                    self.print_metadata_key(f"- {tag}", tag, styles.metadata, self.resolved)

        # Only performers with something to show are printed: the resolved
        # ones, which include the file's tags and removed tags, and when
        # printing all, the ones in the other sources too
        if print_all:
            sources = [self.resolved, self.original, self.youtube, self.fromdesc, self.fromtags, self.musicbrainz]
            performer_tags = self.performer_tags_in_print_order(*sources)
        else:
            performer_tags = self.performer_tags_in_print_order(self.resolved)
        if performer_tags:
            print("  Performers:")
            for tag_id in performer_tags:
                self.print_resolved_tag(self.performer_print_name(tag_id), tag_id, print_all)
        for tag_id, tag_data in self.base_patterns.items():
            self.print_resolved_tag(tag_data["print"], tag_id, print_all)

        print("")

    def print_resolved_tag(self, printed_tag_name: str, tag_id: str, print_all: bool) -> None:
        """Print the line showing what will be saved in one of the song's tags.

        The resolved tags are the tags that will be saved to the song's
        file. The line shows the tag's resolved value, colored by how it
        compares to the value the file has now:

        - Red (styles.removed), with "(Removed)" after the name: the tag
          will be removed from the file. The value shown is the one the
          file has now.
        - Green (styles.changed): the tag will get the value shown.
        - Cyan (styles.metadata): the tag keeps the value it has now.
          If print_all is set, the values found in all sources are shown
          instead, each in the color of its source, so that they can be
          compared before choosing a value.
        - Gray (styles.unset) "Not found": the tag has no value and won't
          get one.

        For example, if the title "Song (Live)" will be changed to
        "Song", the line is "  Title: Song" in green.

        :param printed_tag_name: The name the tag is shown with, e.g.
            "Title" for the tag "title".
        :param tag_id: The name of the tag in the file, e.g. "title".
        :param print_all: Whether to show the values from all sources for
            a tag that keeps the value it has now.
        """
        resolved_tag = self.resolved.get(tag_id)
        all_sources_tag = self.get_tag_data(tag_id)
        # If the user chose to remove a tag that existed before
        if resolved_tag == REMOVED_TAG:
            self.print_metadata_key(printed_tag_name, tag_id, styles.removed, self.original)
        # If the resolved tag differs from the original tag
        elif resolved_tag is not None and resolved_tag != self.original.get(tag_id, []):
            self.print_metadata_key(printed_tag_name, tag_id, styles.changed, self.resolved)
        # original and resolved are equal, but other tags exist
        elif len(all_sources_tag) > 0 and print_all:
            print("  " + printed_tag_name + ": " + " | ".join(all_sources_tag))
        else:
            self.print_metadata_key(printed_tag_name, tag_id, styles.metadata, self.resolved)

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
        original_date = self.original.get("date")
        if original_date and re.match(r"\d\d\d\d\d\d\d\d", original_date[0]):
            del self.original["date"]

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
        musicbrainz_value = self.musicbrainz.get(field, [])
        new_values = yt_value + from_desc_value + from_tags_value + musicbrainz_value
        if only_new:
            return Utils().remove_duplicates(new_values)
        else:
            return Utils().remove_duplicates(old_value + new_values)

    def modify_resolved_field(self) -> None:
        """Manually add key-value pairs to the set of resolved tags."""
        key = " "
        val = " "
        while key and val:
            print("Enter key and value (newline cancels, sequence ' | ' splits tag, and for genre also ',' and ';'):")
            key = input("  Key: ")
            val = input("  Value: ")
            if key and val:
                self.resolved[key] = Utils.split_manual_value(key, val)

    def delete_tag_item(self) -> None:
        """Present a menu for removing tags and remove selected ones.

        Presents the user with a prompt to fill in a field name from
        which to remove keys. The user can then select what values to
        remove from the list of values from this key.
        """
        tags_in_resolved = []
        for tag in self.resolved.keys():
            if tag in self.base_patterns.keys() or self.is_performer_tag(tag):
                if self.resolved[tag] != REMOVED_TAG:
                    tags_in_resolved.append(tag)

        tags_in_resolved = sorted(tags_in_resolved)
        tags_in_resolved.append("Quit")
        removal_menu = TerminalMenu(tags_in_resolved, title="Which field do you want to delete items from?")
        tag_index = removal_menu.show()

        if tag_index is None or isinstance(tag_index, tuple) or tags_in_resolved[tag_index] == "Quit":
            messages.warning("Returning without removing anything")
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
                messages.warning("Returning without removing anything")
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
        all_new_fields += [key for key in self.musicbrainz.keys()]
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

    def changed_tags(self) -> list[str]:
        """Get the names of the tags that would be changed in the file."""
        changed = []
        for tag_name, value in self.resolved.items():
            # A tag that's removed but not in the file isn't a change
            if value != self.original.get(tag_name, REMOVED_TAG):
                changed.append(tag_name)
        return changed

    def keep_pruned_tags_removed(self, pruned_tags: list[str]) -> None:
        """Remove pruned tags again if they were restored.

        Resolving may set a pruned tag back to its original value, e.g.
        when the YouTube description has the same value. Keep such tags
        removed, unless a different value was chosen.

        :param pruned_tags: Tags that were marked for removal before
            resolving.
        """
        for tag_name in pruned_tags:
            resolved_value = self.resolved.get(tag_name, [])
            if Utils.is_equal_when_stripped(resolved_value, self.original.get(tag_name, [])):
                self.resolved[tag_name] = REMOVED_TAG

    def apply_album_level_tags(self, album_level_tags: Tags) -> None:
        """Use album level tags chosen for an earlier song on the same album.

        The given tags are put in resolved and won't be asked about when
        resolving the metadata.

        :param album_level_tags: Tags previously chosen for the album.
        """
        self.album_level_tags = deepcopy(album_level_tags)
        self.resolved.update(deepcopy(album_level_tags))

    def get_album_level_tags(self) -> Tags:
        """Get the resolved tags that should be the same for the album.

        :return: The resolved album level tags, except removed ones.
        """
        return {
            tag: self.resolved[tag].copy()
            for tag in ALBUM_LEVEL_TAGS
            if self.resolved.get(tag) and self.resolved[tag] != REMOVED_TAG
        }

    @staticmethod
    def is_same_album(album_1: list[str], album_2: list[str]) -> bool:
        """Check whether albums are the same, ignoring e.g. "(2011 Remaster)"."""
        pruned_album_1 = [Utils.prune_title(name) for name in album_1]
        pruned_album_2 = [Utils.prune_title(name) for name in album_2]
        return Utils.is_equal_when_normalized(pruned_album_1, pruned_album_2)

    def differs_from_musicbrainz_album(self, albums: list[list[str]]) -> bool:
        """Check whether any of the albums isn't the one found on MusicBrainz."""
        musicbrainz_album = self.musicbrainz.get("album", [])
        if len(musicbrainz_album) == 0:
            return False
        for album in albums:
            if len(album) > 0 and not self.is_same_album(album, musicbrainz_album):
                return True
        return False

    def album_is_musicbrainz_release(self) -> bool:
        """Check whether the album is the release found on MusicBrainz."""
        return self.is_same_album(self.resolved.get("album", []), self.musicbrainz.get("album", []))

    def determine_album_artist(self) -> None:
        """Choose value to use for albumartist tag."""
        all_artists = Utils.remove_duplicates(self.get_field("albumartist", only_new=True) + self.get_field("artist"))
        resolved_artist = self.resolved.get("artist")
        original_artist = self.original.get("artist")

        if len(all_artists) > 1:
            print("-----------------------------------------------")
            self.print_resolved(print_all=True)
            messages.info("Select the album artist:")
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
                    self.resolved[tag_name] = Utils.split_manual_value(tag_name, manual_tag)
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
                    messages.error("Invalid choice, try again")
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
        all_tags_with_new_data += [tag_name for tag_name in self.musicbrainz.keys()]
        all_tags_with_new_data = Utils.remove_duplicates(all_tags_with_new_data)
        pruned_tags = [tag_name for tag_name, value in self.resolved.items() if value == REMOVED_TAG]

        for tag_name in self.album_level_tags.keys():
            messages.success(
                f"{tag_name.title()}: Using value from earlier song on the same album: "
                f"{self.album_level_tags[tag_name]}."
            )

        for tag_name in all_tags_with_new_data:
            if tag_name == "albumartist":
                continue  # Handled by determine_album_artist
            if tag_name in self.album_level_tags:
                continue
            if tag_name in constants.release_tags and not self.album_is_musicbrainz_release():
                # E.g. a single on YouTube may only be on an album on
                # MusicBrainz, and then its track number would be wrong
                continue
            old_value = self.original.get(tag_name, [])
            yt_value = self.youtube.get(tag_name, [])
            from_desc_value = self.fromdesc.get(tag_name, [])
            from_tags_value = self.fromtags.get(tag_name, [])
            musicbrainz_value = self.musicbrainz.get(tag_name, [])
            all_values = self.get_field(tag_name, only_new=True)

            # MusicBrainz may have found the song on another release than
            # the album that the other sources say, e.g. on an album rather
            # than a single, and then the user chooses which is right
            album_differs_from_musicbrainz = tag_name == "album" and self.differs_from_musicbrainz_album(
                [old_value, yt_value, from_tags_value, from_desc_value]
            )

            if tag_name.startswith(constants.MUSICBRAINZ_ID_PREFIX) and len(musicbrainz_value) > 0:
                self.resolved[tag_name] = musicbrainz_value
            elif not old_value and len(all_values) > 0 and not album_differs_from_musicbrainz:
                # In order of preference
                sources = {
                    "YouTube description": yt_value,
                    "tags parsed from original tags": from_tags_value,
                    "tags parsed from YouTube tags": from_desc_value,
                    "MusicBrainz": musicbrainz_value,
                }
                for source, value in sources.items():
                    if len(value) > 0:
                        self.resolved[tag_name] = value
                        if tag_name not in constants.match_tags:
                            messages.warning(
                                f"{tag_name.title()}: No value exists in metadata. Using {source}: {value}."
                            )
                        break
            elif (
                Utils.is_equal_when_stripped(yt_value, old_value)
                and len(old_value) > 0
                and not album_differs_from_musicbrainz
            ):
                messages.success(f"{tag_name.title()}: Metadata matches YouTube description tags.")
                self.resolved[tag_name] = [v.strip() for v in old_value]
                continue
            elif (
                Utils.is_equal_when_stripped(from_desc_value, old_value)
                and len(old_value) > 0
                and not album_differs_from_musicbrainz
            ):
                messages.success(f"{tag_name.title()}: Metadata matches tags parsed from YouTube tags.")
                self.resolved[tag_name] = [v.strip() for v in old_value]
                continue
            elif (
                Utils.is_equal_when_stripped(from_tags_value, old_value)
                and len(old_value) > 0
                and not album_differs_from_musicbrainz
            ):
                messages.success(f"{tag_name.title()}: Metadata matches tags parsed from original tags.")
                self.resolved[tag_name] = [v.strip() for v in old_value]
                continue
            elif (
                Utils.is_equal_when_normalized(musicbrainz_value, old_value)
                and len(old_value) > 0
                and not album_differs_from_musicbrainz
            ):
                messages.success(f"{tag_name.title()}: Metadata matches MusicBrainz.")
                self.resolved[tag_name] = [v.strip() for v in old_value]
                continue
            else:
                redo = True
                print("-----------------------------------------------")
                self.print_resolved(print_all=True)
                while redo:
                    redo = False
                    candidates = []
                    candidate_values: list[list[str]] = []
                    messages.conflict(f"{tag_name.title()}: Mismatch between values in description and metadata:")
                    if len(yt_value) > 0:
                        print("YouTube description: " + styles.youtube(" | ".join(yt_value)))
                        candidates.append("YouTube description")
                        candidate_values.append(yt_value)
                    if len(from_tags_value) > 0:
                        print("Parsed from original tags: " + styles.from_tags(" | ".join(from_tags_value)))
                        candidates.append("Parsed from original tags")
                        candidate_values.append(from_tags_value)

                    print("Existing metadata:  " + styles.metadata(" | ".join(old_value)))
                    candidates.append("Existing metadata")
                    candidate_values.append(old_value)

                    if len(from_desc_value) > 0:
                        print("Parsed from YouTube tags: " + styles.from_desc(" | ".join(from_desc_value)))
                        candidates.append("Parsed from Youtube tags")
                        candidate_values.append(from_desc_value)

                    # Start on the value MusicBrainz agrees with, or on
                    # MusicBrainz if it agrees with none of them
                    cursor = 0
                    if len(musicbrainz_value) > 0:
                        print("MusicBrainz: " + styles.musicbrainz(" | ".join(musicbrainz_value)))
                        cursor = len(candidates)  # MusicBrainz itself
                        for index, value in enumerate(candidate_values):
                            if Utils.is_equal_when_normalized(value, musicbrainz_value):
                                cursor = index
                                break
                        candidates.append("MusicBrainz")

                    candidates.append("Other action")
                    candidates.append("Quit")

                    candidate_menu = TerminalMenu(candidates, cursor_index=cursor)
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

                        case "MusicBrainz":
                            self.resolved[tag_name] = musicbrainz_value

                        case _:
                            raise UserExitException("Skipping this and all later songs")

        self.keep_pruned_tags_removed(pruned_tags)
        if "albumartist" not in self.album_level_tags:
            self.determine_album_artist()
            self.keep_pruned_tags_removed(pruned_tags)
