"""Docker logic for the awslambda hook."""
from __future__ import annotations

import logging
import os
import shlex
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Generic,
    Iterator,
    List,
    Optional,
    TypeVar,
    Union,
)

from docker import DockerClient
from docker.errors import ImageNotFound
from docker.models.images import Image
from docker.types import Mount
from runway._logging import PrefixAdaptor
from runway.compat import cached_property

from .constants import AWS_SAM_BUILD_IMAGE_PREFIX

if TYPE_CHECKING:
    from runway.context import CfnginContext, RunwayContext

    from awslambda.base_classes import Project
    from awslambda.models.args import AwsLambdaHookArgs

LOGGER = logging.getLogger(f"runway.{__name__}")

_ProjectTypeVar = TypeVar("_ProjectTypeVar", bound="Project[AwsLambdaHookArgs]")

# TODO set minimum version of docker SDK to solidify types
#    >= 3.0.0 for docker.images.build return type
# TODO determine image from runtime
#     https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-image-repositories.html
# TODO determine if we need to pin `packaging` https://github.com/pypa/packaging


class DockerDependencyInstaller(Generic[_ProjectTypeVar]):
    """Docker dependency installer."""

    def __init__(
        self,
        context: Union[CfnginContext, RunwayContext],
        project: _ProjectTypeVar,
        *,
        client: Optional[DockerClient] = None,
    ) -> None:
        """Instantiate class.

        Args:
            context: CFNgin or Runway context object.
            project: awslambda project.
            client: Pre-configured :class:`docker.client.DockerClient`.

        """
        self._docker_logger = PrefixAdaptor("docker", LOGGER, "[{prefix}] {msg}")
        self.client = client or DockerClient.from_env(environment=context.env.vars)
        self.ctx = context
        self.options = project.args.docker
        self.project = project

    @cached_property
    def bind_mounts(self) -> List[Mount]:
        """Bind mounts that will be used by the container."""
        return [
            Mount(
                target="/var/task/lambda",
                source=str(self.project.dependency_directory),
                type="bind",
            ),
            Mount(
                target="/var/task/project",
                source=str(self.project.project_root),
                type="bind",
            ),
        ]

    @cached_property
    def install_commands(self) -> List[str]:
        """Commands to run to install dependencies."""
        return []

    @cached_property
    def environmet_variables(self) -> Dict[str, str]:
        """Environment variables to pass to the docker container.

        This is a subset of the environment variables stored in the context
        object as some will cause issues if they are passed.

        """
        return {k: v for k, v in self.ctx.env.vars.items() if k.startswith("DOCKER")}

    @cached_property
    def image(self) -> Union[Image, str]:
        """Docker image that will be used."""

        def _get_image(image_name: str) -> Image:
            try:
                if not self.options.pull:
                    return self.client.images.get(image_name)
                LOGGER.info("pulling docker image %s...", image_name)
            except ImageNotFound:
                LOGGER.info("image not found; pulling docker image %s...", image_name)
            return self.client.images.pull(repository=image_name)

        if self.options.file:
            image, log_stream = self.client.images.build(
                dockerfile=self.options.file.name,
                forcerm=True,
                path=str(self.options.file.parent),
                pull=self.options.pull,
            )
            self.log_docker_msg_dict(log_stream)
            image.tag("runway.cfngin.hooks.awslambda", tag="latest")
            image.reload()
            LOGGER.info("built docker image %s (%s)", ", ".join(image.tags), image.id)
            return image
        if self.options.image:
            return _get_image(self.options.image)
        if self.project.args.runtime:
            return _get_image(
                f"{AWS_SAM_BUILD_IMAGE_PREFIX}{self.project.args.runtime}:latest"
            )
        raise ValueError("docker.file, docker.image, or runtime required")

    @cached_property
    def post_install_commands(self) -> List[str]:
        """Commands to run after dependencies have been installed."""
        return [
            shlex.join(  # TODO test on windows
                ["chown", "-R", f"{os.getuid()}:{os.getgid()}", "/var/task/lambda"]
            )
        ]

    @cached_property
    def runtime(self) -> Optional[str]:
        """AWS Lambda runtime determined from the docker container."""
        return None

    def log_docker_msg_bytes(
        self, stream: Iterator[bytes], *, level: int = logging.INFO
    ) -> List[str]:
        """Log docker output message from blocking generator that return bytes.

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
        """Log docker output message from blocking generator that return dict.

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
        """Install dependencies using docker.

        Commands are run as they are defined in the following cached properties:

        - ``install_commands``
        - ``post_install_commands``

        """
        for cmd in self.install_commands:
            self.run_command(cmd)
        for cmd in self.post_install_commands:
            self.run_command(cmd)

    def run_command(self, command: str, *, level: int = logging.INFO) -> List[str]:
        """Execute equivalent of ``docker container run``.

        Args:
            command: Command to be run.
            level: Log level to use when logging messages.

        Returns:
            List of log messages.

        """
        LOGGER.debug("running command with docker: %s", command)
        container = self.client.containers.create(
            command=command,
            detach=True,
            environment=self.environmet_variables,
            image=self.image,
            mounts=self.bind_mounts,
            working_dir=str(self.project.project_root),
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
                    f"docker container exited with non-zero exit code {exit_code}",
                )
