"""Module for storing tags from different sources and printing them."""
import re
from copy import deepcopy
from typing import Final

from simple_term_menu import TerminalMenu

from retag_opus import constants, messages, styles, utils
from retag_opus.exceptions import UserExitException

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
        self.tags_printed_for_every_song = deepcopy(constants.tags_printed_for_every_song)
        self.manual_album_set = manual_album_set
        if manual_album_set:
            self.tags_printed_for_every_song["discsubtitle"] = self.tags_printed_for_every_song["album"].copy()
            self.tags_printed_for_every_song["discsubtitle"]["print_name"] = "Disc subtitle"
            self.tags_printed_for_every_song["album"]["patterns"] = []
        self.original: Tags = {}
        self.youtube: Tags = {}
        self.parsed_from_original: Tags = {}
        self.parsed_from_youtube: Tags = {}
        self.resolved: Tags = {}
        self.musicbrainz: Tags = {}
        self.album_level_tags: Tags = {}
        # Length of the song in seconds, used to identify it
        self.length: float | None = None

    @staticmethod
    def is_performer_tag(tag_name: str) -> bool:
        """Check if a tag is a performer's role, e.g. "performer:violin"."""
        return tag_name.startswith(constants.PERFORMER_PREFIX)

    def performer_tags_in_print_order(self, *sources: Tags) -> list[str]:
        """Get the performer tags in the sources, in the order to print them.

        First come the common performer tags, in the order of
        constants.common_performer_tags. Then come the others, e.g.
        "performer:theremin" from MusicBrainz, in alphabetical order.

        :param sources: The tags to look for performer tags in.

        :return: Performer tag names, e.g. "performer:violin".
        """
        performer_tags_in_sources = []
        for source in sources:
            for tag_name in source.keys():
                if self.is_performer_tag(tag_name) and tag_name not in performer_tags_in_sources:
                    performer_tags_in_sources.append(tag_name)

        common_performer_tags_in_sources = []
        for tag_name in constants.common_performer_tags:
            if tag_name in performer_tags_in_sources:
                common_performer_tags_in_sources.append(tag_name)

        other_performer_tags_in_sources = []
        for tag_name in performer_tags_in_sources:
            if tag_name not in constants.common_performer_tags:
                other_performer_tags_in_sources.append(tag_name)

        return common_performer_tags_in_sources + sorted(other_performer_tags_in_sources)

    @staticmethod
    def performer_print_name(tag_name: str) -> str:
        """Get the name to print before the values of a performer tag.

        Performers are printed as a list, e.g.:

          Performers:
          - Lead vocals: Freddie Mercury
          - Timpani: Roger Taylor

        :param tag_name: A performer tag, e.g. "performer:timpani".

        :return: The name to print, e.g. "- Timpani".
        """
        role = tag_name.removeprefix(constants.PERFORMER_PREFIX)
        role_with_capital = role[:1].upper() + role[1:]
        return "- " + role_with_capital

    def print_metadata_key(
        self,
        printed_tag_name: str,
        tag_name: str,
        style: styles.Style,
        tags: Tags,
    ) -> None:
        """Print a single metadata key in specified color.

        :param printed_tag_name: The name the tag is shown with, e.g. "Title".
        :param tag_name: The tag to print, e.g. "title".
        :param style: Style to print the value in.
        :param tags: The tags to get the value of the tag from, e.g. the
            resolved tags.
        """
        joined_values = constants.VALUE_SEPARATOR.join(tags.get(tag_name, ["Not found"]))
        value = joined_values.replace(" ", constants.PRINTED_SPACE)
        if self.resolved.get(tag_name) == REMOVED_TAG:
            printed_tag_name = f"{printed_tag_name} (Removed)"
        style = style if tags.get(tag_name) else styles.unset
        print("  " + printed_tag_name + ": " + style(value))

    def print_metadata(self, metadata: Tags, style: styles.Style) -> None:
        """Print metadata of given set of tags in specifed color.

        :param metadata: The set of tags to print.
        :param style: The style to print the tags in.
        """
        if any(self.is_performer_tag(t) for t in metadata.keys()):
            print("  Performers:")
            for tag_name in self.performer_tags_in_print_order(metadata):
                if tag_name in metadata and metadata[tag_name] is not None:
                    self.print_metadata_key(self.performer_print_name(tag_name), tag_name, style, metadata)
        for tag_name, tag_data in self.tags_printed_for_every_song.items():
            self.print_metadata_key(tag_data["print_name"], tag_name, style, metadata)
        print("")

    def get_colored_values_from_all_sources(self, tag_name: str) -> list[str]:
        """Get the values of a tag from all sources, colored by source.

        Returns a list of all values for a specific tag from various
        sources with color depending on source.

        :param tag_name: The tag name for which data should be returned

        :return: List with strings containing the value the given tag
        has in different sources with color codes that differ between
        sources. If no source contains the tag, an empty list is
        returned.
        """
        colored_values: list[str] = []
        original = self.original.get(tag_name)
        youtube = self.youtube.get(tag_name)
        parsed_from_youtube = self.parsed_from_youtube.get(tag_name)
        parsed_from_original = self.parsed_from_original.get(tag_name)
        musicbrainz = self.musicbrainz.get(tag_name)
        if parsed_from_original and parsed_from_original != original:
            colored_values.append(styles.parsed_from_original(" | ".join(parsed_from_original)))
        if parsed_from_youtube and parsed_from_youtube != original:
            colored_values.append(styles.parsed_from_youtube(" | ".join(parsed_from_youtube)))
        if original:
            colored_values.append(styles.original(" | ".join(original)))
        if youtube and original != youtube:
            colored_values.append(styles.youtube(" | ".join(youtube)))
        if musicbrainz and original != musicbrainz:
            colored_values.append(styles.musicbrainz(" | ".join(musicbrainz)))
        return colored_values

    def print_all(self) -> None:
        """Print all tags from all sources.

        Print a block of text with all data from all sources for a given
        tag name, differentiated by color.
        """
        performer_block = []
        there_are_tags = False
        sources = [self.original, self.youtube, self.parsed_from_youtube, self.parsed_from_original, self.musicbrainz]
        for tag_name in self.performer_tags_in_print_order(*sources):
            colored_values = self.get_colored_values_from_all_sources(tag_name)
            if len(colored_values) > 0:
                there_are_tags = True
                performer_block.append(self.performer_print_name(tag_name) + ": " + " | ".join(colored_values))

        main_block = []
        for tag_name, tag_data in self.tags_printed_for_every_song.items():
            colored_values = self.get_colored_values_from_all_sources(tag_name)
            if len(colored_values) > 0:
                there_are_tags = True
                main_block.append(tag_data["print_name"] + ": " + " | ".join(colored_values))
            else:
                main_block.append(tag_data["print_name"] + ": " + styles.unset("Not set"))

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
            self.print_metadata(self.original, styles.original)
        else:
            messages.error("There were no pre-existing tags for this file")

    def print_parsed_from_original(self) -> None:
        """Print all tags parsed from original tags."""
        if self.parsed_from_original:
            self.print_metadata(self.parsed_from_original, styles.parsed_from_original)
        else:
            messages.error("No new data parsed from tags")

    def print_parsed_from_youtube(self) -> None:
        """Print all tags parsed from YouTube description tags."""
        if self.parsed_from_youtube:
            self.print_metadata(self.parsed_from_youtube, styles.parsed_from_youtube)
        else:
            messages.error("No new data parsed from tags parsed from description")

    def print_resolved(self, print_all: bool = False) -> None:
        """Print resolved tags.

        Print the tags in the "resolved" set, meaning that they have
        been assumed to be correct or that they have been manually
        selected to be right.

        :param print_all: Print tags even if they haven't been changed.
        """
        other_tag_names: list[str] = []
        for tag_name in self.resolved.keys():
            if tag_name.startswith(constants.MUSICBRAINZ_ID_PREFIX):
                continue
            if tag_name not in self.tags_printed_for_every_song and not self.is_performer_tag(tag_name):
                other_tag_names.append(tag_name)
        if other_tag_names:
            print("  Other tags:")
            for tag_name in other_tag_names:
                resolved_values = self.resolved.get(tag_name, [])
                joined_resolved_values = " | ".join(resolved_values).replace("\n", " ")
                if resolved_values == REMOVED_TAG:
                    self.print_metadata_key(f"- {tag_name}", tag_name, styles.removed, self.original)
                elif resolved_values != self.original.get(tag_name):
                    self.print_metadata_key(f"- {tag_name}", tag_name, styles.changed, self.resolved)
                elif len(joined_resolved_values) > 200:
                    print(f"  - {tag_name}: " + styles.original(f"[{joined_resolved_values[:65]}...]"))
                else:
                    self.print_metadata_key(f"- {tag_name}", tag_name, styles.original, self.resolved)

        # Only performers with something to show are printed: the resolved
        # ones, which include the file's tags and removed tags, and when
        # printing all, the ones in the other sources too
        if print_all:
            sources = [
                self.resolved,
                self.original,
                self.youtube,
                self.parsed_from_youtube,
                self.parsed_from_original,
                self.musicbrainz,
            ]
            performer_tags = self.performer_tags_in_print_order(*sources)
        else:
            performer_tags = self.performer_tags_in_print_order(self.resolved)
        if performer_tags:
            print("  Performers:")
            for tag_name in performer_tags:
                self.print_resolved_tag(self.performer_print_name(tag_name), tag_name, print_all)
        for tag_name, tag_data in self.tags_printed_for_every_song.items():
            self.print_resolved_tag(tag_data["print_name"], tag_name, print_all)

        print("")

    def print_resolved_tag(self, printed_tag_name: str, tag_name: str, print_all: bool) -> None:
        """Print the line showing what will be saved in one of the song's tags.

        The resolved tags are the tags that will be saved to the song's
        file. The line shows the tag's resolved value, colored by how it
        compares to the value the file has now:

        - Red (styles.removed), with "(Removed)" after the name: the tag
          will be removed from the file. The value shown is the one the
          file has now.
        - Green (styles.changed): the tag will get the value shown.
        - Cyan (styles.original): the tag keeps the value it has now.
          If print_all is set, the values found in all sources are shown
          instead, each in the color of its source, so that they can be
          compared before choosing a value.
        - Gray (styles.unset) "Not found": the tag has no value and won't
          get one.

        For example, if the title "Song (Live)" will be changed to
        "Song", the line is "  Title: Song" in green.

        :param printed_tag_name: The name the tag is shown with, e.g.
            "Title" for the tag "title".
        :param tag_name: The name of the tag in the file, e.g. "title".
        :param print_all: Whether to show the values from all sources for
            a tag that keeps the value it has now.
        """
        resolved_values = self.resolved.get(tag_name)
        colored_values = self.get_colored_values_from_all_sources(tag_name)
        # If the user chose to remove a tag that existed before
        if resolved_values == REMOVED_TAG:
            self.print_metadata_key(printed_tag_name, tag_name, styles.removed, self.original)
        # If the resolved tag differs from the original tag
        elif resolved_values is not None and resolved_values != self.original.get(tag_name, []):
            self.print_metadata_key(printed_tag_name, tag_name, styles.changed, self.resolved)
        # original and resolved are equal, but other tags exist
        elif len(colored_values) > 0 and print_all:
            print("  " + printed_tag_name + ": " + " | ".join(colored_values))
        else:
            self.print_metadata_key(printed_tag_name, tag_name, styles.original, self.resolved)

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

        for tag_name, original_values in self.original.items():
            for removal_pattern in strings_to_delete_tags_based_on:
                if any(re.fullmatch(removal_pattern, value) for value in original_values):
                    self.resolved[tag_name] = REMOVED_TAG

    def add_source_tag(self) -> None:
        """Add a comment tag with the value 'youtube-dl'."""
        original_comment = self.original.get("comment", [])
        source_urls = self.original.get("purl", [])
        is_from_youtube = any("youtube" in url for url in source_urls)
        if is_from_youtube and "youtube-dl" not in original_comment:
            self.resolved["comment"] = original_comment + ["youtube-dl"]

    def get_values_from_all_sources(self, tag_name: str, only_new: bool = False) -> list[str]:
        """Get the values of a tag from all sources.

        :param tag_name: Tag to get values for.
        :param only_new: Whether to leave out the values in the original
            music file.
        """
        original_values = self.original.get(tag_name, [])
        youtube_values = self.youtube.get(tag_name, [])
        parsed_from_youtube_values = self.parsed_from_youtube.get(tag_name, [])
        parsed_from_original_values = self.parsed_from_original.get(tag_name, [])
        musicbrainz_values = self.musicbrainz.get(tag_name, [])
        new_values = youtube_values + parsed_from_youtube_values + parsed_from_original_values + musicbrainz_values
        if only_new:
            return utils.remove_duplicates(new_values)
        else:
            return utils.remove_duplicates(original_values + new_values)

    def modify_resolved_field(self) -> None:
        """Manually add key-value pairs to the set of resolved tags."""
        tag_name = " "
        value = " "
        while tag_name and value:
            print("Enter key and value (newline cancels, sequence ' | ' splits tag, and for genre also ',' and ';'):")
            tag_name = input("  Key: ")
            value = input("  Value: ")
            if tag_name and value:
                self.resolved[tag_name] = utils.split_manual_value(tag_name, value)

    def delete_tag_item(self) -> None:
        """Present a menu for removing tags and remove selected ones.

        Presents the user with a prompt to fill in a field name from
        which to remove keys. The user can then select what values to
        remove from the list of values from this key.
        """
        tags_in_resolved = []
        for tag_name, tag_values in self.resolved.items():
            is_known_tag = tag_name in self.tags_printed_for_every_song or self.is_performer_tag(tag_name)
            if is_known_tag and tag_values != REMOVED_TAG:
                tags_in_resolved.append(tag_name)

        tags_in_resolved.sort()
        tags_in_resolved.append("Quit")
        removal_menu = TerminalMenu(tags_in_resolved, title="Which field do you want to delete items from?")
        tag_index = removal_menu.show()

        if tag_index is None or isinstance(tag_index, tuple) or tags_in_resolved[tag_index] == "Quit":
            messages.warning("Returning without removing anything")
        else:
            selected_tag = tags_in_resolved[tag_index]
            values_in_tag = self.resolved.get(selected_tag, []).copy()
            item_removal_menu = TerminalMenu(
                values_in_tag,
                title=f"Which field should be removed from the '{selected_tag}' tag?",
                multi_select=True,
                show_multi_select_hint=True,
                multi_select_empty_ok=True,
                multi_select_select_on_accept=False,
            )

            indices_to_remove = item_removal_menu.show()
            if isinstance(indices_to_remove, int):
                indices_to_remove = [indices_to_remove]
            elif indices_to_remove is None or len(indices_to_remove) == 0:
                messages.warning("Returning without removing anything")
                return

            for index_to_remove in indices_to_remove:
                self.resolved[selected_tag].remove(values_in_tag[index_to_remove])
                if len(self.resolved[selected_tag]) == 0:
                    self.resolved[selected_tag] = REMOVED_TAG

    def check_any_new_data_exists(self) -> bool:
        """Check whether there are new tags in the sources.

        Check whether the parsing has produced any values for tags that
        weren't already in the metadata of the music file.

        :return: True if there are new values found, otherwise False.
        """
        for tag in self.tags_with_new_data():
            values_from_all_sources = set(self.get_values_from_all_sources(tag))
            original_values = set(self.original.get(tag, []))
            if not original_values.issuperset(values_from_all_sources):
                # If there are no new tags, the set of all tags should
                # not contain anything that is not already in the
                # original tags.
                return True

        for tag, resolved_values in self.resolved.items():
            original_values = set(self.original.get(tag, []))
            if not original_values.issuperset(resolved_values):
                # There may be some automatically added tags in
                # resolved. Check that resolved doesn't contain any tag
                # that doesn't already exist in the original tags.
                return True

        return False

    def tags_with_new_data(self) -> list[str]:
        """Get the names of the tags that Retag Opus found values for.

        The values are the ones from the YouTube description, parsed from
        it or from the song's existing tags, or found on MusicBrainz, as
        opposed to the values the song's file already has. E.g. ["title",
        "artist", "date"] if those are the only tags any of them has a
        value for.
        """
        tag_names: list[str] = []
        for new_source in [self.youtube, self.parsed_from_youtube, self.parsed_from_original, self.musicbrainz]:
            tag_names.extend(new_source.keys())
        return utils.remove_duplicates(tag_names)

    def changed_tags(self) -> list[str]:
        """Get the names of the tags that would be changed in the file."""
        changed_tag_names = []
        for tag_name, value in self.resolved.items():
            # A tag that's removed but not in the file isn't a change
            if value != self.original.get(tag_name, REMOVED_TAG):
                changed_tag_names.append(tag_name)
        return changed_tag_names

    def keep_pruned_tags_removed(self, pruned_tags: list[str]) -> None:
        """Remove pruned tags again if they were restored.

        Resolving may set a pruned tag back to its original value, e.g.
        when the YouTube description has the same value. Keep such tags
        removed, unless a different value was chosen.

        :param pruned_tags: Tags that were marked for removal before
            resolving.
        """
        for tag_name in pruned_tags:
            resolved_values = self.resolved.get(tag_name, [])
            if utils.is_equal_when_stripped(resolved_values, self.original.get(tag_name, [])):
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
        pruned_album_1 = [utils.prune_title(name) for name in album_1]
        pruned_album_2 = [utils.prune_title(name) for name in album_2]
        return utils.is_equal_when_normalized(pruned_album_1, pruned_album_2)

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
        album_artist_candidates = utils.remove_duplicates(
            self.get_values_from_all_sources("albumartist", only_new=True) + self.get_values_from_all_sources("artist")
        )
        resolved_artist = self.resolved.get("artist")
        original_artist = self.original.get("artist")

        if len(album_artist_candidates) > 1:
            print("-----------------------------------------------")
            self.print_resolved(print_all=True)
            messages.info("Select the album artist:")
            selected_album_artist = utils.select_single_value(album_artist_candidates)
            if len(selected_album_artist) > 0:
                self.resolved["albumartist"] = selected_album_artist
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
        original_artists = self.original.get("artist")
        youtube_artists = self.youtube.get("artist")
        if original_artists is not None and youtube_artists is not None:
            if (
                len(original_artists) == 1
                and utils.split_tag(original_artists[0]) == youtube_artists
                or utils.is_equal_when_stripped(original_artists, youtube_artists)
            ):
                self.resolved["artist"] = youtube_artists

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
                entered_value = input("Value: ")
                if entered_value:
                    self.resolved[tag_name] = utils.split_manual_value(tag_name, entered_value)
                else:
                    print("No input, not changing tag")
                    return True
                return False
            case "[p] Print description metadata":
                print("-----------------------------------------------")
                self.print_youtube()
                return True
            case "[s] Select items from a list":
                values_from_all_sources = self.get_values_from_all_sources(tag_name)
                tag_selection_menu = TerminalMenu(
                    values_from_all_sources,
                    title="Select the items you want in this tag",
                    multi_select=True,
                    show_multi_select_hint=True,
                    multi_select_empty_ok=True,
                    multi_select_select_on_accept=False,
                )

                selected_indices = tag_selection_menu.show()
                if isinstance(selected_indices, int):
                    selected_indices = [selected_indices]
                elif selected_indices is None:
                    messages.error("Invalid choice, try again")
                    return True

                self.resolved[tag_name] = []
                for selected_index in selected_indices:
                    self.resolved[tag_name].append(values_from_all_sources[selected_index])

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
        pruned_tags = [tag_name for tag_name, value in self.resolved.items() if value == REMOVED_TAG]

        for tag_name, album_level_value in self.album_level_tags.items():
            messages.success(
                f"{tag_name.title()}: Using value from earlier song on the same album: {album_level_value}."
            )

        for tag_name in self.tags_with_new_data():
            if tag_name == "albumartist":
                continue  # Handled by determine_album_artist
            if tag_name in self.album_level_tags:
                continue
            if tag_name in constants.release_tags and not self.album_is_musicbrainz_release():
                # E.g. a single on YouTube may only be on an album on
                # MusicBrainz, and then its track number would be wrong
                continue
            original_values = self.original.get(tag_name, [])
            youtube_values = self.youtube.get(tag_name, [])
            parsed_from_youtube_values = self.parsed_from_youtube.get(tag_name, [])
            parsed_from_original_values = self.parsed_from_original.get(tag_name, [])
            musicbrainz_values = self.musicbrainz.get(tag_name, [])
            new_values = self.get_values_from_all_sources(tag_name, only_new=True)

            # MusicBrainz may have found the song on another release than
            # the album that the other sources say, e.g. on an album rather
            # than a single, and then the user chooses which is right
            album_differs_from_musicbrainz = tag_name == "album" and self.differs_from_musicbrainz_album(
                [original_values, youtube_values, parsed_from_original_values, parsed_from_youtube_values]
            )
            # The existing value can be kept if a source agrees with it
            can_keep_original_values = len(original_values) > 0 and not album_differs_from_musicbrainz
            stripped_original_values = [v.strip() for v in original_values]

            if tag_name.startswith(constants.MUSICBRAINZ_ID_PREFIX) and len(musicbrainz_values) > 0:
                self.resolved[tag_name] = musicbrainz_values
            elif not original_values and len(new_values) > 0 and not album_differs_from_musicbrainz:
                # In order of preference
                sources = {
                    "YouTube description": youtube_values,
                    "tags parsed from original tags": parsed_from_original_values,
                    "tags parsed from YouTube tags": parsed_from_youtube_values,
                    "MusicBrainz": musicbrainz_values,
                }
                for source, source_values in sources.items():
                    if len(source_values) > 0:
                        self.resolved[tag_name] = source_values
                        if tag_name not in constants.track_position_tags:
                            messages.warning(
                                f"{tag_name.title()}: No value exists in metadata. Using {source}: {source_values}."
                            )
                        break
            elif can_keep_original_values and utils.is_equal_when_stripped(youtube_values, original_values):
                messages.success(f"{tag_name.title()}: Metadata matches YouTube description tags.")
                self.resolved[tag_name] = stripped_original_values
            elif can_keep_original_values and utils.is_equal_when_stripped(parsed_from_youtube_values, original_values):
                messages.success(f"{tag_name.title()}: Metadata matches tags parsed from YouTube tags.")
                self.resolved[tag_name] = stripped_original_values
            elif can_keep_original_values and utils.is_equal_when_stripped(
                parsed_from_original_values, original_values
            ):
                messages.success(f"{tag_name.title()}: Metadata matches tags parsed from original tags.")
                self.resolved[tag_name] = stripped_original_values
            elif can_keep_original_values and utils.is_equal_when_normalized(musicbrainz_values, original_values):
                messages.success(f"{tag_name.title()}: Metadata matches MusicBrainz.")
                self.resolved[tag_name] = stripped_original_values
            else:
                redo = True
                print("-----------------------------------------------")
                self.print_resolved(print_all=True)
                while redo:
                    redo = False
                    candidates = []
                    candidate_values: list[list[str]] = []
                    messages.conflict(f"{tag_name.title()}: Mismatch between values in description and metadata:")
                    if len(youtube_values) > 0:
                        print("YouTube description: " + styles.youtube(" | ".join(youtube_values)))
                        candidates.append("YouTube description")
                        candidate_values.append(youtube_values)
                    if len(parsed_from_original_values) > 0:
                        print(
                            "Parsed from original tags: "
                            + styles.parsed_from_original(" | ".join(parsed_from_original_values))
                        )
                        candidates.append("Parsed from original tags")
                        candidate_values.append(parsed_from_original_values)

                    print("Existing metadata:  " + styles.original(" | ".join(original_values)))
                    candidates.append("Existing metadata")
                    candidate_values.append(original_values)

                    if len(parsed_from_youtube_values) > 0:
                        print(
                            "Parsed from YouTube tags: "
                            + styles.parsed_from_youtube(" | ".join(parsed_from_youtube_values))
                        )
                        candidates.append("Parsed from Youtube tags")
                        candidate_values.append(parsed_from_youtube_values)

                    # Start on the value MusicBrainz agrees with, or on
                    # MusicBrainz if it agrees with none of them
                    cursor = 0
                    if len(musicbrainz_values) > 0:
                        print("MusicBrainz: " + styles.musicbrainz(" | ".join(musicbrainz_values)))
                        cursor = len(candidates)  # MusicBrainz itself
                        for index, value in enumerate(candidate_values):
                            if utils.is_equal_when_normalized(value, musicbrainz_values):
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
                            self.resolved[tag_name] = original_values

                        case "YouTube description":
                            self.resolved[tag_name] = youtube_values

                        case "Parsed from original tags":
                            self.resolved[tag_name] = parsed_from_original_values

                        case "Parsed from Youtube tags":
                            self.resolved[tag_name] = parsed_from_youtube_values

                        case "MusicBrainz":
                            self.resolved[tag_name] = musicbrainz_values

                        case _:
                            raise UserExitException("Skipping this and all later songs")

        self.keep_pruned_tags_removed(pruned_tags)
        if "albumartist" not in self.album_level_tags:
            self.determine_album_artist()
            self.keep_pruned_tags_removed(pruned_tags)
