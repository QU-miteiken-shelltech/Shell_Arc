import mmap
from typing import Literal, Optional

from shellarc_msk.mskex.msk_differror import (
    MSKDiff_NonComparableError, MSKDiff_SettingsContradictionError
)
from shellarc_msk.mskex.msk_objerror import MSKObject_FormatError

class MSKDF_DiffSolver:
    def __init__(self, 
                 ours: bytearray | mmap.mmap, 
                 theirs: bytearray,
                 chunk_size: Optional[int]=None):
        self.ours = ours
        self.theirs = theirs
        self.chunk_size = chunk_size

    def identity_diff(self) -> bool:
        return self.ours == self.theirs

    def parallel_diff(
            self,
            ignore_exceeding: Optional[Literal["ours", "theirs"]] = None
            ) -> list[tuple[bytes, bytes]]:
        if self.chunk_size is None:
            raise MSKDiff_NonComparableError(
                msg="identical chunk size is required for parallel diff"
            )
        
        our_len = len(self.ours)
        their_len = len(self.theirs)
        if our_len % self.chunk_size != 0 or their_len % self.chunk_size != 0:
            raise MSKObject_FormatError("Binary data length invalid")
        if our_len != their_len:
            if (ignore_exceeding is None or
                (our_len < their_len and ignore_exceeding == "ours") or
                (our_len > their_len and ignore_exceeding == "theirs")):
                raise MSKDiff_SettingsContradictionError(msg="Ignoring policy offended")
        iterable_len = min(our_len, their_len)

        mv_ours = memoryview(self.ours)[: iterable_len]
        mv_theirs = memoryview(self.theirs)[: iterable_len]
        diffs = []

        def search(start: int, end: int):
            if iterable_len == 0:
                return []
            if mv_ours[start:end] == mv_theirs[start:end]:
                return

            if end - start == self.chunk_size:
                diffs.append((bytes(mv_ours[start:end]), bytes(mv_theirs[start:end])))
                return

            mid = (((start + end) // 2) // self.chunk_size) * self.chunk_size
            if mid == start:
                mid = start + self.chunk_size
            elif mid == end:
                mid = end - self.chunk_size

            search(start, mid)
            search(mid, end)
        search(0, iterable_len)

        return diffs

    def excessive_diff(
            self,
            exceeding: Literal["ours", "theirs"]="ours"
            ) -> list[bytes] | bytearray:
        our_len = len(self.ours)
        their_len = len(self.theirs)
        if (self.chunk_size is not None and
            (our_len % self.chunk_size != 0 or their_len % self.chunk_size != 0)):
            raise MSKDiff_SettingsContradictionError(
                msg="Binary data length not eqial while chunk size is fixed"
            )
        if ((exceeding == "ours" and our_len < their_len) or
            (exceeding == "theirs" and their_len < our_len)):
            raise MSKDiff_SettingsContradictionError(
                msg="Exceeding target mismatch"
            )
        if our_len == their_len:
            return []
        
        exceeding_start = min(our_len, their_len)
        ba = self.ours[exceeding_start :] if exceeding == "ours" else ba = self.theirs[exceeding_start :]
        return (
            [bytes(ba[i : i + self.chunk_size]) 
             for i in range(0, len(ba), self.chunk_size)] 
             if self.chunk_size is not None 
             else ba
        )

    