"""Module for editing a song's tags in the terminal.

The functions here print the tags of a TagTable, let the user choose
among the values that the sources found, and let them edit the tags to
save by hand. The choices end up in TagTable.resolved.
"""

from simple_term_menu import TerminalMenu

from retag_opus import constants, messages, styles
from retag_opus.exceptions import UserExitException
from retag_opus.tag_table import MUSICBRAINZ, ORIGINAL, REMOVED_TAG, YOUTUBE, TagTable, capitalize_first_letter
from retag_opus.tags import Tags, is_performer_tag, split_manual_value


def tags_of_all_sources(tag_table: TagTable) -> list[Tags]:
    """Get the tags of every source, the song's file included."""
    all_sources = tag_table.sources_in_order_of_preference() + [ORIGINAL]
    return [tag_table.tags_from(source) for source in all_sources]


def performer_tags_in_print_order(*sources: Tags) -> list[str]:
    """Get the sources' performer tags, in the order to print them.

    First come the common performer tags, in the order of
    constants.common_performer_tags. Then come the others, e.g.
    "performer:theremin" from MusicBrainz, in alphabetical order.
    """
    performer_tags_in_sources = []
    for source in sources:
        for tag_name in source.keys():
            if is_performer_tag(tag_name) and tag_name not in performer_tags_in_sources:
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


def performer_print_name(tag_name: str) -> str:
    """Get the name to print before the values of a performer tag.

    Performers are printed as a list, e.g.:

      Performers:
      - Lead vocals: Freddie Mercury
      - Timpani: Roger Taylor

    so performer_print_name("performer:timpani") gives "- Timpani".
    """
    role = tag_name.removeprefix(constants.PERFORMER_PREFIX)
    return "- " + capitalize_first_letter(role)


def print_tag(
    tag_table: TagTable,
    printed_tag_name: str,
    tag_name: str,
    style: styles.Style,
    tags_to_print: Tags,
) -> None:
    """Print the values that tags_to_print has for a tag, in a style.

    The line is e.g. "  Title: Song". A tag without values is printed
    as "Not found", and "(Removed)" is added after the name of a tag
    that the song's resolved tags remove.
    """
    joined_values = constants.VALUE_SEPARATOR.join(tags_to_print.get(tag_name, ["Not found"]))
    value = joined_values.replace(" ", constants.PRINTED_SPACE)
    if tag_table.resolved.get(tag_name) == REMOVED_TAG:
        printed_tag_name = f"{printed_tag_name} (Removed)"
    style = style if tags_to_print.get(tag_name) else styles.unset
    print("  " + printed_tag_name + ": " + style(value))


def print_tags(tag_table: TagTable, tags_to_print: Tags, style: styles.Style) -> None:
    """Print the performers and the common tags of tags_to_print."""
    if any(is_performer_tag(tag_name) for tag_name in tags_to_print.keys()):
        print("  Performers:")
        for tag_name in performer_tags_in_print_order(tags_to_print):
            if tag_name in tags_to_print and tags_to_print[tag_name] is not None:
                print_tag(tag_table, performer_print_name(tag_name), tag_name, style, tags_to_print)
    for tag_name, print_name in constants.tags_printed_for_every_song.items():
        print_tag(tag_table, print_name, tag_name, style, tags_to_print)
    print("")


def styled_values_from_all_sources(tag_table: TagTable, tag_name: str) -> list[str]:
    """Get a tag's values in all sources, styled by source.

    The sources come in order of preference, with the song's file
    last. Sources with the same values as the file are left out.
    E.g. with the artist "A" in the file and "B" in the YouTube
    description, it's ["B", "A"], with "B" in the YouTube style. If
    no source has the tag, the list is empty.
    """
    styled_values: list[str] = []
    original_values = tag_table.values_from(ORIGINAL, tag_name)
    for source, values in tag_table.found_values(tag_name):
        if values != original_values:
            styled_values.append(source.style(constants.VALUE_SEPARATOR.join(values)))
    if original_values:
        styled_values.append(ORIGINAL.style(constants.VALUE_SEPARATOR.join(original_values)))
    return styled_values


def print_all_sources(tag_table: TagTable) -> None:
    """Print every tag's values in all sources, colored by source."""
    performer_block = []
    there_are_tags = False
    for tag_name in performer_tags_in_print_order(*tags_of_all_sources(tag_table)):
        styled_values = styled_values_from_all_sources(tag_table, tag_name)
        if len(styled_values) > 0:
            there_are_tags = True
            performer_block.append(performer_print_name(tag_name) + ": " + " | ".join(styled_values))

    main_block = []
    for tag_name, print_name in constants.tags_printed_for_every_song.items():
        styled_values = styled_values_from_all_sources(tag_table, tag_name)
        if len(styled_values) > 0:
            there_are_tags = True
            main_block.append(print_name + ": " + " | ".join(styled_values))
        else:
            main_block.append(print_name + ": " + styles.unset("Not set"))

    if there_are_tags:
        if len(performer_block) > 0:
            print("Performers:")
            print("\n".join(performer_block))
        print("\n".join(main_block) + "\n")
    else:
        messages.error("There's no data to be printed")


