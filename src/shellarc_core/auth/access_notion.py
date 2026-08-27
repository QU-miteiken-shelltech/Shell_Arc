import os
from pathlib import Path

from dotenv import load_dotenv
from notion_client import Client

from shellarc_core.exception.structure_error import SA_AuthError, SA_ErrorCode


class Notion_Access:
    def __init__(self):
        load_dotenv(verbose=True)
        project_ctx_dir = Path(os.environ.get("SHELLARC_PROJECT_CTX", None))
        dotenv_path = project_ctx_dir / ".env"
        if not dotenv_path.exists():
            raise SA_AuthError(
                error_log=f"dotenv_path {dotenv_path} not exist",
                error_code=SA_ErrorCode.SA_9001
            )
        load_dotenv(dotenv_path)
        notion_token = os.environ.get("Notion_token")
        self.notion = Client(auth=notion_token)

    @property
    def get_notion_client(self):
        return self.notion
