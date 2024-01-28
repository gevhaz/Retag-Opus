"""Tests for app.py and cli.py."""
import re
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock

import pytest
from colorama import Fore
from mutagen import oggopus
from pydub import AudioSegment

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


@pytest.fixture
def music_directory():
    """Yield path to temporary directory with fake opus file."""
    with TemporaryDirectory() as temp_dir:
        opus_file = Path(temp_dir) / "test.opus"
        opus_file.touch()
        yield temp_dir


def test_print_version(capsys):
    """Test printing version."""
    with pytest.raises(SystemExit):
        app.run(["--version"])
    out, _ = capsys.readouterr()
    assert re.match(r"^retag \(version 0.4.1\)$", out)


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
        "\n  Other tags:"
        f"\n  - synopsis: {Fore.CYAN}[Provided to YouTube by Rich Men's Group Digital Ltd.  Proper Good...]{Fore.RESET}"
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
        "\n  Other tags:"
        f"\n  - synopsis: {Fore.CYAN}[Provided to YouTube by Rich Men's Group Digital Ltd.  Proper Good...]{Fore.RESET}"
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
    mock_show.side_effect = [0, 1, 0, 1, 0]

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


def test_pass(capsys, music_directory, monkeypatch):
    """User selecting "Pass" for a song should undo changes."""
    mock_show = Mock()
    mock_save = Mock()
    # The last one is for the "Pass" selection. Earlier ones are for
    # selecting tags in the tag selection menu.
    mock_show.side_effect = [0, 0, 0, 0, 0]

    monkeypatch.setattr(oggopus.OggOpus, "__init__", lambda *_: None)
    monkeypatch.setattr(oggopus.OggOpus, "items", lambda *_: metadata)
    monkeypatch.setattr(utils.TerminalMenu, "__init__", lambda *_, **__: None)
    monkeypatch.setattr(utils.TerminalMenu, "show", mock_show)
    monkeypatch.setattr(oggopus.OggOpus, "save", mock_save)

    exit_code = app.run(["--directory", music_directory])

    actual_output = capsys.readouterr().out.split("\n")
    expected_last_output_line = f"{Fore.YELLOW}Pass. Skipping song: test"

    assert exit_code == 0
    assert expected_last_output_line == actual_output[-2]
    mock_save.assert_not_called()


def test_quit_through_escape(capsys, music_directory, monkeypatch):
    """Pressing Escape in the selection menu should quit.

    Escape will return 'None' from the selection menu, so we simulate
    pressing escape by adding None as a side effect for the first menu
    after all tags have been selected.
    """
    mock_show = Mock()
    mock_save = Mock()
    # The last one is for the "Pass" selection. Earlier ones are for
    # selecting tags in the tag selection menu.
    mock_show.side_effect = [0, 0, 0, 0, None]

    monkeypatch.setattr(oggopus.OggOpus, "__init__", lambda *_: None)
    monkeypatch.setattr(oggopus.OggOpus, "items", lambda *_: metadata)
    monkeypatch.setattr(utils.TerminalMenu, "__init__", lambda *_, **__: None)
    monkeypatch.setattr(utils.TerminalMenu, "show", mock_show)
    monkeypatch.setattr(oggopus.OggOpus, "save", mock_save)

    exit_code = app.run(["--directory", music_directory])

    actual_output = capsys.readouterr().out.split("\n")
    expected_last_output_line = "RetagOpus exited successfully: Skipping this and all later songs"

    assert exit_code == 0
    assert expected_last_output_line == actual_output[-2]
    mock_save.assert_not_called()


