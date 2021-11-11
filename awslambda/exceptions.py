"""High-level exceptions."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict

from runway.cfngin.exceptions import CfnginError
from runway.exceptions import RunwayError

if TYPE_CHECKING:
    from pathlib import Path

    from runway.core.providers.aws.s3 import Bucket


class BucketAccessDeniedError(CfnginError):  # TODO should this be a RunwayError?
    """Access denied to S3 Bucket."""

    bucket_name: str
    """Name of the S3 Bucket."""

    def __init__(self, bucket: Bucket) -> None:
        """Instantiate class.

        Args:
            bucket: AWS S3 Bucket object.

        """
        self.bucket_name = bucket.name
        self.message = f"access denied for bucket {bucket.name}"
        super().__init__()


class BucketNotFoundError(CfnginError):  # TODO should this be a RunwayError?
    """S3 Bucket not found."""

    bucket_name: str
    """Name of the S3 Bucket"""

    def __init__(self, bucket: Bucket) -> None:
        """Instantiate class.

        Args:
            bucket: AWS S3 Bucket object.

        """
        self.bucket_name = bucket.name
        self.message = f"bucket {bucket.name} not found"
        super().__init__()


class DeploymentPackageEmptyError(CfnginError):
    """Deployment package is empty.

    This can be caused by an incorrect source code directory or a gitignore rule
    unintentionally ignoring all source code.

    Any empty deployment package is determined by checking the size of the
    archive file. If the size is <=22 (the size a zip file End of Central
    Directory Record) it has no contents.

    """

    archive_file: Path
    """The deployment package archive file."""

    def __init__(self, archive_file: Path) -> None:
        """Instantiate class.

        Args:
            archive_file: The empty archive file.

        """
        self.message = f"{archive_file.name} contains no files"
        super().__init__()


class DockerConnectionRefusedError(RunwayError):  # TODO move to runway.exceptions
    """Docker connection refused.

    This can be caused by a number of reasons:

    - Docker is not installed.
    - Docker service is not running.
    - The current user does not have adequate permissions (e.g. not a member of
      the ``docker`` group).

    """

    def __init__(self) -> None:
        """Instantiate class."""
        self.message = (
            "Docker connection refused; install Docker, ensure it is running, "
            "and ensure the current user has adequate permissions"
        )
        super().__init__()


class DockerExecFailedError(RunwayError):  # TODO move to runway.exceptions
    """Docker failed when trying to execute a command.

    This can be used for ``docker container run``, ``docker container start``
    and ``docker exec`` equivalents.

    """

    exit_code: int
    """The ``StatusCode`` returned by Docker."""

    def __init__(self, response: Dict[str, Any]) -> None:
        """Instantiate class.

        Args:
            response: The return value of :meth:`docker.models.containers.Container.wait`,
                Docker API's response as a Python dictionary.
                This can contain important log information pertinant to troubleshooting
                that may not streamed.

        """
        self.exit_code = response.get("StatusCode", 1)  # we can assume this will be > 0
        self.message = response.get("Error", {}).get(
            "Message", "error message undefined"
        )
        super().__init__()


class RequiredTagNotFoundError(CfnginError):  # TODO should this be a RunwayError?
    """Required tag not found on resource."""

    resource: str
    """An ID or name to identify a resource."""

    tag_key: str
    """Key of the tag that could not be found."""

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


class RuntimeMismatchError(CfnginError):
    """Required runtime does not match the detected runtime."""

    detected_runtime: str
    """Runtime detected on the build system."""

    expected_runtime: str
    """Explicitly defined runtime that was expected."""

    def __init__(self, expected_runtime: str, detected_runtime: str) -> None:
        """Instantiate class.

        Args:
            expected_runtime: Explicitly defined runtime that was expected.
            detected_runtime: Runtime detected on the build system.

        """
        self.detected_runtime = detected_runtime
        self.expected_runtime = expected_runtime
        self.message = (
            f"{detected_runtime} runtime determined from the build system"
            f" does not match the expected {expected_runtime} runtime"
        )
        super().__init__()
