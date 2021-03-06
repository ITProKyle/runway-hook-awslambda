"""Pipenv interface."""
from __future__ import annotations

import logging
import re
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final, Tuple, Union

from runway.cfngin.exceptions import CfnginError
from runway.compat import cached_property
from typing_extensions import Literal

from ...base_classes import DependencyManager
from ...utils import Version

if TYPE_CHECKING:
    from _typeshed import StrPath

    from ...source_code import SourceCode

LOGGER = logging.getLogger(f"runway.{__name__}")


class PipenvExportFailedError(CfnginError):
    """Pipenv export failed to produce a ``requirements.txt`` file."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Instantiate class. All args/kwargs are passed to parent method."""
        self.message = (
            "pipenv lock to requirements.txt format failed; review pipenv's"
            " output above to troubleshoot"
        )
        super().__init__(*args, **kwargs)


class PipenvNotFoundError(CfnginError):
    """Pipenv not installed or found in $PATH."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Instantiate class. All args/kwargs are passed to parent method."""
        self.message = (
            "pipenv not installed or not in PATH! "
            "Install it according to pipenv docs (https://pipenv.pypa.io/en/latest/) "
            "and ensure it is available in PATH."
        )
        super().__init__(*args, **kwargs)


class Pipenv(DependencyManager):
    """Pipenv dependency manager."""

    CONFIG_FILES: Final[Tuple[Literal["Pipfile"], Literal["Pipfile.lock"]]] = (
        "Pipfile",
        "Pipfile.lock",
    )
    EXECUTABLE: Final[Literal["pipenv"]] = "pipenv"

    @cached_property
    def version(self) -> Version:
        """pipenv version."""
        cmd_output = self._run_command([self.EXECUTABLE, "--version"])
        match = re.search(r"^pipenv, version (?P<version>\S*)", cmd_output)
        if not match:
            LOGGER.warning(
                "unable to parse pipenv version from output:\n%s", cmd_output
            )
            return Version("0.0.0")
        return Version(match.group("version"))

    def export(self, *, dev: bool = False, output: StrPath) -> Path:
        """Export the lock file to other formats (requirements.txt only).

        The underlying command being executed by this method is
        ``pipenv lock --requirements``.

        Args:
            dev: Include development dependencies.
            output: Path to the output file.

        """
        output = Path(output)
        try:
            result = self._run_command(
                self.generate_command(
                    "lock",
                    dev=dev,
                    requirements=True,
                ),
                suppress_output=True,
            )
        except subprocess.CalledProcessError as exc:
            raise PipenvExportFailedError from exc
        output.parent.mkdir(exist_ok=True, parents=True)  # ensure directory exists
        output.write_text(result)
        return output


def is_pipenv_project(source_code: Union[Path, SourceCode]) -> bool:
    """Determine if source code is a pipenv project.

    Args:
        source_code: Source code object.

    """
    if not (source_code / Pipenv.CONFIG_FILES[0]).is_file():
        return False

    if not (source_code / Pipenv.CONFIG_FILES[1]).is_file():
        LOGGER.warning("%s not found; creating it...", Pipenv.CONFIG_FILES[1])
    return True
