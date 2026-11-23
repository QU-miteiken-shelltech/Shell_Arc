import struct

from shellarc_msk.mskob.adress_obj import MSK_Address
from shellarc_msk.mskob.hexindex_obj import MSK_HexIndex
from shellarc_msk.mskob.type_obj import MSK_Type
from shellarc_msk.mskut.path_solver import MSKUT_PathSolver
from shellarc_msk.mskut.on_ram_data import MSKUT_OnRamData

class MSK_VersionedAdress(MSK_Address):
    def __init__(self,
                 adress_index: MSK_HexIndex | None=None,
                 adress_type: MSK_Type | None=None,
                 adress_value: str | None=None, 
                 do_make: bool=False
                 ) -> None:
        super().__init__(
            adress_index=adress_index,
            adress_type=adress_type,
            adress_value=adress_value
        )
        self.do_make = do_make

        mskfs_pathsolver = MSKUT_PathSolver()

        self.veradress_bin_file = mskfs_pathsolver.mskfs_space / ".msk_ver_adress"
        if not self.veradress_bin_file.exists():
            with open(self.veradress_bin_file, "wb") as f:
                f.write(b"\x00" * 8)
        if MSKUT_OnRamData.veradress_bin is None:
            with open(self.veradress_bin_file, "rb") as f:
                MSKUT_OnRamData.veradress_bin = bytearray(f.read())

        if self.self_chunk_offset() == -1:
            raise ValueError("This address is not decleared as a versioned address"
                             "Make it versioned by turning the do_make flag True")

    def _set_slot_pos(self, slot_pos: int):
        self.slot_pos = slot_pos

    def _rank_one(self, bit_chunk: bytearray) -> int:
        if not hasattr(self, "slot_pos"):
            raise RuntimeError("slot_pos attribute not found")
        count_target = bit_chunk[0 : self.slot_pos // 8 + 1]
        bit_count = len(count_target) * 8
        if self.slot_pos <= 0:
            return 0
        if self.slot_pos >= bit_count:
            raise ValueError("Slot position cannot be larger than the total bit count")
        int_val = int.from_bytes(count_target, "big")
        shift_amount = bit_count - self.slot_pos

        return (int_val >> shift_amount).bit_count()
        
    @property
    def self_chunk_offset(self) -> int:
        if not hasattr(self, "slot_pos"):
            raise RuntimeError("slot_pos attribute not found")
        index_header_length = struct.unpack("<Q", MSKUT_OnRamData.veradress_bin[0:8])[0]
        required_header_len = (self.slot_pos // 8) + 1
        if index_header_length < required_header_len:
            if not self.do_make:
                return 1
            zero_bytes_to_add = required_header_len - index_header_length
            MSKUT_OnRamData.veradress_bin[8 + index_header_length : 8 + index_header_length] = b"\x00" * zero_bytes_to_add
            MSKUT_OnRamData.veradress_bin[0:8] = struct.pack("<Q", required_header_len)
            return -1
        index_header = MSKUT_OnRamData.veradress_bin[8 : 8 + index_header_length]
        my_flag = (index_header[self.slot_pos // 8] >> (7 - self.slot_pos % 8)) & 1
        if my_flag == 0 or not self.do_make:
            return -1
        occupied_count_before_self = self._rank_one(index_header)
        offset_to_self = 8 + len(index_header) + occupied_count_before_self * 8
        return offset_to_self

    @property
    def version(self) -> int:
        offset_to_self = self.self_chunk_offset
        if offset_to_self == -1:
            return 0
        _version = struct.unpack("<Q", MSKUT_OnRamData.veradress_bin[offset_to_self : offset_to_self + 8])[0]
        return _version

    def update_version(self) -> int:
        current_version = self.version
        if current_version == 0:
            flag_chunk = (MSKUT_OnRamData.veradress_bin[8 + self.slot_pos // 8])
            flag_chunk ^= (1 << (7 - self.slot_pos % 8))
            MSKUT_OnRamData.veradress_bin[8 + self.slot_pos // 8] = flag_chunk
            self_chunk_offset = self.self_chunk_offset
            if self_chunk_offset == -1:
                return 0
            current_version += 1
            MSKUT_OnRamData.veradress_bin[self_chunk_offset : self_chunk_offset] = struct.pack("<Q", current_version)
        else:
            self_chunk_offset = self.self_chunk_offset
            current_version += 1
            MSKUT_OnRamData.veradress_bin[self_chunk_offset : self_chunk_offset + 8] = struct.pack("<Q", current_version)
        self._write_binaries()
        return current_version

    def _write_binaries(self) -> None:
        with open(self.veradress_bin_file, "wb") as f:
            f.write(bytes(MSKUT_OnRamData.veradress_bin))



