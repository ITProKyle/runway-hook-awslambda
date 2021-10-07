"""Constant values."""
from runway.constants import DOT_RUNWAY_DIR

AWS_SAM_BUILD_IMAGE_PREFIX = (  #: Prefix for build image registries.
    "public.ecr.aws/sam/build-"
)
BASE_WORK_DIR = DOT_RUNWAY_DIR / "awslambda"
