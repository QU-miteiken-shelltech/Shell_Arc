from shellarc_core.auth.access_spread_sheet import AccessSpreadSheet as A_GCP
from shellarc_core.cfg.cfg_io import Cfg_IO as Cfg_IO
from shellarc_core.cfg.cfg_io import Cfg_item
from shellarc_core.cfg.spreadsheet_map_io import SpreadsheetMap_IO as SMap_IO
import gspread_formatting as g_fmt
from gspread.utils import rowcol_to_a1


class GCP_IO:
    def __init__(self):
        cfg_io = Cfg_IO()
        spreadsheet_key = cfg_io.get_cfg_setting(Cfg_item.SPREADSHEET_KEY)
        self.a_gcp = A_GCP(spreadsheet_key=spreadsheet_key)
        self.smap_io = SMap_IO()


    def get_info(self,
                 info_type: str,
                 cut_num: int,
                 page_idx: int=0
                 ) -> str | None:
        """Get the specified information from the Google Spreadsheet based on the provided information type, cut number, and page index.

        Args:
            info_type (str): The type of information to retrieve from the spreadsheet (e.g., "status", "assigned_person").
            cut_num (int): The cut number of the component to get the information for.
            page_idx (int): The index of the spreadsheet page to retrieve the information from (Default : 0).

        Returns:
            str | None: The retrieved information from the spreadsheet as a string, 
                or None if the cell is empty or does not contain any value.
        """
        spreadsheet = self.a_gcp.spreadsheet_obj(page_idx=page_idx)
        cell_coord = self.smap_io.get_cell_coord(
            cut_num=cut_num,
            item=info_type,
            page_idx=page_idx
        )
        rtn = spreadsheet.cell(
            row=cell_coord[0], 
            col=cell_coord[1]
            ).value
        return str(rtn) if rtn is not None else None
    

    def update_info(self,
                    info_type: str,
                    cut_num: int,
                    new_value: str,
                    page_idx: int=0
                    ) -> None:
        """Update the specified information in the Google Spreadsheet based on the provided information type, cut number, new value, and page index.

        Args:
            info_type (str): The type of information to update in the spreadsheet (e.g., "status", "assigned_person").
            cut_num (int): The cut number of the component to update the information for.
            new_value (str): The new value to be updated in the spreadsheet for the specified information type and cut number.
            page_idx (int): The index of the spreadsheet page to update the information in (Default : 0).
        """
        spreadsheet = self.a_gcp.spreadsheet_obj(page_idx=page_idx)
        cell_coord = self.smap_io.get_cell_coord(
            cut_num=cut_num,
            item=info_type,
            page_idx=page_idx
        )
        spreadsheet.update_cell(
            row=cell_coord[0],
            col=cell_coord[1],
            value=new_value
        )


    def color_cell(self,
                   info_type: str,
                   cut_num: int,
                   target_color: tuple[float],
                   page_idx: int=0
                   ) -> None:
        """Color a specific cell in the Google Spreadsheet based on the provided information type, cut number, target color, and page index.

        Args:
            info_type (str): The type of information corresponding to the cell to be colored in the spreadsheet (e.g., "status", "assigned_person").
            cut_num (int): The cut number of the component corresponding to the cell to be colored.
            target_color (tuple[float]): A tuple representing the RGB color values (each value should be between 0 and 1) to be applied as the background color of the specified cell.
            page_idx (int): The index of the spreadsheet page where the cell to be colored is located (Default : 0).
        """
        spreadsheet = self.a_gcp.spreadsheet_obj(page_idx=page_idx)
        cell_coord = self.smap_io.get_cell_coord(
            cut_num=cut_num,
            item=info_type,
            page_idx=page_idx
        )
        cell_address = rowcol_to_a1(
            row=cell_coord[0],
            col=cell_coord[1]
        )
        fmt =g_fmt.CellFormat(
            backgroundColor=g_fmt.Color(target_color[0], target_color[1], target_color[2])
            )
        g_fmt.format_cell_range(
            spreadsheet,
            cell_address,
            fmt
        )        

    @property
    def spreadsheet_cache(self,
                          page_idx: int=0
                          ) -> list:
        """Get the cached values of the specified spreadsheet page, and if the cache is not available, 
        retrieve the values from the spreadsheet and store them in the cache for future access.

        Args:
            page_idx (int): The index of the spreadsheet page to get the cached values for (Default : 0).
        
        Returns:
            _spreadsheet_cache (list): A list of lists representing the cached values of the specified spreadsheet page, where each
        """
        spreadsheet = self.a_gcp.spreadsheet_obj(page_idx=page_idx)
        if not hasattr(self, "_spreadsheet_cache"):
            self._spreadsheet_cache = spreadsheet.get_all_values()
        return self._spreadsheet_cache


