"""Hook for creating an AWS Lambda Function using Python runtime."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from runway.compat import cached_property

from .base_classes import FunctionHook
from .models.args import PythonFunctionHookArgs
from .python_requirements import PythonDeploymentPackage, PythonProject

if TYPE_CHECKING:
    from runway.context import CfnginContext

    from .base_classes import DeploymentPackage

LOGGER = logging.getLogger(f"runway.{__name__}")


class PythonFunction(FunctionHook[PythonProject]):
    """Hook for creating an AWS Lambda Function using Python runtime."""

    args: PythonFunctionHookArgs

    def __init__(self, context: CfnginContext, **kwargs: Any) -> None:
        """Instantiate class."""
        super().__init__(context)
        self.args = PythonFunctionHookArgs.parse_obj(kwargs)

    @cached_property
    def deployment_package(self) -> DeploymentPackage[PythonProject]:
        """AWS Lambda deployment package."""
        return PythonDeploymentPackage.init(self.project)

    @cached_property
    def project(self) -> PythonProject:
        """Project being deployed as an AWS Lambda Function."""
        return PythonProject(self.args, self.ctx)

    def cleanup(self) -> None:
        """Cleanup after execution."""
        self.project.cleanup()

    def cleanup_on_error(self) -> None:
        """Cleanup after an error has occurred."""
        self.deployment_package.delete()
        self.project.cleanup_on_error()

    def pre_deploy(self) -> Any:
        """Run during the **pre_deploy** stage."""
        try:
            self.deployment_package.upload()
            return self.build_response("deploy").dict(by_alias=True)
        except BaseException:
            self.cleanup_on_error()
            raise
        finally:
            self.cleanup()
