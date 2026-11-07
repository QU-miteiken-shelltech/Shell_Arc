import struct
from typing import Optional

from shellarc_msk.mskfs.path_solver import MSKFS_PathSolver
from shellarc_msk.mskob.hexindex_obj import MSK_HexIndex
from shellarc_msk.mskob.type_obj import MSK_Type

class MSK_Property:
    property_bin = None
    property_offset_bin = None

    def __init__(self,
                 prop_index: MSK_HexIndex | None=None,
                 prop_type: MSK_Type | None=None,
                 prop_name: str | None=None
                 ) -> None:
        if prop_index is None and (prop_type is None or prop_name is None):
            raise ValueError("MSK_Property cannot be made from None")

        self.prop_index : Optional[MSK_HexIndex] = None
        self.prop_type : Optional[MSK_Type] = None
        self.prop_name : Optional[str] = None

        if prop_type is not None and prop_name is not None:
            type_name = prop_type.type_name
            self.prop_index = MSK_HexIndex(
                value=f"{type_name}::{prop_name}",
                do_make=True            
            )
            self.prop_type = prop_type
            self.prop_name = prop_name
            allow_make = True
        else:
            allow_make = False

        mskfs_pathsolver = MSKFS_PathSolver()

        self.property_bin_file = mskfs_pathsolver.mskfs_config / ".msk_property"
        if not self.property_bin_file.exists():
            with open(self.property_bin_file, "wb") as f:
                f.write(b"")
        if self.property_bin is None:
            with open(self.property_bin_file, "rb") as f:
                self.property_bin = f.read()

        self.property_offset_file = mskfs_pathsolver.mskfs_config / ".msk_property_offset"
        if not self.property_offset_file.exists():
            with open(self.property_offset_file, "wb") as f:
                f.write(b"")
        if self.property_offset_bin is None:
            with open(self.property_offset_file, "rb") as f:
                self.property_offset_bin = f.read()

        my_prop = self._search_target_prop(
            # when made from (type, name) the index to look for is the computed one
            target_prop_index=self.prop_index if allow_make else prop_index,
            allow_make=allow_make
        )
        self.prop_index : MSK_HexIndex = my_prop[0]
        self.prop_type : MSK_Type = my_prop[1]
        self.prop_name : str = my_prop[2]
        

    def _search_target_prop(self,
                            target_prop_index: MSK_HexIndex,
                            allow_make: bool=False
                            ) -> Optional[tuple[MSK_HexIndex, MSK_Type, str]]:
        num_chunks = len(self.property_offset_bin) // 8

        for i in range(0, num_chunks):
            offset_pos = i * 8
            chunk_offset = struct.unpack("<Q", self.property_offset_bin[offset_pos : offset_pos + 8])[0]
            if i == num_chunks - 1:
                chunk_next_offset = len(self.property_bin)
            else:
                chunk_next_offset = struct.unpack("<Q", self.property_offset_bin[offset_pos + 8 : offset_pos + 16])[0]

            current_prop_index = MSK_HexIndex.from_bytes(self.property_bin[chunk_offset : chunk_offset + 16])
            if current_prop_index == target_prop_index:
                current_type_index = MSK_HexIndex.from_bytes(self.property_bin[chunk_offset + 16 : chunk_offset + 32])
                current_type = MSK_Type(type_index=current_type_index)
                current_prop_name = self.property_bin[chunk_offset + 32 : chunk_next_offset].decode("utf-8")
                return (current_prop_index, current_type, current_prop_name)

        if (allow_make and 
            (self.prop_index is not None and self.prop_type is not None and self.prop_name is not None)):
            self._make_new_type()
            return (self.prop_index, self.prop_type, self.prop_name)
        else:
            return (MSK_HexIndex(value=None), None, None)

    def _make_new_type(self):
        new_type_bytes = self.prop_index.to_bytes() + self.prop_type.type_index.to_bytes() + self.prop_name.encode("utf-8")
        # the offset file holds the START position of each record
        self.property_offset_bin += len(self.property_bin).to_bytes(8, byteorder="little")
        self.property_bin += new_type_bytes
        self._write_binaries()

    def __eq__(self, other):
        if not isinstance(other, MSK_Property):
            return NotImplemented
        return self.prop_index == other.prop_index

    def __hash__(self):
        return hash(self.prop_index)

    def _write_binaries(self):
        with open(self.property_bin_file, "wb") as f:
            f.write(self.property_bin)
        with open(self.property_offset_file, "wb") as f:
            f.write(self.property_offset_bin)