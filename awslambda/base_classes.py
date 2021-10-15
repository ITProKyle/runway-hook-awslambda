"""Base classes."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    Generic,
    Optional,
    Set,
    Tuple,
    TypeVar,
    cast,
    overload,
)

from runway.cfngin.hooks.protocols import CfnginHookProtocol
from runway.compat import cached_property
from typing_extensions import Literal

from .constants import BASE_WORK_DIR
from .mixins import CliInterfaceMixin
from .models.args import AwsLambdaHookArgs
from .models.responses import AwsLambdaHookDeployResponse
from .source_code import SourceCode

if TYPE_CHECKING:
    from _typeshed import StrPath
    from runway._logging import RunwayLogger
    from runway.context import CfnginContext
    from runway.utils import BaseModel

    from .deployment_package import DeploymentPackage
    from .type_defs import AwsLambdaHookDeployResponseTypedDict

LOGGER = cast("RunwayLogger", logging.getLogger(f"runway.{__name__}"))

_AwsLambdaHookArgsTypeVar = TypeVar(
    "_AwsLambdaHookArgsTypeVar", bound=AwsLambdaHookArgs, covariant=True
)


class DependencyManager(CliInterfaceMixin):
    """Dependency manager for the AWS Lambda runtime.

    Dependency managers are interfaced with via subprocess to ensure that the
    correct version is being used. This is primarily target at Python
    dependency manager that we could import and use directly.

    """

    CONFIG_FILES: ClassVar[Tuple[str, ...]]

    def __init__(self, context: CfnginContext, cwd: StrPath) -> None:
        """Instantiate class.

        Args:
            context: CFNgin or Runway context object.
            cwd: Working directory where commands will be run.

        """
        self.ctx = context
        self.cwd = cwd if isinstance(cwd, Path) else Path(cwd)

    @cached_property
    def version(self) -> str:
        """Get executable version."""
        raise NotImplementedError


class Project(Generic[_AwsLambdaHookArgsTypeVar]):
    """Project continaing source code for an AWS Lambda Function."""

    #: Name of the default cache directory.
    DEFAULT_CACHE_DIR_NAME: ClassVar[str] = "cache"

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
    def cache_dir(self) -> Optional[Path]:
        """Directory where a dependency manager's cache data will be stored.

        Returns:
            Explicit cache directory if provided or default cache directory if
            it is not provided. If configured to not use cache, will always be
            ``None``.

        """
        if not self.args.use_cache:
            return None
        cache_dir = (
            self.args.cache_dir
            if self.args.cache_dir
            else BASE_WORK_DIR / self.DEFAULT_CACHE_DIR_NAME
        )
        cache_dir.mkdir(exist_ok=True, parents=True)
        return cache_dir

    @cached_property
    def dependency_directory(self) -> Path:
        """Directory to use as the target of ``pip install --target``."""
        result = self.build_directory / "dependencies"
        result.mkdir(exist_ok=True, parents=True)
        return result

    @cached_property
    def metadata_files(self) -> Tuple[Path, ...]:
        """Project metadata files (e.g. ``project.json``, ``pyproject.toml``)."""
        return ()

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
        source_code = SourceCode(
            self.args.source_code,
            include_files_in_hash=self.metadata_files,
            project_root=self.project_root,
        )
        for rule in self.args.extend_gitignore:
            source_code.add_filter_rule(rule)
        return source_code

    @cached_property
    def project_root(self) -> Path:
        """Root directory of the project.

        The top-level directory containing the source code and all
        configuration/metadata files (e.g. pyproject.toml, package.json).

        The project root can be different from the source code directory but,
        if they are different, the project root should contain the source code
        directory. If it does not, the source code directory will be always
        be used.

        The primary use case for this property is to allow configuration files
        to exist outside of the source code directory. The ``project_type``
        can and should rely on the value of this property when determining the
        type.

        """
        top_lvl_dir = (
            self.ctx.config_path.parent
            if self.ctx.config_path.is_file()
            else (
                self.ctx.config_path
                if self.ctx.config_path.is_dir()
                else self.args.source_code
            )
        )
        if top_lvl_dir == self.args.source_code:
            return top_lvl_dir

        parents = list(self.args.source_code.parents)
        if top_lvl_dir not in parents:
            LOGGER.info(
                "ignoring project directory; "
                "source code located outside of project directory"
            )
            return self.args.source_code

        dirs_to_check = [
            self.args.source_code,
            *parents[: parents.index(top_lvl_dir) + 1],
        ]
        for dir_to_check in dirs_to_check:
            for check_for_file in self.supported_metadata_files:
                if next(dir_to_check.glob(check_for_file), None):
                    return dir_to_check
        # reached if all dirs in between source and top-level are missing metadata files
        return top_lvl_dir

    @cached_property
    def project_type(self) -> str:
        """Type of project (e.g. poetry, yarn).

        This should be considered more of a "subtype" as the subclass should
        distinguish project language. The value of this property should reflect
        the project/dependency management tool used within the project.

        The value of this property should be calculated without initalizing
        other properties (e.g. ``source_code``) except for ``project_root``
        so that it can be used in their initialization process.

        """
        raise NotImplementedError

    @cached_property
    def supported_metadata_files(self) -> Set[str]:
        """Names of all supported metadata files.

        Returns:
            Set of file names - not paths.

        """
        return set()

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

    @overload
    def build_response(self, stage: Literal["plan"]) -> AwsLambdaHookDeployResponse:
        ...

    def build_response(
        self, stage: Literal["deploy", "destroy", "plan"]
    ) -> Optional[BaseModel]:
        """Build response object that will be returned by this hook.

        Args:
            stage: The current stage being executed by the hook.

        """
        if stage == "deploy":
            return self._build_response_deploy()
        if stage == "destroy":
            return self._build_response_destroy()
        if stage == "plan":
            return self._build_response_plan()
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

    def _build_response_plan(self) -> AwsLambdaHookDeployResponse:
        """Build response for plan stage."""
        try:
            return AwsLambdaHookDeployResponse(
                bucket_name=self.deployment_package.bucket.name,
                code_sha256=self.deployment_package.code_sha256,
                object_key=self.deployment_package.object_key,
                object_version_id=self.deployment_package.object_version_id,
                runtime=self.deployment_package.runtime,
            )
        except FileNotFoundError:
            return AwsLambdaHookDeployResponse(
                bucket_name=self.deployment_package.bucket.name,
                code_sha256="WILL CALCULATE WHEN BUILT",
                object_key=self.deployment_package.object_key,
                object_version_id=self.deployment_package.object_version_id,
                runtime=self.deployment_package.runtime,
            )

    def plan(self) -> AwsLambdaHookDeployResponseTypedDict:
        """Run during the **plan** stage."""
        return cast(
            "AwsLambdaHookDeployResponseTypedDict",
            self.build_response("plan").dict(by_alias=True),
        )

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
