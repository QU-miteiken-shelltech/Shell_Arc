import struct
from typing import Optional

from shellarc_msk.mskfs.on_ram_data import MSKFS_OnRamData
from shellarc_msk.mskfs.path_solver import MSKFS_PathSolver
from shellarc_msk.mskob.hexindex_obj import MSK_HexIndex
from shellarc_msk.mskob.type_obj import MSK_Type

class MSK_Adress:
    def __init__(self,
                 adress_index: MSK_HexIndex | None=None,
                 adress_type: MSK_Type | None=None,
                 adress_value: str | None=None
                 ) -> None:
        if adress_index is None and (adress_type is None or adress_value is None):
            raise ValueError("MSK_Adress cannot be made from None")

        self.adress_index : Optional[MSK_HexIndex] = MSK_HexIndex(value=None)
        self.type : Optional[MSK_Type] = MSK_Type(type_index=MSK_HexIndex(value=None))
        self.value : Optional[str] = None

        if adress_index == MSK_HexIndex(value=None):
            return

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
        if MSKFS_OnRamData.adress_bin is None:
            with open(self.adress_bin_file, "rb") as f:
                MSKFS_OnRamData.adress_bin = bytearray(f.read())

        self.adress_offset_file = mskfs_pathsolver.mskfs_config / ".msk_adress_offset"
        # a missing OR empty file (e.g. made by an older version) starts as one empty page
        if not self.adress_offset_file.exists() or self.adress_offset_file.stat().st_size == 0:
            with open(self.adress_offset_file, "wb") as f:
                init_zeros = b'\x00' * (120000 * 8)
                f.write(init_zeros)
        if MSKFS_OnRamData.adress_offset_bin is None:
            with open(self.adress_offset_file, "rb") as f:
                offset_bin = bytearray(f.read())
            if len(offset_bin) % (120000 * 8) != 0:
                raise ValueError("'.msk_adress_offset' is not a whole number of pages "
                                 "(made by an older format?)")
            MSKFS_OnRamData.adress_offset_bin = offset_bin
  

        my_adress = self._search_target_adress(
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
        num_pages = len(MSKFS_OnRamData.adress_offset_bin) // (120000 * 8)

        adress_index_int = int(target_adress_index, 0)
        do_hit = False
        # Every page is an independent open-addressing table (linear probing, wrapping around).
        # A slot holds (record offset in adress_bin + 1); 0 means "empty" and ends the probe of that page.
        for page in range(0, num_pages):
            prim_offset_pos = adress_index_int % (120000 - 1)
            for _ in range(0, 120000 - 1):
                offset_start = page * (120000 * 8) + 8
                offset_pos = offset_start + prim_offset_pos * 8
                slot = struct.unpack("<Q", MSKFS_OnRamData.adress_offset_bin[offset_pos : offset_pos + 8])[0]
                if slot == 0:
                    break
                chunk_offset = slot - 1
                current_adress_index = MSK_HexIndex.from_bytes(MSKFS_OnRamData.adress_bin[chunk_offset : chunk_offset + 16])
                if current_adress_index == target_adress_index:
                    do_hit = True
                    break
                prim_offset_pos = (prim_offset_pos + 1) % (120000 - 1)
            if do_hit:
                break

        if do_hit:
            # record = index(16) + type(16) + value length(8, "<Q") + value
            current_type_index = MSK_HexIndex.from_bytes(MSKFS_OnRamData.adress_bin[chunk_offset + 16 : chunk_offset + 32])
            current_type = MSK_Type(type_index=current_type_index)
            value_len = struct.unpack("<Q", MSKFS_OnRamData.adress_bin[chunk_offset + 32 : chunk_offset + 40])[0]
            current_value = MSKFS_OnRamData.adress_bin[chunk_offset + 40 : chunk_offset + 40 + value_len].decode("utf-8")
            return (current_adress_index, current_type, current_value)

        if (allow_make and 
            self.adress_index is not None and self.type is not None and self.value is not None):
            self._make_new_adress()
            return (self.adress_index, self.type, self.value)
        else:
            return (MSK_HexIndex(value=None), None, None)

    def _make_new_adress(self):
        # record = index(16) + type(16) + value length(8, "<Q") + value
        value_bin = self.value.encode("utf-8")
        new_adress_bytes = (self.adress_index.to_bytes() + self.type.type_index.to_bytes() +
                            struct.pack("<Q", len(value_bin)) + value_bin)
        # a slot holds (record offset + 1), so that 0 can mean "empty slot"
        new_offset_bytes = (len(MSKFS_OnRamData.adress_bin) + 1).to_bytes(8, byteorder="little")

        # New records go into the newest page. The first 8 bytes of a page count its filled slots.
        num_pages = len(MSKFS_OnRamData.adress_offset_bin) // (120000 * 8)
        page_start = (num_pages - 1) * (120000 * 8)
        filled_num = struct.unpack("<Q", MSKFS_OnRamData.adress_offset_bin[page_start : page_start + 8])[0]
        if filled_num >= 80000:
            MSKFS_OnRamData.adress_offset_bin += b'\x00' * (120000 * 8)
            num_pages += 1
            page_start += 120000 * 8
            filled_num = 0

        adress_index_int = int(self.adress_index, 0)
        prim_offset_pos = adress_index_int % (120000 - 1)
        for _ in range(0, 120000 - 1):
            offset_start = page_start + 8
            offset_pos = offset_start + prim_offset_pos * 8
            chunk_offset_bytes = MSKFS_OnRamData.adress_offset_bin[offset_pos : offset_pos + 8]
            if chunk_offset_bytes == b'\x00' * 8:
                break
            prim_offset_pos = (prim_offset_pos + 1) % (120000 - 1)
        else:
            raise RuntimeError("adress table page is full")

        MSKFS_OnRamData.adress_bin += new_adress_bytes
        MSKFS_OnRamData.adress_offset_bin = (MSKFS_OnRamData.adress_offset_bin[: offset_pos] +
                                             new_offset_bytes +
                                             MSKFS_OnRamData.adress_offset_bin[offset_pos + 8 :])
        MSKFS_OnRamData.adress_offset_bin[page_start : page_start + 8] = struct.pack("<Q", filled_num + 1)

        self._append_binaries(
            appended_adress_bytes=new_adress_bytes,
            offset_bin=MSKFS_OnRamData.adress_offset_bin
        )

    def __eq__(self, other):
        if not isinstance(other, MSK_Adress):
            return NotImplemented
        return self.adress_index == other.adress_index

    def __hash__(self):
        return hash(self.adress_index)

    def _append_binaries(self, 
                         appended_adress_bytes: bytes, 
                         offset_bin: bytes
                         ) -> None:
        with open(self.adress_bin_file, "ab") as f:
            f.write(appended_adress_bytes)
        with open(self.adress_offset_file, "wb") as f:
            f.write(offset_bin)