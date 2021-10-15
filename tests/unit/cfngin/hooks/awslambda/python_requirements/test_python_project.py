"""Test runway.cfngin.hooks.awslambda.python_requirements._python_project."""
# pylint: disable=no-self-use,protected-access
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, List, Sequence

import pytest
from mock import Mock

from awslambda.python_requirements._python_project import (
    PythonProject,
    PythonRequirementsNotFoundError,
)
from awslambda.python_requirements.dependency_managers._pip import (
    Pip,
    PipInstallFailedError,
)
from awslambda.python_requirements.dependency_managers._pipenv import (
    Pipenv,
    PipenvNotFoundError,
)
from awslambda.python_requirements.dependency_managers._poetry import (
    Poetry,
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

    @pytest.mark.parametrize("disabled", [False, True])
    def test_docker(self, disabled: bool, mocker: MockerFixture) -> None:
        """Test docker."""
        ctx = Mock()
        mock_class = mocker.patch(
            f"{MODULE}.PythonDockerDependencyInstaller", return_value="success"
        )
        obj = PythonProject(Mock(docker=Mock(disable=disabled)), ctx)

        if disabled:
            assert not obj.docker
            mock_class.assert_not_called()
        else:
            assert obj.docker == mock_class.return_value
            mock_class.assert_called_once_with(ctx, obj)

    @pytest.mark.parametrize(
        "pipenv, poetry", [(False, False), (False, True), (True, False), (True, True)]
    )
    def test_install_dependencies(
        self, mocker: MockerFixture, pipenv: bool, poetry: bool
    ) -> None:
        """Test install_dependencies."""
        mocker.patch.object(PythonProject, "pipenv", pipenv)
        mocker.patch.object(PythonProject, "poetry", poetry)
        dependency_directory = mocker.patch.object(
            PythonProject, "dependency_directory", "dependency_directory"
        )
        mock_pip = mocker.patch.object(PythonProject, "pip", Mock())
        requirements_txt = mocker.patch.object(
            PythonProject, "requirements_txt", "requirements_txt"
        )
        assert not PythonProject(
            Mock(cache_dir="foo", use_cache=True), Mock()
        ).install_dependencies()
        mock_pip.install.assert_called_once_with(
            cache_dir="foo",
            no_cache_dir=False,
            no_deps=bool(pipenv or poetry),
            requirements=requirements_txt,
            target=dependency_directory,
        )

    def test_install_dependencies_docker(self, mocker: MockerFixture) -> None:
        """Test install_dependencies using Docker."""
        mock_docker = mocker.patch.object(PythonProject, "docker")
        mock_pip = mocker.patch.object(PythonProject, "pip")
        mocker.patch.object(
            PythonProject, "dependency_directory", "dependency_directory"
        )
        assert not PythonProject(Mock(), Mock()).install_dependencies()
        mock_docker.install.assert_called_once_with()
        mock_pip.assert_not_called()

    def test_install_dependencies_does_not_catch_errors(
        self, mocker: MockerFixture
    ) -> None:
        """Test install_dependencies does not catch errors."""
        mocker.patch.object(PythonProject, "pipenv", False)
        mocker.patch.object(PythonProject, "poetry", False)
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
            assert not PythonProject(
                Mock(cache_dir="foo", use_cache=True), Mock()
            ).install_dependencies()
        mock_pip.install.assert_called_once_with(
            cache_dir="foo",
            no_cache_dir=False,
            no_deps=False,
            requirements=requirements_txt,
            target=dependency_directory,
        )

    @pytest.mark.parametrize(
        "project_type, expected_files",
        [
            ("pip", Pip.CONFIG_FILES),
            ("pipenv", Pipenv.CONFIG_FILES),
            ("pipenv", [Pipenv.CONFIG_FILES[1]]),
            ("poetry", Poetry.CONFIG_FILES),
            ("poetry", [Poetry.CONFIG_FILES[1]]),
        ],
    )
    def test_metadata_files(
        self,
        expected_files: Sequence[str],
        mocker: MockerFixture,
        project_type: str,
        tmp_path: Path,
    ) -> None:
        """Test metadata_files.

        expected_files can be a subset of <class>.CONFIG_FILES to ensure that
        return value only contains files that exist as these files are created.

        """
        expected = tuple(tmp_path / expected_file for expected_file in expected_files)
        for expected_file in expected:
            expected_file.touch()
        mocker.patch.object(PythonProject, "project_root", tmp_path)
        mocker.patch.object(PythonProject, "project_type", project_type)
        assert PythonProject(Mock(), Mock()).metadata_files == expected

    def test_pip(self, mocker: MockerFixture) -> None:
        """Test pip."""
        ctx = Mock()
        pip_class = mocker.patch(f"{MODULE}.Pip", return_value="Pip")
        project_root = mocker.patch.object(PythonProject, "project_root")
        assert PythonProject(Mock(), ctx).pip == pip_class.return_value
        pip_class.assert_called_once_with(ctx, project_root)

    def test_pipenv(self, mocker: MockerFixture) -> None:
        """Test pipenv."""
        ctx = Mock()
        pipenv_class = mocker.patch(
            f"{MODULE}.Pipenv",
            Mock(found_in_path=Mock(return_value=True), return_value="Pipenv"),
        )
        mocker.patch.object(PythonProject, "project_type", "pipenv")
        project_root = mocker.patch.object(PythonProject, "project_root")
        assert (
            PythonProject(Mock(use_poetry=True), ctx).pipenv
            == pipenv_class.return_value
        )
        pipenv_class.found_in_path.assert_called_once_with()
        pipenv_class.assert_called_once_with(ctx, project_root)

    def test_pipenv_not_in_path(self, mocker: MockerFixture) -> None:
        """Test pipenv not in path."""
        pipenv_class = mocker.patch(
            f"{MODULE}.Pipenv",
            Mock(found_in_path=Mock(return_value=False)),
        )
        mocker.patch.object(PythonProject, "project_type", "pipenv")
        mocker.patch.object(PythonProject, "project_root")
        with pytest.raises(PipenvNotFoundError):
            assert PythonProject(Mock(use_pipenv=True), Mock()).pipenv
        pipenv_class.found_in_path.assert_called_once_with()

    def test_pipenv_not_pipenv_project(self, mocker: MockerFixture) -> None:
        """Test pipenv project is not a pipenv project."""
        mocker.patch.object(PythonProject, "project_type", "poetry")
        mocker.patch.object(PythonProject, "project_root")
        assert not PythonProject(Mock(use_pipenv=True), Mock()).pipenv

    def test_poetry(self, mocker: MockerFixture) -> None:
        """Test poetry."""
        ctx = Mock()
        poetry_class = mocker.patch(
            f"{MODULE}.Poetry",
            Mock(found_in_path=Mock(return_value=True), return_value="Poetry"),
        )
        mocker.patch.object(PythonProject, "project_type", "poetry")
        project_root = mocker.patch.object(PythonProject, "project_root")
        assert (
            PythonProject(Mock(use_poetry=True), ctx).poetry
            == poetry_class.return_value
        )
        poetry_class.found_in_path.assert_called_once_with()
        poetry_class.assert_called_once_with(ctx, project_root)

    def test_poetry_not_in_path(self, mocker: MockerFixture) -> None:
        """Test poetry not in path."""
        poetry_class = mocker.patch(
            f"{MODULE}.Poetry",
            Mock(found_in_path=Mock(return_value=False)),
        )
        mocker.patch.object(PythonProject, "project_type", "poetry")
        mocker.patch.object(PythonProject, "project_root")
        with pytest.raises(PoetryNotFoundError):
            assert PythonProject(Mock(use_poetry=True), Mock()).poetry
        poetry_class.found_in_path.assert_called_once_with()

    def test_poetry_not_poetry_project(self, mocker: MockerFixture) -> None:
        """Test poetry project is not a poetry project."""
        mocker.patch.object(PythonProject, "project_type", "pipenv")
        mocker.patch.object(PythonProject, "project_root")
        assert not PythonProject(Mock(use_poetry=True), Mock()).poetry

    @pytest.mark.parametrize(
        "pipenv_project, poetry_project, use_pipenv, use_poetry, expected",
        [
            (False, False, False, False, "pip"),
            (False, False, False, True, "pip"),
            (False, False, True, True, "pip"),
            (False, True, False, False, "pip"),
            (False, True, True, False, "pip"),
            (True, False, False, False, "pip"),
            (True, False, False, True, "pip"),
            (True, True, False, False, "pip"),
            (False, True, False, True, "poetry"),
            (False, True, True, True, "poetry"),
            (True, True, True, True, "poetry"),
            (True, True, True, False, "pipenv"),
            (True, False, True, False, "pipenv"),
            (True, False, True, True, "pipenv"),
        ],
    )
    def test_project_type(
        self,
        caplog: LogCaptureFixture,
        expected: str,
        mocker: MockerFixture,
        pipenv_project: bool,
        poetry_project: bool,
        tmp_path: Path,
        use_pipenv: bool,
        use_poetry: bool,
    ) -> None:
        """Test project_type."""
        caplog.set_level(logging.WARNING)
        mocker.patch.object(PythonProject, "project_root", tmp_path)
        mock_is_pipenv_project = mocker.patch(
            f"{MODULE}.is_pipenv_project", return_value=pipenv_project
        )
        mock_is_poetry_project = mocker.patch(
            f"{MODULE}.is_poetry_project", return_value=poetry_project
        )
        assert (
            PythonProject(
                Mock(use_pipenv=use_pipenv, use_poetry=use_poetry),
                Mock(),
            ).project_type
            == expected
        )
        mock_is_poetry_project.assert_called_once_with(tmp_path)
        if poetry_project:
            if use_poetry:
                mock_is_pipenv_project.assert_not_called()
            else:
                assert (
                    "poetry project detected but use of poetry is explicitly disabled"
                    in caplog.messages
                )
        else:
            mock_is_pipenv_project.assert_called_once_with(tmp_path)
        if (pipenv_project and not use_pipenv) and sum(
            [poetry_project, use_poetry]
        ) != 2:
            assert (
                "pipenv project detected but use of pipenv is explicitly disabled"
                in caplog.messages
            )

    def test_requirements_txt(self, mocker: MockerFixture, tmp_path: Path) -> None:
        """Test requirements_txt."""
        expected = tmp_path / "requirements.txt"
        expected.touch()
        mock_is_pip_project = mocker.patch(
            f"{MODULE}.is_pip_project", return_value=True
        )
        mocker.patch.object(PythonProject, "pipenv", None)
        mocker.patch.object(PythonProject, "poetry", None)
        mocker.patch.object(PythonProject, "project_root", tmp_path)
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
        mocker.patch.object(PythonProject, "project_root")
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
        mocker.patch.object(PythonProject, "project_root")
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
        mocker.patch.object(PythonProject, "project_root", tmp_path)
        with pytest.raises(PythonRequirementsNotFoundError) as excinfo:
            assert PythonProject(Mock(), Mock()).requirements_txt
        mock_is_pip_project.assert_called_once_with(
            tmp_path, file_name="requirements.txt"
        )
        assert (
            f"{tmp_path} does not contain a requirements file" in excinfo.value.message
        )

    def test_runtime(self) -> None:
        """Test runtime."""
        assert PythonProject(Mock(runtime="foo"), Mock()).runtime == "foo"

    @pytest.mark.parametrize(
        "use_pipenv, use_poetry, update_expected",
        [
            (False, False, []),
            (False, True, [*Poetry.CONFIG_FILES]),
            (True, False, [*Pipenv.CONFIG_FILES]),
            (True, True, [*Poetry.CONFIG_FILES, *Pipenv.CONFIG_FILES]),
        ],
    )
    def test_supported_metadata_files(
        self, update_expected: List[str], use_pipenv: bool, use_poetry: bool
    ) -> None:
        """Test supported_metadata_files."""
        expected = {*Pip.CONFIG_FILES}
        if update_expected:
            expected.update(update_expected)
        assert (
            PythonProject(
                Mock(use_pipenv=use_pipenv, use_poetry=use_poetry), Mock()
            ).supported_metadata_files
            == expected
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
