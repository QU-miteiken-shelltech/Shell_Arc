import mmap
import os
import atexit
from typing import Optional

class MSKFS_OnRamData:
    adress_bin : Optional[bytes] = None
    adress_offset_bin : Optional[bytes] = None
    field_bin : Optional[bytes] = None
    field_offset_bin : Optional[bytes] = None
    property_bin : Optional[bytes] = None
    property_offset_bin : Optional[bytes] = None
    type_bin : Optional[bytes] = None
    type_offset_bin : Optional[bytes] = None


class MSKFS_OnRamMmap:
    container_bins: Optional[dict[str, mmap.mmap]] = None

    @classmethod
    def register(cls, field_name: str, filepath: str):
        if cls.container_bins is None:
            cls.container_bins = {}
            atexit.register(cls.close_all)
        try:
            # mmap cannot map an empty file: keep b"" until the first entity is appended
            if os.path.getsize(filepath) == 0:
                cls.container_bins[field_name] = b""
                return
            f = open(filepath, "r+b")
            cls.container_bins[field_name] = mmap.mmap(f.fileno(), 0)
        except Exception as e:
            print(f"'{field_name}' mmap register failed: {e}")
            raise

    @classmethod
    def close_all(cls):
        if cls.container_bins:
            for name, mm in cls.container_bins.items():
                try:
                    if not hasattr(mm, "close"):  # b"" placeholder of an empty file
                        continue
                    mm.close()
                    print(f"'{name}' mmap closed")
                except Exception as e:
                    print(f"'{name}' gives an error upon closing: {e}")
            cls.container_bins = None