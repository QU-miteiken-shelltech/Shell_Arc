import mimetypes
from pathlib import Path

import requests

from shellarc_client.engine.transfer.transfer_base import TransferBase, RemoteKeyPrefix

class FileTransfer(TransferBase):
    def __init__(self):
        super().__init__()

    def upload_file(self,
                    local_file_path: Path | str,
                    r2_key_prefix: RemoteKeyPrefix,
                    r2_filename: str,
                    ) -> str:
        if isinstance(file_path, str):
            file_path = Path(file_path)
        content_type = mimetypes.guess_type(file_path.name)[0] or "appliction/octet-stream"
        ext = file_path.suffix.lstrip(".")
        r2_filename = r2_filename.lstrip("/")
        r2_key = f"{r2_key_prefix}{r2_filename}"

        resp = self.msk_post(
            url_path="/upload/presign",
            body={
                "contentType": content_type,
                "ext": ext,
                "key": r2_key
            }
        )
        resp.raise_for_status()
        info = resp.json()

        with file_path.open("rb") as f:
            put = requests.put(
                url=info["url"],
                data=f,
                headers=info["headers"],
                timeout=300
            )
        put.raise_for_status()

        resp = self.msk_post(
            url_path="/upload/complete",
            body={"key": info["key"]}
        )
        resp.raise_for_status()

        return info["key"]

    def download_file(self,
                      r2_key_prefix: RemoteKeyPrefix,
                      r2_filename: str,
                      local_destination_path: Path | str
                      ) -> Path:
        if isinstance(local_destination_path, str):
            local_destination_path = Path(local_destination_path)
        if local_destination_path.is_dir():
            raise ValueError("User cannot download a file as a folder")
        r2_filename = r2_filename.lstrip("/")
        r2_key = f"{r2_key_prefix}{r2_filename}"

        resp = self.msk_post(
            url_path="/download/presign",
            body={
                "key": r2_key,
                "filename": r2_filename
            }
        )
        resp.raise_for_status()
        presigned_url = resp.json()["url"]

        with requests.get(url=presigned_url, stream=True, timeout=600) as resp:
            resp.raise_for_status()
            with local_destination_path.open("wb") as f:
                for chunk in resp.iter_content(chunk_size=1024 * 1024):
                    f.write(chunk)

        return local_destination_path




