"""
GCP_IO (スプレッドシート) の Mock 実装。クラス名は依頼に合わせて Mock_Spreadsheet_IO とする。

設計判断:
- 実クラスが依存している SpreadsheetMap_IO（info_type + cut_num から実際の
  セル座標(row, col)を計算する設定）は再現しない。過剰実装だと判断したため、
  Mockでは `(info_type, cut_num, page_idx)` をそのままキーにした辞書で値を持つ。
  → もしテストで「実際の行列座標に書き込まれているか」まで検証したい場合は、
    このMockでは検証できない。その場合は別途相談してほしい。
- `color_cell` は実クラスと同様、値そのものではなく色を別領域に記録する
  （テストで `assert mock.get_colored_cell(...) == (1,0,0)` のように検証できるようにしている）。
- `spreadsheet_cache` は実クラスの `get_all_values()` 相当。Mockでは初期化時に
  渡された2次元リストをそのまま返す。
"""


class Mock_Spreadsheet_IO:
    def __init__(
        self,
        initial_data: dict[tuple[str, int, int], str] | None = None,
        initial_cache: list[list[str]] | None = None,
    ):
        self._data: dict[tuple[str, int, int], str] = dict(initial_data or {})
        self._colors: dict[tuple[str, int, int], tuple[float, ...]] = {}
        self._cache: list[list[str]] = initial_cache or []

    def get_info(self, info_type: str, cut_num: int, page_idx: int = 0) -> str | None:
        return self._data.get((info_type, cut_num, page_idx))

    def update_info(self, info_type: str, cut_num: int, new_value: str, page_idx: int = 0) -> None:
        self._data[(info_type, cut_num, page_idx)] = new_value

    def color_cell(
        self,
        info_type: str,
        cut_num: int,
        target_color: tuple[float, ...],
        page_idx: int = 0,
    ) -> None:
        self._colors[(info_type, cut_num, page_idx)] = target_color

    def get_colored_cell(self, info_type: str, cut_num: int, page_idx: int = 0) -> tuple[float, ...] | None:
        """テスト用の検証ヘルパー（Mock専用メソッド、実クラスには存在しない）。"""
        return self._colors.get((info_type, cut_num, page_idx))

    @property
    def spreadsheet_cache(self) -> list:
        return self._cache
