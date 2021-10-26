"""Test runway.cfngin.hooks.awslambda.base_classes."""
# pylint: disable=no-self-use,protected-access
from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest
from mock import Mock

from awslambda.base_classes import (
    AwsLambdaHook,
    DependencyManager,
    FunctionHook,
    LayerHook,
    Project,
)
from awslambda.models.args import AwsLambdaHookArgs
from awslambda.models.responses import AwsLambdaHookDeployResponse

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

    def test_build_response_deploy(self, mocker: MockerFixture) -> None:
        """Test build_response."""
        deployment_package = mocker.patch.object(
            AwsLambdaHook,
            "deployment_package",
            Mock(
                bucket=Mock(),
                code_sha256="sha256",
                object_key="key",
                object_version_id="version",
                runtime="runtime",
            ),
        )
        deployment_package.bucket.name = "test-bucket"
        assert AwsLambdaHook(Mock()).build_response(
            "deploy"
        ) == AwsLambdaHookDeployResponse(
            bucket_name=deployment_package.bucket.name,
            code_sha256=deployment_package.code_sha256,  # type: ignore
            object_key=deployment_package.object_key,  # type: ignore
            object_version_id=deployment_package.object_version_id,  # type: ignore
            runtime=deployment_package.runtime,  # type: ignore
        )

    def test_build_response_destroy(self) -> None:
        """Test build_response."""
        assert not AwsLambdaHook(Mock()).build_response("destroy")

    def test_build_response_plan(self, mocker: MockerFixture) -> None:
        """Test build_response."""
        deployment_package = mocker.patch.object(
            AwsLambdaHook,
            "deployment_package",
            Mock(
                bucket=Mock(),
                code_sha256="sha256",
                object_key="key",
                object_version_id="version",
                runtime="runtime",
            ),
        )
        deployment_package.bucket.name = "test-bucket"
        assert AwsLambdaHook(Mock()).build_response(
            "plan"
        ) == AwsLambdaHookDeployResponse(
            bucket_name=deployment_package.bucket.name,
            code_sha256=deployment_package.code_sha256,  # type: ignore
            object_key=deployment_package.object_key,  # type: ignore
            object_version_id=deployment_package.object_version_id,  # type: ignore
            runtime=deployment_package.runtime,  # type: ignore
        )

    def test_build_response_plan_handle_file_not_found_error(
        self, mocker: MockerFixture
    ) -> None:
        """Test build_response."""
        mocker.patch.object(
            AwsLambdaHook,
            "deployment_package",
            Mock(
                bucket=Mock(),
                code_sha256="sha256",
                object_key="key",
                object_version_id="version",
                runtime="runtime",
            ),
        )
        mocker.patch(
            f"{MODULE}.AwsLambdaHookDeployResponse",
            side_effect=[FileNotFoundError, "success"],
        )
        assert AwsLambdaHook(Mock()).build_response("plan") == "success"

    def test_deployment_package(self) -> None:
        """Test deployment_package."""
        with pytest.raises(NotImplementedError):
            assert AwsLambdaHook(Mock()).deployment_package

    def test_plan(self, mocker: MockerFixture) -> None:
        """Test plan."""
        response_obj = Mock(dict=Mock(return_value="success"))
        build_response = mocker.patch.object(
            AwsLambdaHook, "build_response", return_value=response_obj
        )
        assert AwsLambdaHook(Mock()).plan() == response_obj.dict.return_value
        build_response.assert_called_once_with("plan")
        response_obj.dict.assert_called_once_with(by_alias=True)

    def test_post_deploy(self, caplog: LogCaptureFixture) -> None:
        """Test post_deploy."""
        caplog.set_level(logging.WARNING, logger=f"runway.{MODULE}")
        assert AwsLambdaHook(Mock()).post_deploy()
        assert (
            f"post_deploy not implimented for {AwsLambdaHook.__name__}"
            in caplog.messages
        )

    def test_post_destroy(self, caplog: LogCaptureFixture) -> None:
        """Test post_destroy."""
        caplog.set_level(logging.WARNING, logger=f"runway.{MODULE}")
        assert AwsLambdaHook(Mock()).post_destroy()
        assert (
            f"post_destroy not implimented for {AwsLambdaHook.__name__}"
            in caplog.messages
        )

    def test_pre_deploy(self, caplog: LogCaptureFixture) -> None:
        """Test pre_deploy."""
        caplog.set_level(logging.WARNING, logger=f"runway.{MODULE}")
        assert AwsLambdaHook(Mock()).pre_deploy()
        assert (
            f"pre_deploy not implimented for {AwsLambdaHook.__name__}"
            in caplog.messages
        )

    def test_pre_destroy(self, caplog: LogCaptureFixture) -> None:
        """Test pre_destroy."""
        caplog.set_level(logging.WARNING, logger=f"runway.{MODULE}")
        assert AwsLambdaHook(Mock()).pre_destroy()
        assert (
            f"pre_destroy not implimented for {AwsLambdaHook.__name__}"
            in caplog.messages
        )

    def test_project(self) -> None:
        """Test project."""
        with pytest.raises(NotImplementedError):
            assert AwsLambdaHook(Mock()).project


