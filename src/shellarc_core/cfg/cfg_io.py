import json
import os
from enum import Enum
from pathlib import Path
from typing import Any

from shellarc_core.exception.structure_error import SA_ErrorCode, SA_ProjStructError


class Cfg_item(Enum):
    """Enum for configuration items in the project settings.
    """
    PROJ_NAME = "project_name"
    BUCKET_NAME = "bucket_name"
    COLL_NAME = "collection_name"
    SPREADSHEET_KEY = "spreadsheet_key"
    CUTNUM = "cut_num"
    COMPONENT = "components"
    GIT_LREPO = "git_repo_local"
    LOCAL_BACKUP = "local_backup_dir"
    NOTION_DBID = "notion_dbid"
    STORYBOARD_URL = "storybaord_url"


class Cfg_IO:
    def __init__(self):
        project_ctx_dir = Path(os.environ.get("SHELLARC_PROJECT_CTX", None))
        cfg_path = project_ctx_dir / "project_settings.json"
        if not cfg_path.exists():
            raise SA_ProjStructError(
                error_log="project cfg_path not exist",
                error_code=SA_ErrorCode.SA_4001,
            )
        with open(cfg_path, "r", encoding="utf-8") as f:
            self.cfg = json.load(f)


    def get_cfg_setting(self,
                        *args
                        ) -> Any:
        """Get the value of a specific configuration item from the project settings.

        Args:
            *args: A variable number of arguments representing the keys to access the desired configuration item.

        Returns:
            current_item (Any): The value of the requested configuration item, which can be of any data type depending on the structure of the project settings JSON file.
        """
        current_item = self.cfg
        for k in args:
            if not isinstance(current_item, dict):
                raise SA_ProjStructError(
                    error_log=f"key {args} does not exist in the curret config file",
                    error_code=SA_ErrorCode.SA_4002
                )
            if isinstance(k, Cfg_item):
                k = k.value
            current_item = current_item.get(k, None)
        return current_item
        