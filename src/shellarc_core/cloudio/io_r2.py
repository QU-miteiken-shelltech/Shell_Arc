import tempfile
import datetime
import os
import time
from typing import overload, Union
from pathlib import Path

import boto3

from shellarc_core.auth.access_r2 import Cloudflare_R2_service_Access as A_R2
from shellarc_core.cfg.cfg_io import Cfg_IO as Cfg_IO
from shellarc_core.cfg.cfg_io import Cfg_item
from shellarc_core.exception.structure_error import (
    SA_ProjStructError, SA_CommunicationError, SA_ErrorCode
)

class R2_IO:
    def __init__(self, 
                 bucket_name: str | None=None
                 ):
        a_r2 = A_R2()
        self.s3_client: boto3.client = a_r2.s3_client
        cfg_io = Cfg_IO()
        self.bucket_name = cfg_io.get_cfg_setting(Cfg_item.BUCKET_NAME) if bucket_name is None else bucket_name


    def get_s3obj_size(self,
                       target_s3_file: str
                       ) -> int:
        """Get the size of the specified S3 object in megabytes (MB) by retrieving the object's metadata from the R2 storage.

        Args:
            target_s3_file (str): The key (file path) of the S3 object to get the size of.

        Returns:
            int: The size of the S3 object in megabytes (MB).
        """
        s3_obj = self.s3_client.get_object(
            Bucket=self.bucket_name,
            Key=target_s3_file,
        )
        size_bytes = float(s3_obj.get('ContentLength'))
        size_mb = size_bytes / 1024 / 1024
        return int(size_mb)


    def issue_presigned_url(self,
                            target_s3_file: str,
                            url_client_method: str,
                            http_method: str,
                            time_limit: int=180
                            ) -> str:
        """Issue a presigned URL for the specified S3 object in the R2 storage, allowing temporary access to the object for uploading or downloading.

        Args:
            target_s3_file (str): The key (file path) of the S3 object to issue the presigned URL for.
            url_client_method (str): The S3 client method to generate the presigned URL for (e.g., "get_object", "put_object").
            http_method (str): The HTTP method to be used with the presigned URL (e.g., "GET", "PUT").
            time_limit (int): The expiration time for the presigned URL in seconds (Default : 180).

        Returns:
            presigned_url (str): The generated presigned URL for the specified S3 object, 
                which can be used for temporary access to the object for uploading or downloading.
        """
        presigned_url = self.s3_client.generate_presigned_url(
            ClientMethod=url_client_method,
            Params={
                "Bucket" : self.bucket_name,
                "Key" : target_s3_file
            },
            ExpiresIn=time_limit,
            HttpMethod=http_method
        )
        return presigned_url
    
    def get_path_with_ext(self,
                          path_without_ext: str
                          ) -> str:
        response = self.s3_client.list_objects_v2(
            Bucket=self.bucket_name,
            Prefix=path_without_ext
            )
        exact_path_w_ext = response["Contents"][0]["Key"]
        return exact_path_w_ext
    
    def get_paths_with_prefix(self,
                              file_prefix: str
                              ) -> list[str]:
        response = self.s3_client.list_objects_v2(
            Bucket=self.bucket_name,
            Prefix=file_prefix
            )
        paths_list = [response["Contents"][i]["Key"] for i in range(0, len(response["Contents"]))]
        return paths_list
    
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
                    url_prefix: str | None=None
                    ) -> str | None:
        """Upload a file to the R2 storage by either directly uploading the file from a local path 
        or by writing the file content from bytes to a temporary file and then uploading it.

        Args:
            uploading_file (bytes | str | Path): The file to be uploaded, which can be provided as bytes content, 
                a local file path as a string, or a Path object.
            file_path (str | Path): The destination file path in the R2 storage where the file should be uploaded, 
                which can be provided as a string or a Path object.
        """
        if isinstance(file_path, Path):
            file_path = str(file_path)
        if uploading_file is None:
            raise SA_ProjStructError(
                error_log="Uploading file to R2 storage is None",
                error_code=SA_ErrorCode.SA_5101
            )
        if isinstance(uploading_file, bytes):
            with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                tmp_file.write(uploading_file)
                tmp_file_path = tmp_file.name
        else:
            if isinstance(uploading_file, Path):
                uploading_file = str(uploading_file)
            tmp_file_path = uploading_file
        try:
            self.s3_client.upload_file(
                tmp_file_path,
                self.bucket_name,
                file_path
            )
        except Exception as e:
            raise SA_CommunicationError(
                error_log=f"Communication error with R2 when uploading [{e}]",
                error_code=SA_ErrorCode.SA_8001
            )
        finally:
            if isinstance(uploading_file, bytes) and Path(tmp_file_path).exists():
                os.unlink(tmp_file_path)
        if url_prefix is None: 
            return
        else:
            return f"{url_prefix}/{file_path}"


    def download_file(self,
                      to_download_file: str,
                      download_destination: str,
                      file_naming: str
                      ) -> None:
        """Download a file from the R2 storage to a specified local destination by using the S3 client's download_file method.

        Args:
            to_download_file (str): The key (file path) of the file in the R2 storage to be downloaded.
            download_destination (str): The local directory path where the downloaded file should be saved.
            file_naming (str): The name to be given to the downloaded file when saving it to the local destination.
        """
        try:
            self.s3_client.download_file(
                self.bucket_name,
                to_download_file,
                f"{download_destination}/{file_naming}"
            )
            time.sleep(1)
        except Exception as e:
            raise SA_CommunicationError(
                error_log=f"Communication error with R2 when downloading [{e}]",
                error_code=SA_ErrorCode.SA_8001
            )

    