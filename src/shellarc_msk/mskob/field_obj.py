import struct
from typing import Optional

from shellarc_msk.mskfs.path_solver import MSKFS_PathSolver
from shellarc_msk.mskob.property_obj import MSK_Property
from shellarc_msk.mskob.type_obj import MSK_Type
from shellarc_msk.mskob.hexindex_obj import MSK_HexIndex

class MSK_Field:
    field_bin = None
    field_offset_bin = None

    def __init__(self,
                 field_name: str
                 ) -> None:
        mskfs_pathsolver = MSKFS_PathSolver()

        self.field_offset_file = mskfs_pathsolver.mskfs_config / ".msk_field_offset"
        if not self.field_offset_file.exists():
            with open(self.field_offset_file, "wb") as f:
                f.write(b"")
        if self.field_offset_bin is None:
            with open(self.field_offset_file, "rb") as f:
                self.field_offset_bin = f.read()

        self.field_file = mskfs_pathsolver.mskfs_config / ".msk_field"
        if not self.field_file.exists():
            with open(self.field_file, "wb") as f:
                f.write(b"")
        with open(self.field_file, "rb") as f:
            self.field_bin = f.read()

        self.pos_index = -1
        self.field_ls = self._get_field_bin(
            target_field_name=field_name
        )
        self.field_name = field_name

    def _get_field_bin(self, 
                      target_field_name: str
                      ) -> Optional[list[tuple[MSK_Property, MSK_Type]]]:
        num_chunks = len(self.field_offset_bin) // 8
        if num_chunks == 0:
            return None

        for i in range(0, num_chunks):
            offset_pos = i * 8
            chunk_offset = struct.unpack("<Q", self.field_offset_bin[offset_pos : offset_pos + 8])[0]
            if i == num_chunks - 1:
                chunk_next_offset = len(self.field_bin)
            else:
                chunk_next_offset = struct.unpack("<Q", self.field_offset_bin[offset_pos + 8 : offset_pos + 16])[0]

            field_name_len = struct.unpack("<Q", self.field_bin[chunk_offset : chunk_offset + 8])[0]
            current_field_name = self.field_bin[chunk_offset + 8 : chunk_offset + 8 + field_name_len].decode("utf-8")
            if current_field_name == target_field_name:
                self.pos_index = i
                field_len = chunk_next_offset - chunk_offset - 8 - field_name_len
                field_prop_count = field_len // 32
                field_prop_offset_start = chunk_offset + 8 + field_name_len
                rtn = []
                for j in range(0, field_prop_count):
                    current_start = field_prop_offset_start + j * 32
                    current_prop_index = MSK_HexIndex(self.field_bin[current_start : current_start + 16].decode("utf-8"))
                    current_prop = MSK_Property(prop_index=current_prop_index)
                    current_type_index = MSK_HexIndex(self.field_bin[current_start + 16 : current_start + 32].decode("utf-8"))
                    current_type = MSK_Type(type_index=current_type_index)
                    rtn.append((current_prop, current_type))
                return rtn

        self._declear_field(field_name=self.field_name)
        return []

    def _declear_field(self, 
                  field_name: str
                  ) -> None:
        field_name_bin = field_name.encode("utf-8")
        field_name_len_int = len(field_name_bin)
        field_name_len_bin = struct.pack("<Q", field_name_len_int)
        empty_field = field_name_len_bin + field_name_bin
        self.field_bin += empty_field
        self.field_offset_bin += struct.pack("<Q", len(empty_field))
        self._write_binaries()

    def def_field(self, prop: MSK_Property, type: MSK_Type) -> None:
        if (prop, type) in self.field_ls:
            return

        new_bin = prop.prop_index.to_bytes() + type.type_index.to_bytes()
        shift = len(new_bin)

        num_chunks = len(self.field_offset_bin) // 8
        offsets = list(struct.unpack(f"<{num_chunks}Q", self.field_offset_bin))

        if self.pos_index == num_chunks - 1:
            insert_at = len(self.field_bin)
        else:
            insert_at = offsets[self.pos_index + 1]

        for i in range(self.pos_index + 1, num_chunks):
            offsets[i] += shift
        self.field_offset_bin = struct.pack(f"<{num_chunks}Q", *offsets)

        self.field_bin = self.field_bin[:insert_at] + new_bin + self.field_bin[insert_at:]

        self.field_ls.append((prop, type))
        self._write_binaries()

    def _write_binaries(self):
        with open(self.field_file, "wb") as f:
            f.write(self.field_bin)
        with open(self.field_offset_file, "wb") as f:
            f.write(self.field_offset_bin)

