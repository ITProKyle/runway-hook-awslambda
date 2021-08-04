"""Top-level exceptions."""
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
