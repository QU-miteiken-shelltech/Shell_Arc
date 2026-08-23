from typing import Protocol, runtime_checkable, overload
from pathlib import Path


@runtime_checkable
class Interface_R2(Protocol):
    """Protocol interface for R2 (Cloudflare R2 / S3-compatible) storage IO operations.
    """

    def get_s3obj_size(self,
                       target_s3_file: str
                       ) -> int:
        """Get the size of the specified S3 object in megabytes (MB).

        Args:
            target_s3_file (str): The key (file path) of the S3 object to get the size of.

        Returns:
            int: The size of the S3 object in megabytes (MB).
        """
        ...

    def issue_presigned_url(self,
                            target_s3_file: str,
                            url_client_method: str,
                            http_method: str,
                            time_limit: int = 180
                            ) -> str:
        """Issue a presigned URL for the specified S3 object in the R2 storage.

        Args:
            target_s3_file (str): The key (file path) of the S3 object to issue the presigned URL for.
            url_client_method (str): The S3 client method to generate the presigned URL for (e.g., "get_object", "put_object").
            http_method (str): The HTTP method to be used with the presigned URL (e.g., "GET", "PUT").
            time_limit (int): The expiration time for the presigned URL in seconds (Default : 180).

        Returns:
            presigned_url (str): The generated presigned URL for the specified S3 object.
        """
        ...

    def get_path_with_ext(self,
                          path_without_ext: str
                          ) -> str:
        """Get the full path with extension for the specified path prefix.

        Args:
            path_without_ext (str): The file path prefix without extension.

        Returns:
            str: The exact path with extension.
        """
        ...

    def get_paths_with_prefix(self,
                              file_prefix: str
                              ) -> list[str] | None:
        """Get all paths matching the specified prefix.

        Args:
            file_prefix (str): The file path prefix to search for.

        Returns:
            list[str] | None: A list of matching paths, or None if no matches found.
        """
        ...

    def upload_file(self,
                    uploading_file: bytes | str | Path,
                    file_path: str | Path,
                    url_prefix: str | None = None
                    ) -> str | None:
        """Upload a file to the R2 storage.

        Args:
            uploading_file (bytes | str | Path): The file to be uploaded (bytes content, local file path, or Path object).
            file_path (str | Path): The destination file path in the R2 storage.
            url_prefix (str | None): The URL prefix for constructing the public URL. If None, no URL is returned.

        Returns:
            str | None: The public URL of the uploaded file if url_prefix is provided, otherwise None.
        """
        ...

    def download_file(self,
                      to_download_file: str,
                      download_destination: str,
                      file_naming: str
                      ) -> None:
        """Download a file from the R2 storage to a specified local destination.

        Args:
            to_download_file (str): The key (file path) of the file in the R2 storage to be downloaded.
            download_destination (str): The local directory path where the downloaded file should be saved.
            file_naming (str): The name to be given to the downloaded file.
        """
        ...
