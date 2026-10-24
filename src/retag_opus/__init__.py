"""Init file and version container.

This file makes the folder recognized as a module and exposes the
version. The version is read from the installed package's metadata, so
it's only set in pyproject.toml, e.g. with `uv version --bump minor`.
"""

from importlib.metadata import version
from typing import Final

__version__: Final[str] = version("retag_opus")
