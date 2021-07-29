"""Argument data models."""
# pylint: disable=no-self-argument,no-self-use
from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from pydantic import DirectoryPath, validator
from runway.cfngin.hooks.base import HookArgsBaseModel


class AwsLambdaHookArgs(HookArgsBaseModel):
    """Base class for AWS Lambda hook arguments."""

    bucket_name: str  # s3 bucket to store zip
    extend_gitignore: List[str] = []  # add more filter rules
    function_name: str  # name of function (arbitrary - internal use)
    object_prefix: Optional[str] = None  # prefix to append zip
    runtime: str  # lambda function runtime
    source_code: DirectoryPath  # path to source code

    @validator("source_code")
    def _resolve_path(cls, v: Path) -> Path:
        return v.resolve()


class PythonFunctionHookArgs(AwsLambdaHookArgs):
    """Hook arguments for a Python function."""

    extend_pip_args: Optional[List[str]] = None  # extra args to pass to pip command
    use_pipenv: bool = True  # explicitly disable the use of pipenv
    use_poetry: bool = True  # explicitly disable the use of poetry
