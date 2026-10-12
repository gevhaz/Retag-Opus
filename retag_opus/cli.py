"""Module for parsing command line arguments."""
import argparse
from argparse import Namespace
from typing import Sequence

import shtab

from retag_opus import __version__


class Cli:
    """Class for parsing command line arguments."""

    @staticmethod
    def parse_arguments(argv: Sequence[str] | None) -> Namespace:
        """Create parser and parse CLI arguments, and return them."""
        parser = argparse.ArgumentParser()

        shtab.add_argument_to(parser, ["-s", "--print-completion"])

        parser.add_argument(
            "-a",
            "--album",
            action="store",
            required=False,
            default=None,
            dest="manual_album",
            help="Manually sets the album tag to the given value and puts any parsed album in the " "discsubtitle tag",
        )

        parser.add_argument(
            "-d",
            "--directory",
            action="store",
            required=True,
            dest="dir",
            help="directory in which the files to be retagged are " "located",
        ).complete = shtab.DIRECTORY  # type: ignore

        parser.add_argument(
            "-i",
            "--individual",
            action="store_true",
            default=False,
            dest="individual",
            help="Choose album level tags separately for each song, even for songs that are from the same album",
        )

        parser.add_argument(
            "-m",
            "--musicbrainz",
            action=argparse.BooleanOptionalAction,
            default=None,
            dest="musicbrainz",
            help="Look up songs on MusicBrainz, overriding the configuration file",
        )

        parser.add_argument(
            "-V",
            "--version",
            action="version",
            version=f"retag (version {__version__})",
        )

        return parser.parse_args(argv)
