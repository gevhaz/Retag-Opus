"""Tests for description_parser.py."""
from retag_opus.description_parser import DescriptionParser


def test_parse_credits() -> None:
    """Credits are put in tags named as on MusicBrainz."""
    parser = DescriptionParser()
    parser.parse(
        "Provided to YouTube by Label\n"
        "\n"
        "Song · Singer\n"
        "\n"
        "Album\n"
        "\n"
        "Lead Vocal: Singer\n"
        "Background Vocal: Choir\n"
        "Drums: Drummer\n"
        "Lyricist: Poet\n"
        "Writer: Song Smith\n"
    )
    assert parser.tags["performer:lead vocals"] == ["Singer"]
    assert parser.tags["performer:background vocals"] == ["Choir"]
    assert parser.tags["performer:drums (drum set)"] == ["Drummer"]
    assert parser.tags["lyricist"] == ["Poet"]
    assert parser.tags["writer"] == ["Song Smith"]
