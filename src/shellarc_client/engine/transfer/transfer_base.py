import os
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from dotenv import load_dotenv

import requests

class RemoteKeyPrefix(StrEnum):
    PROJECT_FILE = "production/stage/"
    DATA_BINARY = "production/data/"

class TransferBase:
    def __init__(self):
        load_dotenv(str(Path(__file__).resolve().parents[4] / ".secret/.env"))
        TOKEN = os.environ["R2_API_TOKEN"]
        self.AUTH = {"Authorization" : f"Bearer {TOKEN}"}
        self.API_URL = os.environ["API_ENTRY_URL"]

    def msk_post(self, url_path: str, body: dict, timeout: int=20) -> requests.Response:
        if not url_path.startswith("/"):
            url_path = f"/{url_path}"
        resp = requests.post(
            url=f"{self.API_URL}{url_path}",
            headers=self.AUTH,
            json=body,
            timeout=timeout
        )
        return resp