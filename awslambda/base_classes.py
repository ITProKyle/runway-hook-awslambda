"""Base classes."""
from __future__ import annotations

import base64
import hashlib
import logging
import mimetypes
import shlex
import shutil
import subprocess
import zipfile
from contextlib import suppress
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    Dict,
    Generic,
    Iterator,
    List,
    Optional,
    Sequence,
    TypeVar,
    Union,
    cast,
    overload,
)
from urllib.parse import urlencode

from runway.cfngin.hooks.protocols import CfnginHookProtocol
from runway.compat import cached_property
from runway.core.providers.aws.s3 import Bucket
from typing_extensions import Literal

from .constants import BASE_WORK_DIR
from .exceptions import BucketAccessDenied, BucketNotFound
from .models.args import AwsLambdaHookArgs
from .models.responses import AwsLambdaHookDeployResponse
from .source_code import SourceCode

if TYPE_CHECKING:
    from pathlib import Path

    import igittigitt
    from runway._logging import RunwayLogger
    from runway.context import CfnginContext
    from runway.utils import BaseModel

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
            BASE_WORK_DIR / f"{self.args.function_name}.{self.source_code.md5_hash}"
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
    def source_code(self) -> SourceCode:
        """Project source code.

        Lazy load source code object.
        Extends gitignore as needed.

        """
        source_code = SourceCode(self.args.source_code)
        for rule in self.args.extend_gitignore:
            source_code.add_filter_rule(rule)
        return source_code


_ProjectTypeVar = TypeVar("_ProjectTypeVar", bound=Project[AwsLambdaHookArgs])


# TODO move to runway.utils or similar
def calculate_lambda_code_sha256(file_path: Path) -> str:
    """Calculate the CodeSha256 of a deployment package.

    Returns:
        Value to pass to CloudFormation ``AWS::Lambda::Version.CodeSha256``.

    """
    file_hash = hashlib.sha256()
    read_size = 1024 * 10_000_000  # 10mb - number of bytes in each read operation
    with open(file_path, "rb") as buf:
        # python 3.7 compatable version of `while chunk := buf.read(read_size):`
        chunk = buf.read(read_size)  # seed chunk with initial value
        while chunk:
            file_hash.update(chunk)
            chunk = buf.read(read_size)  # read in new chunk
    return base64.b64encode(file_hash.digest()).decode()


# TODO move to runway.utils or similar
def calculate_s3_content_md5(file_path: Path) -> str:
    """Calculate the ContentMD5 value for a file being uploaded to AWS S3.

    Value will be the base64 encoded.

    """
    file_hash = hashlib.md5()
    read_size = 1024 * 10_000_000  # 10mb - number of bytes in each read operation
    with open(file_path, "rb") as buf:
        # python 3.7 compatable version of `while chunk := buf.read(read_size):`
        chunk = buf.read(read_size)  # seed chunk with initial value
        while chunk:
            file_hash.update(chunk)
            chunk = buf.read(read_size)  # read in new chunk
    return base64.b64encode(file_hash.digest()).decode()


