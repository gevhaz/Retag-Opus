"""Tests for app.py and cli.py."""
import re
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from colorama import Fore
from mutagen import oggopus

from retag_opus import app, utils

metadata = [
        ("title", ["Proper Goodbyes (feat. Benny Ivor) (2039 Remaster)"]),
        ("artist", ["artist 1 and artist 2"]),
        (
            "synopsis",
            [
                "Provided to YouTube by Rich Men's Group Digital Ltd."
                "\n\nProper Goodbyes (feat. Ben Ivor) (2036 Remaster) · The Global · Ben Ivor"
                "\n\nProper Goodbyes (feat. Ben Ivor)"
                "\n\n℗ 2022 The Global under exclusive license to 5BE Ltd"
                "\n\nReleased on: 2029-08-22"
            ],
        ),
    ]


def test_print_version(capsys):
    """Test printing version."""
    with pytest.raises(SystemExit):
        app.run(["--version"])
    out, _ = capsys.readouterr()
    assert re.match(r"^retag \(version 0.3.0\)$", out)


def test_print_help(capsys):
    """Test printing help."""
    with pytest.raises(SystemExit):
        app.run(["--help"])
    out, _ = capsys.readouterr()
    assert re.match(r"^usage:.*", out)


def test_print_completion_script(capsys):
    """Test printing completion scripts."""
    with pytest.raises(SystemExit):
        app.run(["--print-completion", "bash"])
    out, _ = capsys.readouterr()
    assert re.match(r"^# AUTOMATICALLY GENERATED by `shtab`", out)


def test_no_songs_in_directory(capsys):
    """Test logging warning when no opus files in provided dir."""
    with TemporaryDirectory() as temp_dir:
        exit_code = app.run(["--directory", temp_dir])
    out, _ = capsys.readouterr()
    assert exit_code == 0
    assert re.match(r"^\x1b\[33mThere appears to be no .opus files in the provided directory /tmp.*", out)


def test_directory_not_found(capsys):
    """Providing non-existent directory."""
    exit_code = app.run(["--directory", "/this/does/not/exist/"])
    out, _ = capsys.readouterr()
    assert exit_code == 1
    assert re.match(r"^\x1b\[31m/this/does/not/exist/ is not a directory!\n", out)


@pytest.fixture
def music_directory():
    """Yield path to temporary directory with fake opus file."""
    with TemporaryDirectory() as temp_dir:
        opus_file = Path(temp_dir) / "test.opus"
        opus_file.touch()
        yield temp_dir


def test_file_without_metadata(capsys, music_directory, monkeypatch):
    """If a file without metadata is found, say that and exit."""

    monkeypatch.setattr(oggopus.OggOpus, "__init__", lambda *_: None)
    monkeypatch.setattr(oggopus.OggOpus, "items", lambda *_: {})

    exit_code = app.run(["--directory", music_directory])

    actual_output, _ = capsys.readouterr()
    expected_output = (
        "\n"
        f"{Fore.BLUE}Song 1 of 1{Fore.RESET}\n"
        f"{Fore.BLUE}----- Song: test -----{Fore.RESET}\n"
        f"{Fore.YELLOW}No new data exists. Skipping song.{Fore.RESET}\n"
    )

    assert exit_code == 0
    assert actual_output == expected_output


def test_file_with_no_new_metadata(capsys, music_directory, monkeypatch):
    """File with no description should be skipped."""

    monkeypatch.setattr(oggopus.OggOpus, "__init__", lambda *_: None)
    monkeypatch.setattr(oggopus.OggOpus, "items", lambda *_: [("artist", ["artist 1"])])

    exit_code = app.run(["--directory", music_directory])

    actual_output, _ = capsys.readouterr()
    expected_output = (
        "\n"
        f"{Fore.BLUE}Song 1 of 1{Fore.RESET}\n"
        f"{Fore.BLUE}----- Song: test -----{Fore.RESET}\n"
        f"{Fore.YELLOW}No new data exists. Skipping song.{Fore.RESET}\n"
    )

    assert exit_code == 0
    assert actual_output == expected_output


