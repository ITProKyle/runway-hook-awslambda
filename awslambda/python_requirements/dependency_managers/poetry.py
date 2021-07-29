"""Poetry CLI interface."""
from __future__ import annotations

from typing import Any, Final, List, Optional

from runway.compat import cached_property
from typing_extensions import Literal

from .base_classes import PythonDependencyManager


class Poetry(PythonDependencyManager):
    """Poetry dependency manager."""

    EXECUTABLE: Final[Literal["poetry"]] = "poetry"

    @cached_property
    def version(self) -> str:
        """Get poetry version."""
        return self._run_command([self.EXECUTABLE, "--version"])

    def export(  # pylint: disable=arguments-differ
        self,
        *,
        dev: bool = False,
        extras: Optional[List[str]] = None,
        output: str = "requirements.txt",
        output_format: str = "requirements.txt",
        with_credentials: bool = True,
        without_hashes: bool = True,
        **_kwargs: Any,
    ) -> None:
        """Export the lock file to other formats.

        Args:
            dev: Include development dependencies.
            extras: Extra sets of dependencies to include.
            output: The name of the output file.
            output_format: The format to export to.
            with_credentials: Include credentials for extra indices.
            without_hashes: Exclude hashes from the exported file.

        """
        cmd = self.generate_command(
            "export",
            dev=dev,
            extras=extras,
            format=output_format,
            output=output,
            with_credentials=with_credentials,
            without_hashes=without_hashes,
        )
        self._run_command(cmd)
