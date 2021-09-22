"""AWS Lambda hooks."""
import sys

from ._python import PythonFunction

if sys.version_info < (3, 8):
    # importlib.metadata is standard lib for python>=3.8, use backport
    from importlib_metadata import (  # type: ignore # pylint: disable=E
        PackageNotFoundError,
        version,
    )
else:
    from importlib.metadata import (  # type: ignore # pylint: disable=E
        PackageNotFoundError,
        version,
    )

__all__ = ["__version__", "PythonFunction"]

try:
    __version__ = version(__name__)
except PackageNotFoundError:
    # package is not installed
    __version__ = "0.0.0"
