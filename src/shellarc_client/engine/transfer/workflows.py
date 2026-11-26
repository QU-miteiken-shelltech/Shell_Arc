import base64
import shutil
from typing import Optional, Callable
from datetime import datetime
from pathlib import Path

from shellarc_client.engine.transfer.durable_lock import LockRemote
from shellarc_client.engine.transfer.file_transfer import FileTransfer
from shellarc_client.engine.transfer.network_utils import NetworkUtils
from shellarc_client.engine.transfer.transfer_base import RemoteKeyPrefix
from shellarc_client.engine.mskio import write_msk
from shellarc_client.engine.mount import mount_file_manager
from shellarc_client.engine.config.read_config import ReadClientConfig
from shellarc_msk.mskob.container_obj import MSK_Container
from shellarc_msk.mskob.property_obj import MSK_Property
from shellarc_msk.mskut.path_solver import MSKUT_PathSolver
from shellarc_msk.mskdf.msk_merge import merge_container_coll

MYNAME = "midukiみづき"

def _encode_nonascii(string: str):
    if not string.isascii():
        rtn_str = base64.b64encode(string.encode("utf-8")).decode("ascii")
        rtn_str = f"B64{rtn_str}"
    else:
        rtn_str = string
    rtn_str.replace("_", "+")
    rtn_str.replace("/", "*")
    return rtn_str

def r2_filename_factory(cut_num_indicator: str,
                        component: str,
                        person: str,
                        ext: str
                        ):
    print(f"@@{cut_num_indicator} / {component} / {person}")
    ext = ext.lstrip(".")
    r2_filename = (
        f"{_encode_nonascii(cut_num_indicator)}_"
        f"{_encode_nonascii(component)}_"
        f"{_encode_nonascii(person)}_"
        f"{datetime.now().strftime("%y%m%d%H%M%S")}"
        f".{ext}"
    )
    return r2_filename

def sync_data(field_name: str,
              writing_operation: Optional[Callable]=None):
    if not NetworkUtils.check_url_connection():
        raise ValueError("Internet not connected")
    
    with LockRemote() as lock:
        if lock.token is None:
            raise ValueError("Remote locked")
        file_transfer = FileTransfer()
        field_name = field_name
        bin_dict: dict[str, bytearray] = {
            ".msk_adress_offset" : bytearray(),
            ".msk_adress" : bytearray(),
            f".msk_container_{field_name}" : bytearray()
        }
        for bin_filename in [".msk_adress_offset", ".msk_adress", f".msk_container_{field_name}"]:
            local_destination_path=str(MSKUT_PathSolver().mskfs_tmp / bin_filename)   
            file_transfer.download_file(
                r2_key_prefix=RemoteKeyPrefix.DATA_BINARY,
                r2_filename=bin_filename.lstrip("."),
                local_destination_path=local_destination_path   
            )
            with open(local_destination_path, "rb") as f:
                bin_dict[bin_filename] = bytearray(f.read())
        print("Start merge")
        merge_result = merge_container_coll(
            field_name=field_name,
            incoming_container_bin=bin_dict[f".msk_container_{field_name}"],
            incoming_address_bin=bin_dict[".msk_adress"],
            incoming_address_offset_bin=bin_dict[".msk_adress_offset"]
        )

        if writing_operation is None or not callable(writing_operation):
            return
        writing_operation()
        print("Start overwrite")
        try:
            if (lock.durable_locker.match_token(token=lock.token) and
                lock.durable_locker.query_lock_info().get("remainingMs", 0.0) > 20.0):
                for bin_filename in [".msk_adress_offset", ".msk_adress", f".msk_container_{field_name}"]:
                    local_path=str(MSKUT_PathSolver().mskfs_space / bin_filename)
                    file_transfer.upload_file(
                        local_file_path=local_path,
                        r2_key_prefix=RemoteKeyPrefix.DATA_BINARY,
                        r2_filename=bin_filename.lstrip(".")
                    )     
            else:
                raise Exception
        except Exception as e:
            print(f"Upload exception : {e}")
            for bin_filename in [".msk_adress_offset", ".msk_adress", f".msk_container_{field_name}"]:
                backup_path = MSKUT_PathSolver().mskfs_backup / bin_filename
                local_main_dir = MSKUT_PathSolver().mskfs_space
                shutil.copy2(src=backup_path, dst=local_main_dir)
                print("recovered")
            return
    
def put_to_storage(affiliated_container: MSK_Container,
                   local_file_path: str | Path):
    if not isinstance(local_file_path, Path):
        local_file_path = Path(local_file_path)
    if not local_file_path.exists():
        raise ValueError(f"File to upload ({local_file_path}) not exist")
    field_name=affiliated_container.field_name

    r2_filename = r2_filename_factory(
        cut_num_indicator=affiliated_container.request_entity(
            MSK_Property(prop_index=ReadClientConfig.get_config_item("indicators_settings", "cut_num"))).address.value,
        component=affiliated_container.request_entity(
            MSK_Property(prop_index=ReadClientConfig.get_config_item("indicators_settings", "work"))).address.value,
        person=MYNAME,
        ext=local_file_path.suffix
    )
    def write_on_pulled():
        print("start_upload_file")
        print(f"r2filename {r2_filename}")

        write_msk.update_info(
            prop=MSK_Property(prop_index=ReadClientConfig.get_config_item("indicators_settings", "person")),
            new_value=MYNAME,
            container=affiliated_container
        )
        print(132)
        write_msk.update_info(
            prop=MSK_Property(prop_index=ReadClientConfig.get_config_item("indicators_settings", "file")),
            new_value=r2_filename,
            container=affiliated_container
        )
        print(138)
        write_msk.proceed_info(
            prop=MSK_Property(prop_index=ReadClientConfig.get_config_item("indicators_settings", "progress")),
            proceed_step=1,
            container=affiliated_container
        )

    print("start_sync_data")
    FileTransfer().upload_file(
        local_file_path=local_file_path,
        r2_key_prefix=RemoteKeyPrefix.PROJECT_FILE,
        r2_filename=r2_filename
    )
    sync_data(field_name=field_name, writing_operation=write_on_pulled)
        
def get_from_storage(affiliated_container: MSK_Container,
                     send_to_mount: bool=True,
                     dest_dir: Optional[str | Path]=None):
    if not send_to_mount and dest_dir is None:
        raise ValueError("A download destination directory must be designated")
    if dest_dir is not None and not isinstance(dest_dir, Path):
        dest_dir = Path(dest_dir)
    field_name=affiliated_container.field_name
    sync_data(field_name=field_name)

    affiliated_container = MSK_Container(
        field_name=field_name,
        container_index=affiliated_container.container_index
    )
    r2_filename = affiliated_container.request_entity(
        requesting_prop=MSK_Property(prop_index=ReadClientConfig.get_config_item("indicators_settings", "file"))
    ).address.value
    if r2_filename is None:
        raise ValueError("Requested file not yet exist")
    local_destination_path =(ReadClientConfig.get_mounted_dir() / r2_filename 
                             if send_to_mount else dest_dir / r2_filename)
    FileTransfer().download_file(
        r2_key_prefix=RemoteKeyPrefix.PROJECT_FILE,
        r2_filename=r2_filename,
        local_destination_path=local_destination_path
    )
    if send_to_mount:
        mount_file_manager.write_file_status(
            info={local_destination_path : {
                "affiliation" : str(affiliated_container.container_index)
            }}
        )