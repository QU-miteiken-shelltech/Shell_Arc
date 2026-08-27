"""
R2_IO の Mock 実装。

設計判断:
- boto3 / S3 には一切アクセスしない。`self._store` という dict (key -> bytes) を
  仮想的なバケットとして扱う。
- `upload_file` に str/Path が渡された場合、実際にローカルディスクから読み込む
  （テストコードが用意した一時ファイルの中身を検証したいケースを想定）。
  bytesが渡された場合はそのまま格納する。
- 例外系は実クラスと同じ `shellarc_core.exception` のクラスを使い、
  呼び出し側のエラーハンドリングコードをそのままテストできるようにしている。
"""

from pathlib import Path
from typing import Union

from shellarc_core.exception.structure_error import (
    SA_CommunicationError,
    SA_ErrorCode,
    SA_ProjStructError,
)


class Mock_R2_IO:
    def __init__(self, bucket_name: str | None = None):
        self.bucket_name = bucket_name or "mock-bucket"
        self._store: dict[str, bytes] = {}
        self.uploaded_calls: list[str] = []  # テストでアップロード回数/対象を検証するための記録

    def seed(self, file_path: str, content: bytes) -> None:
        """テストのセットアップ用: あらかじめストレージにオブジェクトを仕込む（実クラスには存在しないMock専用メソッド）。"""
        self._store[file_path] = content

    def get_s3obj_size(self, target_s3_file: str) -> int:
        if target_s3_file not in self._store:
            raise SA_CommunicationError(
                error_log=f"Mock object not found: {target_s3_file}",
                error_code=SA_ErrorCode.SA_8001,
            )
        size_bytes = len(self._store[target_s3_file])
        return int(size_bytes / 1024 / 1024)

    def issue_presigned_url(
        self,
        target_s3_file: str,
        url_client_method: str,
        http_method: str,
        time_limit: int = 180,
    ) -> str:
        return f"https://mock-r2.local/{self.bucket_name}/{target_s3_file}?method={url_client_method}&http={http_method}&expires={time_limit}"

    def get_path_with_ext(self, path_without_ext: str) -> str:
        matches = [k for k in self._store if k.startswith(path_without_ext)]
        if not matches:
            raise SA_CommunicationError(
                error_log=f"No object found with prefix: {path_without_ext}",
                error_code=SA_ErrorCode.SA_8001,
            )
        return matches[0]

    def get_paths_with_prefix(self, file_prefix: str) -> list[str] | None:
        matches = [k for k in self._store if k.startswith(file_prefix)]
        return matches if matches else None

    def upload_file(
        self,
        uploading_file: Union[bytes, str, Path],
        file_path: Union[str, Path],
        url_prefix: str | None = None,
    ) -> str | None:
        if isinstance(file_path, Path):
            file_path = str(file_path)
        if uploading_file is None:
            raise SA_ProjStructError(
                error_log="Uploading file to R2 storage is None",
                error_code=SA_ErrorCode.SA_5101,
            )
        if isinstance(uploading_file, bytes):
            content = uploading_file
        else:
            local_path = Path(uploading_file)
            content = local_path.read_bytes() if local_path.exists() else b""
        self._store[file_path] = content
        self.uploaded_calls.append(file_path)
        if url_prefix is None:
            return None
        return f"{url_prefix}/{file_path}"

    def download_file(self, to_download_file: str, download_destination: str, file_naming: str) -> None:
        if to_download_file not in self._store:
            raise SA_CommunicationError(
                error_log=f"Mock object not found: {to_download_file}",
                error_code=SA_ErrorCode.SA_8001,
            )
        dest = Path(download_destination) / file_naming
        dest.write_bytes(self._store[to_download_file])
