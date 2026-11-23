from shellarc_client.engine.transfer.durable_lock import LockRemote
from shellarc_client.engine.transfer.file_transfer import FileTransfer
from shellarc_client.engine.transfer.network_utils import NetworkUtils
from shellarc_client.engine.mskio import write_msk


def put_to_storage(remote_file_name: str):
    if not NetworkUtils.check_url_connection():
        raise ValueError("Internet not connected")
    with LockRemote() as lock:
        if lock.token is None:
            raise ValueError("Remote locked")
        
        

def get_from_storage():
    pass