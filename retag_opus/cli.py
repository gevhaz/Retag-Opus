import argparse
from argparse import Namespace

import shtab


class Cli:
    @staticmethod
    def parse_arguments() -> Namespace:
        parser = argparse.ArgumentParser()

        shtab.add_argument_to(parser, ["-s", "--print-completion"])  # type: ignore

        parser.add_argument(
            "-a",
            "--all",
            action="store_true",
            default=False,
            dest="fix_descriptionless",
            help="Even if there is no YouTube description, suggest improving existing tags",
        )

        parser.add_argument(
            "-b",
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
            "-V", "--version", action="version", version="%(prog)s (version {version})".format(version="0.3.0")
        )

        return parser.parse_args()
