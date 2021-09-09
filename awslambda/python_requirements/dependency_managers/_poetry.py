"""Poetry CLI interface."""
from __future__ import annotations

import logging
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final, List, Optional, Union

import tomli
from runway.cfngin.exceptions import CfnginError
from runway.compat import cached_property
from typing_extensions import Literal

from ...base_classes import DependencyManager

if TYPE_CHECKING:
    from _typeshed import StrPath

    from ...source_code import SourceCode

LOGGER = logging.getLogger(f"runway.{__name__}")


class PoetryExportFailedError(CfnginError):
    """Poetry export failed to produce a ``requirements.txt`` file."""

    def __init__(self, output: str, *args: Any, **kwargs: Any) -> None:
        """Instantiate class. All args/kwargs are passed to parent method.

        Args:
            output: The output from running ``poetry export``.

        """
        self.message = f"poetry export failed with the following output:\n{output}"
        super().__init__(*args, **kwargs)


class PoetryNotFoundError(CfnginError):
    """Poetry not installed or found in $PATH."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Instantiate class. All args/kwargs are passed to parent method."""
        self.message = (
            "poetry not installed or not in PATH! "
            "Install it according to poetry docs (https://python-poetry.org/) "
            "and ensure it is available in PATH."
        )
        super().__init__(*args, **kwargs)


class Poetry(DependencyManager):
    """Poetry dependency manager."""

    EXECUTABLE: Final[Literal["poetry"]] = "poetry"

    @cached_property
    def version(self) -> str:
        """Get poetry version."""
        return self._run_command([self.EXECUTABLE, "--version"])

    def export(
        self,
        *,
        dev: bool = False,
        extras: Optional[List[str]] = None,
        output: StrPath,
        output_format: str = "requirements.txt",
        with_credentials: bool = True,
        without_hashes: bool = True,
    ) -> Path:
        """Export the lock file to other formats.

        Args:
            dev: Include development dependencies.
            extras: Extra sets of dependencies to include.
            output: Path to the output file.
            output_format: The format to export to.
            with_credentials: Include credentials for extra indices.
            without_hashes: Exclude hashes from the exported file.

        Returns:
            Path to the output file.

        """
        output = Path(output)
        try:
            result = self._run_command(
                self.generate_command(
                    "export",
                    dev=dev,
                    extras=extras,
                    format=output_format,
                    output=output.name,
                    with_credentials=with_credentials,
                    without_hashes=without_hashes,
                )
            )
            requirements_txt = self.source_code.root_directory / output.name
            if requirements_txt.is_file():
                output.parent.mkdir(exist_ok=True, parents=True)
                return requirements_txt.rename(output)
        except subprocess.CalledProcessError as exc:
            raise PoetryExportFailedError(exc.stderr) from exc
        raise PoetryExportFailedError(result)


def is_poetry_project(source_code: Union[Path, SourceCode]) -> bool:
    """Determine if source code is a poetry project.

    Args:
        source_code: Source code object.

    """
    pyproject_path = source_code / "pyproject.toml"

    if not pyproject_path.is_file():
        return False

    # check for PEP-517 definition
    pyproject = tomli.loads(pyproject_path.read_text())
    build_system_requires: Optional[List[str]] = pyproject.get("build-system", {}).get(
        "requires"
    )

    if build_system_requires:
        for req in build_system_requires:
            if req.startswith("poetry"):
                LOGGER.debug("poetry project detected")
                return True
    return False
