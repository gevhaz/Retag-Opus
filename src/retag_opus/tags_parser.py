"""Module for parsing text in the existing metadata keys.

This module is for parsing text in the existing metadata keys, rather
that the YouTube description.
"""

from retag_opus import titles, utils

Tags = dict[str, list[str]]


def alternatives(tags: Tags) -> Tags:
    """Find other values for tags in the tags themselves.

    The values are offered as a choice next to the given ones. For
    example, the artist "Singer & Rapper" gives the artists "Singer"
    and "Rapper", and the title "Song (Live)" gives the title "Song"
    and the version "Live". See split_artists_and_genres() and
    parse_titles() for what is found.

    :param tags: The tags to look in, e.g. the ones in a song's file.

    :return: Only the tags whose values differ from the given ones.
    """
    # Parse the title with the split values, so that e.g. a featured
    # artist is added to them instead of replaced by them
    split_tags = split_artists_and_genres(tags)
    tags_from_titles = parse_titles(tags | split_tags)
    return split_tags | tags_from_titles


def parse_titles(tags: Tags) -> Tags:
    """Parse the titles in tags for metadata that belongs in other tags.

    For example, the title "Song (Live) (feat. Singer)" gives the title
    "Song", the version "Live" and the artist "Singer", and the title
    "Song [Instrumental]" gives the genre "Instrumental".
    A video title like "Artist - Song" is split into the artist and the
    title when one side is the existing artist.

    :param tags: The tags to parse, e.g. the ones in a song's file.

    :return: Only the tags whose values differ from the given ones.
    """
    parsed_tags: Tags = {}
    original_titles = tags.get("title", [])

    original_artists = tags.get("artist", [])
    if len(original_artists) == 1:
        original_artists = utils.split_tag(original_artists[0])
    featured_artists = []

    original_versions = tags.get("version", [])
    versions_from_titles = []

    original_genres = tags.get("genre", [])
    genres_from_titles = []

    for title in original_titles:
        featured_artists += titles.featured_artists(title)
        versions_from_titles += titles.versions(title)
        if titles.is_instrumental(title):
            genres_from_titles.append("Instrumental")

    if set(versions_from_titles) != set(original_versions) and len(versions_from_titles) > 0:
        parsed_tags["version"] = utils.remove_duplicates(original_versions + versions_from_titles)

    if set(genres_from_titles) != set(original_genres) and len(genres_from_titles) > 0:
        parsed_tags["genre"] = utils.remove_duplicates(original_genres + genres_from_titles)

    artists_of_song = original_artists
    if len(original_titles) > 0:
        pruned_title = titles.prune_title(original_titles[0])
        artist_and_title = titles.split_artist_from_title(pruned_title, original_artists)
        if artist_and_title is not None:
            # The artist as named in the title replaces the YouTube
            # channel, e.g. "Ellen Allien" for "Ellen Allien UFO"
            named_artist, artist_from_title, pruned_title = artist_and_title
            artists_of_song = []
            for artist in original_artists:
                artists_of_song.append(artist_from_title if artist == named_artist else artist)
        if original_titles[0] != pruned_title:
            parsed_tags["title"] = [pruned_title]

    artist_differs_in_title = artists_of_song != original_artists
    has_new_featured_artists = set(featured_artists) != set(original_artists) and len(featured_artists) > 0
    if artist_differs_in_title or has_new_featured_artists:
        parsed_tags["artist"] = utils.remove_duplicates(artists_of_song + featured_artists)
    return parsed_tags


def split_artists_and_genres(tags: Tags) -> Tags:
    """Split a single artist or genre on predefined separators.

    For example, the artist "Singer, Guitarist" becomes "Singer" and
    "Guitarist". Tags that already have several values, or that have
    nothing to split, are left out.

    :param tags: The tags to split values of.

    :return: The artist and genre tags that were split.
    """
    split_tags: Tags = {}
    tags_to_split = ["genre", "artist"]

    for tag in tags_to_split:
        original_values = tags.get(tag)
        if original_values is not None and len(original_values) == 1:
            split_tag_values = utils.split_tag(original_values[0])
            if split_tag_values != original_values:
                split_tags[tag] = split_tag_values
    return split_tags