def test_resetting_tags(capsys, music_directory, monkeypatch):
    """User selecting "Reset" for a song should reset tags.

    When the user uses the "Reset" option, tags should be reset to how
    they were from the start and the tag selection process should start
    over.

    In this test, we select some tags so that they are all resolved,
    then check that the get reset before quitting.
    """
    mock_show = Mock()
    mock_save = Mock()
    # The last one is for the "Pass" selection. Earlier ones are for
    # selecting tags in the tag selection menu.
    mock_show.side_effect = [0, 0, 0, 0, 2, None]

    monkeypatch.setattr(oggopus.OggOpus, "__init__", lambda *_: None)
    monkeypatch.setattr(oggopus.OggOpus, "items", lambda *_: metadata)
    monkeypatch.setattr(utils.TerminalMenu, "__init__", lambda *_, **__: None)
    monkeypatch.setattr(utils.TerminalMenu, "show", mock_show)
    monkeypatch.setattr(oggopus.OggOpus, "save", mock_save)

    exit_code = app.run(["--directory", music_directory])

    actual_output = capsys.readouterr().out
    expected_regex = re.compile(
        # Original status print
        re.escape(
            rf"Artist(s): {Fore.YELLOW}artist 1 | artist 2{Fore.RESET} | "
            rf"{Fore.GREEN}The Global | Ben Ivor{Fore.RESET} | "
            rf"{Fore.CYAN}artist 1 and artist 2{Fore.RESET} | "
            rf"{Fore.MAGENTA}The Global | Ben Ivor{Fore.RESET}"
        )
        + r".*"
        # # One of the resolved status prints
        + re.escape(rf"Artist(s): {Fore.GREEN}The Global | Ben Ivor{Fore.RESET}") + ".*"
        # # Reset status print (same as first)
        + re.escape(
            rf"Artist(s): {Fore.YELLOW}artist 1 | artist 2{Fore.RESET} | "
            rf"{Fore.GREEN}The Global | Ben Ivor{Fore.RESET} | "
            rf"{Fore.CYAN}artist 1 and artist 2{Fore.RESET} | "
            rf"{Fore.MAGENTA}The Global | Ben Ivor{Fore.RESET}"
        )
        + ".*",
        re.DOTALL,
    )

    assert exit_code == 0
    assert expected_regex.search(actual_output)
    mock_save.assert_not_called()


def test_saving(music_directory, monkeypatch, capsys):
    """User selecting "Save" for a song should save resolved tags.

    When the user uses the "Save" option, resolved tags should be saved
    to the file being processed.
    """
    # Setup
    original_metadata = {
        "title": ["Proper Goodbyes (feat. Benny Ivor) (2039 Remaster)"],
        "artist": ["artist 1 and artist 2"],
        "purl": ["www.youtube.com"],
        "synopsis": [
            "Provided to YouTube by Rich Men's Group Digital Ltd."
            "\n\nProper Goodbyes (feat. Ben Ivor) (2036 Remaster) · The Global · Ben Ivor"
            "\n\nProper Goodbyes (feat. Ben Ivor)"
            "\n\n℗ 2022 The Global under exclusive license to 5BE Ltd"
            "\n\nReleased on: 2029-08-22"
        ],
    }

    expected_metadata = original_metadata.copy()
    # Manually selected
    expected_metadata["title"] = ["Proper Goodbyes (feat. Ben Ivor) (2036 Remaster)"]  # Chose "youtube"
    expected_metadata["artist"] = ["The Global", "Ben Ivor"]  # Chose "youtube"
    expected_metadata["albumartist"] = ["The Global"]  # Chose the second alternative
    # Automatically resolved
    expected_metadata["comment"] = ["youtube-dl"]
    expected_metadata["date"] = ["2029-08-22"]
    expected_metadata["copyright"] = ["2022 The Global under exclusive license to 5BE Ltd"]
    expected_metadata["version"] = ["2039 Remaster"]
    expected_metadata["album"] = ["Proper Goodbyes (feat. Ben Ivor)"]
    expected_metadata["organization"] = ["Rich Men's Group Digital Ltd."]
    expected_metadata["encoder"] = ["Lavc60.3.100 libopus"]

    mock_show = Mock()
    # First: Choose youtube for 'artist'
    # Second: Choose youtube for 'title'
    # Third: Select album artist "The Global"
    # Fourth: Save file
    mock_show.side_effect = [0, 0, 0, 1, 1]

    monkeypatch.setattr(utils.TerminalMenu, "__init__", lambda *_, **__: None)
    monkeypatch.setattr(utils.TerminalMenu, "show", mock_show)

    # Create an opus file for testing saving
    silence = AudioSegment.silent(duration=1000)
    test_opus_file_path = Path(music_directory) / "test.opus"
    silence.export(test_opus_file_path, format="opus")
    # Tags are not handled well by pydub so we fix it afterward:
    test_opus_file: oggopus.OggOpus = oggopus.OggOpus(test_opus_file_path)
    for tag_name, tag_value in original_metadata.items():
        test_opus_file[tag_name] = tag_value
    test_opus_file.save()

    # Execute
    exit_code = app.run(["--directory", music_directory])

    # Assert
    actual_metadata: oggopus.OggOpus = oggopus.OggOpus(test_opus_file_path)

    # Check exit code
    assert exit_code == 0

    # Check log
    assert "Metadata saved for file: test" in capsys.readouterr().out

    # Check tag content
    # assert actual_metadata == expected_metadata
    # Check tag by tag instead so that the diff is more readable
    for tag_name, tag_value in expected_metadata.items():
        if tag_name == "encoder":
            continue
        assert actual_metadata[tag_name] == tag_value

    # A bit double, but have to cover the case when tags other than
    # the ones in expected_metadata have been added.
    for tag_name, tag_value in actual_metadata.items():
        if tag_name == "encoder":
            continue
        assert expected_metadata[tag_name] == tag_value


