"""Test runway.cfngin.hooks.awslambda.models.args."""
# pylint: disable=no-self-use,protected-access
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

import pytest
from pydantic import ValidationError

from awslambda.models.args import AwsLambdaHookArgs, DockerOptions, PythonHookArgs

MODULE = "awslambda.models.args"


class TestAwsLambdaHookArgs:
    """Test AwsLambdaHookArgs."""

    @pytest.mark.parametrize("value", ["foobar", None])
    def test__check_tag_value_length(self, value: Optional[str]) -> None:
        """Test _check_tag_value_length."""
        obj = AwsLambdaHookArgs(
            bucket_name="test-bucket",
            license=value,
            runtime="test",
            source_code="./",  # type: ignore
        )
        assert obj.license == value

    def test__check_tag_value_length_raise_value_error(self) -> None:
        """Test _check_tag_value_length raise ValueError."""
        with pytest.raises(ValueError):
            AwsLambdaHookArgs(
                bucket_name="test-bucket",
                license="0" * 256,
                runtime="test",
                source_code="./",  # type: ignore
            )

    def test___resolve_path(self) -> None:
        """Test _resolve_path."""
        obj = AwsLambdaHookArgs(  # these are all required fields
            bucket_name="test-bucket",
            runtime="test",
            source_code="./",  # type: ignore
        )
        assert obj.source_code.is_absolute()
        assert obj.source_code == Path.cwd()

    def test__validate_runtime_or_docker(self, tmp_path: Path) -> None:
        """Test _validate_runtime_or_docker."""
        obj = AwsLambdaHookArgs(
            bucket_name="test-bucket",
            runtime="test",
            source_code=tmp_path,
        )
        assert obj.runtime == "test"

    @pytest.mark.parametrize(
        "kwargs", [{"image": "test"}, {"file": ""}, {"file": "", "image": "test"}]
    )
    def test__validate_runtime_or_docker_docker_no_runtime(
        self, kwargs: Dict[str, Any], tmp_path: Path
    ) -> None:
        """Test _validate_runtime_or_docker no runtime if Docker."""
        if "file" in kwargs:
            dockerfile = tmp_path / "Dockerfile"
            dockerfile.touch()  # file has to exist
            kwargs["file"] = dockerfile
        obj = AwsLambdaHookArgs(
            bucket_name="test-bucket",
            docker=DockerOptions.parse_obj(kwargs),
            source_code=tmp_path,
        )
        assert not obj.runtime

    def test__validate_runtime_or_docker_docker_disabled(self, tmp_path: Path) -> None:
        """Test _validate_runtime_or_docker.

        With ``runtime=None`` and ``docker.disabled=True``.

        """
        with pytest.raises(ValidationError) as excinfo:
            AwsLambdaHookArgs(
                bucket_name="test-bucket",
                docker=DockerOptions(disabled=True),
                source_code=tmp_path,
            )
        errors = excinfo.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("runtime",)
        assert errors[0]["msg"] == "runtime must be provided if docker.disabled is True"

    def test__validate_runtime_or_docker_no_runtime_or_docker(
        self, tmp_path: Path
    ) -> None:
        """Test _validate_runtime_or_docker no runtime or docker."""
        with pytest.raises(ValidationError) as excinfo:
            AwsLambdaHookArgs(
                bucket_name="test-bucket",
                source_code=tmp_path,
            )
        errors = excinfo.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("runtime",)
        assert errors[0]["msg"] == "docker.file, docker.image, or runtime is required"

    def test_field_defaults(self, tmp_path: Path) -> None:
        """Test field defaults."""
        obj = AwsLambdaHookArgs(  # these are all required fields
            bucket_name="test-bucket",
            runtime="test",
            source_code=tmp_path,
        )
        assert obj.extend_gitignore == []
        assert not obj.object_prefix

    def test_source_code_is_file(self, tmp_path: Path) -> None:
        """Test source_code is file."""
        source_path = tmp_path / "foo"
        source_path.write_text("bar")
        with pytest.raises(ValidationError) as excinfo:
            AwsLambdaHookArgs(  # these are all required fields
                bucket_name="test-bucket",
                runtime="test",
                source_code=source_path,
            )
        errors = excinfo.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("source_code",)
        assert errors[0]["msg"] == f'path "{source_path}" does not point to a directory'

    def test_source_code_not_exist(self, tmp_path: Path) -> None:
        """Test source_code directory does not exist."""
        source_path = tmp_path / "foo"
        with pytest.raises(ValidationError) as excinfo:
            AwsLambdaHookArgs(  # these are all required fields
                bucket_name="test-bucket",
                runtime="test",
                source_code=source_path,
            )
        errors = excinfo.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("source_code",)
        assert (
            errors[0]["msg"]
            == f'file or directory at path "{source_path}" does not exist'
        )


class TestPythonHookArgs:
    """Test PythonHookArgs."""

    def test_extra(self, tmp_path: Path) -> None:
        """Test extra fields."""
        obj = PythonHookArgs(
            bucket_name="test-bucket",
            invalid=True,  # type: ignore
            runtime="test",
            source_code=tmp_path,
        )
        assert not obj.get("invalid")

    def test_field_defaults(self, tmp_path: Path) -> None:
        """Test field defaults."""
        obj = PythonHookArgs(  # these are all required fields
            bucket_name="test-bucket",
            runtime="test",
            source_code=tmp_path,
        )
        assert not obj.extend_pip_args
        assert obj.use_pipenv
        assert obj.use_poetry
