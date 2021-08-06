"""Argument data models."""
# pylint: disable=no-self-argument,no-self-use
from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from pydantic import DirectoryPath, validator
from runway.cfngin.hooks.base import HookArgsBaseModel


class AwsLambdaHookArgs(HookArgsBaseModel):
    """Base class for AWS Lambda hook arguments.

    Attributes:
        bucket_name: Name of the S3 Bucket where deployment package is/will
            be stored.
        extend_gitignore: gitignore rules that should be added to the rules
            already defined in a ``.gitignore`` file in the source code directory.
            This can be used with or without an existing file.
        function_name: Name of the lambda function.
        object_prefix: Prefix to add to the S3 Object key.
        runtime: Runtime of the Lambda Function.
        source_code: Path to the Lambda Function source code.

    """

    bucket_name: str
    extend_gitignore: List[str] = []
    function_name: str
    object_prefix: Optional[str] = None
    runtime: str
    source_code: DirectoryPath

    @validator("source_code")
    def _resolve_path(cls, v: Path) -> Path:
        return v.resolve()


class PythonFunctionHookArgs(AwsLambdaHookArgs):
    """Hook arguments for a Python function.

    Args:
        extend_pip_args: Additional arguments that should be passed to pip.
        use_pipenv: Whether pipenv should be used if determined appropriate.
        use_poetry: Whether poetry should be used if determined appropriate.

    """

    extend_pip_args: Optional[List[str]] = None
    use_pipenv: bool = True
    use_poetry: bool = True