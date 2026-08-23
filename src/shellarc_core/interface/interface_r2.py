from typing import (
    Protocol, overload, runtime_checkable
)
from pathlib import Path


@runtime_checkable
class IR2_IO(Protocol):
    """Structural interface for R2 storage I/O operations.

    Any object exposing these methods/attributes satisfies this Protocol,
    regardless of whether it explicitly inherits from it. Use this type
    wherever R2 storage access is needed (constructor args, function params)
    instead of the concrete `R2_IO` class, so implementations can be swapped
    (real client, mock, stub) without changing consumer code.

    NOTE: `s3_client` and construction/config-loading are intentionally
    excluded — they're implementation details of `R2_IO`, not part of the
    behavioral contract consumers depend on.
    """

    bucket_name: str

    def get_s3obj_size(self,
                        target_s3_file: str
                        ) -> int:
        """Get the size of the specified S3 object in MB."""
        ...

    def issue_presigned_url(self,
                             target_s3_file: str,
                             url_client_method: str,
                             http_method: str,
                             time_limit: int = 180
                             ) -> str:
        """Issue a presigned URL for temporary access to an S3 object."""
        ...

    def get_path_with_ext(self,
                           path_without_ext: str
                           ) -> str:
        """Resolve the full key (with extension) for a given path prefix."""
        ...

    def get_paths_with_prefix(self,
                               file_prefix: str
                               ) -> list[str] | None:
        """List all object keys under a given prefix."""
        ...

    @overload
    def upload_file(self,
                     uploading_file: bytes | str | Path,
                     file_path: str | Path,
                     url_prefix: str
                     ) -> str: ...

    @overload
    def upload_file(self,
                     uploading_file: bytes | str | Path,
                     file_path: str | Path,
                     url_prefix: None
                     ) -> None: ...

    def upload_file(self,
                     uploading_file: bytes | str | Path,
                     file_path: str | Path,
                     url_prefix: str | None = None
                     ) -> str | None:
        """Upload a file (from bytes or local path) to R2 storage."""
        ...

    def download_file(self,
                       to_download_file: str,
                       download_destination: str,
                       file_naming: str
                       ) -> None:
        """Download a file from R2 storage to a local destination."""
        ...
