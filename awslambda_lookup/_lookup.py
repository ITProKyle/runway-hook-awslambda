"""Dedicated lookup for use with :class:`~awslambda.base_classes.AwsLambdaHook` based hooks.

.. important::
    This lookup does not support arguments.
    Any arguments passed to the lookup directly will be discarded.

.. note::
    To use this lookup during development, it must be manually registered in the
    CFNgin configuration file. To simplify this, registering
    :class:`awslambda_lookup.AwsLambdaLookup` registers all related lookups.

    .. code-block:: yaml
      :caption: Example

      lookups:
        awslambda: awslambda_lookup.AwsLambdaLookup

To use this hook, there must be a :class:`~awslambda.base_classes.AwsLambdaHook`
based hook defined in the :attr:`~cfngin.config.pre_deploy` section of the CFNgin
configuration file. This hook must also define a :attr:`~cfngin.hook.data_key`
that is unique within the CFNgin configuration file (it can be reused in other
CFNgin configuration files). The :attr:`~cfngin.hook.data_key` is then passed
to the lookup as it's input/query. This allows the lookup to function during a
``runway plan``.

"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Final, List, Optional, Union, cast

from pydantic import ValidationError
from runway.context import RunwayContext
from runway.lookups.handlers.base import LookupHandler
from runway.utils import load_object_from_string
from troposphere.awslambda import Code
from typing_extensions import Literal

from awslambda.base_classes import AwsLambdaHook
from awslambda.models.responses import AwsLambdaHookDeployResponse

from .exceptions import CfnginOnlyLookupError

if TYPE_CHECKING:
    from runway.config import CfnginConfig
    from runway.config.models.cfngin import CfnginHookDefinitionModel
    from runway.context import CfnginContext

LOGGER = logging.getLogger(f"runway.{__name__}")


class AwsLambdaLookup(LookupHandler):
    """Lookup for :class:`~awslambda.base_classes.AwsLambdaHook` responses."""

    TYPE_NAME: Final[Literal["awslambda"]] = "awslambda"

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
                "expected AwsLambdaHookDeployResponseTypedDict, "
                f"not {context.hook_data[data_key]}"
            ) from None

    @staticmethod
    def get_required_hook_definition(
        config: CfnginConfig, data_key: str
    ) -> CfnginHookDefinitionModel:
        """Get the required Hook definition from the CFNgin config.

        Currently, this only supports finding the data_key pre_deploy.

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
            hook_def for hook_def in config.pre_deploy if hook_def.data_key == data_key
        ]
        if not hooks_with_data_key:
            raise ValueError(f"no hook definition found with data_key {data_key}")
        if len(hooks_with_data_key) > 1:
            raise ValueError(
                f"more than one hook definition found with data_key {data_key}"
            )
        return hooks_with_data_key.pop()

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
        # checks for RunwayContext to allow mocks to pass
        if isinstance(context, RunwayContext):
            raise CfnginOnlyLookupError(  # TODO make this an exception in the runway repo
                cls.TYPE_NAME
            )
        query, _ = cls.parse(value)
        return cls.get_deployment_package_data(context, query)

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
        if (
            not isinstance(kls, type)
            or not hasattr(kls, "__subclasscheck__")
            or not issubclass(kls, AwsLambdaHook)
        ):
            raise TypeError(
                f"hook path {hook_def.path} for hook with data_key {hook_def.data_key} "
                "must be a subclass of AwsLambdaHook to use this lookup"
            )
        return cast(AwsLambdaHook[Any], kls(context, **hook_def.args))

    class Code(LookupHandler):
        """Lookup for :class:`~awslambda.base_classes.AwsLambdaHook` responses."""

        TYPE_NAME: Final[Literal["awslambda.Code"]] = "awslambda.Code"

        @classmethod
        def handle(  # pylint: disable=arguments-differ
            cls,
            value: str,
            context: Union[CfnginContext, RunwayContext],
            *args: Any,
            **kwargs: Any,
        ) -> Code:
            """Retrieve metadata for an AWS Lambda deployment package.

            Args:
                value: Value to resolve.
                context: The current context object.

            Returns:
                Value that can be passed into CloudFormation property
                ``AWS::Lambda::Function.Code``.

            """
            return Code(
                **AwsLambdaLookup.handle(value, context, *args, **kwargs).dict(
                    by_alias=True,
                    exclude_none=True,
                    include={"bucket_name", "object_key", "object_version_id"},
                )
            )

    class CodeSha256(LookupHandler):
        """Lookup for :class:`~awslambda.base_classes.AwsLambdaHook` responses."""

        TYPE_NAME: Final[Literal["awslambda.CodeSha256"]] = "awslambda.CodeSha256"

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
                Value that can be passed into CloudFormation property
                ``AWS::Lambda::Version.CodeSha256``.

            """
            return AwsLambdaLookup.handle(value, context, *args, **kwargs).code_sha256

    class CompatibleArchitectures(LookupHandler):
        """Lookup for :class:`~awslambda.base_classes.AwsLambdaHook` responses."""

        TYPE_NAME: Final[
            Literal["awslambda.CompatibleArchitectures"]
        ] = "awslambda.CompatibleArchitectures"

        @classmethod
        def handle(  # pylint: disable=arguments-differ
            cls,
            value: str,
            context: Union[CfnginContext, RunwayContext],
            *args: Any,
            **kwargs: Any,
        ) -> Optional[List[str]]:
            """Retrieve metadata for an AWS Lambda deployment package.

            Args:
                value: Value to resolve.
                context: The current context object.

            Returns:
                Value that can be passed into CloudFormation property
                ``AWS::Lambda::LayerVersion.CompatibleArchitectures``.

            """
            _query, lookup_args = cls.parse(value)
            return cls.format_results(
                AwsLambdaLookup.handle(
                    value, context, *args, **kwargs
                ).compatible_architectures,
                **lookup_args,
            )

    class CompatibleRuntimes(LookupHandler):
        """Lookup for :class:`~awslambda.base_classes.AwsLambdaHook` responses."""

        TYPE_NAME: Final[
            Literal["awslambda.CompatibleRuntimes"]
        ] = "awslambda.CompatibleRuntimes"

        @classmethod
        def handle(  # pylint: disable=arguments-differ
            cls,
            value: str,
            context: Union[CfnginContext, RunwayContext],
            *args: Any,
            **kwargs: Any,
        ) -> Any:
            """Retrieve metadata for an AWS Lambda deployment package.

            Args:
                value: Value to resolve.
                context: The current context object.

            Returns:
                Value that can be passed into CloudFormation property
                ``AWS::Lambda::LayerVersion.CompatibleRuntimes``.

            """
            _query, lookup_args = cls.parse(value)
            return cls.format_results(
                AwsLambdaLookup.handle(
                    value, context, *args, **kwargs
                ).compatible_runtimes,
                **lookup_args,
            )

    class LicenseInfo(LookupHandler):
        """Lookup for :class:`~awslambda.base_classes.AwsLambdaHook` responses."""

        TYPE_NAME: Final[Literal["awslambda.LicenseInfo"]] = "awslambda.LicenseInfo"

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
                Value that can be passed into CloudFormation property
                ``AWS::Lambda::LayerVersion.LicenseInfo``.

            """
            _query, lookup_args = cls.parse(value)
            return cls.format_results(
                AwsLambdaLookup.handle(value, context, *args, **kwargs).license,
                **lookup_args,
            )

    class Runtime(LookupHandler):
        """Lookup for :class:`~awslambda.base_classes.AwsLambdaHook` responses."""

        TYPE_NAME: Final[Literal["awslambda.Runtime"]] = "awslambda.Runtime"

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
                Value that can be passed into CloudFormation property
                ``AWS::Lambda::Function.Runtime``.

            """
            return AwsLambdaLookup.handle(value, context, *args, **kwargs).runtime

    class S3Bucket(LookupHandler):
        """Lookup for :class:`~awslambda.base_classes.AwsLambdaHook` responses."""

        TYPE_NAME: Final[Literal["awslambda.S3Bucket"]] = "awslambda.S3Bucket"

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
                Value that can be passed into CloudFormation property
                ``AWS::Lambda::Function.Code.S3Bucket`` or
                ``AWS::Lambda::LayerVersion.Content.S3Bucket``.

            """
            return AwsLambdaLookup.handle(value, context, *args, **kwargs).bucket_name

    class S3Key(LookupHandler):
        """Lookup for :class:`~awslambda.base_classes.AwsLambdaHook` responses."""

        TYPE_NAME: Final[Literal["awslambda.S3Key"]] = "awslambda.S3Key"

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
                Value that can be passed into CloudFormation property
                ``AWS::Lambda::Function.Code.S3Key`` or
                ``AWS::Lambda::LayerVersion.Content.S3Key``.

            """
            return AwsLambdaLookup.handle(value, context, *args, **kwargs).object_key

    class S3ObjectVersion(LookupHandler):
        """Lookup for :class:`~awslambda.base_classes.AwsLambdaHook` responses."""

        TYPE_NAME: Final[
            Literal["awslambda.S3ObjectVersion"]
        ] = "awslambda.S3ObjectVersion"

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
                Value that can be passed into CloudFormation property
                ``AWS::Lambda::Function.Code.S3ObjectVersion`` or
                ``AWS::Lambda::LayerVersion.Content.S3ObjectVersion``.

            """
            return AwsLambdaLookup.handle(
                value, context, *args, **kwargs
            ).object_version_id
