"""High-level exceptions."""
from __future__ import annotations

from typing import TYPE_CHECKING

from runway.cfngin.exceptions import CfnginError

if TYPE_CHECKING:
    from runway.core.providers.aws.s3 import Bucket


class BucketAccessDenied(CfnginError):
    """Access denied to S3 Bucket."""

    bucket_name: str

    def __init__(self, bucket: Bucket) -> None:
        """Instantiate class.

        Args:
            bucket: AWS S3 Bucket object.

        """
        self.bucket_name = bucket.name
        self.message = f"access denied for bucket {bucket.name}"
        super().__init__()


class BucketNotFound(CfnginError):
    """S3 Bucket not found."""

    bucket_name: str

    def __init__(self, bucket: Bucket) -> None:
        """Instantiate class.

        Args:
            bucket: AWS S3 Bucket object.

        """
        self.bucket_name = bucket.name
        self.message = f"bucket {bucket.name} not found"
        super().__init__()


class RequiredTagNotFound(CfnginError):
    """Required tag not found on resource."""

    resource: str
    tag_key: str

    def __init__(self, resource: str, tag_key: str) -> None:
        """Instantiate class.

        Args:
            resource: An ID or name to identify a resource.
            tag_key: Key of the tag that could not be found.

        """
        self.resource = resource
        self.tag_key = tag_key
        self.message = f"required tag '{tag_key}' not found for {resource}"
        super().__init__()
