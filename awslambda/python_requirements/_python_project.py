"""Python project."""
from __future__ import annotations

import logging
import shutil
from typing import TYPE_CHECKING, Any, Optional, Set, Tuple, Union

from runway.cfngin.exceptions import CfnginError
from runway.compat import cached_property
from typing_extensions import Literal

from ..base_classes import Project
from ..constants import BASE_WORK_DIR
from ..models.args import PythonFunctionHookArgs
from ._python_docker import PythonDockerDependencyInstaller
from .dependency_managers import (
    Pip,
    Pipenv,
    PipenvNotFoundError,
    Poetry,
    PoetryNotFoundError,
    is_pip_project,
    is_pipenv_project,
    is_poetry_project,
)

if TYPE_CHECKING:
    from pathlib import Path

    from _typeshed import StrPath

    from ..source_code import SourceCode

LOGGER = logging.getLogger(f"runway.{__name__}")


class PythonRequirementsNotFoundError(CfnginError):
    """Python requirements file not found.

    A python requirements file (e.g. ``requirements.txt``, ``pyproject.toml``)
    is required.

    """

    def __init__(
        self, source_code: Union[SourceCode, StrPath], *args: Any, **kwargs: Any
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
    def docker(self) -> Optional[PythonDockerDependencyInstaller]:
        """Docker interface that can be used to build the project."""
        if self.args.docker.disable:
            return None
        # TODO ensure docker is available
        return PythonDockerDependencyInstaller(self.ctx, self)

    @cached_property
    def metadata_files(self) -> Tuple[Path, ...]:
        """Project metadata files.

        Files are only included in return value if they exist.

        """
        if self.project_type == "poetry":
            config_files = [
                self.project_root / config_file for config_file in Poetry.CONFIG_FILES
            ]
        elif self.project_type == "pipenv":
            config_files = [
                self.project_root / config_file for config_file in Pipenv.CONFIG_FILES
            ]
        else:
            config_files = [
                self.project_root / config_file for config_file in Pip.CONFIG_FILES
            ]
        return tuple(path for path in config_files if path.exists())

    @cached_property
    def pip(self) -> Pip:
        """Pip dependency manager."""
        return Pip(self.ctx, self.project_root)

    @cached_property
    def pipenv(self) -> Optional[Pipenv]:
        """Pipenv dependency manager.

        Return:
            If the project uses pipenv and pipenv is not explicitly disabled,
            an object for interfacing with pipenv will be returned.

        Raises:
            PipenvNotFoundError: pipenv is not installed or not found in PATH.

        """
        if self.project_type != "pipenv":
            return None
        if Pipenv.found_in_path():
            return Pipenv(self.ctx, self.project_root)
        raise PipenvNotFoundError

    @cached_property
    def poetry(self) -> Optional[Poetry]:
        """Poetry dependency manager.

        Return:
            If the project uses poetry and poetry is not explicitly disabled,
            an object for interfacing with poetry will be returned.

        Raises:
            PoetryNotFound: poetry is not installed or not found in PATH.

        """
        if self.project_type != "poetry":
            return None
        if Poetry.found_in_path():
            return Poetry(self.ctx, self.project_root)
        raise PoetryNotFoundError

    @cached_property
    def project_type(self) -> Literal["pip", "pipenv", "poetry"]:
        """Type of python project."""
        if is_poetry_project(self.project_root):
            if self.args.use_poetry:
                return "poetry"
            LOGGER.warning(
                "poetry project detected but use of poetry is explicitly disabled"
            )
        if is_pipenv_project(self.project_root):
            if self.args.use_pipenv:
                return "pipenv"
            LOGGER.warning(
                "pipenv project detected but use of pipenv is explicitly disabled"
            )
        return "pip"

    @cached_property
    def requirements_txt(self) -> Path:
        """Dependency file for the project."""
        if self.poetry:  # prioritize poetry
            return self.poetry.export(output=self.tmp_requirements_txt)
        if self.pipenv:
            return self.pipenv.export(output=self.tmp_requirements_txt)
        requirements_txt = self.project_root / "requirements.txt"
        if is_pip_project(self.project_root, file_name=requirements_txt.name):
            return requirements_txt
        raise PythonRequirementsNotFoundError(self.project_root)

    @cached_property
    def runtime(self) -> str:
        """Runtime of the deployment package."""
        return self.args.runtime  # TODO account for docker

    @cached_property
    def supported_metadata_files(self) -> Set[str]:
        """Names of all supported metadata files.

        Returns:
            Set of file names - not paths.

        """
        file_names = {*Pip.CONFIG_FILES}
        if self.args.use_poetry:
            file_names.update(Poetry.CONFIG_FILES)
        if self.args.use_pipenv:
            file_names.update(Pipenv.CONFIG_FILES)
        return file_names

    @cached_property
    def tmp_requirements_txt(self) -> Path:
        """Temporary requirements.txt file.

        This path is only used when exporting from another format.

        """
        return BASE_WORK_DIR / f"{self.source_code.md5_hash}.requirements.txt"

    def cleanup(self) -> None:
        """Cleanup temporary files after the build process has run."""
        if (self.poetry or self.pipenv) and self.tmp_requirements_txt.exists():
            self.tmp_requirements_txt.unlink()
        shutil.rmtree(self.dependency_directory, ignore_errors=True)

    def install_dependencies(self) -> None:
        """Install project dependencies."""
        LOGGER.debug("installing dependencies to %s...", self.dependency_directory)
        if self.docker:
            self.docker.install()
        else:
            self.pip.install(
                requirements=self.requirements_txt,
                target=self.dependency_directory,
            )
        LOGGER.debug(
            "dependencies successfully installed to %s", self.dependency_directory
        )
