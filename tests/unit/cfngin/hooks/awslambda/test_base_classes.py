"""Test runway.cfngin.hooks.awslambda.base_classes."""
# pylint: disable=no-self-use,protected-access
from __future__ import annotations

import logging
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional

import pytest
from mock import Mock

from awslambda.base_classes import (
    AwsLambdaHook,
    DependencyManager,
    FunctionHook,
    LayerHook,
    Project,
)

if TYPE_CHECKING:
    from pytest import LogCaptureFixture
    from pytest_mock import MockerFixture
    from runway.context import CfnginContext

MODULE = "awslambda.base_classes"


class TestAwsLambdaHook:
    """Test AwsLambdaHook."""

    def test___init__(self, cfngin_context: CfnginContext) -> None:
        """Test __init__."""
        obj: Any = AwsLambdaHook(cfngin_context)
        # only one attribute is currently set by this base class
        assert obj.ctx

    def test_build_response_deploy(
        self, cfngin_context: CfnginContext, mocker: MockerFixture
    ) -> None:
        """Test build_response."""
        deployment_package = mocker.patch.object(
            AwsLambdaHook,
            "deployment_package",
            Mock(
                bucket=Mock(),
                code_sha256="sha256",
                object_key="key",
                object_version_id="version",
            ),
        )
        deployment_package.bucket.name = "test-bucket"
        assert AwsLambdaHook(cfngin_context).build_response("deploy").dict() == {
            "bucket_name": deployment_package.bucket.name,
            "code_sha256": deployment_package.code_sha256,
            "object_key": deployment_package.object_key,
            "object_version_id": deployment_package.object_version_id,
        }

    def test_build_response_destroy(self, cfngin_context: CfnginContext) -> None:
        """Test build_response."""
        assert not AwsLambdaHook(cfngin_context).build_response("destroy")

    def test_deployment_package(self, cfngin_context: CfnginContext) -> None:
        """Test deployment_package."""
        with pytest.raises(NotImplementedError):
            assert AwsLambdaHook(cfngin_context).deployment_package

    def test_post_deploy(
        self, caplog: LogCaptureFixture, cfngin_context: CfnginContext
    ) -> None:
        """Test post_deploy."""
        caplog.set_level(logging.WARNING, logger=MODULE)
        assert AwsLambdaHook(cfngin_context).post_deploy()
        assert (
            f"post_deploy not implimented for {AwsLambdaHook.__name__}"
            in caplog.messages
        )

    def test_post_destroy(
        self, caplog: LogCaptureFixture, cfngin_context: CfnginContext
    ) -> None:
        """Test post_destroy."""
        caplog.set_level(logging.WARNING, logger=MODULE)
        assert AwsLambdaHook(cfngin_context).post_destroy()
        assert (
            f"post_destroy not implimented for {AwsLambdaHook.__name__}"
            in caplog.messages
        )

    def test_pre_deploy(
        self, caplog: LogCaptureFixture, cfngin_context: CfnginContext
    ) -> None:
        """Test pre_deploy."""
        caplog.set_level(logging.WARNING, logger=MODULE)
        assert AwsLambdaHook(cfngin_context).pre_deploy()
        assert (
            f"pre_deploy not implimented for {AwsLambdaHook.__name__}"
            in caplog.messages
        )

    def test_pre_destroy(
        self, caplog: LogCaptureFixture, cfngin_context: CfnginContext
    ) -> None:
        """Test pre_destroy."""
        caplog.set_level(logging.WARNING, logger=MODULE)
        assert AwsLambdaHook(cfngin_context).pre_destroy()
        assert (
            f"pre_destroy not implimented for {AwsLambdaHook.__name__}"
            in caplog.messages
        )

    def test_project(self, cfngin_context: CfnginContext) -> None:
        """Test project."""
        with pytest.raises(NotImplementedError):
            assert AwsLambdaHook(cfngin_context).project


