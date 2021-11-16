"""Dedicated lookups for use with :class:`~awslambda.base_classes.AwsLambdaHook` based hooks.

.. important::
    These lookusp does not support arguments.
    Any arguments passed to the lookups will be discarded.

.. note::
    To use these lookups during development, they must be manually registered
    in the CFNgin configuration file. To simplify this, registering
    :class:`awslambda_lookup.AwsLambdaLookup` registers all related lookups.

    .. code-block:: yaml
      :caption: Example

      lookups:
        awslambda: awslambda_lookup.AwsLambdaLookup

"""
import sys

from runway.cfngin.lookups.registry import register_lookup_handler

from ._lookup import AwsLambdaLookup

if sys.version_info < (3, 8):  # cov: ignore
    # importlib.metadata is standard lib for python>=3.8, use backport
    from importlib_metadata import (  # type: ignore # pylint: disable=E
        PackageNotFoundError,
        version,
    )
else:
    from importlib.metadata import (  # type: ignore # pylint: disable=E
        PackageNotFoundError,
        version,
    )

__all__ = ["__version__", "AwsLambdaLookup"]

# quick way to register everything with one line in the CFNgin config file
register_lookup_handler(AwsLambdaLookup.Code.TYPE_NAME, AwsLambdaLookup.Code)
register_lookup_handler(
    AwsLambdaLookup.CodeSha256.TYPE_NAME, AwsLambdaLookup.CodeSha256
)
register_lookup_handler(
    AwsLambdaLookup.CompatibleArchitectures.TYPE_NAME,
    AwsLambdaLookup.CompatibleArchitectures,
)
register_lookup_handler(
    AwsLambdaLookup.CompatibleRuntimes.TYPE_NAME, AwsLambdaLookup.CompatibleRuntimes
)
register_lookup_handler(
    AwsLambdaLookup.LicenseInfo.TYPE_NAME, AwsLambdaLookup.LicenseInfo
)
register_lookup_handler(AwsLambdaLookup.Runtime.TYPE_NAME, AwsLambdaLookup.Runtime)
register_lookup_handler(AwsLambdaLookup.S3Bucket.TYPE_NAME, AwsLambdaLookup.S3Bucket)
register_lookup_handler(AwsLambdaLookup.S3Key.TYPE_NAME, AwsLambdaLookup.S3Key)
register_lookup_handler(
    AwsLambdaLookup.S3ObjectVersion.TYPE_NAME, AwsLambdaLookup.S3ObjectVersion
)

try:  # cov: ignore
    __version__ = version(__name__)
except PackageNotFoundError:  # cov: ignore
    # package is not installed
    __version__ = "0.0.0"
