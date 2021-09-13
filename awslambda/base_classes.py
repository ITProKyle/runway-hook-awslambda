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
    TypeVar,
    Union,
    cast,
    overload,
)

from runway.cfngin.hooks.protocols import CfnginHookProtocol
from runway.compat import cached_property
from typing_extensions import Literal

from .constants import BASE_WORK_DIR
from .models.args import AwsLambdaHookArgs
from .models.responses import AwsLambdaHookDeployResponse
from .source_code import SourceCode

if TYPE_CHECKING:
    from pathlib import Path

    from runway._logging import RunwayLogger
    from runway.context import CfnginContext
    from runway.utils import BaseModel

    from .deployment_package import DeploymentPackage

LOGGER = cast("RunwayLogger", logging.getLogger(f"runway.{__name__}"))

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

    @overload
    def _run_command(
        self,
        command: Union[Sequence[str], str],
        *,
        suppress_output: Literal[True] = ...,
    ) -> str:
        ...

    @overload
    def _run_command(
        self,
        command: Union[Sequence[str], str],
        *,
        suppress_output: Literal[False] = ...,
    ) -> None:
        ...

    def _run_command(
        self, command: Union[Sequence[str], str], *, suppress_output: bool = True
    ) -> Optional[str]:
        """Run command.

        Args:
            command: Command to pass to shell to execute.
            suppress_output: If ``True``, the output of the subprocess written
                to ``sys.stdout`` and ``sys.stderr`` will be captured and
                returned as a string instead of being being written directly.

        """
        cmd_str = command if isinstance(command, str) else shlex.join(command)
        LOGGER.verbose("running command: %s", cmd_str)
        if suppress_output:
            return subprocess.check_output(
                cmd_str,
                cwd=self.source_code.root_directory,
                env=self.ctx.env.vars,
                shell=True,
                stderr=subprocess.PIPE,
                text=True,
            )
        subprocess.check_call(
            cmd_str,
            cwd=self.source_code.root_directory,
            env=self.ctx.env.vars,
            shell=True,
        )
        return None

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


class Project(Generic[_AwsLambdaHookArgsTypeVar]):
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
    def build_directory(self) -> Path:
        """Directory being used to build deployment package."""
        result = (
            BASE_WORK_DIR
            / self.runtime
            / f"{self.source_code.root_directory.name}.{self.source_code.md5_hash}"
        )
        result.mkdir(exist_ok=True, parents=True)
        return result

    @cached_property
    def dependency_directory(self) -> Path:
        """Directory use as the target of ``pip install --target``."""
        result = self.build_directory / "dependencies"
        result.mkdir(exist_ok=True, parents=True)
        return result

    @cached_property
    def runtime(self) -> str:
        """Runtime of the deployment package."""
        return self.args.runtime

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

    def cleanup(self) -> None:
        """Cleanup project files at the end of execution.

        If any cleanup is needed (e.g. removal of temporary dependency directory)
        it should be implimented here. Hook's should call this method in a
        ``finally`` block to ensure it is run even if the rest of the hook
        encountered an error.

        """

    def install_dependencies(self) -> None:
        """Install project dependencies.

        Arguments/options should be read from the ``args`` attribute of this
        object instead of being passed into the method call. The method itself
        only exists for timing and filling in custom handling that is required
        for each project type.

        """
        raise NotImplementedError


_ProjectTypeVar = TypeVar("_ProjectTypeVar", bound=Project[AwsLambdaHookArgs])


class AwsLambdaHook(CfnginHookProtocol, Generic[_ProjectTypeVar]):
    """Base class for AWS Lambda hooks."""

    args: AwsLambdaHookArgs
    ctx: CfnginContext

    # pylint: disable=super-init-not-called
    def __init__(self, context: CfnginContext, **_kwargs: Any) -> None:
        """Instantiate class.

        This method should be overridden by subclasses.
        This is required to set the value of the args attribute.

        Args:
            context: CFNgin context object (passed in by CFNgin).

        """
        self.ctx = context

    @cached_property
    def deployment_package(self) -> DeploymentPackage[_ProjectTypeVar]:
        """AWS Lambda deployment package."""
        raise NotImplementedError

    @cached_property
    def project(self) -> _ProjectTypeVar:
        """Project being deployed as an AWS Lambda Function."""
        raise NotImplementedError

    @overload
    def build_response(self, stage: Literal["deploy"]) -> AwsLambdaHookDeployResponse:
        ...

    @overload
    def build_response(self, stage: Literal["destroy"]) -> Optional[BaseModel]:
        ...

    def build_response(
        self, stage: Literal["deploy", "destroy"]
    ) -> Optional[BaseModel]:
        """Build response object that will be returned by this hook.

        Args:
            stage: The current stage being executed by the hook.

        """
        if stage == "deploy":
            return self._build_response_deploy()
        if stage == "destroy":
            return self._build_response_destroy()
        raise NotImplementedError("only deploy and destroy are supported")

    def _build_response_deploy(self) -> AwsLambdaHookDeployResponse:
        """Build response for deploy stage."""
        return AwsLambdaHookDeployResponse(
            bucket_name=self.deployment_package.bucket.name,
            code_sha256=self.deployment_package.code_sha256,
            object_key=self.deployment_package.object_key,
            object_version_id=self.deployment_package.object_version_id,
            runtime=self.deployment_package.runtime,
        )

    def _build_response_destroy(self) -> Optional[BaseModel]:
        """Build response for destroy stage."""
        return None

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


class FunctionHook(AwsLambdaHook[_ProjectTypeVar]):
    """Hook used in the creation of an AWS Lambda Function."""

    @cached_property
    def deployment_package(self) -> DeploymentPackage[_ProjectTypeVar]:
        """AWS Lambda deployment package."""
        raise NotImplementedError

    @cached_property
    def project(self) -> _ProjectTypeVar:
        """Project being deployed as an AWS Lambda Function."""
        raise NotImplementedError


class LayerHook(AwsLambdaHook[_ProjectTypeVar]):
    """Hook used in the create of an AWS Lambda Layer."""

    @cached_property
    def deployment_package(self) -> DeploymentPackage[_ProjectTypeVar]:
        """AWS Lambda deployment package."""
        raise NotImplementedError

    @cached_property
    def project(self) -> _ProjectTypeVar:
        """Project being deployed as an AWS Lambda Function."""
        raise NotImplementedError
