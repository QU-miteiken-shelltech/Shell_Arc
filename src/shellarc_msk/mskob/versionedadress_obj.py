import struct

from shellarc_msk.mskob.adress_obj import MSK_Address
from shellarc_msk.mskob.hexindex_obj import MSK_HexIndex
from shellarc_msk.mskob.type_obj import MSK_Type
from shellarc_msk.mskfs.path_solver import MSKFS_PathSolver
from shellarc_msk.mskfs.on_ram_data import MSKFS_OnRamData

class MSK_VersionedAdress(MSK_Address):
    def __init__(self,
                 adress_index: MSK_HexIndex | None=None,
                 adress_type: MSK_Type | None=None,
                 adress_value: str | None=None
                 ) -> None:
        super().__init__(
            adress_index=adress_index,
            adress_type=adress_type,
            adress_value=adress_value
        )

        mskfs_pathsolver = MSKFS_PathSolver()

        self.veradress_bin_file = mskfs_pathsolver.mskfs_config / ".msk_ver_adress"
        if not self.veradress_bin_file.exists():
            with open(self.veradress_bin_file, "wb") as f:
                f.write(b"")
        if MSKFS_OnRamData.veradress_bin is None:
            with open(self.veradress_bin_file, "rb") as f:
                MSKFS_OnRamData.veradress_bin = bytearray(f.read())

    def _set_slot_pos(self, slot_pos: int):
        self.slot_pos = slot_pos

    def _count_ones(self, bit_chunk: bytearray) -> int:
        count_target = bit_chunk[0 : self.slot_pos]
        ...

    @property
    def self_chunk_offset(self) -> int:
        if not hasattr(self, "slot_pos"):
            raise RuntimeError("slot_pos attribute not found")
        header_length = struct.unpack("<Q", MSKFS_OnRamData.veradress_bin[0:8])[0]
        occupation_map = MSKFS_OnRamData.veradress_bin[8 : 8 + header_length]
        my_flag = (occupation_map[self.slot_pos // 8] >> (8 - self.slot_pos % 8)) & 1
        if my_flag == 0:
            return -1
        occupied_count_before_self = self._count_ones(occupation_map)
        offset_to_self = 8 + header_length + occupied_count_before_self * 8
        return offset_to_self

    @property
    def version(self) -> int:
        offset_to_self = self.self_chunk_offset
        if offset_to_self == -1:
            return 0
        _version = struct.unpack("<Q", MSKFS_OnRamData.veradress_bin[offset_to_self : offset_to_self + 8])[0]
        return _version

    def update_version(self) -> int:
        current_version = self.version
        if current_version == 0:
            header_length = struct.unpack("<Q", MSKFS_OnRamData.veradress_bin[0:8])[0]
            flag_chunk = (MSKFS_OnRamData.veradress_bin[8 + self.slot_pos // 8])
            flag_chunk ^= (1 << (8 - self.slot_pos % 8))
            MSKFS_OnRamData.veradress_bin[8 + self.slot_pos // 8] = flag_chunk
            self_chunk_offset = self.self_chunk_offset
            MSKFS_OnRamData.veradress_bin[self_chunk_offset : self_chunk_offset] = struct.pack("<Q", current_version + 1)
        else:
            self_chunk_offset = self.self_chunk_offset
            MSKFS_OnRamData.veradress_bin[self_chunk_offset : self_chunk_offset] = struct.pack("<Q", current_version + 1)
        self._write_binaries()

    def _write_binaries(self) -> None:
        with open(self.veradress_bin_file, "wb") as f:
            f.write(bytes(MSKFS_OnRamData.veradress_bin))



