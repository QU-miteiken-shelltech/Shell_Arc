from collections import UserDict

MSKCC_NULL = object()

class MSKCC_CacheData(UserDict):
    def cache_data(self, callable_obj, index, rtn, source_hash):
        if not callable(callable_obj):
            raise ValueError("Cache data must be linked to a callable")
        self.setdefault(callable_obj, {})
        if source_hash != self[callable_obj].get("source_hash", ""):
            self[callable_obj]["source_hash"] = source_hash
            self[callable_obj]["data"] = {}
        self[callable_obj].setdefault("data", {})[index] = rtn

    def find_cache(self, callable_obj, index, source_hash):
        if not callable(callable_obj):
            raise ValueError("Cache data must be linked to a callable")
        if callable_obj not in self:
            return MSKCC_NULL
        if source_hash != self[callable_obj].get("source_hash", ""):
            return MSKCC_NULL
        return self[callable_obj].get("data", {}).get(index, MSKCC_NULL)

    def __setitem__(self, key, value):
        super().__setitem__(key, value)

    def __getitem__(self, key):
        return super().__getitem__(key)

MSKCC_CACHE = MSKCC_CacheData({})

# cache_scheme = {
#     {
#         callable : {
#             source_hash : str,
#             data : {index : rtn}
#         }
#     }
# }