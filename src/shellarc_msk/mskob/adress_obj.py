import struct
from typing import Optional

from shellarc_msk.mskfs.path_solver import MSKFS_PathSolver
from shellarc_msk.mskob.hexindex_obj import MSK_HexIndex
from shellarc_msk.mskob.type_obj import MSK_Type

class MSK_Adress:
    adress_bin = None
    adress_offset_bin = None

    def __init__(self,
                 adress_index: MSK_HexIndex | None=None,
                 adress_type: MSK_Type | None=None,
                 adress_value: str | None=None
                 ) -> None:
        if adress_index is None and (adress_type is None or adress_value is None):
            raise ValueError("MSK_Adress cannot be made from None")

        self.adress_index : Optional[MSK_HexIndex] = None
        self.type : Optional[MSK_Type] = None
        self.value : Optional[str] = None

        if adress_type is not None and adress_value is not None:
            self.adress_index = MSK_HexIndex(
                value=adress_value,
                do_make=True
            )
            self.type : MSK_Type = adress_type
            self.value : str = adress_value
            allow_make = True
        else:
            allow_make = False
        
        mskfs_pathsolver = MSKFS_PathSolver()

        self.adress_bin_file = mskfs_pathsolver.mskfs_config / ".msk_adress"
        if not self.adress_bin_file.exists():
            with open(self.adress_bin_file, "wb") as f:
                f.write(b"")
        if self.adress_bin is None:
            with open(self.adress_bin_file, "rb") as f:
                self.adress_bin = f.read()

        self.adress_offset_file = mskfs_pathsolver.mskfs_config / ".msk_adress_offset"
        if not self.adress_offset_file.exists():
            with open(self.adress_offset_file, "wb") as f:
                f.write(b"")
        if self.adress_offset_bin is None:
            with open(self.adress_offset_file, "rb") as f:
                self.adress_offset_bin = f.read()
  

        my_adress = self._search_target_adress(
            # when made from (type, value) the index to look for is the computed one
            target_adress_index=self.adress_index if allow_make else adress_index,
            allow_make=allow_make
        )
        self.adress_index = my_adress[0]
        self.type = my_adress[1]
        self.value = my_adress[2]
        

    def _search_target_adress(self,
                              target_adress_index: MSK_HexIndex,
                              allow_make: bool=False
                              ) -> Optional[tuple[MSK_HexIndex, MSK_Type, str]]:
        num_chunks = len(self.adress_offset_bin) // 8

        for i in range(0, num_chunks):
            offset_pos = i * 8
            chunk_offset = struct.unpack("<Q", self.adress_offset_bin[offset_pos : offset_pos + 8])[0]
            if i == num_chunks - 1:
                chunk_next_offset = len(self.adress_bin)
            else:
                chunk_next_offset = struct.unpack("<Q", self.adress_offset_bin[offset_pos + 8 : offset_pos + 16])[0]

            current_adress_index = MSK_HexIndex.from_bytes(self.adress_bin[chunk_offset : chunk_offset + 16])
            if current_adress_index == target_adress_index:
                current_type_index = MSK_HexIndex.from_bytes(self.adress_bin[chunk_offset + 16 : chunk_offset + 32])
                current_type = MSK_Type(type_index=current_type_index)
                current_value = self.adress_bin[chunk_offset + 32 : chunk_next_offset].decode("utf-8")
                return (current_adress_index, current_type, current_value)

        if (allow_make and 
            self.adress_index is not None and self.type is not None and self.value is not None):
            self._make_new_type()
            return (self.adress_index, self.type, self.value)
        else:
            return (MSK_HexIndex(value=None), None, None)

    def _make_new_type(self):
        new_type_bytes = self.adress_index.to_bytes() + self.type.type_index.to_bytes() + self.value.encode("utf-8")
        # the offset file holds the START position of each record
        self.adress_offset_bin += len(self.adress_bin).to_bytes(8, byteorder="little")
        self.adress_bin += new_type_bytes
        self._write_binaries()

    def __eq__(self, other):
        if not isinstance(other, MSK_Adress):
            return NotImplemented
        return self.adress_index == other.adress_index

    def __hash__(self):
        return hash(self.adress_index)

    def _write_binaries(self):
        with open(self.adress_bin_file, "wb") as f:
            f.write(self.adress_bin)
        with open(self.adress_offset_file, "wb") as f:
            f.write(self.adress_offset_bin)