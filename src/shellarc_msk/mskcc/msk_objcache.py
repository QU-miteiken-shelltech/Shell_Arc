from functools import wraps
import xxhash
import time
import sys, os

from shellarc_msk.mskcc.cache_data import MSKCC_CACHE, MSKCC_NULL

MASTER_COUNT = 0

def mskcc_object_cache(source_bin):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if __debug__:
                ts = time.time()
                global MASTER_COUNT
                MASTER_COUNT += 1

                chain = []
                frame = sys._getframe(1)
                
                while frame:
                    filename = os.path.basename(frame.f_code.co_filename)
                    lineno = frame.f_lineno
                    chain.append(f"{filename}:{lineno}")
                    frame = frame.f_back
                called_from = " -> ".join(reversed(chain))

            source_hash = xxhash.xxh3_64_hexdigest(source_bin) if source_bin is not None else "0" * 16
            index = None
            for k, v in kwargs.items():
                if k.endswith("_index"): 
                    index = v
            if index is None:
                raise ValueError("None index is passed")
            cached = MSKCC_CACHE.find_cache(
                callable_obj=func,
                index=index,
                source_hash=source_hash
            )
            if cached is not MSKCC_NULL:
                if __debug__: print(f"FOUND : {time.time() - ts} (accu : {MASTER_COUNT}) ({called_from})")
                return cached
            data = func(*args, **kwargs)
            MSKCC_CACHE.cache_data(
                callable_obj=func,
                index=index,
                rtn=data,
                source_hash=source_hash
            )
            if __debug__: print(f"NEW : {time.time() - ts} (accu : {MASTER_COUNT}) ({called_from})")
            return data
        return wrapper
    return decorator