"""Argument data models."""
# pylint: disable=no-self-argument,no-self-use
from __future__ import annotations

import sys
from pathlib import Path
from typing import List, Optional

from pydantic import DirectoryPath, Extra, FilePath, validator
from runway.cfngin.hooks.base import HookArgsBaseModel
from runway.utils import BaseModel


class DockerOptions(BaseModel):
    """Docker options."""

    disabled: bool = False
    """Explicitly disable the use of docker (default ``False``).

    If not disabled and Docker is unreachable, the hook will result in an error.

    .. rubric:: Example
    .. code-block:: yaml

        args:
          docker:
            disabled: true

    """

    file: Optional[FilePath] = None  # TODO resolve path
    """Dockerfile to use to build an image for use in this process.

    This, ``image`` , or ``runtime`` must be provided.
    If not provided, ``image`` will be used.

    .. rubric:: Example
    .. code-block:: yaml

        args:
          docker:
            file: Dockerfile

    """

    image: Optional[str] = None
    """Docker image to use. If the image does not exist locally, it will be pulled.

    This, ``file`` (takes precedence), or ``runtime`` must be provided.
    If only ``runtime`` is provided, it will be used to determine the appropriate
    image to use.

    .. rubric:: Example
    .. code-block:: yaml

        args:
          docker:
            image: public.ecr.aws/sam/build-python3.9:latest

    """

    pull: bool = True
    """Always download updates to the specified image before use.
    When building an image, the ``FROM`` image will be updated during the build
    process  (default ``True``).

    .. rubric:: Example
    .. code-block:: yaml

        args:
          docker:
            pull: false

    """

    class Config:
        """Model configuration."""

        extra = Extra.ignore


class AwsLambdaHookArgs(HookArgsBaseModel):
    """Base class for AWS Lambda hook arguments."""

    bucket_name: str
    """Name of the S3 Bucket where deployment package is/will  be stored.
    The Bucket must be in the same region the Lambda Function is being deployed in."""

    cache_dir: Optional[DirectoryPath] = None  # TODO resolve path
    """Explicitly define the directory location.
    Must be an absolute path or it will be relative to the CFNgin module directory."""

    docker: DockerOptions = DockerOptions()
    """Docker options."""

    extend_gitignore: List[str] = []
    """gitignore rules that should be added to the rules already defined in a
    ``.gitignore`` file in the source code directory.
    This can be used with or without an existing file.
    Files that match a gitignore rule will not be included in the deployment package.

    .. rubric:: Example
    .. code-block:: yaml

        args:
          extend_gitignore:
            - cfngin.yml
            - poetry.lock
            - poetry.toml
            - pyproject.toml

    """

    object_prefix: Optional[str] = None
    """Prefix to add to the S3 Object key."""

    runtime: str
    """Runtime of the Lambda Function."""

    source_code: DirectoryPath
    """Path to the Lambda Function source code."""

    use_cache: bool = True
    """Whether to use a cache directory with pip that will persist builds (default ``True``)."""

    @validator("source_code", allow_reuse=True)
    def _resolve_path(cls, v: Path) -> Path:
        return v.resolve()


class PythonFunctionHookArgs(AwsLambdaHookArgs):
    """Hook arguments for a Python function."""

    extend_pip_args: Optional[List[str]] = None
    """Additional arguments that should be passed to pip."""

    # TODO factor docker image into runtime
    # TODO get runtime from custom image
    runtime: str = f"python{sys.version_info.major}.{sys.version_info.minor}"
    """Runtime of the Lambda Function.
    The value must be a Python runtime supported by AWS Lambda
    (https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html)."""

    use_pipenv: bool = True
    """Whether pipenv should be used if determined appropriate."""

    use_poetry: bool = True
    """Whether poetry should be used if determined appropriate."""

    class Config:
        """Model configuration."""

        extra = Extra.ignore
