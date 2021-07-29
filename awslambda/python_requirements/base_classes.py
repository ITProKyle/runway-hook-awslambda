"""Base classes."""
from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

from runway.compat import cached_property

from ..base_classes import Project
from ..models.args import PythonFunctionHookArgs
from .dependency_managers.base_classes import PythonDependencyManager

if TYPE_CHECKING:
    from pathlib import Path


_PythonDependencyManagerTypeVar = TypeVar(
    "_PythonDependencyManagerTypeVar", bound=PythonDependencyManager, covariant=True
)


class PythonProject(Project[PythonFunctionHookArgs, _PythonDependencyManagerTypeVar]):
    """Python project containing source code for an AWS Lambda Function."""

    @cached_property
    def dependency_manager(self) -> _PythonDependencyManagerTypeVar:
        """Determine and return the dependency manager to use."""
        raise NotImplementedError

    @classmethod
    def is_project(cls, source_code_path: Path) -> bool:
        """Determine if source code is a poetry project.

        Args:
            source_code_path: Path to the source code of the project.

        """
        raise NotImplementedError