def test_deleting_tag(music_directory, monkeypatch, capsys):
    """User selecting "Save" for a song should save resolved tags.

    When the user uses the "Save" option, resolved tags should be saved
    to the file being processed.
    """
    # Setup
    original_metadata = {
        "title": ["Proper Goodbyes (feat. Benny Ivor) (2039 Remaster)"],
        "artist": ["artist 1 and artist 2"],
        "purl": ["www.youtube.com"],
        "synopsis": [
            "Provided to YouTube by Rich Men's Group Digital Ltd."
            "\n\nProper Goodbyes (feat. Ben Ivor) (2036 Remaster) · The Global · Ben Ivor"
            "\n\nProper Goodbyes (feat. Ben Ivor)"
            "\n\n℗ 2022 The Global under exclusive license to 5BE Ltd"
            "\n\nReleased on: 2029-08-22"
        ],
    }

    expected_metadata = original_metadata.copy()
    # Manually selected
    expected_metadata["title"] = ["Proper Goodbyes (feat. Ben Ivor) (2036 Remaster)"]  # Chose "youtube"
    expected_metadata["artist"] = ["The Global", "Ben Ivor"]  # Chose "youtube"
    expected_metadata["albumartist"] = ["The Global"]  # Chose the second alternative
    # Automatically resolved
    expected_metadata["comment"] = ["youtube-dl"]
    expected_metadata["date"] = ["2029-08-22"]
    expected_metadata["copyright"] = ["2022 The Global under exclusive license to 5BE Ltd"]
    expected_metadata["version"] = ["2039 Remaster"]
    expected_metadata["organization"] = ["Rich Men's Group Digital Ltd."]
    expected_metadata["encoder"] = ["Lavc60.3.100 libopus"]

    mock_show = Mock()
    # First: Choose youtube for 'artist'
    # Second: Choose youtube for 'title'
    # Third: Select album artist "The Global"
    # Fourth: Select album artist from list
    # Fifth: delete tag
    # Sixth: Select album
    # Seventh: Delete the only tag
    # Eigth: Save file
    mock_show.side_effect = [0, 0, 0, 1, 4, 0, 0, 1]

    monkeypatch.setattr(utils.TerminalMenu, "__init__", lambda *_, **__: None)
    monkeypatch.setattr(utils.TerminalMenu, "show", mock_show)

    # Create an opus file for testing saving
    silence = AudioSegment.silent(duration=1000)
    test_opus_file_path = Path(music_directory) / "test.opus"
    silence.export(test_opus_file_path, format="opus")
    # Tags are not handled well by pydub so we fix it afterward:
    test_opus_file: oggopus.OggOpus = oggopus.OggOpus(test_opus_file_path)
    for tag_name, tag_value in original_metadata.items():
        test_opus_file[tag_name] = tag_value
    test_opus_file.save()

    # Execute
    exit_code = app.run(["--directory", music_directory])

    # Assert
    actual_metadata: oggopus.OggOpus = oggopus.OggOpus(test_opus_file_path)

    # Check exit code
    assert exit_code == 0

    # Check log
    assert "Metadata saved for file: test" in capsys.readouterr().out

    # Check tag content
    # assert actual_metadata == expected_metadata
    # Check tag by tag instead so that the diff is more readable
    for tag_name, tag_value in expected_metadata.items():
        if tag_name == "encoder":
            continue
        assert actual_metadata[tag_name] == tag_value

    # A bit double, but have to cover the case when tags other than
    # the ones in expected_metadata have been added.
    for tag_name, tag_value in actual_metadata.items():
        if tag_name == "encoder":
            continue
        assert expected_metadata[tag_name] == tag_value

    # This is the core of the test:
    assert "album" not in actual_metadata
    assert "albumartist" in actual_metadata
