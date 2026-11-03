from pathlib import Path
from typing import Optional
import json
import uuid
import hashlib

from shellarc_msk.mskfs.path_solver import MSKFS_PathSolver
from shellarc_msk.mskfs.on_ram_data import MSKFS_OnRam

class MSKFS_MetafilesIo:
    def __init__(self):
        mskfs_pathsolver = MSKFS_PathSolver()
        self.field_file = mskfs_pathsolver.mskfs_config / ".msk_field"
        self.container_file = mskfs_pathsolver.mskfs_config / ".msk_container"
        self.access_file = mskfs_pathsolver.mskfs_config / ".msk_access"
        for metafile in [self.field_file, self.container_file, self.access_file]:
            if not metafile.exists():
                with open(metafile, "w", encoding="utf-8") as f:
                    json.dump({}, f, ensure_ascii=False, indent=3)

    def get_all_fields(self) -> Optional[dict[str, str]]:
        with open(self.field_file, "r", encoding="utf-8") as f:
            current_fields = json.load(f)
        return current_fields

    def get_field(self, 
                  field_name: str
                  ) -> Optional[dict[str, str]]:
        current_fields = self.get_all_fields()
        return current_fields.get(field_name, None)

    def set_field(self, 
                  field_name: str, 
                  new_field_def: dict[str, str]
                  ) -> None:
        current_fields = self.get_all_fields()
        current_fields[field_name] = new_field_def
        with open(self.field_file, "r", encoding="utf-8") as f:
            json.dump(current_fields, f, ensure_ascii=False, indent=3)

    def append_field(self,
                     field_name: str, 
                     new_field_items: dict[str, str]
                     ) -> None:
        current_field = self.get_all_fields().get(field_name, {})
        for k,v in new_field_items.items():
            current_field[k] = v
        self.set_field(field_name=field_name, new_field_def=current_field)

    def get_full_containers(self) -> dict:
        with open(self.container_file, "r", encoding="utf-8") as f:
            current_full_containers = json.load(f)
        return current_full_containers

    def get_all_containers(self,
                           field_name: str
                           ) -> dict[str, dict[str, str]]:
        current_full_containers = self.get_full_containers()
        return current_full_containers.get(field_name, None)

    def get_container(self, 
                      field_name: str,
                      container_index: str
                      ) -> dict[str, str]:
        current_containers = self.get_all_containers(field_name=field_name)
        return current_containers.get(container_index, None) if current_containers is not None else None

    def set_container(self, 
                      field_name: str,
                      container_index: str,
                      container_data: dict[str, str]
                      ) -> None:
        current_full_containers = self.get_full_containers()
        current_full_containers[field_name][container_index] = container_data
        with open(self.container_file, "w", encoding="utf-8") as f:
            json.dump(current_full_containers, f, ensure_ascii=False, indent=3)

    def make_index(self, 
                   content: Optional[str]=None
                   ) -> str:
        if content is None:
            adress = f"0x{uuid.uuid4().hex}"
        else:
            adress = hashlib.md5(content.encode('utf-8')).hexdigest()
        return adress

    def append_container(self,
                         field_name: str,
                         container_data: dict[str, str]
                         ) -> None:
        new_index = self.make_index()
        self.set_container(
            field_name=field_name,
            container_index=new_index,
            container_data=container_data
        )

    def update_container(self,
                         field_name: str,
                         container_index: str,
                         container_data: dict[str, str]
                         ) -> None:
        target_container = self.get_container(field_name=field_name, container_index=container_index)
        for k,v in container_data.items():
            target_container[k] = v
        self.set_container(field_name=field_name, container_index=container_index, container_data=target_container)

    def get_access_map(self):
        if MSKFS_OnRam.ACCESS_MAP is not None:
            return MSKFS_OnRam.ACCESS_MAP
        with open(self.access_file, "r", encoding="utf-8") as f:
            access_map = json.load(f)
        MSKFS_OnRam.ACCESS_MAP = access_map
        return access_map

    def ref_access_map(self, adress: str) -> Optional[dict[str, str]]:
        if MSKFS_OnRam.ACCESS_MAP is not None:
            access_map = MSKFS_OnRam.ACCESS_MAP
        else:
            access_map = self.get_access_map()
        return access_map.get(adress, None)

    def write_access_map(self, 
                         value_type: str, 
                         value: str
                         ) -> None:
        if MSKFS_OnRam.ACCESS_MAP is None:
            access_map = self.get_access_map()
        else:
            access_map = MSKFS_OnRam.ACCESS_MAP
        new_item = {"type" : value_type, "value" : value}
        adress = self.make_index(content=str(new_item))
        if adress in MSKFS_OnRam.ACCESS_MAP:
            return
        MSKFS_OnRam.ACCESS_MAP[adress] = new_item
        with open(self.access_file, "w", encoding="utf-8") as f:
            json.dump(MSKFS_OnRam.ACCESS_MAP, f, ensure_ascii=False, indent=2)
        