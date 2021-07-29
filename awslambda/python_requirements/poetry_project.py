"""Poetry project."""
from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

import tomli
from runway.compat import cached_property

from .base_classes import PythonProject
from .dependency_managers.poetry import Poetry

if TYPE_CHECKING:
    from pathlib import Path


class PoetryProject(PythonProject[Poetry]):
    """Poetry project."""

    @cached_property
    def dependency_manager(self) -> Poetry:
        """Determine and return the dependency manager to use."""
        return Poetry(self.ctx, self.source_code)

    @classmethod
    def is_project(cls, source_code_path: Path) -> bool:
        """Determine if source code is a poetry project.

        Args:
            source_code_path: Path to the source code of the project.

        """
        pyproject_path = source_code_path / "pyproject.toml"

        if not pyproject_path.is_file():
            return False

        pyproject = tomli.loads(pyproject_path.read_text())
        build_system_requires: Optional[List[str]] = pyproject.get(
            "build-system", {}
        ).get("requires")

        if build_system_requires:
            for req in build_system_requires:
                if req.startswith("poetry"):
                    return True
        return False
