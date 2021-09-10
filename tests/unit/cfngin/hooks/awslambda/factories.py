"""Factories and other classes."""
from __future__ import annotations

from typing import TYPE_CHECKING

from mock import Mock
from runway.compat import cached_property

from awslambda.base_classes import Project
from awslambda.models.args import AwsLambdaHookArgs

if TYPE_CHECKING:
    from pathlib import Path


class MockProject(Project[AwsLambdaHookArgs]):
    """Mock Project."""

    @cached_property
    def build_directory(self) -> Path:
        """Directory being used to build deployment package."""
        result = (
            self.args.source_code
            / f"{self.args.function_name}.{self.source_code.md5_hash}"
        )
        result.mkdir(exist_ok=True, parents=True)
        return result

    install_dependencies = Mock(return_value=None)