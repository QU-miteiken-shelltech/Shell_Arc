from __future__ import annotations
from typing import TYPE_CHECKING
import mmap

from shellarc_msk.mskfs.on_ram_data import MSKFS_OnRamMmap
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

        mskfs_pathsolver = MSKFS_PathSolver()
        self.field_bin_file = mskfs_pathsolver.mskfs_config / f".msk_container_{field_name}"
        if (MSKFS_OnRamMmap.container_bins is None or
            field_name not in MSKFS_OnRamMmap.container_bins):
            if not self.field_bin_file.exists():
                with open(self.field_bin_file, "wb") as f:
                    f.write(b"")
            MSKFS_OnRamMmap.register(
                field_name=field_name,
                filepath=self.field_bin_file
            )
        self.container_bin = MSKFS_OnRamMmap.container_bins[field_name]

    def chunks_iter(self):
        entity_count = len(self.container_bin) // 48
        for i in range(entity_count):
            start = i * 48
            chunk = self.container_bin[start : start + 48]
            yield chunk

    def entities_iter(self):
        for chunk in self.chunks_iter():
            yield MSK_Entity(entity_chunk=chunk)

    def masking_comparison(self,
                           reversed_container_bin: bytes,
                           unit_mask: bytes,
                           unit_comparer: bytes,
                           entity_count: int, 
                           compare_range: tuple[int, int]
                           ) -> list[int]:
        mask_bin = unit_mask * entity_count
        comparer_raw_bin = unit_comparer * entity_count
        if not (len(mask_bin) 
            == len(comparer_raw_bin) 
            == len(reversed_container_bin) 
            == len(self.container_bin)):
            raise ValueError("All comparison masks must be of same size")

        compare_range_size = compare_range[1] - compare_range[0]
        if compare_range[0] < 0 or compare_range[1] > 48:
            raise ValueError("Compare range out of range 48")

        comparer_bin = bytes(
            (ai & ~mi | bi & mi) & 0xFF 
            for ai, mi, bi 
            in zip(reversed_container_bin, mask_bin, comparer_raw_bin)
        )
        result_bin = bytes(
            a == b for a, b
            in zip(comparer_bin, self.container_bin)
        )

        target_pattern = b'\xff' * compare_range_size
        mv = memoryview(self.container_bin)
        found_indices = []
        for n in range(0, entity_count):
            pos = n * 48 + compare_range[0]
            if mv[pos : pos + compare_range_size] == target_pattern:
                found_indices.append(n)

        return found_indices


    def filter_container(self,
                         conditions: list[tuple[MSK_Property, MSK_Adress]],
                         max_count: int=1
                         ) -> list[MSK_Container]:
        entity_count = len(self.container_bin) // 48
        reversed_container_bin = bytes(~b & 0xFF for b in self.container_bin)

        found_indices = []
        for condition in conditions:
            unit_comparer = (
                (b'\x00' * 16) +
                condition[0].prop_index.to_bytes() + 
                condition[1].adress_index.to_bytes()
            )
            found_indices.extend(
                self.masking_comparison(
                    reversed_container_bin=reversed_container_bin,
                    unit_mask=(b'\x00' * 16) + (b'\x01' * 32),
                    unit_comparer=unit_comparer,
                    entity_count=entity_count,
                    compare_range=(16, 48)
                )
            )

        indices_offsetcount_dict : dict[MSK_HexIndex, list[int]] = {}
        for i in range(0, entity_count):
            idx = MSK_HexIndex(self.container_bin[i * 48 : i * 48 + 16])
            if idx not in indices_offsetcount_dict:
                indices_offsetcount_dict[idx] = [i]
            else:
                indices_offsetcount_dict[idx].append(i)

        rtn = [
            MSK_Container(
                field_name=self.field_name,
                container_offset_counts=v
            )
            for _,v in indices_offsetcount_dict.items()
        ]

        return rtn[: max_count]

    def request_container(self,
                          container_index: MSK_HexIndex
                          ) -> MSK_Container:
        from shellarc_msk.mskob.container_obj import MSK_Container
        return MSK_Container(
            field_name=self.field_name,
            container_index=container_index
        )

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
        self._write_container_binaries()

    def _write_container_binaries(self):
        self.container_bin.flush()
            