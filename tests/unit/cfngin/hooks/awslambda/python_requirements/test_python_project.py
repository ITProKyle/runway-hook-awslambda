"""Test runway.cfngin.hooks.awslambda.python_requirements._python_project."""
# pylint: disable=no-self-use,protected-access
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pytest
from mock import Mock

from awslambda.python_requirements._python_project import (
    PythonProject,
    PythonRequirementsNotFoundError,
)
from awslambda.python_requirements.dependency_managers._pip import PipInstallFailedError
from awslambda.python_requirements.dependency_managers._pipenv import (
    PipenvNotFoundError,
)
from awslambda.python_requirements.dependency_managers._poetry import (
    PoetryNotFoundError,
)

if TYPE_CHECKING:
    from pathlib import Path

    from pytest import LogCaptureFixture
    from pytest_mock import MockerFixture


MODULE = "awslambda.python_requirements._python_project"


class TestPythonProject:
    """Test PythonProject."""

    @pytest.mark.parametrize(
        "file_exists, pipenv_value, poetry_value",
        [
            (False, False, False),
            (False, False, True),
            (False, True, True),
            (False, True, False),
            (True, False, False),
            (True, False, True),
            (True, True, True),
        ],
    )
    def test_cleanup(
        self,
        file_exists: bool,
        mocker: MockerFixture,
        pipenv_value: bool,
        poetry_value: bool,
    ) -> None:
        """Test cleanup."""
        dependency_directory = mocker.patch.object(
            PythonProject, "dependency_directory", "dependency_directory"
        )
        mock_rmtree = mocker.patch("shutil.rmtree")
        tmp_requirements_txt = mocker.patch.object(
            PythonProject,
            "tmp_requirements_txt",
            Mock(exists=Mock(return_value=file_exists)),
        )
        mocker.patch.object(PythonProject, "pipenv", pipenv_value)
        mocker.patch.object(PythonProject, "poetry", poetry_value)

        assert not PythonProject(Mock(), Mock()).cleanup()
        if pipenv_value or poetry_value:
            tmp_requirements_txt.exists.assert_called_once_with()
        else:
            tmp_requirements_txt.exists.assert_not_called()
        if (
            max([sum([file_exists, pipenv_value]), sum([file_exists, poetry_value])])
            == 2
        ):
            tmp_requirements_txt.unlink.assert_called_once_with()
        else:
            tmp_requirements_txt.unlink.assert_not_called()
        mock_rmtree.assert_called_once_with(dependency_directory, ignore_errors=True)

    def test_install_dependencies(self, mocker: MockerFixture) -> None:
        """Test install_dependencies."""
        dependency_directory = mocker.patch.object(
            PythonProject, "dependency_directory", "dependency_directory"
        )
        mock_pip = mocker.patch.object(PythonProject, "pip", Mock())
        requirements_txt = mocker.patch.object(
            PythonProject, "requirements_txt", "requirements_txt"
        )
        assert not PythonProject(Mock(), Mock()).install_dependencies()
        mock_pip.install.assert_called_once_with(
            requirements=requirements_txt, target=dependency_directory
        )

    def test_install_dependencies_does_not_catch_errors(
        self, mocker: MockerFixture
    ) -> None:
        """Test install_dependencies does not catch errors."""
        dependency_directory = mocker.patch.object(
            PythonProject, "dependency_directory", "dependency_directory"
        )
        mock_pip = mocker.patch.object(
            PythonProject, "pip", Mock(install=Mock(side_effect=PipInstallFailedError))
        )
        requirements_txt = mocker.patch.object(
            PythonProject, "requirements_txt", "requirements_txt"
        )
        with pytest.raises(PipInstallFailedError):
            assert not PythonProject(Mock(), Mock()).install_dependencies()
        mock_pip.install.assert_called_once_with(
            requirements=requirements_txt, target=dependency_directory
        )

    def test_pip(self, mocker: MockerFixture) -> None:
        """Test pip."""
        ctx = Mock()
        pip_class = mocker.patch(f"{MODULE}.Pip", return_value="Pip")
        source_code = mocker.patch.object(PythonProject, "source_code")
        assert PythonProject(Mock(), ctx).pip == pip_class.return_value
        pip_class.assert_called_once_with(ctx, source_code)

    def test_pipenv(self, mocker: MockerFixture) -> None:
        """Test pipenv."""
        ctx = Mock()
        mock_is_pipenv_project = mocker.patch(
            f"{MODULE}.is_pipenv_project", return_value=True
        )
        pipenv_class = mocker.patch(
            f"{MODULE}.Pipenv",
            Mock(found_in_path=Mock(return_value=True), return_value="Pipenv"),
        )
        source_code = mocker.patch.object(PythonProject, "source_code")
        mocker.patch.object(PythonProject, "poetry", None)
        assert (
            PythonProject(Mock(use_poetry=True), ctx).pipenv
            == pipenv_class.return_value
        )
        mock_is_pipenv_project.assert_called_once_with(source_code)
        pipenv_class.found_in_path.assert_called_once_with()
        pipenv_class.assert_called_once_with(ctx, source_code)

    def test_pipenv_explicit_disable(
        self, caplog: LogCaptureFixture, mocker: MockerFixture
    ) -> None:
        """Test pipenv project but pipenv is explicitly disabled."""
        caplog.set_level(logging.WARNING)
        mock_is_pipenv_project = mocker.patch(
            f"{MODULE}.is_pipenv_project", return_value=True
        )
        source_code = mocker.patch.object(PythonProject, "source_code")
        mocker.patch.object(PythonProject, "poetry", None)
        assert not PythonProject(Mock(use_pipenv=False), Mock()).pipenv
        mock_is_pipenv_project.assert_called_once_with(source_code)
        assert (
            "pipenv project detected but use of pipenv is explicitly disabled"
            in caplog.messages
        )

    def test_pipenv_not_in_path(self, mocker: MockerFixture) -> None:
        """Test pipenv not in path."""
        mock_is_pipenv_project = mocker.patch(
            f"{MODULE}.is_pipenv_project", return_value=True
        )
        pipenv_class = mocker.patch(
            f"{MODULE}.Pipenv",
            Mock(found_in_path=Mock(return_value=False)),
        )
        source_code = mocker.patch.object(PythonProject, "source_code")
        mocker.patch.object(PythonProject, "poetry", None)
        with pytest.raises(PipenvNotFoundError):
            assert PythonProject(Mock(use_pipenv=True), Mock()).pipenv
        mock_is_pipenv_project.assert_called_once_with(source_code)
        pipenv_class.found_in_path.assert_called_once_with()

    def test_pipenv_not_poetry_pipenv(self, mocker: MockerFixture) -> None:
        """Test pipenv project is not a pipenv project."""
        mock_is_pipenv_project = mocker.patch(
            f"{MODULE}.is_pipenv_project", return_value=False
        )
        source_code = mocker.patch.object(PythonProject, "source_code")
        mocker.patch.object(PythonProject, "poetry", None)
        assert not PythonProject(Mock(use_pipenv=True), Mock()).pipenv
        mock_is_pipenv_project.assert_called_once_with(source_code)

    def test_poetry(self, mocker: MockerFixture) -> None:
        """Test poetry."""
        ctx = Mock()
        mock_is_poetry_project = mocker.patch(
            f"{MODULE}.is_poetry_project", return_value=True
        )
        poetry_class = mocker.patch(
            f"{MODULE}.Poetry",
            Mock(found_in_path=Mock(return_value=True), return_value="Poetry"),
        )
        source_code = mocker.patch.object(PythonProject, "source_code")
        mocker.patch.object(PythonProject, "pipenv", None)
        assert (
            PythonProject(Mock(use_poetry=True), ctx).poetry
            == poetry_class.return_value
        )
        mock_is_poetry_project.assert_called_once_with(source_code)
        poetry_class.found_in_path.assert_called_once_with()
        poetry_class.assert_called_once_with(ctx, source_code)

    def test_poetry_explicit_disable(
        self, caplog: LogCaptureFixture, mocker: MockerFixture
    ) -> None:
        """Test poetry project but poetry is explicitly disabled."""
        caplog.set_level(logging.WARNING)
        mock_is_poetry_project = mocker.patch(
            f"{MODULE}.is_poetry_project", return_value=True
        )
        source_code = mocker.patch.object(PythonProject, "source_code")
        mocker.patch.object(PythonProject, "pipenv", None)
        assert not PythonProject(Mock(use_poetry=False), Mock()).poetry
        mock_is_poetry_project.assert_called_once_with(source_code)
        assert (
            "poetry project detected but use of poetry is explicitly disabled"
            in caplog.messages
        )

    def test_poetry_not_in_path(self, mocker: MockerFixture) -> None:
        """Test poetry not in path."""
        mock_is_poetry_project = mocker.patch(
            f"{MODULE}.is_poetry_project", return_value=True
        )
        poetry_class = mocker.patch(
            f"{MODULE}.Poetry",
            Mock(found_in_path=Mock(return_value=False)),
        )
        source_code = mocker.patch.object(PythonProject, "source_code")
        mocker.patch.object(PythonProject, "pipenv", None)
        with pytest.raises(PoetryNotFoundError):
            assert PythonProject(Mock(use_poetry=True), Mock()).poetry
        mock_is_poetry_project.assert_called_once_with(source_code)
        poetry_class.found_in_path.assert_called_once_with()

    def test_poetry_not_poetry_project(self, mocker: MockerFixture) -> None:
        """Test poetry project is not a poetry project."""
        mock_is_poetry_project = mocker.patch(
            f"{MODULE}.is_poetry_project", return_value=False
        )
        source_code = mocker.patch.object(PythonProject, "source_code")
        mocker.patch.object(PythonProject, "pipenv", None)
        assert not PythonProject(Mock(use_poetry=True), Mock()).poetry
        mock_is_poetry_project.assert_called_once_with(source_code)

    def test_requirements_txt(self, mocker: MockerFixture, tmp_path: Path) -> None:
        """Test requirements_txt."""
        expected = tmp_path / "requirements.txt"
        expected.touch()
        mock_is_pip_project = mocker.patch(
            f"{MODULE}.is_pip_project", return_value=True
        )
        mocker.patch.object(PythonProject, "pipenv", None)
        mocker.patch.object(PythonProject, "poetry", None)
        mocker.patch.object(PythonProject, "source_code", tmp_path)
        assert PythonProject(Mock(), Mock()).requirements_txt == expected
        mock_is_pip_project.assert_called_once_with(tmp_path, file_name=expected.name)

    def test_requirements_txt_pipenv(self, mocker: MockerFixture) -> None:
        """Test requirements_txt."""
        expected = "foo.txt"
        pipenv = mocker.patch.object(
            PythonProject, "pipenv", Mock(export=Mock(return_value=expected))
        )
        tmp_requirements_txt = mocker.patch.object(
            PythonProject, "tmp_requirements_txt", "tmp_requirements_txt"
        )
        mocker.patch.object(PythonProject, "poetry", None)
        mocker.patch.object(PythonProject, "source_code")
        assert PythonProject(Mock(), Mock()).requirements_txt == expected
        pipenv.export.assert_called_once_with(output=tmp_requirements_txt)

    def test_requirements_txt_poetry(self, mocker: MockerFixture) -> None:
        """Test requirements_txt."""
        expected = "foo.txt"
        poetry = mocker.patch.object(
            PythonProject, "poetry", Mock(export=Mock(return_value=expected))
        )
        tmp_requirements_txt = mocker.patch.object(
            PythonProject, "tmp_requirements_txt", "tmp_requirements_txt"
        )
        mocker.patch.object(PythonProject, "pipenv", None)
        mocker.patch.object(PythonProject, "source_code")
        assert PythonProject(Mock(), Mock()).requirements_txt == expected
        poetry.export.assert_called_once_with(output=tmp_requirements_txt)

    def test_requirements_txt_raise_python_requirements_not_found(
        self, mocker: MockerFixture, tmp_path: Path
    ) -> None:
        """Test requirements_txt raise PythonRequirementsNotFoundError."""
        mock_is_pip_project = mocker.patch(
            f"{MODULE}.is_pip_project", return_value=False
        )
        mocker.patch.object(PythonProject, "pipenv", None)
        mocker.patch.object(PythonProject, "poetry", None)
        mocker.patch.object(PythonProject, "source_code", tmp_path)
        with pytest.raises(PythonRequirementsNotFoundError) as excinfo:
            assert PythonProject(Mock(), Mock()).requirements_txt
        mock_is_pip_project.assert_called_once_with(
            tmp_path, file_name="requirements.txt"
        )
        assert (
            f"{tmp_path} does not contain a requirements file" in excinfo.value.message
        )

    def test_tmp_requirements_txt(self, mocker: MockerFixture, tmp_path: Path) -> None:
        """Test tmp_requirements_txt."""
        mocker.patch(f"{MODULE}.BASE_WORK_DIR", tmp_path)
        source_code = mocker.patch.object(
            PythonProject, "source_code", Mock(md5_hash="hash")
        )
        assert (
            PythonProject(Mock(), Mock()).tmp_requirements_txt
            == tmp_path / f"{source_code.md5_hash}.requirements.txt"
        )
