"""AWS Lambda Python Deployment Package."""
from __future__ import annotations

import igittigitt

from ..base_classes import DeploymentPackage
from .python_project import PythonProject


class PythonDeploymentPackage(DeploymentPackage[PythonProject]):
    """AWS Lambda Python Deployment Package."""

    gitignore_filter: igittigitt.IgnoreParser
    project: PythonProject

    def __init__(
        self,
        project: PythonProject,
    ) -> None:
        """Instantiate class.

        Args:
            project: Project that is being built into a deployment package.
            gitignore_filter: Filter to use when zipping dependencies.
                If file/folder matches the filter, it should be ignored.

        """
        super().__init__(project, gitignore_filter=igittigitt.IgnoreParser())

        # TODO make this configurable
        self.gitignore_filter.add_rule(
            "**/__pycache__*", self.project.dependency_directory
        )
        # self.gitignore_filter.add_rule("**/bin", self.project.dependency_directory)
        self.gitignore_filter.add_rule(
            "**/*.dist-info***/*.dist-info*", self.project.dependency_directory
        )
        self.gitignore_filter.add_rule(
            "**/*.py[c|o]", self.project.dependency_directory
        )
