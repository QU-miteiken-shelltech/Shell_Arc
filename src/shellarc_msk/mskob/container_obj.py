from shellarc_msk.mskob.field_obj import MSK_Field
from shellarc_msk.mskob.entity_obj import MSK_Entity
from shellarc_msk.mskob.property_obj import MSK_Property
from shellarc_msk.mskob.adress_obj import MSK_Adress
from shellarc_msk.mskob.type_obj import MSK_Type
from shellarc_msk.mskob.hexindex_obj import MSK_HexIndex
from shellarc_msk.mskfs.path_solver import MSKFS_PathSolver

class MSK_Containers(MSK_Field):
    def __init__(self,
                 field_name: str
                 ) -> None:
        self.field : MSK_Field = MSK_Field(
            field_name=field_name
        )

        self.container_bin = None
        self.field_bin_file = mskfs_pathsolver.mskfs_config / f".msk_container_{field_name}"
        if self.container_bin is None:
            mskfs_pathsolver = MSKFS_PathSolver()
            if not self.field_bin_file.exists():
                with open(self.field_bin_file, "wb") as f:
                    f.write(b"")
            with open(self.field_bin_file, "rb") as f:
                self.container_bin = f.read()

    def filter_entities(self,
                        filter: dict,
                        max_count: int=1
                        ) -> list[MSK_HexIndex]:
         # filter = {property_name : (value, type)}
        entity_count = len(self.container_bin) // 48
        rtn: list[MSK_HexIndex] = []

        for i in range(0, entity_count):
            current_entity = MSK_Entity(
                container_bin=self.container_bin,
                entity_count=i
            )
            if current_entity.prop in filter:
                if (current_entity.address.value == filter[current_entity.prop][0] and
                    current_entity.address.type.type_name == filter[current_entity.prop][1]):
                    rtn.append(current_entity.container_index)
            if len(rtn >= max_count):
                break

        return rtn

    def request_adress(self,
                       container_index: MSK_HexIndex,
                       requesting_prop: MSK_Property
                       ) -> MSK_Adress:
        entity_count = len(self.container_bin) // 48

        for i in range(0, entity_count):
            current_entity = MSK_Entity(
                container_bin=self.container_bin,
                entity_count=i
            )
            if (current_entity.container_index == container_index and
                current_entity.prop == requesting_prop):
                return current_entity.address

        return MSK_Adress(adress_index=MSK_HexIndex(value=None))

    def request_position(self,
                         container_index: MSK_HexIndex,
                         requesting_prop: MSK_Property
                         ) -> int:
        entity_count = len(self.container_bin) // 48

        for i in range(0, entity_count):
            current_entity = MSK_Entity(
                container_bin=self.container_bin,
                entity_count=i
            )
            if (current_entity.container_index == container_index and
                current_entity.prop == requesting_prop):
                return i * 48

        return -1

    def write_entity(self,
                     info: dict,
                     do_override: bool=False
                     ) -> None:
        container = self.filter_entities(
            filter=info,
            max_count=1
        )
        prop_type_name = [v for _,v in info.items()][0][1]
        prop_type = MSK_Type(type_name=prop_type_name)
        requesting_prop=MSK_Property(
            prop_type=prop_type,
            prop_name=[k for k,_ in info.items()][0]
        )
        adress = MSK_Adress(
            adress_type=prop_type,
            adress_value=[v for _,v in info.items()][0][0]
        )
        if (requesting_prop, prop_type) not in self.field_ls and not do_override:
            raise ValueError("Properties undefined in Field shall only be defined as overrides")
        
        new_entity = container[0].to_bytes() + requesting_prop.prop_index.to_bytes() + adress.adress_index.to_bytes()
        if len(new_entity) != 48:
            raise ValueError("An entiny of a container must be of length 48 bytes")
        if container:
            pos = self.request_position(
                container_index=container[0],
                requesting_prop=requesting_prop
            )
            self.container_bin[pos : pos + 48] = new_entity
        else:
            self.container_bin += new_entity
        self._write_binaries(new_bin=self.container_bin)

    def _write_binaries(self,
                        new_bin: bytes):
        with open(self.field_bin_file, "wb") as f:
            f.write(new_bin)
            