from typing import TYPE_CHECKING

from shellarc_msk.mskob.field_obj import MSK_Field
from shellarc_msk.mskob.entity_obj import MSK_Entity
from shellarc_msk.mskob.property_obj import MSK_Property
from shellarc_msk.mskob.adress_obj import MSK_Adress
from shellarc_msk.mskob.hexindex_obj import MSK_HexIndex
from shellarc_msk.mskfs.path_solver import MSKFS_PathSolver
if TYPE_CHECKING:
    from shellarc_msk.mskob.container_obj import MSK_Container

class MSK_ContainerCollection(MSK_Field):
    def __init__(self,
                 field_name: str
                 ) -> None:
        super().__init__(field_name=field_name)
        self.container_bin = None
        self.field_bin_file = mskfs_pathsolver.mskfs_config / f".msk_container_{field_name}"
        if self.container_bin is None:
            mskfs_pathsolver = MSKFS_PathSolver()
            if not self.field_bin_file.exists():
                with open(self.field_bin_file, "wb") as f:
                    f.write(b"")
            with open(self.field_bin_file, "rb") as f:
                self.container_bin = f.read()

    def entities_iter(self):
        entity_count = len(self.container_bin) // 48
        for i in range(entity_count):
            start = i * 48
            chunk = self.container_bin[start : start + 48]
            yield MSK_Entity(entity_chunk=chunk)

    def filter_container(self,
                         conditions: list[tuple[MSK_Property, MSK_Adress]],
                         max_count: int=1
                         ) -> list[MSK_Container]:
        rtn: list[MSK_Container] = []

        container_index_list = []
        for entity in self.entities_iter():
            for condition in conditions:
                if entity.prop != conditions[0] or entity.address != condition[1]:
                    continue
                container_index_list.append(entity.container_index)
            if len(container_index_list) >= max_count:
                break

        for container_index in container_index_list:
            from shellarc_msk.mskob.container_obj import MSK_Container
            rtn.append(
                self.request_container(container_index=container_index)
            )
        return rtn

    def request_container(self,
                          container_index: MSK_HexIndex
                          ) -> MSK_Container:
        from shellarc_msk.mskob.container_obj import MSK_Container
        return MSK_Container(
            field_name=self.field_name,
            container_index=container_index
        )

    def request_adress(self,
                       container_index: MSK_HexIndex,
                       requesting_prop: MSK_Property
                       ) -> MSK_Adress:
        for entity in self.entities_iter():
            if (entity.container_index == container_index and
                entity.prop == requesting_prop):
                return entity.address

        return MSK_Adress(adress_index=MSK_HexIndex(value=None))

    def request_position(self,
                         container_index: MSK_HexIndex,
                         requesting_prop: MSK_Property
                         ) -> int:
        i = 0
        for entity in self.entities_iter():
            if (entity.container_index == container_index and
                entity.prop == requesting_prop):
                return i * 48
            i += 1

        return -1

    def write_entity(self,
                     container_index: MSK_HexIndex,
                     prop: MSK_Property,
                     adress: MSK_Adress,
                     do_override: bool=False
                     ) -> None:
        if (prop, prop.prop_type) not in self.field_ls and not do_override:
            raise ValueError("Properties undefined in Field shall only be defined as overrides")
        if prop.prop_type != adress.type:
            raise ValueError("Type unmatch")
        
        new_entity = (container_index.to_bytes() + 
                      prop.prop_index.to_bytes() + 
                      adress.adress_index.to_bytes()
                      )
        if len(new_entity) != 48:
            raise ValueError("An entiny of a container must be of length 48 bytes")
        pos = self.request_position(
            container_index=container_index,
            requesting_prop=prop
        )
        if pos == -1:
            self.container_bin += new_entity
        else:
            self.container_bin = self.container_bin[: pos] + new_entity + self.container_bin[pos + 48 :]
        self._write_binaries(new_bin=self.container_bin)

    def _write_binaries(self,
                        new_bin: bytes):
        with open(self.field_bin_file, "wb") as f:
            f.write(new_bin)
            