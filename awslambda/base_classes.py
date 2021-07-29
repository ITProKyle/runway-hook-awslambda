"""Base classes."""
from __future__ import annotations

import logging
import shlex
import shutil
import subprocess
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    Generic,
    List,
    Optional,
    Sequence,
    Type,
    TypeVar,
    Union,
    cast,
)

from runway.cfngin.hooks.base import Hook
from runway.compat import cached_property

from .constants import LOGGER_PREFIX
from .models.args import AwsLambdaHookArgs
from .source_code import SourceCode

if TYPE_CHECKING:
    from pathlib import Path

    from runway.cfngin.providers.aws.default import Provider
    from runway.context import CfnginContext

LOGGER = logging.getLogger(f"{LOGGER_PREFIX}")

_AwsLambdaHookArgsTypeVar = TypeVar(
    "_AwsLambdaHookArgsTypeVar", bound=AwsLambdaHookArgs, covariant=True
)


class DependencyManager:
    """Dependency manager for the AWS Lambda runtime.

    Dependency managers are interfaced with via subprocess to ensure that the
    correct version is being used. This is primarily target at Python
    dependency manager that we could import and use directly.

    """

    EXECUTABLE: ClassVar[str]

    ctx: CfnginContext
    source_code: SourceCode

    def __init__(self, context: CfnginContext, source_code: SourceCode) -> None:
        """Instantiate class."""
        self.ctx = context
        self.source_code = source_code

    @cached_property
    def version(self) -> str:
        """Get executable version."""
        raise NotImplementedError

    def _run_command(self, command: Union[List[str], str]) -> str:
        """Run command.

        Args:
            command: Command to pass to shell to execute.

        """
        return subprocess.check_output(
            command,
            cwd=self.source_code.root_directory,
            env=self.ctx.env.vars,
            shell=True,
            stderr=subprocess.PIPE,
            text=True,
        )

    @classmethod
    def generate_command(
        cls,
        command: str,
        **kwargs: Optional[Union[bool, Sequence[str], str]],
    ) -> List[str]:
        """Generate command to be executed and log it.

        Args:
            command: Poetry command to run.
            args: Additional args to pass to poetry.

        Returns:
            The full command to be passed into a subprocess.

        """
        cmd = [cls.EXECUTABLE, command]
        for k, v in kwargs.items():
            if isinstance(v, str):
                cmd.extend([cls.convert_to_cli_arg(k), v])
            elif isinstance(v, (list, set, tuple)):
                for i in cast(Sequence[str], v):
                    cmd.extend([cls.convert_to_cli_arg(k), i])
            elif isinstance(v, bool) and v:
                cmd.append(cls.convert_to_cli_arg(k))
        LOGGER.debug("generated command: %s", shlex.join(cmd))
        return cmd

    @classmethod
    def found_in_path(cls) -> bool:
        """Determine if executable is found in $PATH."""
        if shutil.which(cls.EXECUTABLE):
            return True
        return False

    @staticmethod
    def convert_to_cli_arg(arg_name: str, *, prefix: str = "--") -> str:
        """Convert string kwarg name into a CLI argument."""
        return f"{prefix}{arg_name.replace('_', '-')}"


_DependencyManagerTypeVar = TypeVar(
    "_DependencyManagerTypeVar", bound=DependencyManager, covariant=True
)


class Project(Generic[_AwsLambdaHookArgsTypeVar, _DependencyManagerTypeVar]):
    """Project continaing source code for an AWS Lambda Function."""

    args: _AwsLambdaHookArgsTypeVar
    ctx: CfnginContext

    def __init__(self, args: _AwsLambdaHookArgsTypeVar, context: CfnginContext) -> None:
        """Instantiate class.

        Args:
            args: Parsed hook arguments.
            context: Context object.

        """
        self.args = args
        self.ctx = context

    @cached_property
    def dependency_manager(self) -> _DependencyManagerTypeVar:
        """Determine and return the dependency manager to use."""
        raise NotImplementedError

    @cached_property
    def source_code(self) -> SourceCode:
        """Project source code.

        Lazy load source code object.
        Extends gitignore as needed.

        """
        source_code = SourceCode(self.args.source_code)
        for rule in self.args.extend_gitignore:
            source_code.add_filter_rule(rule)
        return source_code

    @classmethod
    def is_project(cls, source_code_path: Path) -> bool:
        """Determine if source code is a poetry project.

        Args:
            source_code_path: Path to the source code of the project.

        """
        raise NotImplementedError


_ProjectTypeVar = TypeVar(
    "_ProjectTypeVar", bound=Project[AwsLambdaHookArgs, DependencyManager]
)


class AwsLambdaHook(Generic[_AwsLambdaHookArgsTypeVar, _ProjectTypeVar], Hook):
    """Base class for AWS Lambda hooks."""

    # TODO make this is ClassVar in runway repo
    ARGS_PARSER: ClassVar[Type[_AwsLambdaHookArgsTypeVar]]  # type: ignore

    args: AwsLambdaHookArgs

    def __init__(self, context: CfnginContext, provider: Provider, **kwargs: Any):
        """Instantiate class.

        Args:
            context: Context object. (passed in by CFNgin)
            provider: Provider object. (passed in by CFNgin)

        """
        super().__init__(context=context, provider=provider, **kwargs)

    @cached_property
    def project(self) -> _ProjectTypeVar:
        """Project being deployed as an AWS Lambda Function."""
        raise NotImplementedError

    def post_deploy(self) -> Any:
        """Run during the **post_deploy** stage."""
        LOGGER.warning("post_deploy not implimented for %s", self.__class__.__name__)
        return True

    def post_destroy(self) -> Any:
        """Run during the **post_destroy** stage."""
        LOGGER.warning("post_destroy not implimented for %s", self.__class__.__name__)
        return True

    def pre_deploy(self) -> Any:
        """Run during the **pre_deploy** stage."""
        LOGGER.warning("pre_deploy not implimented for %s", self.__class__.__name__)
        return True

    def pre_destroy(self) -> Any:
        """Run during the **pre_destroy** stage."""
        LOGGER.warning("pre_destroy not implimented for %s", self.__class__.__name__)
        return True


class FunctionHook(AwsLambdaHook[_AwsLambdaHookArgsTypeVar, _ProjectTypeVar]):
    """Hook used in the creation of an AWS Lambda Function."""

    @cached_property
    def project(self) -> _ProjectTypeVar:
        """Project being deployed as an AWS Lambda Function."""
        raise NotImplementedError


class LayerHook(AwsLambdaHook[_AwsLambdaHookArgsTypeVar, _ProjectTypeVar]):
    """Hook used in the create of an AWS Lambda Layer."""

    @cached_property
    def project(self) -> _ProjectTypeVar:
        """Project being deployed as an AWS Lambda Function."""
        raise NotImplementedError
