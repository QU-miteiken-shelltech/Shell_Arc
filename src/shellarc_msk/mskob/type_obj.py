import struct 
import hashlib
from typing import Optional, Self, TYPE_CHECKING

from shellarc_msk.mskut.on_ram_data import MSKUT_OnRamData
from shellarc_msk.mskut.path_solver import MSKUT_PathSolver
from shellarc_msk.mskob.hexindex_obj import MSK_HexIndex
from shellarc_msk.mskcc.msk_objcache import mskcc_object_cache
from shellarc_msk.mskex.msk_objerror import MSKObject_NoneCreationError

class MSK_Type:
    def __init__(self,
                 type_index: MSK_HexIndex | None=None,
                 type_name: str | None=None,
                 type_literals: list[str] | None=None,
                 allow_make: bool=False
                 ) -> None:
        from shellarc_msk.mskob.adress_obj import MSK_Address
        if type_index is None and type_name is None:
            raise MSKObject_NoneCreationError(
                msg="MSK_Type cannot be made from None"
            )

        self.type_index : MSK_HexIndex = MSK_HexIndex(value=None)
        self.type_name : Optional[str] = None
        self.type_literals: list[MSK_HexIndex] | None = None

        if type_index == MSK_HexIndex(value=None):
            return

        if type_name is not None:
            type_index = MSK_HexIndex(
                value=type_name,
                do_make=True
            )
            self.type_index = type_index
            self.type_name = type_name
            self.type_literals = [
                MSK_Address(adress_type=self, adress_value=a).adress_index 
                for a in type_literals
            ] if type_literals is not None else None
            allow_make = allow_make
        else:
            allow_make = False

        mskfs_pathsolver = MSKUT_PathSolver()

        self.type_bin_file = mskfs_pathsolver.mskfs_space / ".msk_type"
        if not self.type_bin_file.exists():
            with open(self.type_bin_file, "wb") as f:
                f.write(b"")
        if MSKUT_OnRamData.type_bin is None:
            with open(self.type_bin_file, "rb") as f:
                MSKUT_OnRamData.type_bin = bytearray(f.read())

        self.type_offset_file = mskfs_pathsolver.mskfs_space / ".msk_type_offset"
        if not self.type_offset_file.exists():
            with open(self.type_offset_file, "wb") as f:
                f.write(b"")
        if MSKUT_OnRamData.type_offset_bin is None:
            with open(self.type_offset_file, "rb") as f:
                MSKUT_OnRamData.type_offset_bin = bytearray(f.read())

        my_type = self._search_target_type(
            target_type_index=type_index,
            allow_make=allow_make
        )
        self.type_index = my_type[0]
        self.type_name = my_type[1]
        self.type_literals = my_type[2]

    @classmethod
    def list_types(cls) -> list[Self]:
        num_chunks = len(MSKUT_OnRamData.type_offset_bin) // 8
        type_list = []
        for i in range(0, num_chunks):
            offset_pos = i * 8
            chunk_offset = struct.unpack("<Q", MSKUT_OnRamData.type_offset_bin[offset_pos : offset_pos + 8])[0]
            if i == num_chunks - 1:
                chunk_next_offset = len(MSKUT_OnRamData.type_bin)
            else:
                chunk_next_offset = struct.unpack("<Q", MSKUT_OnRamData.type_offset_bin[offset_pos + 8 : offset_pos + 16])[0]
            current_type_index = MSK_HexIndex.from_bytes(MSKUT_OnRamData.type_bin[chunk_offset : chunk_offset + 16])
            current_type_name = MSKUT_OnRamData.type_bin[chunk_offset + 16 : chunk_next_offset].decode("utf-8")
            type_list.append(
                MSK_Type(
                    type_index=current_type_index,
                    type_name=current_type_name
                )
            )
        return type_list

    @mskcc_object_cache(source=lambda self: MSKUT_OnRamData.type_bin)
    def _search_target_type(self,
                            target_type_index: MSK_HexIndex,
                            allow_make: bool=False
                            ) -> Optional[tuple[MSK_HexIndex, str, list[MSK_HexIndex]]]:
        num_chunks = len(MSKUT_OnRamData.type_offset_bin) // 8

        for i in range(0, num_chunks):
            offset_pos = i * 8
            chunk_offset = struct.unpack("<Q", MSKUT_OnRamData.type_offset_bin[offset_pos : offset_pos + 8])[0]
            if i == num_chunks - 1:
                chunk_next_offset = len(MSKUT_OnRamData.type_bin)
            else:
                chunk_next_offset = struct.unpack("<Q", MSKUT_OnRamData.type_offset_bin[offset_pos + 8 : offset_pos + 16])[0]

            current_type_index = MSK_HexIndex.from_bytes(MSKUT_OnRamData.type_bin[chunk_offset : chunk_offset + 16])
            if current_type_index == target_type_index:
                current_type_name_len = struct.unpack(
                    "<Q", MSKUT_OnRamData.type_bin[chunk_offset + 16 : chunk_offset + 24]
                )[0]
                current_type_name = MSKUT_OnRamData.type_bin[chunk_offset + 24 : chunk_next_offset + 24 + current_type_name_len].decode("utf-8")
                current_type_literals_raw = MSKUT_OnRamData.type_bin[chunk_next_offset + 24 + current_type_name_len : chunk_next_offset]
                current_type_literals = [
                    MSK_HexIndex.from_bytes(
                        current_type_literals_raw[i * 16 : i * 16 + 16]
                    ) for i in range(0, (chunk_next_offset - (chunk_next_offset + 24 + current_type_name_len)) // 16)
                ]
                current_type_literals = current_type_literals if current_type_literals else None
                return (current_type_index, current_type_name, current_type_literals)

        if allow_make and (self.type_index is not None and self.type_name is not None):
            self._make_new_type()
            return(self.type_index, self.type_name, self.type_literals)
        else:
            return (MSK_HexIndex(value=None), None, None)

    def _make_new_type(self):
        type_name_bytes = self.type_name.encode("utf-8")
        new_type_bytes = (
            self.type_index.to_bytes() + 
            struct.pack("<Q", len(type_name_bytes)) +
            type_name_bytes 
        )
        if self.type_literals is not None:
            new_type_bytes += b"".join(hexixndex.to_bytes() for hexixndex in self.type_literals)
        new_offset_bytes = len(MSKUT_OnRamData.type_bin).to_bytes(8, byteorder="little")
        MSKUT_OnRamData.type_offset_bin += new_offset_bytes
        MSKUT_OnRamData.type_bin += new_type_bytes
        self._append_binaries(new_type_bytes, new_offset_bytes)

    def __eq__(self, other):
        if not isinstance(other, MSK_Type):
            return NotImplemented
        return self.type_index == other.type_index

    def __hash__(self):
        return hash(self.type_index)

    def _append_binaries(self, record_bytes: bytes, offset_bytes: bytes):
        # append only the new record (the files are never rewritten)
        with open(self.type_bin_file, "ab") as f:
            f.write(record_bytes)
        with open(self.type_offset_file, "ab") as f:
            f.write(offset_bytes)

    def __str__(self):
        rtn_str = (
            f"type_index : {self.type_index} \n"
            f"type_name : {self.type_name}"
        )
        return rtn_str