def test_file_with_new_metadata(capsys, music_directory, monkeypatch):
    """File with description and original data should handle conflict.

    A file that has the artist tag set in the original metadata, but
    also contains information about the artist in the YouTube
    description, should ask the user how to resolve the conflicting
    artist names.

    Other basic fields from the YouTube Description should just be
    taken as they are when there is no conflict, without user
    interaction.
    """

    metadata_no_title = [
            (
                "artist",
                ["artist 1"],
            ),
            (
                "synopsis",
                [
                    "Provided to YouTube by Rich Men's Group Digital Ltd."
                    "\n\nProper Goodbyes (feat. Ben Ivor) · The Global · Ben Ivor"
                    "\n\nProper Goodbyes (feat. Ben Ivor)"
                    "\n\n℗ 2022 The Global under exclusive license to 5BE Ltd"
                    "\n\nReleased on: 2029-08-22"
                ],
            ),
        ]

    monkeypatch.setattr(oggopus.OggOpus, "__init__", lambda *_: None)
    monkeypatch.setattr(oggopus.OggOpus, "items", lambda *_: metadata_no_title)
    monkeypatch.setattr(utils.TerminalMenu, "__init__", lambda *_, **__: None)
    monkeypatch.setattr(utils.TerminalMenu, "show", lambda _: (x for x in [0, 1]))

    exit_code = app.run(["--directory", music_directory])

    actual_output, _ = capsys.readouterr()
    expected_output = (
        f"\n{Fore.BLUE}Song 1 of 1{Fore.RESET}"
        f"\n{Fore.BLUE}----- Song: test -----{Fore.RESET}"
        f"\n{Fore.YELLOW}Organization: No value exists in metadata. "
        f'Using parsed data: ["Rich Men\'s Group Digital Ltd."].{Fore.RESET}'
        f"\n-----------------------------------------------"
        f"\n  Title: {Fore.GREEN}Proper Goodbyes{Fore.RESET} | "
        f"{Fore.MAGENTA}Proper Goodbyes (feat. Ben Ivor){Fore.RESET}"
        f"\n  Album: {Fore.MAGENTA}Proper Goodbyes (feat. Ben Ivor){Fore.RESET}"
        f"\n  Album Artist: {Fore.MAGENTA}The Global{Fore.RESET}"
        "\n  Artist(s): "
        f"{Fore.GREEN}The Global | Ben Ivor{Fore.RESET}"
        f" | {Fore.CYAN}artist 1{Fore.RESET}"
        f" | {Fore.MAGENTA}The Global | Ben Ivor{Fore.RESET}"
        f"\n  Date: {Fore.MAGENTA}2029-08-22{Fore.RESET}"
        f"\n  Genre: {Fore.BLACK}Not found{Fore.RESET}"
        f"\n  Version: {Fore.BLACK}Not found{Fore.RESET}"
        f"\n  Performer: {Fore.BLACK}Not found{Fore.RESET}"
        f"\n  Organization: {Fore.GREEN}Rich Men's Group Digital Ltd.{Fore.RESET}"
        f"\n  Copyright: {Fore.MAGENTA}2022 The Global under exclusive license to 5BE Ltd{Fore.RESET}"
        f"\n  Composer: {Fore.BLACK}Not found{Fore.RESET}"
        f"\n  Conductor: {Fore.BLACK}Not found{Fore.RESET}"
        f"\n  Arranger: {Fore.BLACK}Not found{Fore.RESET}"
        f"\n  Author: {Fore.BLACK}Not found{Fore.RESET}"
        f"\n  Producer: {Fore.BLACK}Not found{Fore.RESET}"
        f"\n  Publisher: {Fore.BLACK}Not found{Fore.RESET}"
        f"\n  Lyricist: {Fore.BLACK}Not found{Fore.RESET}"
        f"\n\n{Fore.RED}Artist: Mismatch between values in description and metadata:{Fore.RESET}"
        f"\nYouTube description: {Fore.MAGENTA}The Global | Ben Ivor{Fore.RESET}"
        f"\nExisiting metadata:  {Fore.CYAN}artist 1{Fore.RESET}"
        f"\nParsed from YouTube tags: {Fore.GREEN}The Global | Ben Ivor{Fore.RESET}"
        f"\nRetagOpus exited successfully: Skipping this and all later songs\n"
    )

    assert exit_code == 0
    assert actual_output == expected_output


