"""Test runway.cfngin.hooks.awslambda.python_requirements.dependency_managers._pip."""
# pylint: disable=no-self-use,protected-access
from __future__ import annotations

import logging
import shlex
import subprocess
from typing import TYPE_CHECKING, Dict, List, Union

import pytest
from mock import Mock

from awslambda.python_requirements.dependency_managers._pip import (
    Pip,
    PipInstallFailedError,
    is_pip_project,
)

if TYPE_CHECKING:
    from pathlib import Path

    from pytest import LogCaptureFixture
    from pytest_mock import MockerFixture


class TestPip:
    """Test Pip."""

    @pytest.mark.parametrize("command", ["test", ["test"]])
    def test_generate_command(
        self,
        caplog: LogCaptureFixture,
        command: Union[List[str], str],
        mocker: MockerFixture,
    ) -> None:
        """Test generate_command."""
        caplog.set_level(logging.DEBUG)
        expected = ["python", "-m", "pip", "test", "--foo", "bar"]
        kwargs = {"foo": "bar"}
        mock_generate_command_handle_kwargs = mocker.patch.object(
            Pip, "_generate_command_handle_kwargs", return_value=["--foo", "bar"]
        )
        assert Pip.generate_command(command, **kwargs) == expected
        mock_generate_command_handle_kwargs.assert_called_once_with(**kwargs)
        assert f"generated command: {shlex.join(expected)}" in caplog.messages

    @pytest.mark.parametrize("target_already_exists", [False, True])
    def test_install(
        self, mocker: MockerFixture, target_already_exists: bool, tmp_path: Path
    ) -> None:
        """Test install."""
        requirements_txt = tmp_path / "requirements.txt"
        target = tmp_path / "foo" / "bar"
        if target_already_exists:
            target.mkdir(parents=True)
        mock_generate_command = mocker.patch.object(
            Pip, "generate_command", return_value="generate_command"
        )
        mock_run_command = mocker.patch.object(
            Pip, "_run_command", return_value="_run_command"
        )

        assert (
            Pip(Mock(), Mock()).install(requirements=requirements_txt, target=target)
            == target
        )
        assert target.is_dir(), "target directory and parents created"
        mock_generate_command.assert_called_once_with(
            "install",
            disable_pip_version_check=True,
            requirement=str(requirements_txt),
            target=str(target),
        )
        mock_run_command.assert_called_once_with(
            mock_generate_command.return_value, suppress_output=False
        )

    def test_install_raise_from_called_process_error(
        self, mocker: MockerFixture, tmp_path: Path
    ) -> None:
        """Test install raise from CalledProcessError."""
        requirements_txt = tmp_path / "requirements.txt"
        target = tmp_path / "foo" / "bar"
        mocker.patch.object(Pip, "generate_command", return_value="generate_command")
        mocker.patch.object(
            Pip,
            "_run_command",
            side_effect=subprocess.CalledProcessError(returncode=1, cmd="foo"),
        )

        with pytest.raises(PipInstallFailedError) as excinfo:
            assert Pip(Mock(), Mock()).install(
                requirements=requirements_txt, target=target
            )
        assert (
            excinfo.value.message == "pip failed to install dependencies; "
            "review pip's output above to troubleshoot"
        )

    def test_version(self, mocker: MockerFixture) -> None:
        """Test version."""
        mock_run_command = mocker.patch.object(
            Pip, "_run_command", return_value="success"
        )
        assert Pip(Mock(), Mock()).version == mock_run_command.return_value
        mock_run_command.assert_called_once_with([Pip.EXECUTABLE, "--version"])


@pytest.mark.parametrize(
    "kwargs, expected",
    [
        ({}, False),
        ({}, True),
        ({"file_name": "foo.txt"}, False),
        ({"file_name": "foo.txt"}, True),
    ],
)
def test_is_pip_project(expected: bool, kwargs: Dict[str, str], tmp_path: Path) -> None:
    """Test is_pip_project."""
    requirements_txt = tmp_path / kwargs.get("file_name", "requirements.txt")
    if expected:
        # for this function, the expected result is directly related
        # to the existence of this file
        requirements_txt.touch()
    assert is_pip_project(tmp_path, **kwargs) is expected