"""pip CLI interface."""
from __future__ import annotations

import logging
import shlex
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING, Final, List, Literal, Optional, Sequence, Union, cast

from runway.compat import cached_property

from ...base_classes import DependencyManager

if TYPE_CHECKING:
    from os import PathLike

    from runway._logging import RunwayLogger

    from ...source_code import SourceCode

LOGGER = cast("RunwayLogger", logging.getLogger(f"runway.{__name__}"))


class Pip(DependencyManager):
    """pip CLI interface."""

    EXECUTABLE: Final[Literal["pip"]] = "pip"

    @cached_property
    def version(self) -> str:
        """Get pip version."""
        return self._run_command([self.EXECUTABLE, "--version"])

    def install(
        self, *, requirements: "PathLike[str]", target: "PathLike[str]"
    ) -> None:
        """Install dependencies.

        Args:
            requirements: Path to a ``requirements.txt`` file.
            target: Path to a directory where dependencies will be installed.

        """
        target = Path(target) if not isinstance(target, Path) else target
        target.mkdir(exist_ok=True, parents=True)
        try:
            self._run_command(
                self.generate_command(
                    "install",
                    disable_pip_version_check=True,
                    requirement=str(requirements),
                    target=str(target),
                ),
                suppress_output=False,
            )
        except subprocess.CalledProcessError as exc:
            LOGGER.error(exc.stderr)
            raise

    @classmethod
    def generate_command(
        cls,
        command: Union[List[str], str],
        **kwargs: Optional[Union[bool, Sequence[str], str]],
    ) -> List[str]:
        """Generate command to be executed and log it.

        Args:
            command: Command to run.
            args: Additional args to pass to the command.

        Returns:
            The full command to be passed into a subprocess.

        """
        cmd = [
            "python",
            "-m",
            cls.EXECUTABLE,
            *(command if isinstance(command, list) else [command]),
        ]
        cmd.extend(cls._generate_command_handle_kwargs(**kwargs))
        LOGGER.debug("generated command: %s", shlex.join(cmd))
        return cmd


def is_pip_project(
    source_code: SourceCode, *, file_name: str = "requirements.txt"
) -> bool:
    """Determine if source code is a pip project.

    Args:
        source_code: Source code object.
        file_name: Name of the requirements file. Unlike some other dependency
            manager, this is configurable of pip.

    """
    requirements_txt = source_code.root_directory / file_name

    if requirements_txt.is_file():
        return True
    return False
