from __future__ import annotations
from typing import TYPE_CHECKING, overload, Optional

from shellarc_msk.mskut.on_ram_data import MSKUT_OnRamData, MSKUT_OnRamMmap
from shellarc_msk.mskob.field_obj import MSK_Field
from shellarc_msk.mskob.entity_obj import MSK_Entity
from shellarc_msk.mskob.property_obj import MSK_Property
from shellarc_msk.mskob.adress_obj import MSK_Address
from shellarc_msk.mskob.hexindex_obj import MSK_HexIndex
from shellarc_msk.mskut.path_solver import MSKUT_PathSolver
from shellarc_msk.mskex.msk_objerror import (
    MSKObject_FormatError, MSKObject_ValidationError, MSKObject_QueryLogicError
)
if TYPE_CHECKING:
    from shellarc_msk.mskob.container_obj import MSK_Container

class MSK_ContainerCollection:
    def __init__(self,
                 field_name: str
                 ) -> None:
        # super().__init__(field_name=field_name)
        self.field_name = field_name

        mskfs_pathsolver = MSKUT_PathSolver()
        self.field_bin_file = mskfs_pathsolver.mskfs_space / f".msk_container_{field_name}"
        if (MSKUT_OnRamMmap.container_bins is None or
            field_name not in MSKUT_OnRamMmap.container_bins):
            if not self.field_bin_file.exists():
                with open(self.field_bin_file, "wb") as f:
                    f.write(b"")
            MSKUT_OnRamMmap.register(
                field_name=field_name,
                filepath=self.field_bin_file
            )
        self.container_bin = MSKUT_OnRamMmap.container_bins[field_name]

    def chunks_iter(self):
        entity_count = len(self.container_bin) // 48
        for i in range(entity_count):
            start = i * 48
            chunk = self.container_bin[start : start + 48]
            yield chunk

    def entities_iter(self):
        for chunk in self.chunks_iter():
            yield MSK_Entity(entity_chunk=chunk)

    def container_iter(self):
        from shellarc_msk.mskob.container_obj import MSK_Container

        rows_by_id: dict[bytes, list[int]] = {}
        with memoryview(self.container_bin) as mv:
            for n in range(len(mv) // 48):
                rows_by_id.setdefault(bytes(mv[n * 48 : n * 48 + 16]), []).append(n)

        def _generate():
            for id_bytes, rows in rows_by_id.items():
                yield MSK_Container(
                    field_name=self.field_name,
                    container_index=MSK_HexIndex.from_bytes(id_bytes),
                    container_offset_counts=rows
                )

        return _generate()

    def masking_comparison(self,
                           unit_comparer: bytes,
                           compare_range: tuple[int, int]
                           ) -> list[int]:
        """Row numbers whose bytes [compare_range[0]:compare_range[1]] equal the same bytes
        of the 48-byte pattern `unit_comparer` (the other bytes of the pattern are ignored)."""
        if len(unit_comparer) != 48:
            raise MSKObject_FormatError(
                msg="unit_comparer must be of length 48 bytes"
            )
        start, end = compare_range
        if start < 0 or end > 48 or start >= end:
            raise MSKObject_FormatError(
                msg="Compare range exceeded a range 48"
            )

        target = unit_comparer[start : end]
        with memoryview(self.container_bin) as mv:
            entity_count = len(mv) // 48
            return [
                n for n in range(entity_count)
                if mv[n * 48 + start : n * 48 + end] == target
            ]

    def _rows_of_container(self,
                           container_index: MSK_HexIndex
                           ) -> list[int]:
        """Row numbers of a container, via MSKUT_OnRamData.container_index_table.
        Cached -> returned as is; not cached -> found by scanning and then cached."""
        table = MSKUT_OnRamData.container_index_table
        id_bytes = container_index.to_bytes()

        rows = table.get(container_index)
        if rows is not None:
            # cheap guard: every cached row must still lie in this file and carry this id
            # (protects against an id of another field being asked of this field)
            if all(r * 48 + 16 <= len(self.container_bin)
                   and self.container_bin[r * 48 : r * 48 + 16] == id_bytes
                   for r in rows):
                return rows

        rows = self.masking_comparison(
            unit_comparer=id_bytes + (b'\x00' * 32),
            compare_range=(0, 16)
        )
        if rows:  # an unknown id is not cached
            table[container_index] = rows
        return rows


    def filter_container(self,
                         conditions: list[tuple[MSK_Property, MSK_Address]],
                         max_count: int=1
                         ) -> list[MSK_Container]:
        # local import: container_obj imports this module (circular)
        from shellarc_msk.mskob.container_obj import MSK_Container

        entity_count = len(self.container_bin) // 48

        # all container ids (raw 16 bytes) in order of first appearance; dict = O(1) duplicate check
        all_ids = dict.fromkeys(
            bytes(self.container_bin[i * 48 : i * 48 + 16])
            for i in range(entity_count)
        )

        # a container matches iff EVERY condition (prop, address) is held by one of its rows (AND)
        matched_ids = None
        for condition in conditions:
            unit_comparer = (
                (b'\x00' * 16) +
                condition[0].prop_index.to_bytes() +
                condition[1].adress_index.to_bytes()
            )
            rows = self.masking_comparison(
                unit_comparer=unit_comparer,
                compare_range=(16, 48)
            )
            ids = {bytes(self.container_bin[r * 48 : r * 48 + 16]) for r in rows}
            matched_ids = ids if matched_ids is None else (matched_ids & ids)

        # no condition: every container matches
        selected = [i for i in all_ids if matched_ids is None or i in matched_ids]

        return [
            MSK_Container(
                field_name=self.field_name,
                container_index=MSK_HexIndex.from_bytes(idx)
            )
            for idx in selected[: max_count]
        ]

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
        # byte scan: compare (container id 16B + property id 16B) of each row; no MSK_Entity is built
        key = container_index.to_bytes() + requesting_prop.prop_index.to_bytes()
        with memoryview(self.container_bin) as mv:
            for n in range(len(mv) // 48):
                if mv[n * 48 : n * 48 + 32] == key:
                    return n * 48

        return -1

    @overload
    def write_entity(self,
                     container_index: MSK_HexIndex,
                     prop: MSK_Property,
                     adress: MSK_Address,
                     do_override: bool=False
                     ) -> MSK_Entity:
        ...

    @overload
    def write_entity(self,
                     container_index: MSK_HexIndex,
                     prop: MSK_Property,
                     proceed_step: int,
                     do_override: bool=False
                     ) -> MSK_Entity:
        ...

    def write_entity(self,
                     container_index: MSK_HexIndex,
                     prop: MSK_Property,
                     adress: Optional[MSK_Address]=None,
                     proceed_step: Optional[int]=None,
                     do_override: bool=False
                     ) -> MSK_Entity:
        if adress is None and proceed_step is None:
            raise MSKObject_QueryLogicError(
                msg="An address or an proceed_step is required for writing an entity"
            )
        field_ls = MSK_Field(field_name=self.field_name).field_ls
        if (prop, prop.prop_type) not in field_ls and not do_override:
            raise MSKObject_ValidationError(
                msg="Properties undefined in Field shall only be defined as overrides"
            )
        if adress is not None:
            if prop.prop_type != adress.type:
                raise MSKObject_ValidationError(msg="Type unmatch")
            if (prop.prop_type.type_literals is not None and 
                adress.adress_index not in prop.prop_type.type_literals):
                raise MSKObject_ValidationError(msg="Type Literals Validation Failed")
        
            new_entity_binary = (
                container_index.to_bytes() + 
                prop.prop_index.to_bytes() + 
                adress.adress_index.to_bytes()
            )
            if len(new_entity_binary) != 48:
                raise MSKObject_FormatError(
                    msg="An entiny of a container must be of length 48 bytes"
                )
        pos = self.request_position(
            container_index=container_index,
            requesting_prop=prop
        )
        if pos == -1:
            if adress is None:
                raise MSKObject_QueryLogicError(
                    msg="There is no proceedable value (It is a new entity)"
                )
            new_row = len(self.container_bin) // 48
            with open(self.field_bin_file, "ab") as f:
                f.write(new_entity_binary)
            cached_rows = MSKUT_OnRamData.container_index_table.get(container_index)
            if cached_rows is not None:
                cached_rows.append(new_row)
            MSKUT_OnRamMmap.register(
                field_name=self.field_name,
                filepath=self.field_bin_file
            )
            self.container_bin = MSKUT_OnRamMmap.container_bins[self.field_name]
        else:
            if proceed_step is not None:
                type_literals = prop.prop_type.type_literals
                current_entity = MSK_Entity(entity_chunk=self.container_bin[pos : pos + 48])
                current_address_index = current_entity.address.adress_index
                if not type_literals:
                    raise MSKObject_QueryLogicError(
                        msg=f"Requested property {prop.prop_name} of container {container_index} "
                        f"is of type {prop.prop_type.type_name} which has no literals"
                    )
                current_literal_index = type_literals.index(current_address_index)
                new_literal_index = current_literal_index + proceed_step
                if new_literal_index >= len(type_literals) or new_literal_index < 0:
                    raise MSKObject_QueryLogicError(
                        msg=f"Literal out of range (literal at index {new_literal_index} is queried "
                        f"but the literal list only has a length of {len(type_literals)})"
                    )
                adress = MSK_Address(adress_index=type_literals[new_literal_index]) 
            new_entity_binary = (
                container_index.to_bytes() + 
                prop.prop_index.to_bytes() + 
                adress.adress_index.to_bytes()
             )
            self.container_bin[pos : pos + 48] = new_entity_binary
            self._write_container_binaries()

        return MSK_Entity(entity_chunk=new_entity_binary)

    def _write_container_binaries(self):
        if hasattr(self.container_bin, "flush"):
            self.container_bin.flush()
            