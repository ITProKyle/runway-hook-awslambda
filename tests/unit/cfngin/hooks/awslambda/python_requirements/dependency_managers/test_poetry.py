"""Test runway.cfngin.hooks.awslambda.python_requirements.dependency_managers._poetry."""
# pylint: disable=no-self-use,protected-access
from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING, Any, Dict

import pytest
import tomli_w
from mock import Mock

from awslambda.python_requirements.dependency_managers._poetry import (
    Poetry,
    PoetryExportFailedError,
    is_poetry_project,
)

if TYPE_CHECKING:
    from pathlib import Path

    from pytest_mock import MockerFixture


class TestPoetry:
    """Test Poetry."""

    def test_config_files(self) -> None:
        """Test CONFIG_FILES."""
        assert Poetry.CONFIG_FILES == ("poetry.lock", "pyproject.toml")

    @pytest.mark.parametrize(
        "export_kwargs",
        [
            {},
            {
                "dev": True,
                "extras": ["foo"],
                "output_format": "pipenv",
                "with_credentials": False,
                "without_hashes": False,
            },
        ],
    )
    def test_export(
        self,
        export_kwargs: Dict[str, Any],
        mocker: MockerFixture,
        tmp_path: Path,
    ) -> None:
        """Test export."""
        expected = tmp_path / "expected" / "test.requirements.txt"
        mock_generate_command = mocker.patch.object(
            Poetry, "generate_command", return_value="generate_command"
        )
        mock_run_command = mocker.patch.object(
            Poetry, "_run_command", return_value="_run_command"
        )
        (tmp_path / "test.requirements.txt").touch()  # created by _run_command

        obj = Poetry(Mock(), tmp_path)
        assert obj.export(output=expected, **export_kwargs) == expected
        assert expected.is_file()
        export_kwargs.update({"output": expected.name})
        export_kwargs.update(
            {"format": export_kwargs.pop("output_format", "requirements.txt")}
        )
        export_kwargs.setdefault("dev", False)
        export_kwargs.setdefault("extras", None)
        export_kwargs.setdefault("with_credentials", True)
        export_kwargs.setdefault("without_hashes", True)
        mock_generate_command.assert_called_once_with("export", **export_kwargs)
        mock_run_command.assert_called_once_with(mock_generate_command.return_value)

    def test_export_raise_from_called_process_error(
        self,
        mocker: MockerFixture,
        tmp_path: Path,
    ) -> None:
        """Test export raise PoetryExportFailedError from CalledProcessError."""
        output = tmp_path / "expected" / "test.requirements.txt"
        mock_generate_command = mocker.patch.object(
            Poetry, "generate_command", return_value="generate_command"
        )
        mocker.patch.object(
            Poetry,
            "_run_command",
            side_effect=subprocess.CalledProcessError(
                returncode=1,
                cmd=mock_generate_command.return_value,
                output="output",
                stderr="stderr",
            ),
        )

        with pytest.raises(PoetryExportFailedError) as excinfo:
            assert Poetry(Mock(), tmp_path).export(output=output)
        assert (
            excinfo.value.message
            == "poetry export failed with the following output:\nstderr"
        )

    def test_export_raise_when_output_does_not_exist(
        self,
        mocker: MockerFixture,
        tmp_path: Path,
    ) -> None:
        """Test export raise PoetryExportFailedError from CalledProcessError."""
        output = tmp_path / "expected" / "test.requirements.txt"
        mocker.patch.object(Poetry, "generate_command", return_value="generate_command")
        mock_run_command = mocker.patch.object(
            Poetry, "_run_command", return_value="_run_command"
        )

        with pytest.raises(PoetryExportFailedError) as excinfo:
            assert Poetry(Mock(), tmp_path).export(output=output)
        assert (
            excinfo.value.message
            == f"poetry export failed with the following output:\n{mock_run_command.return_value}"
        )

    def test_version(self, mocker: MockerFixture, tmp_path: Path) -> None:
        """Test version."""
        mock_run_command = mocker.patch.object(
            Poetry, "_run_command", return_value="success"
        )
        assert Poetry(Mock(), tmp_path).version == mock_run_command.return_value
        mock_run_command.assert_called_once_with([Poetry.EXECUTABLE, "--version"])


@pytest.mark.parametrize(
    "build_system, expected",
    [
        (
            {
                "build-backend": "poetry.core.masonry.api",
                "requires": ["poetry-core>=1.0.0"],
            },
            True,
        ),
        ({"requires": ["poetry-core>=1.0.0"]}, True),
        ({"build-backend": "poetry.core.masonry.api"}, False),
        ({}, False),
    ],
)
def test_is_poetry_project(
    build_system: Dict[str, Any], expected: bool, tmp_path: Path
) -> None:
    """Test is_poetry_project."""
    pyproject_contents = {"build-system": build_system}
    pyproject_path = tmp_path / "pyproject.toml"
    pyproject_path.write_text(tomli_w.dumps(pyproject_contents))
    assert is_poetry_project(tmp_path) is expected


def test_is_poetry_project_file_not_found(tmp_path: Path) -> None:
    """Test is_poetry_project for pyproject.toml not in directory."""
    assert not is_poetry_project(tmp_path)
