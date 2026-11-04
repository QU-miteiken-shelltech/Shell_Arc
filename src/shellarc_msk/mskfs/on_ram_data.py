import json

from shellarc_msk.mskfs.path_solver import MSKFS_PathSolver

class MSKFS_OnRam:
    ACCESS_MAP = None
    CONTAINERS = None
    FIELDS = None

    @classmethod
    def write_to_disk(cls):
        mskfs_pathsolver = MSKFS_PathSolver()
        field_file = mskfs_pathsolver.mskfs_config / ".msk_field"
        container_file = mskfs_pathsolver.mskfs_config / ".msk_container"
        access_file = mskfs_pathsolver.mskfs_config / ".msk_access"
        with open(field_file, "w", encoding="utf-8") as f:
            json.dump(cls.FIELDS, f, ensure_ascii=False, indent=3)
        with open(container_file, "w", encoding="utf-8") as f:
            json.dump(cls.CONTAINERS, f, ensure_ascii=False, indent=3)
        with open(access_file, "w", encoding="utf-8") as f:
            json.dump(cls.ACCESS_MAP, f, ensure_ascii=False, indent=2)

