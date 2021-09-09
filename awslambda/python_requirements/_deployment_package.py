"""AWS Lambda Python Deployment Package."""
from __future__ import annotations

from typing import Optional

from igittigitt import IgnoreParser
from runway.compat import cached_property

from ..deployment_package import DeploymentPackage
from ._python_project import PythonProject


class PythonDeploymentPackage(DeploymentPackage[PythonProject]):
    """AWS Lambda Python Deployment Package."""

    project: PythonProject

    @cached_property
    def gitignore_filter(self) -> Optional[IgnoreParser]:
        """Filter to use when zipping dependencies.

        This should be overridden by subclasses if a filter should be used.

        """
        gitignore_filter = IgnoreParser()

        # TODO make this configurable
        gitignore_filter.add_rule("**/__pycache__*", self.project.dependency_directory)
        gitignore_filter.add_rule("**/*.dist-info*", self.project.dependency_directory)
        gitignore_filter.add_rule("**/*.py[c|o]", self.project.dependency_directory)
        return gitignore_filter
