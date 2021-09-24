"""Lookup for :class:`~awslambda.base_classes.AwsLambdaHook` responses."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, ClassVar, Optional, Union, cast

from pydantic import ValidationError
from runway.context import RunwayContext
from runway.lookups.handlers.base import LookupHandler
from runway.utils import load_object_from_string

from awslambda.base_classes import AwsLambdaHook
from awslambda.models.responses import AwsLambdaHookDeployResponse

from .exceptions import CfnginOnlyLookupError

if TYPE_CHECKING:
    from runway.config import CfnginConfig
    from runway.config.models.cfngin import CfnginHookDefinitionModel
    from runway.context import CfnginContext

LOGGER = logging.getLogger(f"runway.{__name__}")


class AwsLambdaLookup(LookupHandler):
    """Lookup for :class:`~awslambda.base_classes.AwsLambdaHook` responses.

    .. important::
        The :class:`~awslambda.base_classes.AwsLambdaHook` must be defined in
        the current config file with a :attr:`~cfngin.hook.data_key`.

    .. important::
        This lookup does not support arguments.

    """

    NAME: ClassVar[str] = "awslambda"

    @classmethod
    def get_deployment_package_data(
        cls, context: CfnginContext, data_key: str
    ) -> AwsLambdaHookDeployResponse:
        """Get the response of a :class:`~awslambda.base_classes.AwsLambdaHook` run.

        Args:
            context: CFNgin context object.
            data_key: The value of the ``data_key`` field as assigned in a
                Hook definition.

        Returns:
            The :class:`~awslambda.base_classes.AwsLambdaHook` response parsed
            into a data model. This will come from hook data if it exists or it
            will be calculated and added to hook data for future use.

        Raises:
            TypeError: The data stored in hook data does not align with the
                expected data model.

        """
        if data_key not in context.hook_data:
            LOGGER.debug("%s missing from hook_data; attempting to get value", data_key)
            hook = cls.init_hook_class(
                context, cls.get_required_hook_definition(context.config, data_key)
            )
            context.set_hook_data(data_key, hook.plan())
        try:
            return AwsLambdaHookDeployResponse.parse_obj(context.hook_data[data_key])
        except ValidationError:
            raise TypeError(
                "expected hook_data of type AwsLambdaHookDeployResponseTypedDict; "
                f"got {type(context.hook_data[data_key])}"
            ) from None

    @staticmethod
    def get_required_hook_definition(
        config: CfnginConfig, data_key: str
    ) -> CfnginHookDefinitionModel:
        """Get the required Hook definition from the CFNgin config.

        Currently, this only supports finding the data_key in ONE stage.

        Args:
            config: CFNgin config being processed.
            data_key: The value of the ``data_key`` field as assigned in a
                Hook definition.

        Returns:
            The Hook definition set to use the provided ``data_key``.

        Raises:
            ValueError: Either a Hook definition was not found for the provided
                ``data_key`` or, more than one was found.

        """
        hooks_with_data_key = [
            hook_def
            for hook_def in [
                *config.pre_deploy,
                *config.pre_destroy,
                *config.post_deploy,
                *config.post_destroy,
            ]
            if hook_def.data_key == data_key
        ]
        if not hooks_with_data_key:
            raise ValueError("no hook found")
        if len(hooks_with_data_key) > 1:
            raise ValueError("more than one hook definition found with data_key")
        return hooks_with_data_key.pop()

    @staticmethod
    def init_hook_class(
        context: CfnginContext, hook_def: CfnginHookDefinitionModel
    ) -> AwsLambdaHook[Any]:
        """Initialize :class:`~awslambda.base_classes.AwsLambdaHook` subclass instance.

        Args:
            context: CFNgin context object.
            hook_def: The :class:`~awslambda.base_classes.AwsLambdaHook` definition.

        Returns:
            The loaded AwsLambdaHook object.

        """
        kls = load_object_from_string(hook_def.path)
        if not issubclass(kls, AwsLambdaHook):
            raise TypeError(
                "hook path must be a subclass of AwsLambdaHook to use this lookup"
            )
        return cast(AwsLambdaHook[Any], kls(context, **hook_def.args))

    @classmethod
    def handle(  # pylint: disable=arguments-differ
        cls,
        value: str,
        context: Union[CfnginContext, RunwayContext],
        *_args: Any,
        **_kwargs: Any,
    ) -> AwsLambdaHookDeployResponse:
        """Retrieve metadata for an AWS Lambda deployment package.

        Args:
            value: Value to resolve.
            context: The current context object.

        Returns:
            The full :class:`~awslambda.models.response.AwsLambdaHookDeployResponse`
            data model.

        """
        if isinstance(context, RunwayContext):
            raise CfnginOnlyLookupError(  # TODO make this an exception in the runway repo
                cls.NAME
            )
        query, _ = cls.parse(value)
        return cls.get_deployment_package_data(context, query)

    class CodeSha256(LookupHandler):
        """Lookup for :class:`~awslambda.base_classes.AwsLambdaHook` responses."""

        NAME: ClassVar[str] = "awslambda.CodeSha256"

        @classmethod
        def handle(  # pylint: disable=arguments-differ
            cls,
            value: str,
            context: Union[CfnginContext, RunwayContext],
            *args: Any,
            **kwargs: Any,
        ) -> str:
            """Retrieve metadata for an AWS Lambda deployment package.

            Args:
                value: Value to resolve.
                context: The current context object.

            Returns:
                Value that can be passed into CloudFormation resource as the
                ``CodeSha256`` property.

            """
            return AwsLambdaLookup.handle(value, context, *args, **kwargs).code_sha256

    class Runtime(LookupHandler):
        """Lookup for :class:`~awslambda.base_classes.AwsLambdaHook` responses."""

        NAME: ClassVar[str] = "awslambda.Runtime"

        @classmethod
        def handle(  # pylint: disable=arguments-differ
            cls,
            value: str,
            context: Union[CfnginContext, RunwayContext],
            *args: Any,
            **kwargs: Any,
        ) -> str:
            """Retrieve metadata for an AWS Lambda deployment package.

            Args:
                value: Value to resolve.
                context: The current context object.

            Returns:
                Value that can be passed into CloudFormation resource as the
                ``Runtime`` property.

            """
            return AwsLambdaLookup.handle(value, context, *args, **kwargs).runtime

    class S3Bucket(LookupHandler):
        """Lookup for :class:`~awslambda.base_classes.AwsLambdaHook` responses."""

        NAME: ClassVar[str] = "awslambda.S3Bucket"

        @classmethod
        def handle(  # pylint: disable=arguments-differ
            cls,
            value: str,
            context: Union[CfnginContext, RunwayContext],
            *args: Any,
            **kwargs: Any,
        ) -> str:
            """Retrieve metadata for an AWS Lambda deployment package.

            Args:
                value: Value to resolve.
                context: The current context object.

            Returns:
                Value that can be passed into CloudFormation resource as the
                ``S3Bucket`` property.

            """
            return AwsLambdaLookup.handle(value, context, *args, **kwargs).bucket_name

    class S3Key(LookupHandler):
        """Lookup for :class:`~awslambda.base_classes.AwsLambdaHook` responses."""

        NAME: ClassVar[str] = "awslambda.S3Key"

        @classmethod
        def handle(  # pylint: disable=arguments-differ
            cls,
            value: str,
            context: Union[CfnginContext, RunwayContext],
            *args: Any,
            **kwargs: Any,
        ) -> str:
            """Retrieve metadata for an AWS Lambda deployment package.

            Args:
                value: Value to resolve.
                context: The current context object.

            Returns:
                Value that can be passed into CloudFormation resource as the
                ``S3Key`` property.

            """
            return AwsLambdaLookup.handle(value, context, *args, **kwargs).object_key

    class S3ObjectVersion(LookupHandler):
        """Lookup for :class:`~awslambda.base_classes.AwsLambdaHook` responses."""

        NAME: ClassVar[str] = "awslambda.S3ObjectVersion"

        @classmethod
        def handle(  # pylint: disable=arguments-differ
            cls,
            value: str,
            context: Union[CfnginContext, RunwayContext],
            *args: Any,
            **kwargs: Any,
        ) -> Optional[str]:
            """Retrieve metadata for an AWS Lambda deployment package.

            Args:
                value: Value to resolve.
                context: The current context object.

            Returns:
                Value that can be passed into CloudFormation resource as the
                ``S3ObjectVersion`` property.

            """
            return AwsLambdaLookup.handle(
                value, context, *args, **kwargs
            ).object_version_id


TYPE_NAME = AwsLambdaLookup.NAME