def print_youtube_tags(tag_table: TagTable) -> None:
    """Print the tags parsed from the YouTube description."""
    if tag_table.tags_from(YOUTUBE):
        print_tags(tag_table, tag_table.tags_from(YOUTUBE), styles.youtube)
    else:
        messages.error("No new data parsed from description")


def print_resolved_tags(tag_table: TagTable, with_all_sources: bool = False) -> None:
    """Print the tags that will be saved to the song's file.

    Tags without a line of their own are listed first as other tags,
    leaving out MusicBrainz IDs. with_all_sources also shows the values
    of all sources for tags that keep the value they have now, see
    print_resolved_tag().
    """
    other_tag_names: list[str] = []
    for tag_name in tag_table.resolved.keys():
        if tag_name.startswith(constants.MUSICBRAINZ_ID_PREFIX):
            continue
        if tag_name not in constants.tags_printed_for_every_song and not is_performer_tag(tag_name):
            other_tag_names.append(tag_name)
    if other_tag_names:
        print("  Other tags:")
        for tag_name in other_tag_names:
            resolved_values = tag_table.resolved.get(tag_name, [])
            joined_resolved_values = constants.VALUE_SEPARATOR.join(resolved_values).replace("\n", " ")
            if resolved_values == REMOVED_TAG:
                print_tag(tag_table, f"- {tag_name}", tag_name, styles.removed, tag_table.tags_from(ORIGINAL))
            elif resolved_values != tag_table.values_from(ORIGINAL, tag_name):
                print_tag(tag_table, f"- {tag_name}", tag_name, styles.changed, tag_table.resolved)
            elif len(joined_resolved_values) > 200:
                print(f"  - {tag_name}: " + styles.original(f"[{joined_resolved_values[:65]}...]"))
            else:
                print_tag(tag_table, f"- {tag_name}", tag_name, styles.original, tag_table.resolved)

    # Only performers with something to show are printed: the resolved
    # ones, which include the file's tags and removed tags, and when
    # printing all, the ones in the other sources too
    if with_all_sources:
        performer_tags = performer_tags_in_print_order(tag_table.resolved, *tags_of_all_sources(tag_table))
    else:
        performer_tags = performer_tags_in_print_order(tag_table.resolved)
    if performer_tags:
        print("  Performers:")
        for tag_name in performer_tags:
            print_resolved_tag(tag_table, performer_print_name(tag_name), tag_name, with_all_sources)
    for tag_name, print_name in constants.tags_printed_for_every_song.items():
        print_resolved_tag(tag_table, print_name, tag_name, with_all_sources)

    print("")


def print_resolved_tag(tag_table: TagTable, printed_tag_name: str, tag_name: str, with_all_sources: bool) -> None:
    """Print the line showing what will be saved in a tag.

    The resolved tags are the tags that will be saved to the song's
    file. The line shows the tag's resolved value, colored by how it
    compares to the value the file has now:

    - Red (styles.removed), with "(Removed)" after the name: the tag
      will be removed from the file. The value shown is the one the
      file has now.
    - Green (styles.changed): the tag will get the value shown.
    - Cyan (styles.original): the tag keeps the value it has now.
      If with_all_sources is set, the values found in all sources are
      shown instead, each in the color of its source, so that they can
      be compared before choosing a value.
    - Gray (styles.unset) "Not found": the tag has no value and
      won't get one.

    For example, if the title "Song (Live)" will be changed to
    "Song", the line is "  Title: Song" in green. printed_tag_name is
    what the tag is called in the line, e.g. "Title" for "title".
    """
    resolved_values = tag_table.resolved.get(tag_name)
    styled_values = styled_values_from_all_sources(tag_table, tag_name)
    # If the user chose to remove a tag that existed before
    if resolved_values == REMOVED_TAG:
        print_tag(tag_table, printed_tag_name, tag_name, styles.removed, tag_table.tags_from(ORIGINAL))
    # If the resolved tag differs from the original tag
    elif resolved_values is not None and resolved_values != tag_table.values_from(ORIGINAL, tag_name):
        print_tag(tag_table, printed_tag_name, tag_name, styles.changed, tag_table.resolved)
    # original and resolved are equal, but other tags exist
    elif len(styled_values) > 0 and with_all_sources:
        print("  " + printed_tag_name + ": " + " | ".join(styled_values))
    else:
        print_tag(tag_table, printed_tag_name, tag_name, styles.original, tag_table.resolved)


def enter_tags_by_hand(tag_table: TagTable) -> None:
    """Let the user type tags and values to save, until one is empty."""
    tag_name = " "
    value = " "
    while tag_name and value:
        print("Enter key and value (newline cancels, sequence ' | ' splits tag, and for genre also ',' and ';'):")
        tag_name = input("  Key: ")
        value = input("  Value: ")
        if tag_name and value:
            tag_table.resolved[tag_name] = split_manual_value(tag_name, value)