class TestDependencyManager:
    """Test DependencyManager."""

    def test___init__(self, cfngin_context: CfnginContext, tmp_path: Path) -> None:
        """Test __init__."""
        obj = DependencyManager(cfngin_context, tmp_path)
        assert obj.ctx == cfngin_context
        assert obj.cwd == tmp_path

    def test_version(self, tmp_path: Path) -> None:
        """Test version."""
        with pytest.raises(NotImplementedError):
            assert DependencyManager(Mock(), tmp_path).version


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

    def test_build_directory(self, mocker: MockerFixture, tmp_path: Path) -> None:
        """Test build_directory."""
        mocker.patch.object(
            Project, "source_code", Mock(md5_hash="hash", root_directory=tmp_path)
        )
        mocker.patch(f"{MODULE}.BASE_WORK_DIR", tmp_path)
        expected = tmp_path / f"{tmp_path.name}.hash"

        obj = Project(Mock(), Mock())
        assert obj.build_directory == expected
        assert expected.is_dir()

    def test_cache_dir(self, tmp_path: Path) -> None:
        """Test cache_dir."""
        cache_dir = tmp_path / "test"
        cache_dir.mkdir()
        args = AwsLambdaHookArgs(
            bucket_name="",
            cache_dir=cache_dir,
            runtime="foo",
            source_code=tmp_path,
            use_cache=True,
        )
        assert Project(args, Mock()).cache_dir == cache_dir

    def test_cache_dir_default(self, mocker: MockerFixture, tmp_path: Path) -> None:
        """Test cache_dir default."""
        mocker.patch(f"{MODULE}.BASE_WORK_DIR", tmp_path)
        cache_dir = tmp_path / Project.DEFAULT_CACHE_DIR_NAME
        cache_dir.mkdir()
        args = AwsLambdaHookArgs(
            bucket_name="",
            runtime="foo",
            source_code=tmp_path,
            use_cache=True,
        )
        assert Project(args, Mock()).cache_dir == cache_dir

    def test_cache_dir_disabled(self, tmp_path: Path) -> None:
        """Test cache_dir disabled."""
        args = AwsLambdaHookArgs(
            bucket_name="",
            runtime="foo",
            source_code=tmp_path,
            use_cache=False,
        )
        assert not Project(args, Mock()).cache_dir

    def test_cleanup(self) -> None:
        """Test cleanup. Should do nothing."""
        assert not Project(Mock(), Mock()).cleanup()

    def test_dependency_directory(self, mocker: MockerFixture, tmp_path: Path) -> None:
        """Test dependency_directory."""
        mocker.patch.object(Project, "build_directory", tmp_path)
        expected = tmp_path / "dependencies"

        obj = Project(Mock(), Mock())
        assert obj.dependency_directory == expected
        assert expected.is_dir()

    def test_install_dependencies(self) -> None:
        """Test install_dependencies."""
        with pytest.raises(NotImplementedError):
            assert Project(Mock(), Mock()).install_dependencies()

    def test_metadata_files(self) -> None:
        """Test metadata_files."""
        assert Project(Mock(), Mock()).metadata_files == ()

    def test_project_root(self, tmp_path: Path) -> None:
        """Test project_root."""
        config_path = tmp_path / "config.yml"
        config_path.touch()
        assert (
            Project(
                Mock(source_code=tmp_path), Mock(config_path=config_path)
            ).project_root
            == tmp_path
        )

    def test_project_root_config_path_is_dir(self, tmp_path: Path) -> None:
        """Test project_root ctx.config_path is a directory."""
        assert (
            Project(Mock(source_code=tmp_path), Mock(config_path=tmp_path)).project_root
            == tmp_path
        )

    def test_project_root_config_path_not_parent_of_source_code(
        self, caplog: LogCaptureFixture, tmp_path: Path
    ) -> None:
        """Test project_root ctx.config_path is not a parent of args.source_code."""
        caplog.set_level(logging.INFO)
        config_path_dir = tmp_path / "project"
        config_path_dir.mkdir()
        config_path = config_path_dir / "config.yml"
        config_path.touch()
        src_path = tmp_path / "src" / "lambda_function"
        assert (
            Project(
                Mock(source_code=src_path), Mock(config_path=config_path)
            ).project_root
            == src_path
        )
        assert (
            "ignoring project directory; "
            "source code located outside of project directory"
        ) in caplog.messages

    @pytest.mark.parametrize("create_metadata_file", [False, True])
    def test_project_root_config_path_parent_of_source_code(
        self,
        create_metadata_file: bool,
        mocker: MockerFixture,
        tmp_path: Path,
    ) -> None:
        """Test project_root ctx.config_path is a parent of args.source_code."""
        config_path = tmp_path / "config.yml"
        config_path.touch()
        mocker.patch.object(Project, "supported_metadata_files", {"test.txt"})
        src_path = tmp_path / "src" / "lambda_function"
        src_path.mkdir(parents=True)
        if create_metadata_file:
            (src_path / "test.txt").touch()
        assert Project(
            Mock(source_code=src_path), Mock(config_path=config_path)
        ).project_root == (src_path if create_metadata_file else tmp_path)

    def test_project_type(self) -> None:
        """Test project_type."""
        with pytest.raises(NotImplementedError):
            assert Project(Mock(), Mock()).project_type

    def test_runtime(self) -> None:
        """Test runtime."""
        args = Mock(runtime="runtime")
        assert Project(args, Mock()).runtime == args.runtime

    def test_runtime_docker(self, mocker: MockerFixture) -> None:
        """Test runtime with docker."""
        docker = mocker.patch.object(
            Project, "docker", Mock(runtime="foo"), create=True
        )
        args = Mock(runtime="bar")
        assert Project(args, Mock()).runtime == docker.runtime

    def test_runtime_raise_value_error(self, mocker: MockerFixture) -> None:
        """Test runtime raise ValueError."""
        mocker.patch.object(Project, "docker", None, create=True)
        with pytest.raises(ValueError) as excinfo:
            assert not Project(Mock(runtime=None), Mock()).runtime
        assert (
            str(excinfo.value)
            == "runtime could not be determined from arguments or Docker image"
        )

    def test_source_code(self, mocker: MockerFixture) -> None:
        """Test source_code."""
        args = Mock(extend_gitignore=["rule0"], source_code="foo")
        metadata_files = mocker.patch.object(
            Project,
            "metadata_files",
            ("foo", "bar"),
        )
        project_root = mocker.patch.object(Project, "project_root")
        source_code = Mock()
        source_code_base_class = mocker.patch(
            f"{MODULE}.SourceCode", Mock(return_value=source_code)
        )

        obj = Project(args, Mock())
        assert obj.source_code == source_code
        source_code_base_class.assert_called_once_with(
            args.source_code,
            include_files_in_hash=metadata_files,
            project_root=project_root,
        )
        source_code.add_filter_rule.assert_called_once_with(args.extend_gitignore[0])

    def test_supported_metadata_files(self) -> None:
        """Test supported_metadata_files."""
        assert Project(Mock(), Mock()).supported_metadata_files == set()