def test_file_with_new_metadata_from_many_sources(capsys, music_directory, monkeypatch):
    """Conflicts between all sources should be handles.

    A file that has the artist tag set in the original metadata, but
    also contains information about the artist in the YouTube
    description, should ask the user how to resolve the conflicting
    artist names. To complicate things, the original data hasn't split
    the artist field properly, so it's one long string with a comma
    instead of a list of strings.

    Other basic fields from the YouTube Description should just be
    taken as they are when there is no conflict, without user
    interaction.
    """

    monkeypatch.setattr(oggopus.OggOpus, "__init__", lambda *_: None)
    monkeypatch.setattr(oggopus.OggOpus, "items", lambda *_: metadata)
    monkeypatch.setattr(utils.TerminalMenu, "__init__", lambda *_, **__: None)
    monkeypatch.setattr(utils.TerminalMenu, "show", lambda _: (x for x in [0, 1]))

    exit_code = app.run(["--directory", music_directory])

    actual_output, _ = capsys.readouterr()
    expected_output = (
        f"\n{Fore.BLUE}Song 1 of 1{Fore.RESET}"
        f"\n{Fore.BLUE}----- Song: test -----{Fore.RESET}"
        f"\n{Fore.YELLOW}Organization: No value exists in metadata. "
        f'Using parsed data: ["Rich Men\'s Group Digital Ltd."].{Fore.RESET}'
        f"\n-----------------------------------------------"
        "\n  Title: "
        f"{Fore.YELLOW}Proper Goodbyes{Fore.RESET}"
        f" | {Fore.GREEN}Proper Goodbyes{Fore.RESET}"
        f" | {Fore.CYAN}Proper Goodbyes (feat. Benny Ivor) (2039 Remaster){Fore.RESET}"
        f" | {Fore.MAGENTA}Proper Goodbyes (feat. Ben Ivor) (2036 Remaster){Fore.RESET}"
        f"\n  Album: {Fore.MAGENTA}Proper Goodbyes (feat. Ben Ivor){Fore.RESET}"
        f"\n  Album Artist: {Fore.MAGENTA}The Global{Fore.RESET}"
        "\n  Artist(s):"
        f" {Fore.YELLOW}artist 1 | artist 2{Fore.RESET}"
        f" | {Fore.GREEN}The Global | Ben Ivor{Fore.RESET}"
        f" | {Fore.CYAN}artist 1 and artist 2{Fore.RESET}"
        f" | {Fore.MAGENTA}The Global | Ben Ivor{Fore.RESET}"
        f"\n  Date: {Fore.MAGENTA}2029-08-22{Fore.RESET}"
        f"\n  Genre: {Fore.BLACK}Not found{Fore.RESET}"
        f"\n  Version: {Fore.YELLOW}2039 Remaster{Fore.RESET} | {Fore.GREEN}2036 Remaster{Fore.RESET}"
        f"\n  Performer: {Fore.BLACK}Not found{Fore.RESET}"
        f"\n  Organization: {Fore.GREEN}Rich Men's Group Digital Ltd.{Fore.RESET}"
        f"\n  Copyright: {Fore.MAGENTA}2022 The Global under exclusive license to 5BE Ltd{Fore.RESET}"
        f"\n  Composer: {Fore.BLACK}Not found{Fore.RESET}"
        f"\n  Conductor: {Fore.BLACK}Not found{Fore.RESET}"
        f"\n  Arranger: {Fore.BLACK}Not found{Fore.RESET}"
        f"\n  Author: {Fore.BLACK}Not found{Fore.RESET}"
        f"\n  Producer: {Fore.BLACK}Not found{Fore.RESET}"
        f"\n  Publisher: {Fore.BLACK}Not found{Fore.RESET}"
        f"\n  Lyricist: {Fore.BLACK}Not found{Fore.RESET}"
        # All sources should show up here
        f"\n\n{Fore.RED}Artist: Mismatch between values in description and metadata:{Fore.RESET}"
        f"\nYouTube description: {Fore.MAGENTA}The Global | Ben Ivor{Fore.RESET}"
        f"\nParsed from original tags: {Fore.YELLOW}artist 1 | artist 2{Fore.RESET}"
        f"\nExisiting metadata:  {Fore.CYAN}artist 1 and artist 2{Fore.RESET}"
        f"\nParsed from YouTube tags: {Fore.GREEN}The Global | Ben Ivor{Fore.RESET}"
        f"\nRetagOpus exited successfully: Skipping this and all later songs\n"
    )

    assert exit_code == 0
    assert actual_output == expected_output


def test_setting_manual_album(capsys, music_directory, monkeypatch):
    """Test setting a manual album and see that it overrides.

    Test that when the user sets a manual album, that s used for the
    album tag and whatever album is found from the tags is set as the
    "discsubtitle" tag instead. Also double check that the album from
    the description is not set as an album tag.
    """

    mock_show = Mock()
    # The last one is for the "Pass" selection. Earlier ones are for
    # selecting tags in the tag selection menu.
    mock_show.side_effect = [0, 1, 0, 0, 0]

    monkeypatch.setattr(oggopus.OggOpus, "__init__", lambda *_: None)
    monkeypatch.setattr(oggopus.OggOpus, "items", lambda *_: metadata)
    monkeypatch.setattr(utils.TerminalMenu, "__init__", lambda *_, **__: None)
    monkeypatch.setattr(utils.TerminalMenu, "show", mock_show)

    exit_code = app.run(["--directory", music_directory, "--album", "manualalbum"])

    actual_output, _ = capsys.readouterr()
    expected_album_output = f"Album: {Fore.GREEN}manualalbum{Fore.RESET}"
    not_expected_album_output = f"Album: {Fore.MAGENTA}Proper Goodbyes (feat. Ben Ivor){Fore.RESET}"
    expected_discsubtitle_output = f"Disc subtitle: {Fore.MAGENTA}Proper Goodbyes (feat. Ben Ivor){Fore.RESET}"

    assert exit_code == 0
    assert expected_album_output in actual_output
    assert not_expected_album_output not in actual_output
    assert expected_discsubtitle_output in actual_output