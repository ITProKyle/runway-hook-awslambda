"""Test runway.cfngin.hooks.awslambda.models.args."""
# pylint: disable=no-self-use,protected-access
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

from awslambda.models.args import AwsLambdaHookArgs, PythonFunctionHookArgs

MODULE = "awslambda.models.args"


class TestAwsLambdaHookArgs:
    """Test AwsLambdaHookArgs."""

    def test___resolve_path(self) -> None:
        """Test _resolve_path."""
        obj = AwsLambdaHookArgs(  # these are all required fields
            bucket_name="test-bucket",
            function_name="name",
            runtime="test",
            source_code="./",
        )
        assert obj.source_code.is_absolute()
        assert obj.source_code == Path.cwd()

    def test_field_defaults(self, tmp_path: Path) -> None:
        """Test field defaults."""
        obj = AwsLambdaHookArgs(  # these are all required fields
            bucket_name="test-bucket",
            function_name="name",
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
                function_name="name",
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
                function_name="name",
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


class TestPythonFunctionHookArgs:
    """Test PythonFunctionHookArgs."""

    def test_extra(self, tmp_path: Path) -> None:
        """Test extra fields."""
        obj = PythonFunctionHookArgs(
            bucket_name="test-bucket",
            function_name="name",
            invalid=True,
            source_code=tmp_path,
        )
        assert not obj.get("invalid")

    def test_field_defaults(self, tmp_path: Path) -> None:
        """Test field defaults."""
        obj = PythonFunctionHookArgs(  # these are all required fields
            bucket_name="test-bucket",
            function_name="name",
            source_code=tmp_path,
        )
        assert not obj.extend_pip_args
        assert obj.runtime == f"python{sys.version_info.major}.{sys.version_info.minor}"
        assert obj.use_pipenv
        assert obj.use_poetry
