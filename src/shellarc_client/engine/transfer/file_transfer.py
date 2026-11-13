import mimetypes
import os
from pathlib import Path

import requests

API = "https://shellarc2027-communicate.shiinaayame3.workers.dev"

class MSKEngine_FileTransfer:
    def __init__(self):
        TOKEN = os.environ["R2_API_TOKEN"]
        self.AUTH = {"Authorization" : f"Bearer {TOKEN}"}

    def upload_file(self,
                    file_path: Path | str,
                    r2_key: str
                    ) -> str:
        if isinstance(file_path, str):
            file_path = Path(file_path)
        content_type = mimetypes.guess_type(file_path.name)[0] or "appliction/octet-stream"
        ext = file_path.suffix.lstrip(".")

        resp = requests.post(
            url=f"{API}/upload/presign",
            headers=self.AUTH,
            json={
                "contentType": content_type,
                "ext": ext,
                "key": r2_key
            },
            timeout=30
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

        resp = requests.post(
            f"{API}/upload/complete",
            headers=self.AUTH,
            json={"key": info["key"]},
            timeout=30
        )
        resp.raise_for_status()

        return info["key"]

    def download_file(self,
                      r2_filename: str,
                      r2_key: str,
                      local_destination_path: Path | str
                      ) -> Path:
        if isinstance(local_destination_path, str):
            local_destination_path = Path(local_destination_path)
        if local_destination_path.is_dir():
            raise ValueError("User cannot download a file as a folder")
        resp = requests.post(
            url=f"{API}/download/presign",
            headers=self.AUTH,
            json={
                "key": r2_key,
                "filename": r2_filename
            },
            timeout=30
        )
        resp.raise_for_status()
        presigned_url = resp.json()["url"]

        with requests.get(url=presigned_url, stream=True, timeout=600) as resp:
            resp.raise_for_status()
            with local_destination_path.open("wb") as f:
                for chunk in resp.iter_content(chunk_size=1024 * 1024):
                    f.write(chunk)

        return local_destination_path



