"""Test runway.cfngin.hooks.awslambda._python."""
# pylint: disable=no-self-use,protected-access,redefined-outer-name
from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from mock import Mock
from pydantic import ValidationError

from awslambda._python import PythonFunction
from awslambda.models.args import PythonFunctionHookArgs

if TYPE_CHECKING:
    from pathlib import Path

    from pytest_mock import MockerFixture

MODULE = "awslambda._python"


@pytest.fixture(scope="function")
def args(tmp_path: Path) -> PythonFunctionHookArgs:
    """Fixture for creating default function args."""
    return PythonFunctionHookArgs(
        bucket_name="test-bucket",
        runtime="python3.9",
        source_code=tmp_path,
    )


class TestPythonFunction:
    """Test PythonFunction."""

    def test___init__(self, args: PythonFunctionHookArgs) -> None:
        """Test __init__."""
        ctx = Mock()
        obj = PythonFunction(ctx, **args.dict())
        # only two attributes are being set currently
        assert obj.args == args
        assert obj.ctx == ctx

    def test___init___raise_validation_error(self) -> None:
        """Test __init__ raise ValidationError if args are invalid."""
        with pytest.raises(ValidationError):
            PythonFunction(Mock(), invalid=True)

    def test_cleanup(self, args: PythonFunctionHookArgs, mocker: MockerFixture) -> None:
        """Test cleanup."""
        project = mocker.patch.object(PythonFunction, "project")
        assert not PythonFunction(Mock(), **args.dict()).cleanup()
        project.cleanup.assert_called_once_with()

    def test_deployment_package(
        self, args: PythonFunctionHookArgs, mocker: MockerFixture
    ) -> None:
        """Test deployment_package."""
        deployment_package_class = mocker.patch(f"{MODULE}.PythonDeploymentPackage")
        project = mocker.patch.object(PythonFunction, "project", "project")
        assert (
            PythonFunction(Mock(), **args.dict()).deployment_package
            == deployment_package_class.init.return_value
        )
        deployment_package_class.init.assert_called_once_with(project)

    def test_pre_deploy(
        self, args: PythonFunctionHookArgs, mocker: MockerFixture
    ) -> None:
        """Test pre_deploy."""
        model = Mock(dict=Mock(return_value="success"))
        build_response = mocker.patch.object(
            PythonFunction, "build_response", return_value=(model)
        )
        cleanup = mocker.patch.object(PythonFunction, "cleanup")
        deployment_package = mocker.patch.object(PythonFunction, "deployment_package")
        assert (
            PythonFunction(Mock(), **args.dict()).pre_deploy()
            == model.dict.return_value
        )
        deployment_package.upload.assert_called_once_with()
        build_response.assert_called_once_with("deploy")
        model.dict.assert_called_once_with(by_alias=True)
        cleanup.assert_called_once_with()

    def test_pre_deploy_always_cleanup(
        self, args: PythonFunctionHookArgs, mocker: MockerFixture
    ) -> None:
        """Test pre_deploy always cleanup."""
        build_response = mocker.patch.object(
            PythonFunction, "build_response", return_value="success"
        )
        cleanup = mocker.patch.object(PythonFunction, "cleanup")
        deployment_package = mocker.patch.object(
            PythonFunction,
            "deployment_package",
            Mock(upload=Mock(side_effect=Exception)),
        )
        with pytest.raises(Exception):
            assert PythonFunction(Mock(), **args.dict()).pre_deploy()
        deployment_package.upload.assert_called_once_with()
        build_response.assert_not_called()
        cleanup.assert_called_once_with()

    def test_project(self, args: PythonFunctionHookArgs, mocker: MockerFixture) -> None:
        """Test project."""
        ctx = Mock()
        project_class = mocker.patch(f"{MODULE}.PythonProject")
        assert PythonFunction(ctx, **args.dict()).project == project_class.return_value
        project_class.assert_called_once_with(args, ctx)
