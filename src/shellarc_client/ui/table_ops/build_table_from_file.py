import json
from typing import Optional, overload

from shellarc_msk.mskob.field_obj import MSK_Field
from shellarc_msk.mskut.path_solver import MSKUT_PathSolver
from shellarc_client.ui.table_ops.table_header import BuildHeader
from shellarc_client.ui.table_ops.table_view import SetCells


class TableBuilder:
    def __init__(self, table_name, table):
        self.table = table
        client_dir = MSKUT_PathSolver().mskfs_client
        table_file_path = client_dir / f"table_{table_name}.json"
        if not table_file_path.exists():
            raise ValueError(f"Table file of {table_name} not found")
        with open(table_file_path, "r", encoding="utf-8") as f:
            self.table_solutions = json.load(f)
        self.field_name = self.table_solutions.get("field", None)

    def set_header(self, header_pos: int, info: dict, is_vertical: bool):
        repetition = int(info.get("repetition", "1"))
        start_pos = int(info.get("start_pos", "2")) - 1
        max_count = int(info.get("max_count", None)) if info.get("max_count", None) else None
        step = int(info.get("step", "1"))
        key_property_name = info.get("key_property", None)
        do_sort_by_num = info.get("do_sort_by_num", True)
        key_property = None
        for t in MSK_Field(field_name=self.field_name).field_ls:
            if t[0].prop_name == key_property_name: 
                key_property = t[0]
        if key_property is None:
            raise ValueError("Key property not exist")

        header_builder = BuildHeader(
            field_name=self.field_name,
            table=self.table,
            is_vertical=is_vertical
        )
        iterator = header_builder.solve_header(
            key_property=key_property,
            max_count=max_count,
            do_sort_by_num=do_sort_by_num
        )
        for _ in range(repetition):
            next_start_pos = header_builder.write_header(
                header_pos=header_pos,
                start_pos=start_pos,
                step=step,
                iterator=iterator
            )
            start_pos = next_start_pos

    @overload
    def set_cell(self, arrow_info: dict[str, list]) -> None:
        ...
        
    @overload
    def set_cell(self, 
                 arrow_info: dict[str, list],
                 target_prop_name: Optional[str]=None,
                 max_metanode_num: int=1
                 ) -> None:
        ...

    def set_cell(self, 
                 arrow_info,
                 target_prop_name=None,
                 max_metanode_num=1
                 ) -> None:
        if len(arrow_info["upstreams"]) <= 0:
            return
        cells_setter = SetCells(
            table=self.table, arrow_info=arrow_info
        )
        if len(arrow_info["upstreams"]) > 1:
            assert target_prop_name is not None, "A target property must be deisgnated"
            target_prop = None
            for t in MSK_Field(field_name=self.field_name).field_ls:
                if t[0].prop_name == target_prop_name: 
                    target_prop = t[0]
            if target_prop is None:
                raise("Target property not exist")
            cells_setter.resolve_cell(
                target_prop=target_prop,
                max_metanode_num=max_metanode_num
            )
        elif len(arrow_info["upstreams"]) == 1:
            cells_setter.expand_cell_solution()

    def build_table_from_file(self):

        for pos, info in self.table_solutions.get("headers", {}).get("vertical", {}).items():
            self.set_header(header_pos=int(pos), info=info, is_vertical=True)
        for pos, info in self.table_solutions.get("headers", {}).get("horizontal", {}).items():
            self.set_header(header_pos=int(pos), info=info, is_vertical=False)
        for cell_setter in self.table_solutions.get("cell_setters", []):
            arrow_info = cell_setter.get("arrow_info")
            self.set_cell(
                arrow_info=arrow_info,
                target_prop_name=cell_setter.get("target_property", None),
                max_metanode_num=cell_setter.get("max_metanode_num", 1)
            )
        for cell_expander in self.table_solutions.get("cell_expanders", []):
            arrow_info = cell_expander.get("arrow_info")
            self.set_cell(arrow_info=arrow_info)

class TableArchiver:
    def __init__(self):
        pass