class TestDependencyManager:
    """Test DependencyManager."""

    def test___init__(self, cfngin_context: CfnginContext) -> None:
        """Test __init__."""
        source_code = Mock(name="source_code")
        obj = DependencyManager(cfngin_context, source_code)
        assert obj.ctx == cfngin_context
        assert obj.source_code == source_code

    def test__run_command(
        self, cfngin_context: CfnginContext, mocker: MockerFixture
    ) -> None:
        """Test _run_command."""
        mock_subprocess = mocker.patch(
            f"{MODULE}.subprocess.check_output", return_value="success"
        )
        source_code = Mock(root_directory="./")
        obj = DependencyManager(cfngin_context, source_code)
        assert obj._run_command("test") == mock_subprocess.return_value
        mock_subprocess.assert_called_once_with(
            "test",
            cwd=source_code.root_directory,
            env=obj.ctx.env.vars,
            shell=True,
            stderr=subprocess.PIPE,
            text=True,
        )

    def test__run_command_no_suppress_output(
        self, cfngin_context: CfnginContext, mocker: MockerFixture
    ) -> None:
        """Test _run_command."""
        mock_subprocess = mocker.patch(
            f"{MODULE}.subprocess.check_call", return_value=0
        )
        source_code = Mock(root_directory="./")
        obj = DependencyManager(cfngin_context, source_code)
        assert not obj._run_command(["foo", "bar"], suppress_output=False)
        mock_subprocess.assert_called_once_with(
            "foo bar",
            cwd=source_code.root_directory,
            env=obj.ctx.env.vars,
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
            assert (
                DependencyManager.convert_to_cli_arg(provided, prefix=prefix)
                == expected
            )
        else:
            assert DependencyManager.convert_to_cli_arg(provided) == expected

    @pytest.mark.parametrize("return_value", [False, True])
    def test_found_in_path(self, mocker: MockerFixture, return_value: bool) -> None:
        """Test found_in_path."""
        exe = mocker.patch.object(
            DependencyManager, "EXECUTABLE", "foo.exe", create=True
        )
        mock_which = Mock(return_value=return_value)
        mocker.patch(f"{MODULE}.shutil", which=mock_which)
        assert DependencyManager.found_in_path() is return_value
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
        exe = mocker.patch.object(
            DependencyManager, "EXECUTABLE", "test.exe", create=True
        )
        assert DependencyManager.generate_command("command", **provided) == [
            exe,
            "command",
            *expected,
        ]

    def test_version(self, cfngin_context: CfnginContext) -> None:
        """Test version."""
        with pytest.raises(NotImplementedError):
            assert DependencyManager(cfngin_context, Mock()).version


class TestFunctionHook:
    """Test FunctionHook."""

    def test_deployment_package(self, cfngin_context: CfnginContext) -> None:
        """Test deployment_package."""
        with pytest.raises(NotImplementedError):
            assert FunctionHook(cfngin_context).deployment_package

    def test_project(self, cfngin_context: CfnginContext) -> None:
        """Test project."""
        with pytest.raises(NotImplementedError):
            assert FunctionHook(cfngin_context).project


class TestLayerHook:
    """Test LayerHook."""

    def test_deployment_package(self, cfngin_context: CfnginContext) -> None:
        """Test deployment_package."""
        with pytest.raises(NotImplementedError):
            assert LayerHook(cfngin_context).deployment_package

    def test_project(self, cfngin_context: CfnginContext) -> None:
        """Test project."""
        with pytest.raises(NotImplementedError):
            assert LayerHook(cfngin_context).project


class TestProject:
    """Test Project."""

    def test___init__(self, cfngin_context: CfnginContext) -> None:
        """Test __init__."""
        args = Mock(name="args")
        obj = Project(args, cfngin_context)
        assert obj.args == args
        assert obj.ctx == cfngin_context

    def test_build_directory(
        self, cfngin_context: CfnginContext, mocker: MockerFixture, tmp_path: Path
    ) -> None:
        """Test build_directory."""
        mocker.patch.object(Project, "source_code", Mock(md5_hash="hash"))
        mocker.patch(f"{MODULE}.BASE_WORK_DIR", tmp_path)
        expected = tmp_path / "foo.hash"

        obj = Project(Mock(function_name="foo"), cfngin_context)
        assert obj.build_directory == expected
        assert expected.is_dir()

    def test_cleanup(self, cfngin_context: CfnginContext) -> None:
        """Test cleanup. Should do nothing."""
        assert not Project(Mock(), cfngin_context).cleanup()

    def test_dependency_directory(
        self, cfngin_context: CfnginContext, mocker: MockerFixture, tmp_path: Path
    ) -> None:
        """Test dependency_directory."""
        mocker.patch.object(Project, "build_directory", tmp_path)
        expected = tmp_path / "dependencies"

        obj = Project(Mock(), cfngin_context)
        assert obj.dependency_directory == expected
        assert expected.is_dir()

    def test_install_dependencies(self, cfngin_context: CfnginContext) -> None:
        """Test install_dependencies."""
        with pytest.raises(NotImplementedError):
            assert Project(Mock(), cfngin_context).install_dependencies()

    def test_source_code(
        self, cfngin_context: CfnginContext, mocker: MockerFixture
    ) -> None:
        """Test source_code."""
        args = Mock(extend_gitignore=["rule0"], source_code="foo")
        source_code = Mock()
        source_code_base_class = mocker.patch(
            f"{MODULE}.SourceCode", Mock(return_value=source_code)
        )

        obj = Project(args, cfngin_context)
        assert obj.source_code == source_code
        source_code_base_class.assert_called_once_with(args.source_code)
        source_code.add_filter_rule.assert_called_once_with(args.extend_gitignore[0])
