"""Class mixins."""
from __future__ import annotations

import logging
import shlex
import shutil
import subprocess
from typing import (
    TYPE_CHECKING,
    ClassVar,
    Dict,
    List,
    Optional,
    Sequence,
    Union,
    cast,
    overload,
)

from typing_extensions import Literal

if TYPE_CHECKING:
    from pathlib import Path

    from runway._logging import RunwayLogger
    from runway.context import CfnginContext, RunwayContext

LOGGER = cast("RunwayLogger", logging.getLogger(f"runway.{__name__}"))


class CliInterfaceMixin:
    """Mixin for adding CLI interface methods."""

    EXECUTABLE: ClassVar[str]  #: CLI executable.

    ctx: Union[CfnginContext, RunwayContext]  #: CFNgin or Runway context object.
    cwd: Path  #: Working directory where commands will be run.

    @staticmethod
    def convert_to_cli_arg(arg_name: str, *, prefix: str = "--") -> str:
        """Convert string kwarg name into a CLI argument."""
        return f"{prefix}{arg_name.replace('_', '-')}"

    @classmethod
    def found_in_path(cls) -> bool:
        """Determine if executable is found in $PATH."""
        if shutil.which(cls.EXECUTABLE):
            return True
        return False

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
        cmd = [cls.EXECUTABLE, *(command if isinstance(command, list) else [command])]
        cmd.extend(cls._generate_command_handle_kwargs(**kwargs))
        LOGGER.debug("generated command: %s", shlex.join(cmd))
        return cmd

    @classmethod
    def _generate_command_handle_kwargs(
        cls, **kwargs: Optional[Union[bool, Sequence[str], str]]
    ) -> List[str]:
        """Handle kwargs passed to generate_command."""
        result: List[str] = []
        for k, v in kwargs.items():
            if isinstance(v, str):
                result.extend([cls.convert_to_cli_arg(k), v])
            elif isinstance(v, (list, set, tuple)):
                for i in cast(Sequence[str], v):
                    result.extend([cls.convert_to_cli_arg(k), i])
            elif isinstance(v, bool) and v:
                result.append(cls.convert_to_cli_arg(k))
        return result

    @overload
    def _run_command(
        self,
        command: Union[Sequence[str], str],
        *,
        env: Optional[Dict[str, str]] = ...,
        suppress_output: Literal[True] = ...,
    ) -> str:
        ...

    @overload
    def _run_command(
        self,
        command: Union[Sequence[str], str],
        *,
        env: Optional[Dict[str, str]] = ...,
        suppress_output: Literal[False] = ...,
    ) -> None:
        ...

    def _run_command(
        self,
        command: Union[Sequence[str], str],
        *,
        env: Optional[Dict[str, str]] = None,
        suppress_output: bool = True,
    ) -> Optional[str]:
        """Run command.

        Args:
            command: Command to pass to shell to execute.
            env: Environment variables.
            suppress_output: If ``True``, the output of the subprocess written
                to ``sys.stdout`` and ``sys.stderr`` will be captured and
                returned as a string instead of being being written directly.

        """
        cmd_str = command if isinstance(command, str) else shlex.join(command)
        LOGGER.verbose("running command: %s", cmd_str)
        if suppress_output:
            return subprocess.check_output(
                cmd_str,
                cwd=self.cwd,
                env=env or self.ctx.env.vars,
                shell=True,
                stderr=subprocess.PIPE,
                text=True,
            )
        subprocess.check_call(
            cmd_str,
            cwd=self.cwd,
            env=env or self.ctx.env.vars,
            shell=True,
        )
        return None
