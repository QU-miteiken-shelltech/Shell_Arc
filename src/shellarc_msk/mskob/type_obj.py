import struct 
from typing import Optional

from shellarc_msk.mskfs.path_solver import MSKFS_PathSolver
from shellarc_msk.mskob.hexindex_obj import MSK_HexIndex

class MSK_Type:
    type_bin = None
    type_offset_bin = None

    def __init__(self,
                 type_index: MSK_HexIndex | None=None,
                 type_name: str | None=None
                 ) -> None:
        if type_index is None and type_name is None:
            raise ValueError("MSK_Type cannot be made from None")

        self.type_index : Optional[MSK_HexIndex] = None
        self.type_name : Optional[str] = None

        if type_name is not None:
            type_index = MSK_HexIndex(
                value=type_name,
                do_make=True
            )
            self.type_index = type_index
            self.type_name = type_name
            allow_make = True
        else:
            allow_make = False

        mskfs_pathsolver = MSKFS_PathSolver()

        self.type_bin_file = mskfs_pathsolver.mskfs_config / ".msk_type"
        if not self.type_bin_file.exists():
            with open(self.type_bin_file, "wb") as f:
                f.write(b"")
        if self.type_bin is None:
            with open(self.type_bin_file, "rb") as f:
                self.type_bin = f.read()

        self.type_offset_file = mskfs_pathsolver.mskfs_config / ".msk_type_offset"
        if not self.type_offset_file.exists():
            with open(self.type_offset_file, "wb") as f:
                f.write(b"")
        if self.type_offset_bin is None:
            with open(self.type_offset_file, "rb") as f:
                self.type_offset_bin = f.read()

        my_type = self._search_target_type(
            target_type_index=type_index,
            allow_make=allow_make
        )
        self.type_index = my_type[0]
        self.type_name = my_type[1]

        
    def _search_target_type(self,
                            target_type_index: MSK_HexIndex,
                            allow_make: bool=False
                            ) -> Optional[tuple[MSK_HexIndex, str]]:
        num_chunks = len(self.type_offset_bin) // 8
        if num_chunks == 0:
            return None

        for i in range(0, num_chunks):
            offset_pos = i * 8
            chunk_offset = struct.unpack("<Q", self.type_offset_bin[offset_pos : offset_pos + 8])[0]
            if i == num_chunks - 1:
                chunk_next_offset = len(self.type_bin)
            else:
                chunk_next_offset = struct.unpack("<Q", self.type_offset_bin[offset_pos + 8 : offset_pos + 16])[0]

            current_type_index = MSK_HexIndex(value=self.type_bin[chunk_offset : chunk_offset + 16].decode("utf-8"))
            if current_type_index == target_type_index:
                current_type_name = self.type_bin[chunk_offset + 16 : chunk_next_offset].decode("utf-8")
                return (current_type_index, current_type_name)

        if allow_make and (self.type_index is not None and self.type_name is not None):
            self._make_new_type()
            return(self.type_index, self.type_name)
        else:
            return (MSK_HexIndex(value=None), None)

    def _make_new_type(self):
        new_type_bytes = self.type_index.to_bytes() + self.type_name.encode("utf-8")
        self.type_bin += new_type_bytes
        self.type_offset_bin += len(new_type_bytes).to_bytes(8, byteorder="little")
        self._write_binaries()

    def _write_binaries(self):
        with open(self.type_bin_file, "wb") as f:
            f.write(self.type_bin)
        with open(self.type_offset_file, "wb") as f:
            f.write(self.type_offset_bin)