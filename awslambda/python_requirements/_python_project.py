"""Python project."""
from __future__ import annotations

import logging
import shutil
from typing import TYPE_CHECKING, Any, Optional, Union

from runway.cfngin.exceptions import CfnginError
from runway.compat import cached_property

from ..base_classes import Project
from ..constants import BASE_WORK_DIR
from ..models.args import PythonFunctionHookArgs
from .dependency_managers import (
    Pip,
    Poetry,
    PoetryNotFoundError,
    is_pip_project,
    is_poetry_project,
)

if TYPE_CHECKING:
    from pathlib import Path

    from ..source_code import SourceCode

LOGGER = logging.getLogger(f"runway.{__name__}")


class PythonRequirementsNotFoundError(CfnginError):
    """Python requirements file not found.

    A python requirements file (e.g. ``requirements.txt``, ``pyproject.toml``)
    is required.

    """

    def __init__(
        self, source_code: Union[Path, SourceCode, str], *args: Any, **kwargs: Any
    ) -> None:
        """Instantiace class.

        Args:
            source_code: Source code that was checked for a python requirements
                file.

        """
        self.message = (
            f"{source_code} does not contain a requirements file "
            "(e.g. requirements.txt, pyproject.toml)"
        )
        super().__init__()


class PythonProject(Project[PythonFunctionHookArgs]):
    """Python project."""

    @cached_property
    def pip(self) -> Pip:
        """Pip dependency manager."""
        return Pip(self.ctx, self.source_code)

    @cached_property
    def poetry(self) -> Optional[Poetry]:
        """Poetry dependency manager.

        Return:
            If the project uses poetry and poetry is not explicitly disabled,
            an object for interfacing with poetry will be returned.

        Raises:
            PoetryNotFound: poetry is not installed or not found in PATH.

        """
        if not is_poetry_project(self.source_code):
            return None
        if not self.args.use_poetry:
            LOGGER.warning("poetry project detected but use of poetry is disabled")
            return None
        if not Poetry.found_in_path():
            raise PoetryNotFoundError
        return Poetry(self.ctx, self.source_code)

    @cached_property
    def requirements_txt(self) -> Path:
        """Dependency file for the project."""
        if self.poetry:
            return self.poetry.export(output=self.tmp_requirements_txt)
        requirements_txt = self.source_code / "requirements.txt"
        if is_pip_project(self.source_code, file_name=requirements_txt.name):
            return requirements_txt
        raise PythonRequirementsNotFoundError(self.source_code)

    @cached_property
    def tmp_requirements_txt(self) -> Path:
        """Temporary requirements.txt file.

        This path is only used when exporting from another format.

        """
        return BASE_WORK_DIR / f"{self.source_code.md5_hash}.requirements.txt"

    def cleanup(self) -> None:
        """Cleanup temporary files after the build process has run."""
        if self.poetry and self.tmp_requirements_txt.exists():
            self.tmp_requirements_txt.unlink()
        shutil.rmtree(self.dependency_directory, ignore_errors=True)

    def install_dependencies(self) -> None:
        """Install project dependencies."""
        LOGGER.debug("installing dependencies to %s...", self.dependency_directory)
        self.pip.install(
            requirements=self.requirements_txt,
            target=self.dependency_directory,
        )
        LOGGER.debug(
            "dependencies successfully installed to %s", self.dependency_directory
        )
