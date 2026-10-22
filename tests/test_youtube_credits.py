"""Tests for youtube_credits.py."""

import pytest

from retag_opus import youtube_credits


def test_normalize_role() -> None:
    """Roles are compared in lower case, with single spaces."""
    assert youtube_credits.normalize_role(" Associated  Performer ") == "associated performer"


def test_roles_by_category() -> None:
    """Roles are grouped under the category before them."""
    assert youtube_credits.roles_by_category("Producer, Studio  Personnel, Mixer, Associated Performer, Piano") == [
        (None, ["producer"]),
        ("studio personnel", ["mixer"]),
        ("associated performer", ["piano"]),
    ]
    assert youtube_credits.roles_by_category("Associated Performer") == [(None, []), ("associated performer", [])]


@pytest.mark.parametrize(
    ("line", "expected_tags"),
    [
        ("Composer: Com Poser", {"composer": ["Com Poser"]}),
        ("Composer  Lyricist: Song Smith", {"composer": ["Song Smith"], "lyricist": ["Song Smith"]}),
        ("Associated  Performer, Drums: Drum Mer", {"performer:drums (drum set)": ["Drum Mer"]}),
        # A performer role named as on MusicBrainz needs no translation
        ("Piano: Pia Nist", {"performer:piano": ["Pia Nist"]}),
        # Any role of an associated performer is a performer's role
        ("Associated Performer, Theremin: Ther Emin", {"performer:theremin": ["Ther Emin"]}),
        ("Associated Performer: Per Former", {"performer": ["Per Former"]}),
        (
            "Rhythm Guitar, Lead Vocals: Sing Er",
            {"performer:guitar": ["Sing Er"], "performer:lead vocals": ["Sing Er"]},
        ),
        # Like Picard, mastering and recording engineers aren't put in "engineer"
        ("Studio  Personnel, Mixer, Mastering  Engineer: Engi Neer", {"mixer": ["Engi Neer"]}),
        # A category applies to the roles after it, up to the next one
        (
            "Producer, Studio  Personnel, Recording  Engineer, Associated  Performer, Piano, Bass: Dan Nigro",
            {"producer": ["Dan Nigro"], "performer:piano": ["Dan Nigro"], "performer:bass": ["Dan Nigro"]},
        ),
        ("Producer, Associated  Performer: Pro Ducer", {"producer": ["Pro Ducer"], "performer": ["Pro Ducer"]}),
        # Programming isn't an instrument, even for an associated performer
        ("Associated Performer, Programming: Program Mer", {}),
        ("Associated Performer, Unknown: Some One", {}),
        # Without "Associated Performer", an unknown role isn't assumed to be an instrument
        ("Lacquer Cut: Cut Ter", {}),
        ("Released on: 2020-01-01", {}),
        ("Producer: ", {}),
        # A colon in the name is kept
        ("Producer: DJ: Name", {"producer": ["DJ: Name"]}),
    ],
)
def test_parse_credit_line(line: str, expected_tags: dict[str, list[str]]) -> None:
    """Credit lines become tags named after the standards in CLAUDE.md."""
    assert youtube_credits.parse_credit_line(line) == expected_tags
