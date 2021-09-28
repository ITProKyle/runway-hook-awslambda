"""Lookup for :class:`~awslambda.base_classes.AwsLambdaHook` responses.

.. tip::
  To this the awslambda lookup, add the following to a CFNgin config.

  .. code-block:: yaml

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
register_lookup_handler(AwsLambdaLookup.Code.NAME, AwsLambdaLookup.Code)
register_lookup_handler(AwsLambdaLookup.CodeSha256.NAME, AwsLambdaLookup.CodeSha256)
register_lookup_handler(AwsLambdaLookup.Runtime.NAME, AwsLambdaLookup.Runtime)
register_lookup_handler(AwsLambdaLookup.S3Bucket.NAME, AwsLambdaLookup.S3Bucket)
register_lookup_handler(AwsLambdaLookup.S3Key.NAME, AwsLambdaLookup.S3Key)
register_lookup_handler(
    AwsLambdaLookup.S3ObjectVersion.NAME, AwsLambdaLookup.S3ObjectVersion
)

try:  # cov: ignore
    __version__ = version(__name__)
except PackageNotFoundError:  # cov: ignore
    # package is not installed
    __version__ = "0.0.0"
