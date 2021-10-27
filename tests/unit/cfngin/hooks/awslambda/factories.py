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
            self.source_code
            / self.runtime
            / f"{self.source_code.root_directory.name}.{self.source_code.md5_hash}"
        )
        result.mkdir(exist_ok=True, parents=True)
        return result

    @cached_property
    def runtime(self) -> str:
        """Runtime of the build system."""
        return self.args.runtime or "foo0.0"

    @cached_property
    def project_root(self) -> Path:
        """Root directory of the project."""
        return self.args.source_code

    @cached_property
    def project_type(self) -> str:
        """Type of project (e.g. poetry, yarn)."""
        return "mock"

    install_dependencies = Mock(return_value=None)
