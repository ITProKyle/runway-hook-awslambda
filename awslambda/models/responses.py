"""Response data models."""
from typing import Optional

from pydantic import Extra, Field
from runway.utils import BaseModel


class AwsLambdaHookDeployResponse(BaseModel):
    """Data model for AwsLambdaHook deploy response.

    When returned by the hook as ``hook_data``, this model is dumped to a
    standard :class:`~typing.Dict` using the field's aliases as the ``key`` in
    place of the attribute names.
    This is done so that the ``key`` is a direct match to a CloudFormation
    Property where the value should be used.

    Attributes:
        bucket_name: Name of the S3 Bucket where the deployment package is
            located. (alias: ``S3Bucket``)
        code_sha256: SHA256 of the deployment package. This can be used by
            CloudFormation as the value of ``AWS::Lambda::Version.CodeSha256``.
            (alias: ``CodeSha256``)
        object_key: Key (file path) of the deployment package S3 Object.
            (alias: ``S3Key``)
        object_version_id: The version ID of the deployment package S3 Object.
            This will only have a value if the S3 Bucket has versioning enabled.
            (alias: ``S3ObjectVersion``)
        runtime: Runtime of the Lambda Function. (alias: ``Runtime``)

    """

    bucket_name: str = Field(..., alias="S3Bucket")
    code_sha256: str = Field(..., alias="CodeSha256")
    object_key: str = Field(..., alias="S3Key")
    object_version_id: Optional[str] = Field(None, alias="S3ObjectVersion")
    runtime: str = Field(..., alias="Runtime")

    class Config:
        """Model configuration."""

        allow_population_by_field_name = True
        extra = Extra.forbid
