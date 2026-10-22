"""Module for storing a song's tags from all sources and choosing among them.

The tags of a song can be thought of as a table, with a row per tag and
a column per source, e.g.:

            YouTube        tags parsed from   tags parsed from   MusicBrainz   the file
            description    original tags      YouTube tags
    artist  Queen                                                Queen         queen
    title   Song (Live)    Song                                  Song          Song

set_tags() and tags_from() set and get a whole column, e.g.
set_tags(YOUTUBE, {"title": ["Song (Live)"]}), and values_from() gives
one cell, e.g. values_from(YOUTUBE, "title"). The columns with the
values that Retag Opus found come first, in order of preference, and the
file's column, ORIGINAL, comes last, since it's what the others are
compared with. The Source of a column says what it's
called, which style its values are printed in, and how they're compared
with the file's.

Most methods look at one row at a time. found_values() gives the found
values of a tag, leaving out the file and sources without any.
resolve_metadata() goes through the rows with found values, and keeps
the file's value if a source agrees with it, or else asks the user. The
result is MusicTags.resolved, the column that will be saved to the file.
"""
import re
from copy import deepcopy
from typing import Callable, Final, NamedTuple

from simple_term_menu import TerminalMenu

from retag_opus import constants, messages, styles, utils
from retag_opus.exceptions import UserExitException

Tags = dict[str, list[str]]

REMOVED_TAG: Final[list[str]] = ["[Removed]"]

# Tags that should have the same value for all songs on an album
ALBUM_LEVEL_TAGS: Final[list[str]] = ["album", "albumartist", "date", "genre"]


class Source(NamedTuple):
    """A source of values for a song's tags, e.g. the YouTube description.

    The name is used in messages, e.g. "Metadata matches tags parsed
    from original tags", and with a capital first letter in menus. The
    values of the source are printed in its style, and is_equal checks
    whether they agree with the values the song's file has, by default
    ignoring whitespace around them.
    """

    name: str
    style: styles.Style
    is_equal: Callable[[list[str], list[str]], bool] = utils.is_equal_when_stripped

    def capitalized_name(self) -> str:
        """Get the name with a capital first letter, e.g. "Existing metadata"."""
        return self.name[:1].upper() + self.name[1:]


YOUTUBE: Final = Source("YouTube description", styles.youtube)
PARSED_FROM_ORIGINAL: Final = Source("tags parsed from original tags", styles.parsed_from_original)
PARSED_FROM_YOUTUBE: Final = Source("tags parsed from YouTube tags", styles.parsed_from_youtube)
# MusicBrainz uses typographic apostrophes, quotes and dashes, which
# don't make its values differ from the file's
MUSICBRAINZ: Final = Source("MusicBrainz", styles.musicbrainz, utils.is_equal_when_normalized)
# The song's file
ORIGINAL: Final = Source("existing metadata", styles.original)


