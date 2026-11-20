from typing import Optional
import json

from shellarc_msk.mskut.path_solver import MSKUT_PathSolver
from shellarc_client.engine.config.read_config import ReadClientConfig

field_name : str | None = None
headers : dict[str, dict] = {"vertical": {}, "horizontal": {}}
cell_setters : list[dict] = []
cell_expanders : list[dict] = []

def set_field(_field_name: str):
    field_name = _field_name

def set_header(is_vertical: bool,
               header_pos: int,
               repetition: int,
               start_pos: int,
               max_count: Optional[int],
               step: int,
               key_property: str,
               do_sort_by_num: bool
               ):
    orientation = "vertical" if is_vertical else "horizontal"
    headers[orientation][str(header_pos)] = {
        "repetition": str(repetition),
        "start_pos": str(start_pos),
        "max_count": str(max_count) if max_count is not None else "",
        "step": str(step),
        "key_property": key_property,
        "do_sort_by_num": do_sort_by_num
    }

def set_cell_setters(arror_info: dict,
                     max_metanode_num: int,
                     target_property: str,
                     item_display: str,
                     nodes_display: str
                     ):
    cell_setter = {
        "arrow_info": arror_info,
        "max_metanode_num": str(max_metanode_num),
        "target_property": target_property,
        "item_display": item_display,
        "nodes_display": nodes_display
    }
    cell_setters.append(cell_setter)

def set_cell_expanders(arrow_info: dict):
    cell_expander = {
        "arrow_info": arrow_info
    }
    cell_expanders.append(cell_expander)

def clear_captures():
    field_name = None
    headers = {"vertical": {}, "horizontal": {}}
    cell_setters = []
    cell_expanders = []

def write_to_disk(table_name: str):
    table_file_path = MSKUT_PathSolver().mskfs_client / f"table_{table_name}.json"
    table_dict = {
        "field": field_name,
        "headers": headers,
        "cell_setters": cell_setters,
        "cell_expanders": cell_expanders
    }
    with open(table_file_path, "w", encoding="utf-8") as f:
        json.dump(table_dict, f, ensure_ascii=False, indent=3)
    current_table_list = ReadClientConfig.get_config_item("tables")
    current_table_list.append(table_name)
    ReadClientConfig.write_config_item(current_table_list, "tables")
    clear_captures()

                