def remove_values_from_tag(tag_table: TagTable) -> None:
    """Let the user remove values from one of the tags to save.

    The user chooses a tag, then which of its values to remove. A tag
    whose values are all removed is removed from the file.
    """
    tags_in_resolved = []
    for tag_name, tag_values in tag_table.resolved.items():
        is_known_tag = tag_name in constants.tags_printed_for_every_song or is_performer_tag(tag_name)
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
        values_in_tag = tag_table.resolved.get(selected_tag, []).copy()
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
            tag_table.resolved[selected_tag].remove(values_in_tag[index_to_remove])
            if len(tag_table.resolved[selected_tag]) == 0:
                tag_table.resolved[selected_tag] = REMOVED_TAG


def ask_for_other_action(tag_table: TagTable, tag_name: str) -> bool:
    """Let the user set a tag by hand when no source is right.

    The user can select values among the ones all sources found, type
    the value, or remove the tag. Returns whether to show the menu of
    sources again, which is the case when the user goes back, prints
    the description's tags, or enters nothing.
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
                tag_table.resolved[tag_name] = split_manual_value(tag_name, entered_value)
            else:
                print("No input, not changing tag")
                return True
            return False
        case "[p] Print description metadata":
            print("-----------------------------------------------")
            print_youtube_tags(tag_table)
            return True
        case "[s] Select items from a list":
            values_from_all_sources = tag_table.get_values_from_all_sources(tag_name)
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

            tag_table.resolved[tag_name] = []
            for selected_index in selected_indices:
                tag_table.resolved[tag_name].append(values_from_all_sources[selected_index])

            return False
        case "[r] Remove field":
            tag_table.resolved[tag_name] = REMOVED_TAG
            return False
        case _:
            print("Going back to previous menu")
            return True


def resolve_tags(tag_table: TagTable) -> None:
    """Choose the values to save for the tags that sources found.

    A tag gets the sources' value without asking when the file has
    none and the sources agree, and keeps the file's value when a
    source agrees with it. MusicBrainz IDs are taken from MusicBrainz.
    For the other tags, the user is asked.

    :raises UserExitException: Raised when the user chooses to quit
        the app.
    """
    pruned_tags = [tag_name for tag_name, value in tag_table.resolved.items() if value == REMOVED_TAG]

    for tag_name, album_level_value in tag_table.album_level_tags.items():
        messages.success(f"{tag_name.title()}: Using value from earlier song on the same album: {album_level_value}.")

    for tag_name in tag_table.tags_with_new_data():
        if not tag_table.should_resolve(tag_name):
            continue
        original_values = tag_table.values_from(ORIGINAL, tag_name)
        found_values = tag_table.found_values(tag_name)
        musicbrainz_values = tag_table.values_from(MUSICBRAINZ, tag_name)
        agreeing_source = tag_table.agreeing_source(tag_name)

        if tag_name.startswith(constants.MUSICBRAINZ_ID_PREFIX) and len(musicbrainz_values) > 0:
            tag_table.resolved[tag_name] = musicbrainz_values
        elif not original_values and found_values and tag_table.sources_agree(tag_name):
            preferred_source, preferred_values = found_values[0]
            tag_table.resolved[tag_name] = preferred_values
            if tag_name not in constants.track_position_tags:
                messages.warning(
                    f"{tag_name.title()}: No value exists in metadata. "
                    f"Using {tag_table.name_of(preferred_source)}: {preferred_values}."
                )
        elif agreeing_source is not None:
            messages.success(f"{tag_name.title()}: Metadata matches {tag_table.name_of(agreeing_source)}.")
            tag_table.resolved[tag_name] = [value.strip() for value in original_values]
        else:
            ask_for_value(tag_table, tag_name)

    tag_table.keep_pruned_tags_removed(pruned_tags)


def ask_for_value(tag_table: TagTable, tag_name: str) -> None:
    """Let the user choose a tag's value when the sources disagree.

    Each source with values for the tag is a choice, followed by
    the values the song's file has, even if it has none. The menu
    starts on the first choice, which is the most preferred source,
    e.g. the YouTube description if it has values for the tag.

    :raises UserExitException: Raised when the user chooses to quit
        the app.
    """
    print("-----------------------------------------------")
    print_resolved_tags(tag_table, with_all_sources=True)
    candidates = tag_table.found_values(tag_name)
    candidates.append((ORIGINAL, tag_table.values_from(ORIGINAL, tag_name)))

    menu_entries = []
    for source, _ in candidates:
        menu_entries.append(capitalize_first_letter(tag_table.name_of(source)))
    other_action_index = len(menu_entries)
    menu_entries += ["Other action", "Quit"]

    redo = True
    while redo:
        messages.conflict(f"{tag_name.title()}: Mismatch between values in description and metadata:")
        for source, values in candidates:
            shown_name = capitalize_first_letter(tag_table.name_of(source))
            print(f"{shown_name}: " + source.style(constants.VALUE_SEPARATOR.join(values)))

        choice = TerminalMenu(menu_entries).show()
        if not isinstance(choice, int) or choice > other_action_index:
            raise UserExitException("Skipping this and all later songs")
        if choice == other_action_index:
            redo = ask_for_other_action(tag_table, tag_name)
        else:
            _, chosen_values = candidates[choice]
            tag_table.resolved[tag_name] = chosen_values
            redo = False