class MusicTags:
    """Store tags from different sources for a song.

    Stores tags for one song as a dictionary on the same format as the
    one provided by the OggOpus object.
    """

    def __init__(self) -> None:
        """Create empty attributes for each source."""
        self.tags_printed_for_every_song = dict(constants.tags_printed_for_every_song)
        # The tags of each source. The sources other than the song's file
        # come first, most preferred first. When a tag has no value yet, it
        # gets the values of the first of them that has any, and lists of
        # values come in this order, followed by the values the file has.
        self._tags_by_source: dict[Source, Tags] = {
            YOUTUBE: {},
            PARSED_FROM_ORIGINAL: {},
            PARSED_FROM_YOUTUBE: {},
            MUSICBRAINZ: {},
            ORIGINAL: {},
        }
        self.resolved: Tags = {}
        self.album_level_tags: Tags = {}
        # Length of the song in seconds, used to identify it
        self.length: float | None = None

    def values_from(self, source: Source, tag_name: str) -> list[str]:
        """Get the values that a source has for a tag, or [] if it has none.

        Example: values_from(YOUTUBE, "title") gives ["Song"] if the
        YouTube description says the title is "Song".
        """
        return self.tags_from(source).get(tag_name, [])

    def set_tags(self, source: Source, source_tags: Tags) -> None:
        """Set all tags of a source, e.g. the tags parsed from the YouTube description.

        Example: set_tags(YOUTUBE, {"title": ["Song"]}) makes
        values_from(YOUTUBE, "title") give ["Song"].
        """
        self._tags_by_source[source] = source_tags

    def tags_from(self, source: Source) -> Tags:
        """Get all tags of a source, e.g. the tags parsed from the YouTube description.

        The tags are the ones stored, not a copy, so changing them
        changes the song's tags. Example: after set_tags(YOUTUBE,
        {"title": ["Song"]}), tags_from(YOUTUBE) gives {"title": ["Song"]}.
        """
        return self._tags_by_source[source]

    def found_values(self, tag_name: str) -> list[tuple[Source, list[str]]]:
        """Get the values that the sources of new values have for a tag.

        Sources without values for the tag are left out. For example,
        if only the YouTube description and MusicBrainz have an artist,
        found_values("artist") gives [(YOUTUBE, ["Queen"]), (MUSICBRAINZ,
        ["Queen"])].
        """
        values_per_source = []
        for source, source_tags in self._tags_by_source.items():
            values = source_tags.get(tag_name)
            if source != ORIGINAL and values:
                values_per_source.append((source, values))
        return values_per_source

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
        for tag_name, print_name in self.tags_printed_for_every_song.items():
            self.print_metadata_key(print_name, tag_name, style, metadata)
        print("")

    def get_colored_values_from_all_sources(self, tag_name: str) -> list[str]:
        """Get the values of a tag from all sources, each in its source's style.

        The sources come in order of preference, with the song's file
        last. Sources with the same values as the file are left out.
        E.g. with the artist "A" in the file and "B" in the YouTube
        description, it's ["B", "A"], with "B" in the YouTube style. If
        no source has the tag, the list is empty.
        """
        colored_values: list[str] = []
        original_values = self.values_from(ORIGINAL, tag_name)
        for source, values in self.found_values(tag_name):
            if values != original_values:
                colored_values.append(source.style(" | ".join(values)))
        if original_values:
            colored_values.append(ORIGINAL.style(" | ".join(original_values)))
        return colored_values

    def print_all(self) -> None:
        """Print all tags from all sources.

        Print a block of text with all data from all sources for a given
        tag name, differentiated by color.
        """
        performer_block = []
        there_are_tags = False
        for tag_name in self.performer_tags_in_print_order(*self._tags_by_source.values()):
            colored_values = self.get_colored_values_from_all_sources(tag_name)
            if len(colored_values) > 0:
                there_are_tags = True
                performer_block.append(self.performer_print_name(tag_name) + ": " + " | ".join(colored_values))

        main_block = []
        for tag_name, print_name in self.tags_printed_for_every_song.items():
            colored_values = self.get_colored_values_from_all_sources(tag_name)
            if len(colored_values) > 0:
                there_are_tags = True
                main_block.append(print_name + ": " + " | ".join(colored_values))
            else:
                main_block.append(print_name + ": " + styles.unset("Not set"))

        if there_are_tags:
            if len(performer_block) > 0:
                print("Performers:")
                print("\n".join(performer_block))
            print("\n".join(main_block) + "\n")
        else:
            messages.error("There's no data to be printed")

    def print_youtube(self) -> None:
        """Print all tags parsed from youtube description."""
        if self.tags_from(YOUTUBE):
            self.print_metadata(self.tags_from(YOUTUBE), styles.youtube)
        else:
            messages.error("No new data parsed from description")

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
                    self.print_metadata_key(f"- {tag_name}", tag_name, styles.removed, self.tags_from(ORIGINAL))
                elif resolved_values != self.values_from(ORIGINAL, tag_name):
                    self.print_metadata_key(f"- {tag_name}", tag_name, styles.changed, self.resolved)
                elif len(joined_resolved_values) > 200:
                    print(f"  - {tag_name}: " + styles.original(f"[{joined_resolved_values[:65]}...]"))
                else:
                    self.print_metadata_key(f"- {tag_name}", tag_name, styles.original, self.resolved)

        # Only performers with something to show are printed: the resolved
        # ones, which include the file's tags and removed tags, and when
        # printing all, the ones in the other sources too
        if print_all:
            performer_tags = self.performer_tags_in_print_order(self.resolved, *self._tags_by_source.values())
        else:
            performer_tags = self.performer_tags_in_print_order(self.resolved)
        if performer_tags:
            print("  Performers:")
            for tag_name in performer_tags:
                self.print_resolved_tag(self.performer_print_name(tag_name), tag_name, print_all)
        for tag_name, print_name in self.tags_printed_for_every_song.items():
            self.print_resolved_tag(print_name, tag_name, print_all)

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
            self.print_metadata_key(printed_tag_name, tag_name, styles.removed, self.tags_from(ORIGINAL))
        # If the resolved tag differs from the original tag
        elif resolved_values is not None and resolved_values != self.values_from(ORIGINAL, tag_name):
            self.print_metadata_key(printed_tag_name, tag_name, styles.changed, self.resolved)
        # original and resolved are equal, but other tags exist
        elif len(colored_values) > 0 and print_all:
            print("  " + printed_tag_name + ": " + " | ".join(colored_values))
        else:
            self.print_metadata_key(printed_tag_name, tag_name, styles.original, self.resolved)

    def discard_upload_date(self) -> None:
        """If the date is just the upload date, discard it."""
        original_date = self.values_from(ORIGINAL, "date")
        if original_date and re.match(r"\d\d\d\d\d\d\d\d", original_date[0]):
            del self.tags_from(ORIGINAL)["date"]

    def prune_resolved_tags(self, tags_to_delete: list[str], strings_to_delete_tags_based_on: list[str]) -> None:
        """Remove tags that the user wants removed by default."""
        original_tags = self.tags_from(ORIGINAL)
        for tag in tags_to_delete:
            if tag in original_tags:
                self.resolved[tag] = REMOVED_TAG

        for tag_name, original_values in original_tags.items():
            for removal_pattern in strings_to_delete_tags_based_on:
                if any(re.fullmatch(removal_pattern, value) for value in original_values):
                    self.resolved[tag_name] = REMOVED_TAG

    def add_source_tag(self) -> None:
        """Add a comment tag with the value 'youtube-dl'."""
        original_comment = self.values_from(ORIGINAL, "comment")
        source_urls = self.values_from(ORIGINAL, "purl")
        is_from_youtube = any("youtube" in url for url in source_urls)
        if is_from_youtube and "youtube-dl" not in original_comment:
            self.resolved["comment"] = original_comment + ["youtube-dl"]

    def get_values_from_all_sources(self, tag_name: str, only_new: bool = False) -> list[str]:
        """Get the values of a tag from all sources.

        :param tag_name: Tag to get values for.
        :param only_new: Whether to leave out the values in the original
            music file.
        """
        values: list[str] = []
        for _, source_values in self.found_values(tag_name):
            values += source_values
        if not only_new:
            values += self.values_from(ORIGINAL, tag_name)
        return utils.remove_duplicates(values)

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
            original_values = set(self.values_from(ORIGINAL, tag))
            if not original_values.issuperset(values_from_all_sources):
                # If there are no new tags, the set of all tags should
                # not contain anything that is not already in the
                # original tags.
                return True

        for tag, resolved_values in self.resolved.items():
            original_values = set(self.values_from(ORIGINAL, tag))
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
        for source, source_tags in self._tags_by_source.items():
            if source != ORIGINAL:
                tag_names.extend(source_tags.keys())
        return utils.remove_duplicates(tag_names)

    def changed_tags(self) -> list[str]:
        """Get the names of the tags that would be changed in the file."""
        changed_tag_names = []
        for tag_name, value in self.resolved.items():
            original_values = self.values_from(ORIGINAL, tag_name)
            if not original_values:
                # A tag that's removed but not in the file isn't a change
                original_values = REMOVED_TAG
            if value != original_values:
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
            if utils.is_equal_when_stripped(resolved_values, self.values_from(ORIGINAL, tag_name)):
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

    def differs_from_musicbrainz_album(self) -> bool:
        """Check whether another source has an album other than the one found on MusicBrainz."""
        musicbrainz_album = self.values_from(MUSICBRAINZ, "album")
        if len(musicbrainz_album) == 0:
            return False
        for source in self._tags_by_source:
            album = self.values_from(source, "album")
            if source != MUSICBRAINZ and len(album) > 0 and not self.is_same_album(album, musicbrainz_album):
                return True
        return False

    def album_is_musicbrainz_release(self) -> bool:
        """Check whether the album is the release found on MusicBrainz."""
        return self.is_same_album(self.resolved.get("album", []), self.values_from(MUSICBRAINZ, "album"))

    def determine_album_artist(self) -> None:
        """Choose value to use for albumartist tag."""
        album_artist_candidates = utils.remove_duplicates(
            self.get_values_from_all_sources("albumartist", only_new=True) + self.get_values_from_all_sources("artist")
        )
        resolved_artist = self.resolved.get("artist")
        original_artist = self.values_from(ORIGINAL, "artist")

        if len(album_artist_candidates) > 1:
            print("-----------------------------------------------")
            self.print_resolved(print_all=True)
            messages.info("Select the album artist:")
            selected_album_artist = utils.select_single_value(album_artist_candidates)
            if len(selected_album_artist) > 0:
                self.resolved["albumartist"] = selected_album_artist
        elif not self.values_from(ORIGINAL, "albumartist"):
            if resolved_artist:
                self.resolved["albumartist"] = resolved_artist
            elif original_artist:
                self.resolved["albumartist"] = original_artist

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
            original_values = self.values_from(ORIGINAL, tag_name)
            found_values = self.found_values(tag_name)
            musicbrainz_values = self.values_from(MUSICBRAINZ, tag_name)

            # MusicBrainz may have found the song on another release than
            # the album that the other sources say, e.g. on an album rather
            # than a single, and then the user chooses which is right
            album_differs_from_musicbrainz = tag_name == "album" and self.differs_from_musicbrainz_album()
            # The existing value can be kept if a source agrees with it
            agreeing_source = None
            if original_values and not album_differs_from_musicbrainz:
                for source, values in found_values:
                    if source.is_equal(values, original_values):
                        agreeing_source = source
                        break

            if tag_name.startswith(constants.MUSICBRAINZ_ID_PREFIX) and len(musicbrainz_values) > 0:
                self.resolved[tag_name] = musicbrainz_values
            elif not original_values and found_values and not album_differs_from_musicbrainz:
                preferred_source, preferred_values = found_values[0]
                self.resolved[tag_name] = preferred_values
                if tag_name not in constants.track_position_tags:
                    messages.warning(
                        f"{tag_name.title()}: No value exists in metadata. "
                        f"Using {preferred_source.name}: {preferred_values}."
                    )
            elif agreeing_source is not None:
                messages.success(f"{tag_name.title()}: Metadata matches {agreeing_source.name}.")
                self.resolved[tag_name] = [value.strip() for value in original_values]
            else:
                self.ask_for_value(tag_name)

        self.keep_pruned_tags_removed(pruned_tags)
        if "albumartist" not in self.album_level_tags:
            self.determine_album_artist()
            self.keep_pruned_tags_removed(pruned_tags)

    def ask_for_value(self, tag_name: str) -> None:
        """Let the user choose the value of a tag that the sources disagree on.

        Each source with values for the tag is a choice, followed by
        the values the song's file has, even if it has none. The menu
        starts on the first one that MusicBrainz agrees with, so that
        e.g. the YouTube description is suggested if its title is the
        one on MusicBrainz, apart from typography.

        :param tag_name: The tag to choose the value of.

        :raises UserExitException: Raised when the user chooses to quit
            the app.
        """
        print("-----------------------------------------------")
        self.print_resolved(print_all=True)
        candidates = self.found_values(tag_name)
        candidates.append((ORIGINAL, self.values_from(ORIGINAL, tag_name)))

        musicbrainz_values = self.values_from(MUSICBRAINZ, tag_name)
        cursor = 0
        if musicbrainz_values:
            for index, (_, values) in enumerate(candidates):
                if utils.is_equal_when_normalized(values, musicbrainz_values):
                    cursor = index
                    break

        menu_entries = []
        for source, _ in candidates:
            menu_entries.append(source.capitalized_name())
        other_action_index = len(menu_entries)
        menu_entries += ["Other action", "Quit"]

        redo = True
        while redo:
            messages.conflict(f"{tag_name.title()}: Mismatch between values in description and metadata:")
            for source, values in candidates:
                print(f"{source.capitalized_name()}: " + source.style(" | ".join(values)))

            choice = TerminalMenu(menu_entries, cursor_index=cursor).show()
            if not isinstance(choice, int) or choice > other_action_index:
                raise UserExitException("Skipping this and all later songs")
            if choice == other_action_index:
                redo = self.manually_adjust_tag_when_resolving(tag_name)
            else:
                _, chosen_values = candidates[choice]
                self.resolved[tag_name] = chosen_values
                redo = False