class DeploymentPackage(Generic[_ProjectTypeVar]):
    """AWS Lambda Deployment Package.

    Attributes:
        project: Project that is being built into a deployment package.

    """

    project: _ProjectTypeVar

    def __init__(self, project: _ProjectTypeVar) -> None:
        """Instantiate class.

        Args:
            project: Project that is being built into a deployment package.

        """
        self.project = project

    @cached_property
    def archive_file(self) -> Path:
        """Path to archive file."""
        return (
            self.project.build_directory
            / f"{self.project.args.function_name}.{self.project.source_code.md5_hash}.zip"
        )

    @cached_property
    def bucket(self) -> Bucket:
        """AWS S3 bucket where deployment package will be uploaded."""
        bucket = Bucket(self.project.ctx, self.project.args.bucket_name)
        if bucket.forbidden:
            raise BucketAccessDenied(bucket)
        if bucket.not_found:
            raise BucketNotFound(bucket)
        return bucket

    @cached_property
    def code_sha256(self) -> str:
        """SHA256 of the archive file.

        Returns:
            Value to pass to CloudFormation ``AWS::Lambda::Version.CodeSha256``.

        Raises:
            FileNotFoundError: Property accessed before archive file has been built.

        """
        return calculate_lambda_code_sha256(self.archive_file)

    @cached_property
    def gitignore_filter(  # pylint: disable=no-self-use
        self,
    ) -> Optional[igittigitt.IgnoreParser]:
        """Filter to use when zipping dependencies.

        This should be overridden by subclasses if a filter should be used.

        """
        return None

    @cached_property
    def md5_checksum(self) -> str:
        """MD5 of the archive file.

        Returns:
            Value to pass as ContentMD5 when uploading to AWS S3.

        Raises:
            FileNotFoundError: Property accessed before archive file has been built.

        """
        return calculate_s3_content_md5(self.archive_file)

    @cached_property
    def object_key(self) -> str:
        """Key to use when upload object to AWS S3."""
        prefix = "awslambda/functions"
        if self.project.args.object_prefix:
            prefix = (
                f"{prefix}/{self.project.args.object_prefix.lstrip('/').rstrip('/')}"
            )
        return f"{prefix}/{self.archive_file.name}"

    def build(self) -> Path:
        """Build the deployment package."""
        with zipfile.ZipFile(
            self.archive_file, "w", zipfile.ZIP_DEFLATED
        ) as archive_file:
            self._build_zip_dependencies(archive_file)

            # for file_info in archive_file.filelist:
            #     LOGGER.info(file_info)

        # clear cached properties so they can recalculate;
        # handles cached property not being resolved yet
        with suppress(AttributeError):
            del self.code_sha256
        with suppress(AttributeError):
            del self.md5_checksum
        return self.archive_file

    @overload
    def build_tag_set(self, *, url_encoded: Literal[True] = ...) -> str:
        ...

    @overload
    def build_tag_set(self, *, url_encoded: Literal[False] = ...) -> Dict[str, str]:
        ...

    def build_tag_set(self, *, url_encoded: bool = True) -> Union[Dict[str, str], str]:
        """Build tag set to be applied to the S3 object.

        Args:
            url_encoded: Whether to return a dict or URL encoded query string.

        """
        metadata = {
            "runway.cfngin:awslambda.code_sha256": self.code_sha256,
            "runway.cfngin:awslambda.source_code.hash": self.project.source_code.md5_hash,
            "runway.cfngin:awslambda.md5_checksum": self.md5_checksum,
        }
        tags = {**self.project.ctx.tags, **self.project.args.tags, **metadata}
        if url_encoded:
            return urlencode(tags)
        return tags

    def _build_zip_dependencies(self, archive_file: zipfile.ZipFile) -> None:
        """Handle zipping dependencies.

        Args:
            archive_file: Archive file that is currently open and ready to be
                written to.

        """
        for dep in self.iterate_dependency_directory():
            archive_file.write(dep, dep.relative_to(self.project.dependency_directory))

    def iterate_dependency_directory(self) -> Iterator[Path]:
        """Iterate over the contents of the dependency directory.

        If ``gitignore_filter`` is set, it will be used to exclude files.

        """
        for child in self.project.dependency_directory.rglob("*"):
            if child.is_dir():
                continue  # ignore directories
            if self.gitignore_filter and self.gitignore_filter.match(child):
                continue  # ignore files that match the filter
            yield child

    def upload(self, *, build: bool = True) -> None:
        """Upload deployment package.

        Args:
            build: If true, the deployment package will be built before before
                trying to upload it. If false, it must have already been built.

        """
        if build:
            self.build()

        # we don't really need encoding - it can be NoneType so throw it away
        content_type, _content_encoding = mimetypes.guess_type(self.archive_file)

        LOGGER.info(
            "uploading deployment package %s...",
            self.bucket.format_bucket_path_uri(key=self.object_key),
        )

        self.bucket.client.put_object(
            Body=self.archive_file.read_bytes(),
            Bucket=self.project.args.bucket_name,
            ContentMD5=self.md5_checksum,
            ContentType=content_type,
            Key=self.object_key,
            Tagging=self.build_tag_set(),
        )


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
            context: CFNgin context object.

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
        return None

    def _build_response_deploy(self) -> AwsLambdaHookDeployResponse:
        """Build response for deploy stage."""
        return AwsLambdaHookDeployResponse(
            bucket_name=self.deployment_package.bucket.name,
            code_sha256=self.deployment_package.code_sha256,
            object_key=self.deployment_package.object_key,
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
    def project(self) -> _ProjectTypeVar:
        """Project being deployed as an AWS Lambda Function."""
        raise NotImplementedError


class LayerHook(AwsLambdaHook[_ProjectTypeVar]):
    """Hook used in the create of an AWS Lambda Layer."""

    @cached_property
    def project(self) -> _ProjectTypeVar:
        """Project being deployed as an AWS Lambda Function."""
        raise NotImplementedError
