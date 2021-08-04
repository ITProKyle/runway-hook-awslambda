"""Response data models."""
from typing import Optional

from pydantic import Extra, Field
from runway.utils import BaseModel


class AwsLambdaHookDeployResponse(BaseModel):
    """Data model for AwsLambdaHook deploy response."""

    bucket_name: str = Field(..., alias="S3Bucket")
    code_sha256: str = Field(..., alias="CodeSha256")
    object_key: str = Field(..., alias="S3Key")
    object_version: Optional[str] = Field(None, alias="S3ObjectVersion")

    class Config:
        """Model configuration."""

        allow_population_by_field_name = True
        extra = Extra.forbid
