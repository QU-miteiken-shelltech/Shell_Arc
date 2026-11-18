from pathlib import Path
from typing import Any
from collections import defaultdict
from functools import reduce
import operator
import json

from shellarc_msk.mskfs.path_solver import MSKFS_PathSolver

def _recursive_defaultdict():
    return defaultdict(_recursive_defaultdict)

class ReadClientConfig:
    client_config_path = MSKFS_PathSolver().mskfs_client / "client_config.json"
    if not client_config_path.exists():
        with open(client_config_path, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=3)
    with open(client_config_path, "r", encoding="utf-8") as f:
        CLIENT_CONFIG = json.load(f, object_hook=lambda d: defaultdict(_recursive_defaultdict, d))

    @classmethod
    def get_config_item(cls, *args) -> Any:
        with open(cls.client_config_path, "r", encoding="utf-8") as f:
            cls.CLIENT_CONFIG = json.load(f, object_hook=lambda d: defaultdict(_recursive_defaultdict, d))
        current_checking = cls.CLIENT_CONFIG
        for key in args:
            if not isinstance(current_checking, dict):
                break
            current_checking = current_checking.get(key, {})
        return current_checking

    @classmethod
    def write_config_item(cls, val, *args) -> None:
        reduce(operator.getitem, args[:-1], cls.CLIENT_CONFIG)[args[-1]] = val
        with open(cls.client_config_path, "w", encoding="utf-8") as f:
            json.dump(cls.CLIENT_CONFIG, f, ensure_ascii=False, indent=3)
        return cls.CLIENT_CONFIG

    @classmethod
    def get_mounted_dir(cls) -> Path:
        return Path(cls.get_config_item("mounted_dir"))