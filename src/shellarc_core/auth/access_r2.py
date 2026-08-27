import os
from pathlib import Path

import boto3
from dotenv import load_dotenv

from shellarc_core.exception.structure_error import SA_AuthError, SA_ErrorCode


class Cloudflare_R2_service_Access:
    def __init__(self):
        load_dotenv(verbose=True)
        project_ctx_dir = Path(os.environ.get("SHELLARC_PROJECT_CTX", None))
        dotenv_path = project_ctx_dir / ".env"
        if not dotenv_path.exists():
            raise SA_AuthError(
                error_log=f"dotenv_path {dotenv_path} not exist",
                error_code=SA_ErrorCode.SA_9001
            )
        load_dotenv(dotenv_path)
        R2_ACCESS_KEY_ID = os.environ.get("CloudflareR2_access_key_id")
        R2_SECRET_ACCESS_KEY = os.environ.get("CloudflareR2_secret_access_key")
        R2_ENDPOINT_URL = os.environ.get("CloudflareR2_jurisdiction_specific_endpoints")

        try:
            self._s3_client = boto3.client(
                "s3",
                endpoint_url=R2_ENDPOINT_URL,
                aws_access_key_id=R2_ACCESS_KEY_ID,
                aws_secret_access_key=R2_SECRET_ACCESS_KEY,
                region_name="auto"
            )
        except Exception as e:
            self._s3_client = None
            raise SA_AuthError(
                error_log=f"Auth error in CloudflareR2 [{e}]",
                error_code=SA_ErrorCode.SA_9000
            )

    @property
    def s3_client(self) -> boto3.client:
        """Get the Cloudflare R2 S3 client instance (Property)

        Returns:
            _s3_client (boto3.client): The S3 client instance for Cloudflare R2 operations.
        """
        return self._s3_client
        