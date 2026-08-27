import json
import os
from pathlib import Path

from shellarc_core.exception.structure_error import SA_ErrorCode, SA_ProjStructError


class SpreadsheetMap_IO:
    def __init__(self):
        project_ctx_dir = Path(os.environ.get("SHELLARC_PROJECT_CTX", None))
        spreadsheet_map_path = project_ctx_dir / "spreadsheet_map.json"
        if not spreadsheet_map_path.exists():
            raise SA_ProjStructError(
                error_log="project cfg_path not exist",
                error_code=SA_ErrorCode.SA_4101,
            )
        with open(spreadsheet_map_path, "r", encoding="utf-8") as f:
            self.spreadsheet_map = json.load(f)


    def get_cell_coord(self,
                 cut_num: int,
                 item: str,
                 page_idx: int=0
                 ) -> tuple[int]:
        """Get the cell coordinates (row and column indices) for a specific item in the spreadsheet,
        based on the cut number and page index.

        Args:
            cut_num (int): The cut number to determine the row index.
            item (str): The name of the item to determine the column index.
            page_idx (int): The index of the page in the spreadsheet (default : 0).
        """
        row_idx = cut_num + self.spreadsheet_map.get(f"vert_offset_{page_idx}", None)
        if not isinstance(row_idx, int):
            raise SA_ProjStructError(
                error_log="vert_offset not configured properly in spreadsheet map",
                error_code=SA_ErrorCode.SA_4102
            )
        col_idx = self.spreadsheet_map.get(f"items_{page_idx}", {}).get(item, None)
        if not isinstance(col_idx, int):
            raise SA_ProjStructError(
                error_log="requested spreadsheet cell column idx not configured",
                error_code=SA_ErrorCode.SA_4102
            )
        return (row_idx, col_idx)


    def get_vert_offset(self,
                        page_idx: int=0
                        ) -> int:
        """Get the vertical offset for a specific page index in the spreadsheet.

        Args:
            page_idx (int): The index of the page in the spreadsheet (default : 0).

        Returns:
            vert_offset (int): The vertical offset value for the specified page index, which is used
        """
        vert_offset = self.spreadsheet_map.get(f"vert_offset_{page_idx}", None)
        if not isinstance(vert_offset, int):
            raise SA_ProjStructError(
                error_log="vert_offset not configured properly in spreadsheet map",
                error_code=SA_ErrorCode.SA_4102
            )
        return vert_offset
    
    def get_spreadsheet_map_raw(self) -> dict:
        return self.spreadsheet_map
        