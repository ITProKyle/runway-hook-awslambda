"""Test runway.cfngin.hooks.awslambda.python_requirements._deployment_package."""
# pylint: disable=no-self-use,protected-access
from __future__ import annotations

from typing import TYPE_CHECKING

from mock import Mock, call

from awslambda.python_requirements._deployment_package import PythonDeploymentPackage

if TYPE_CHECKING:
    from pathlib import Path

    from pytest_mock import MockerFixture

MODULE = "awslambda.python_requirements._deployment_package"


class TestPythonDeploymentPackage:
    """Test PythonDeploymentPackage."""

    def test_gitignore_filter(self, mocker: MockerFixture) -> None:
        """Test gitignore_filter."""
        mock_ignore_parser = Mock()
        mock_ignore_parser_class = mocker.patch(
            f"{MODULE}.IgnoreParser", return_value=mock_ignore_parser
        )
        project = Mock(dependency_directory="dependency_directory")
        assert PythonDeploymentPackage(project).gitignore_filter == mock_ignore_parser
        mock_ignore_parser_class.assert_called_once_with()
        mock_ignore_parser.add_rule.assert_has_calls(
            [
                call("**/__pycache__*", project.dependency_directory),
                call("**/*.dist-info*", project.dependency_directory),
                call("**/*.py[c|o]", project.dependency_directory),
            ]
        )

    def test_insert_layer_dir(self, tmp_path: Path) -> None:
        """Test insert_layer_dir."""
        assert (
            PythonDeploymentPackage.insert_layer_dir(tmp_path / "foo.txt", tmp_path)
            == tmp_path / "python" / "foo.txt"
        )
        assert (
            PythonDeploymentPackage.insert_layer_dir(
                tmp_path / "bar" / "foo.txt", tmp_path
            )
            == tmp_path / "python" / "bar" / "foo.txt"
        )
