from typing import Optional

from shellarc_engine.transfer.transfer_base import TransferBase

class DurableLock(TransferBase):
    def __init__(self):
        super().__init__()

    def acquire_lock(self, metadata: Optional[dict]=None) -> str | None:
        resp = self.msk_post(
            url_path="/lock/acquire",
            body={
                "name": "MSK_submission",
                "ttlSec": 65,
                "metadata": metadata if metadata is not None else ""
            }
        )
        if resp.status_code == 409:
            return None
        resp.raise_for_status()
        return resp.json().get("token", None)

    def query_lock_info(self) -> dict:
        resp = self.msk_post(
            url_path="/lock/info",
            body={"name": "MSK_submission"}
        )
        resp.raise_for_status()
        return resp.json()

    def is_locked(self) -> bool:
        resp = self.msk_post(
            url_path="/lock/status",
            body={"name": "MSK_submission"}
        )
        resp.raise_for_status()
        return resp.json().get("locked")

    def match_token(self, token: str) -> bool:
        resp = self.msk_post(
            url_path="/lock/token_match",
            body={
                "name": "MSK_submission",
                "token": token
            }
        )
        resp.raise_for_status()
        return resp.json().get("matched")

    def release_lock(self, token: str) -> dict:
        resp = self.msk_post(
            url_path="/lock/release",
            body={
                "name": "MSK_submission",
                "token": token  
            }
        )
        resp.raise_for_status()
        return resp.json()


class LockRemote:
    def __init__(self, metadata: Optional[dict]=None):
        self.metadata = metadata
        self.token = None
        self.durable_locker = DurableLock()

    def __enter__(self):
        self.token = (self.durable_locker.acquire_lock(metadata=self.metadata) 
                      if not self.durable_locker.is_locked() else None)
        return self

    def __exit__(self, *exc):
        if self.token is not None:
            self.durable_locker.release_lock(token=self.token)