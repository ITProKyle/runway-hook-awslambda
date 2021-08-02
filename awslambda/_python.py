"""Hook for creating an AWS Lambda Function using Python runtime."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, ClassVar, Type

from runway.compat import cached_property

from .base_classes import FunctionHook
from .models.args import PythonFunctionHookArgs
from .python_requirements.deployment_package import PythonDeploymentPackage
from .python_requirements.python_project import PythonProject

if TYPE_CHECKING:
    pass

LOGGER = logging.getLogger(f"runway.{__name__}")


class PythonFunction(FunctionHook[PythonFunctionHookArgs, PythonProject]):
    """Hook for creating an AWS Lambda Function using Python runtime."""

    ARGS_PARSER: ClassVar[Type[PythonFunctionHookArgs]] = PythonFunctionHookArgs

    args: PythonFunctionHookArgs

    @cached_property
    def deployment_package(self) -> PythonDeploymentPackage:
        """AWS Lambda deployment package."""
        return PythonDeploymentPackage(self.project)

    @cached_property
    def project(self) -> PythonProject:
        """Project being deployed as an AWS Lambda Function."""
        return PythonProject(self.args, self.context)

    def cleanup(self) -> None:
        """Cleanup."""
        self.project.cleanup()

    def pre_deploy(self) -> Any:
        """Run during the **pre_deploy** stage."""
        self.project.pip.install(
            requirements=self.project.requirements_txt,
            target=self.project.dependency_directory,
        )
        self.deployment_package.build()
        self.cleanup()
        return True
