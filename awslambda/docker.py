"""Docker logic for the awslambda hook."""
from __future__ import annotations

import logging
import os
import platform
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    Dict,
    Iterator,
    List,
    Optional,
    Type,
    TypeVar,
    Union,
    cast,
)

from docker import DockerClient
from docker.errors import DockerException, ImageNotFound
from docker.models.images import Image
from docker.types import Mount
from runway._logging import PrefixAdaptor
from runway.compat import cached_property

from .constants import AWS_SAM_BUILD_IMAGE_PREFIX
from .exceptions import DockerConnectionRefused

if TYPE_CHECKING:
    from pathlib import Path

    from runway._logging import RunwayLogger
    from runway.context import CfnginContext, RunwayContext

    from awslambda.base_classes import Project
    from awslambda.models.args import AwsLambdaHookArgs, DockerOptions

LOGGER = cast("RunwayLogger", logging.getLogger(f"runway.{__name__}"))

DEFAULT_IMAGE_NAME = "runway.cfngin.hooks.awslambda"
DEFAULT_IMAGE_TAG = "latest"

# TODO set minimum version of docker SDK to solidify types
#    >= 3.0.0 for docker.images.build return type
# TODO determine image from runtime
#     https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-image-repositories.html
# TODO determine if we need to pin `packaging` https://github.com/pypa/packaging


_T = TypeVar("_T")


