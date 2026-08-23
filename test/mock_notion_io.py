"""
Notion_IO の Mock 実装。

設計判断:
- 実クラスの __init__ は Notion API を叩いてデータベースをまるごと取得するが、
  Mockではその通信を一切行わない。かわりにコンストラクタで `seed_data` として
  {cut_num: {attr_name: url}} の形の辞書を直接渡せるようにしている。
- `get_image_file` は実際のHTTPダウンロードを行わず、seed_dataとは別に
  `seed_file_bytes` で登録したバイト列をファイルに書き出す（未登録ならプレースホルダーを書く）。
- 実クラスと同じ「存在しないカットへのアクセスはエラー」という挙動 (SA_InvalidRequestObj)
  を再現している。
"""

from pathlib import Path
from typing import Union

from shellarc_core.exception.structure_error import SA_CommunicationError, SA_ErrorCode
from shellarc_core.exception.user_exception import SA_InvalidRequestObj


class Mock_Notion_IO:
    def __init__(
        self,
        cut_num: int,
        seed_data: dict[int, dict[str, str]] | None = None,
    ):
        self.cut_num = cut_num
        self._data: dict[int, dict[str, str]] = seed_data or {}
        self._file_bytes: dict[str, bytes] = {}  # url -> content（get_image_file用）

    def seed_file_bytes(self, url: str, content: bytes) -> None:
        """テストのセットアップ用: 特定のURLに対応するダウンロード内容を仕込む（Mock専用メソッド）。"""
        self._file_bytes[url] = content

    def get_image_url(self, attr_name: str = "画像") -> str:
        cut_entry = self._data.get(self.cut_num)
        if cut_entry is None or attr_name not in cut_entry:
            raise SA_InvalidRequestObj(
                error_log="Requesting lo of an unexisting cut",
                frontend_msg=f"カット{self.cut_num}のLOはまだ存在しません",
            )
        return cut_entry[attr_name]

    def get_image_file(self, download_destination: Union[str, Path], attr_name: str = "画像") -> None:
        image_url = self.get_image_url(attr_name=attr_name)
        content = self._file_bytes.get(image_url)
        if content is None:
            raise SA_CommunicationError(
                error_log="Request failed when getting image from an image url on Notion",
                error_code=SA_ErrorCode.SA_3000,
            )
        Path(download_destination).write_bytes(content)

    def put_image_url(self, img_url: str, attr_name: str = "画像") -> None:
        self._data.setdefault(self.cut_num, {})[attr_name] = img_url
