"""Argument data models."""
# pylint: disable=no-self-argument,no-self-use
from __future__ import annotations

import sys
from pathlib import Path
from typing import List, Optional

from pydantic import DirectoryPath, Extra, validator
from runway.cfngin.hooks.base import HookArgsBaseModel


class AwsLambdaHookArgs(HookArgsBaseModel):
    """Base class for AWS Lambda hook arguments.

    Attributes:
        bucket_name: Name of the S3 Bucket where deployment package is/will
            be stored. The Bucket must be in the same region the Lambda =
            Function is being deployed in.
        extend_gitignore: gitignore rules that should be added to the rules
            already defined in a ``.gitignore`` file in the source code directory.
            This can be used with or without an existing file.
            Files that match a gitignore rule will not be included in the
            deployment package.
        object_prefix: Prefix to add to the S3 Object key.
        runtime: Runtime of the Lambda Function.
        source_code: Path to the Lambda Function source code.

    """

    # docstring & atters must be copied to subclasses for the attributes to be documented

    bucket_name: str
    extend_gitignore: List[str] = []
    object_prefix: Optional[str] = None
    runtime: str
    source_code: DirectoryPath

    @validator("source_code", allow_reuse=True)
    def _resolve_path(cls, v: Path) -> Path:
        return v.resolve()


class PythonFunctionHookArgs(AwsLambdaHookArgs):
    """Hook arguments for a Python function.

    Attributes:
        bucket_name: Name of the S3 Bucket where deployment package is/will
            be stored. The Bucket must be in the same region the Lambda =
            Function is being deployed in.
        extend_gitignore: gitignore rules that should be added to the rules
            already defined in a ``.gitignore`` file in the source code directory.
            This can be used with or without an existing file.
            Files that match a gitignore rule will not be included in the
            deployment package.
        extend_pip_args: Additional arguments that should be passed to pip.
        object_prefix: Prefix to add to the S3 Object key.
        runtime: Runtime of the Lambda Function. The value must be a Python
            runtime supported by AWS Lambda
            (https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html).
        source_code: Path to the Lambda Function source code.
        use_pipenv: Whether pipenv should be used if determined appropriate.
        use_poetry: Whether poetry should be used if determined appropriate.

    """

    bucket_name: str
    extend_gitignore: List[str] = []
    extend_pip_args: Optional[List[str]] = None
    object_prefix: Optional[str] = None
    runtime: str
    runtime: str = f"python{sys.version_info.major}.{sys.version_info.minor}"
    source_code: DirectoryPath
    use_pipenv: bool = True
    use_poetry: bool = True

    class Config:
        """Model configuration."""

        extra = Extra.ignore