class DockerDependencyInstaller:
    """Docker dependency installer."""

    #: Mount path where dependency managers can cache data.
    CACHE_DIR: ClassVar[str] = "/var/task/cache_dir"
    #: Mount path were dependencies will be installed to within the Docker container.
    #: Other files can be moved to this directory to be included in the deployment package.
    DEPENDENCY_DIR: ClassVar[str] = "/var/task/lambda"
    #: Mount path where the project directory is available within the Docker container.
    PROJECT_DIR: ClassVar[str] = "/var/task/project"

    client: DockerClient  #: Docker client.
    ctx: Union[CfnginContext, RunwayContext]  #: Context object.
    options: DockerOptions  #: Hook arguments specific to Docker.

    def __init__(
        self,
        project: Project[AwsLambdaHookArgs],
        *,
        client: Optional[DockerClient] = None,
        context: Optional[Union[CfnginContext, RunwayContext]] = None,
    ) -> None:
        """Instantiate class.

        This is a low-level method that requires the user to implement error
        handling. It is recommended to use
        :meth:`~awslambda.docker.DockerDependencyInstaller.from_project`
        instead of instantiating this class directly.

        Args:
            project: awslambda project.
            client: Pre-configured :class:`docker.client.DockerClient`.
            context: CFNgin or Runway context object.

        """
        context = context or project.ctx

        self._docker_logger = PrefixAdaptor("docker", LOGGER, "[{prefix}] {msg}")
        self.client = client or DockerClient.from_env(environment=context.env.vars)
        self.ctx = context
        self.options = project.args.docker
        self.project = project

    @cached_property
    def bind_mounts(self) -> List[Mount]:
        """Bind mounts that will be used by the container."""
        mounts = [
            Mount(
                target=self.DEPENDENCY_DIR,
                source=str(self.project.dependency_directory),
                type="bind",
            ),
            Mount(
                target=self.PROJECT_DIR,
                source=str(self.project.project_root),
                type="bind",
            ),
        ]
        if self.project.cache_dir:
            mounts.append(
                Mount(
                    target=self.CACHE_DIR,
                    source=str(self.project.cache_dir),
                    type="bind",
                )
            )
        return mounts

    @cached_property
    def environmet_variables(self) -> Dict[str, str]:
        """Environment variables to pass to the Docker container.

        This is a subset of the environment variables stored in the context
        object as some will cause issues if they are passed.

        """
        return {k: v for k, v in self.ctx.env.vars.items() if k.startswith("DOCKER")}

    @cached_property
    def image(self) -> Union[Image, str]:
        """Docker image that will be used.

        Raises:
            ValueError: Insufficient data to determine the desired Docker image.

        """
        if self.options.file:
            return self.build_image(self.options.file)
        if self.options.image:
            return self.pull_image(self.options.image, force=self.options.pull)
        if self.project.args.runtime:
            return self.pull_image(
                f"{AWS_SAM_BUILD_IMAGE_PREFIX}{self.project.args.runtime}:latest",
                force=self.options.pull,
            )
        raise ValueError("docker.file, docker.image, or runtime required")

    @cached_property
    def install_commands(self) -> List[str]:
        """Commands to run to install dependencies."""
        return []

    @cached_property
    def post_install_commands(self) -> List[str]:
        """Commands to run after dependencies have been installed."""
        cmds = [
            *[
                f'cp -v "{extra_file}" "{self.DEPENDENCY_DIR}"'
                for extra_file in self.options.extra_files
            ],
        ]
        if platform.system() != "Windows":
            # methods only exist on POSIX systems
            gid, uid = os.getgid(), os.getuid()  # pylint: disable=no-member
            cmds.append(
                f"chown -R {uid}:{gid} {self.DEPENDENCY_DIR}",
            )
            if self.project.cache_dir:
                cmds.append(f"chown -R {uid}:{gid} {self.CACHE_DIR}")
        return cmds

    @cached_property
    def pre_install_commands(self) -> List[str]:
        """Commands to run before dependencies have been installed."""
        cmds = [
            f"chown -R 0:0 {self.DEPENDENCY_DIR}",
        ]
        if self.project.cache_dir:
            cmds.append(f"chown -R 0:0 {self.CACHE_DIR}")
        return cmds

    @cached_property
    def runtime(self) -> Optional[str]:
        """AWS Lambda runtime determined from the Docker container."""
        return None

    def build_image(
        self,
        docker_file: Path,
        *,
        name: str = DEFAULT_IMAGE_NAME,
        tag: str = DEFAULT_IMAGE_TAG,
    ) -> Image:
        """Build Docker image from Dockerfile.

        This method is exposed as a low-level interface.
        :attr:`~awslambda.docker.DockerDependencyInstaller.image` should be
        used in place for this for most cases.

        Args:
            docker_file: Path to the Dockerfile to build. This path should be
                absolute, must exist, and must be a file.
            name: Name of the Docker image. The name should not contain a tag.
            tag: Tag to apply to the image after it is built.

        Returns:
            Object representing the image that was built.

        """
        image, log_stream = self.client.images.build(
            dockerfile=docker_file.name,
            forcerm=True,
            path=str(docker_file.parent),
            pull=self.options.pull,
        )
        self.log_docker_msg_dict(log_stream)
        image.tag(name, tag=tag)
        image.reload()
        LOGGER.info("built docker image %s (%s)", ", ".join(image.tags), image.id)
        return image

    def log_docker_msg_bytes(
        self, stream: Iterator[bytes], *, level: int = logging.INFO
    ) -> List[str]:
        """Log Docker output message from blocking generator that return bytes.

        Args:
            stream: Blocking generator that returns log messages as bytes.
            level: Log level to use when logging messages.

        Returns:
            List of log messages.

        """
        result: List[str] = []
        for raw_msg in stream:
            msg = raw_msg.decode().strip()
            result.append(msg)
            self._docker_logger.log(level, msg)
        return result

    def log_docker_msg_dict(
        self, stream: Iterator[Dict[str, Any]], *, level: int = logging.INFO
    ) -> List[str]:
        """Log Docker output message from blocking generator that return dict.

        Args:
            stream: Blocking generator that returns log messages as a dict.
            level: Log level to use when logging messages.

        Returns:
            list of log messages.

        """
        result: List[str] = []
        for raw_msg in stream:
            for key in ["stream", "status"]:
                if key in raw_msg:
                    msg = raw_msg[key].strip()
                    result.append(msg)
                    self._docker_logger.log(level, msg)
                    break
        return result

    def install(self) -> None:
        """Install dependencies using Docker.

        Commands are run as they are defined in the following cached properties:

        - :attr:`~awslambda.docker.DockerDependencyInstaller.pre_install_commands`
        - :attr:`~awslambda.docker.DockerDependencyInstaller.install_commands`
        - :attr:`~awslambda.docker.DockerDependencyInstaller.post_install_commands`

        """
        for cmd in self.pre_install_commands:
            self.run_command(cmd)
        for cmd in self.install_commands:
            self.run_command(cmd)
        for cmd in self.post_install_commands:
            self.run_command(cmd)

    def pull_image(self, name: str, *, force: bool = True) -> Image:
        """Pull a Docker image from a repository if it does not exist locally.

        This method is exposed as a low-level interface.
        :attr:`~awslambda.docker.DockerDependencyInstaller.image` should be
        used in place for this for most cases.

        Args:
            name: Name of the Docker image including tag.
            force: Always pull the image even if it exists locally.
                This will ensure that the latest version is always used.

        Returns:
            Object representing the image found locally or pulled from a repository.

        """
        try:
            if not force:
                return self.client.images.get(name)
            LOGGER.info("pulling docker image %s...", name)
        except ImageNotFound:
            LOGGER.info("image not found; pulling docker image %s...", name)
        return self.client.images.pull(repository=name)

    def run_command(self, command: str, *, level: int = logging.INFO) -> List[str]:
        """Execute equivalent of ``docker container run``.

        Args:
            command: Command to be run.
            level: Log level to use when logging messages.

        Returns:
            List of log messages.

        """
        LOGGER.verbose("running command with docker: %s", command)
        container = self.client.containers.create(
            command=command,
            detach=True,
            environment=self.environmet_variables,
            image=self.image,
            mounts=self.bind_mounts,
            working_dir=self.PROJECT_DIR,
        )
        try:
            container.start()
            return self.log_docker_msg_bytes(
                container.logs(stderr=True, stdout=True, stream=True), level=level
            )
        finally:
            exit_code = container.wait().get("StatusCode", 0)
            container.remove(force=True)  # always remove container
            if exit_code != 0:
                raise RuntimeError(  # TODO make custom error
                    f"Docker container exited with non-zero exit code: {exit_code}",
                )

    @classmethod
    def from_project(
        cls: Type[_T], project: Project[AwsLambdaHookArgs]
    ) -> Optional[_T]:
        """Instantiate class from a project.

        High-level method that wraps instantiation in error handling.

        Args:
            project: Project being processed.

        Returns:
            Object to handle dependency installation with Docker if Docker is
            available and not disabled.

        Raises:
            DockerConnectionRefused: Docker is not install or is unreachable.

        """
        if project.args.docker.disabled:
            return None
        try:
            client = DockerClient.from_env(environment=project.ctx.env.vars)
            if client.ping():
                return cls(project, client=client)
        except DockerException as exc:
            # This might be too broad but, it is the only repeated substring
            # between operating systems in similar states.
            if "Error while fetching server API version" in str(exc):
                raise DockerConnectionRefused from exc  # raise informative error
            raise
        # ping failed but method did not return false for some reason
        raise DockerConnectionRefused