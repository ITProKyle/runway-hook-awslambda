"""Test runway.cfngin.hooks.awslambda.mixins."""
# pylint: disable=no-self-use,protected-access
from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING, Any, Dict, List, Optional

import pytest
from mock import Mock

from awslambda.mixins import CliInterfaceMixin

if TYPE_CHECKING:
    from pathlib import Path

    from pytest_mock import MockerFixture
    from runway.context import CfnginContext

MODULE = "awslambda.mixins"


class CliInterface(CliInterfaceMixin):
    """Used in tests."""

    def __init__(self, context: CfnginContext, cwd: Path) -> None:
        """Instantiate class."""
        self.ctx = context
        self.cwd = cwd


class TestCliInterfaceMixin:
    """Test CliInterfaceMixin."""

    @pytest.mark.parametrize("env", [None, {"foo": "bar"}])
    def test__run_command(
        self, env: Optional[Dict[str, str]], mocker: MockerFixture, tmp_path: Path
    ) -> None:
        """Test _run_command."""
        ctx_env = {"foo": "bar", "bar": "foo"}
        mock_subprocess = mocker.patch(
            f"{MODULE}.subprocess.check_output", return_value="success"
        )
        assert (
            CliInterface(Mock(env=Mock(vars=ctx_env)), tmp_path)._run_command(
                "test", env=env
            )
            == mock_subprocess.return_value
        )
        mock_subprocess.assert_called_once_with(
            "test",
            cwd=tmp_path,
            env=env or ctx_env,
            shell=True,
            stderr=subprocess.PIPE,
            text=True,
        )

    def test__run_command_no_suppress_output(
        self, mocker: MockerFixture, tmp_path: Path
    ) -> None:
        """Test _run_command."""
        env = {"foo": "bar"}
        mock_list2cmdline = mocker.patch.object(
            CliInterface, "list2cmdline", return_value="success"
        )
        mock_subprocess = mocker.patch(
            f"{MODULE}.subprocess.check_call", return_value=0
        )
        assert not CliInterface(Mock(env=Mock(vars=env)), tmp_path)._run_command(
            ["foo", "bar"], suppress_output=False
        )
        mock_list2cmdline.assert_called_once_with(["foo", "bar"])
        mock_subprocess.assert_called_once_with(
            mock_list2cmdline.return_value,
            cwd=tmp_path,
            env=env,
            shell=True,
        )

    @pytest.mark.parametrize(
        "prefix, provided, expected",
        [
            (None, "foo", "--foo"),
            ("-", "foo_bar", "-foo-bar"),
            ("--", "foo-bar", "--foo-bar"),
        ],
    )
    def test_convert_to_cli_arg(
        self, expected: str, prefix: Optional[str], provided: str
    ) -> None:
        """Test convert_to_cli_arg."""
        if prefix:
            assert CliInterface.convert_to_cli_arg(provided, prefix=prefix) == expected
        else:
            assert CliInterface.convert_to_cli_arg(provided) == expected

    @pytest.mark.parametrize("return_value", [False, True])
    def test_found_in_path(self, mocker: MockerFixture, return_value: bool) -> None:
        """Test found_in_path."""
        exe = mocker.patch.object(CliInterface, "EXECUTABLE", "foo.exe", create=True)
        mock_which = Mock(return_value=return_value)
        mocker.patch(f"{MODULE}.shutil", which=mock_which)
        assert CliInterface.found_in_path() is return_value
        mock_which.assert_called_once_with(exe)

    @pytest.mark.parametrize(
        "provided, expected",
        [
            ({}, []),
            ({"is_flag": True}, ["--is-flag"]),
            ({"is_flag": False}, []),
            ({"key": "val", "is-flag": True}, ["--key", "val", "--is-flag"]),
            ({"user": ["foo", "bar"]}, ["--user", "foo", "--user", "bar"]),
        ],
    )
    def test_generate_command(
        self,
        expected: List[str],
        mocker: MockerFixture,
        provided: Dict[str, Any],
    ) -> None:
        """Test generate_command."""
        exe = mocker.patch.object(CliInterface, "EXECUTABLE", "test.exe", create=True)
        assert CliInterface.generate_command("command", **provided) == [
            exe,
            "command",
            *expected,
        ]

    def test_list2cmdline_darwin(
        self,
        mocker: MockerFixture,
        platform_darwin: None,  # pylint: disable=unused-argument
    ) -> None:
        """Test list2cmdline on Darwin/macOS systems."""
        mock_list2cmdline = mocker.patch(f"{MODULE}.subprocess.list2cmdline")
        mock_join = mocker.patch(f"{MODULE}.shlex.join", return_value="success")
        assert CliInterface.list2cmdline("foo") == mock_join.return_value
        mock_list2cmdline.assert_not_called()
        mock_join.assert_called_once_with("foo")

    def test_list2cmdline_linus(
        self,
        mocker: MockerFixture,
        platform_linux: None,  # pylint: disable=unused-argument
    ) -> None:
        """Test list2cmdline on Linux systems."""
        mock_list2cmdline = mocker.patch(f"{MODULE}.subprocess.list2cmdline")
        mock_join = mocker.patch(f"{MODULE}.shlex.join", return_value="success")
        assert CliInterface.list2cmdline("foo") == mock_join.return_value
        mock_list2cmdline.assert_not_called()
        mock_join.assert_called_once_with("foo")

    def test_list2cmdline_windows(
        self,
        mocker: MockerFixture,
        platform_windows: None,  # pylint: disable=unused-argument
    ) -> None:
        """Test list2cmdline on Windows systems."""
        mock_list2cmdline = mocker.patch(
            f"{MODULE}.subprocess.list2cmdline", return_value="success"
        )
        mock_join = mocker.patch(f"{MODULE}.shlex.join")
        assert CliInterface.list2cmdline("foo") == mock_list2cmdline.return_value
        mock_list2cmdline.assert_called_once_with("foo")
        mock_join.assert_not_called()
