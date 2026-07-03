import sys
import datetime
import os
import pickle
from pathlib import Path

import bpy
import send2trash

from .shellarc_core.utils.common_initialisation import CommonInitialisation as Common
from .shellarc_core.processor.request_r2 import Cloudflare_R2_service as R2Service

class BlenderOperation:
    def __init__(self):
        pass

    def make_new_file(self,
                      asset_name: str,
                      saving_dir: str
                      ) -> None:
        bpy.ops.wm.read_homefile(app_template='')
        default_coll = bpy.data.collections.get("Collection")
        default_coll.name = asset_name
        if not Path(saving_dir).exists():
            Path(saving_dir).mkdir(parents=True)
        bpy.ops.wm.save_as_mainfile(filepath=f"{saving_dir}/{asset_name}.blend")

    def open_file(self,
                  local_path: str
                  ) -> None:
        bpy.ops.wm.open_mainfile(filepath=local_path)

    def snapshot_file(self) -> None:
        if not "snapshot_path" in bpy.context.scene \
            or bpy.context.scene["snapshot_path"] == ""\
            or not Path(bpy.context.scene["snapshot_path"]).exists():
            if sys.platform == "win32":
                snapshot_dir = Path(os.environ.get("APPDATA", home / "AppData" / "Roaming")) / "ShellArc2026" / "snapshot"
            elif sys.platform == "darwin":
                snapshot_dir = Path.home() / "Library" / "Application Support" / "ShellArc2026" / "snapshot"
            snapshot_dir.mkdir(exist_ok=True, parents=True)
            current_file_path = bpy.data.filepath
            snapshot_path = snapshot_dir / f"{Path(current_file_path).stem}_snapshot.blend"
            bpy.context.scene["snapshot_path"] = str(snapshot_path)
        snapshot_path = bpy.context.scene["snapshot_path"]
        bpy.ops.wm.save_as_mainfile(filepath=snapshot_path, 
                                    copy=True)

    def save_file(self) -> str:
        current_file_path = bpy.data.filepath
        bpy.ops.wm.save_as_mainfile()
        return current_file_path
    
    @staticmethod
    def delete_snapshot_dir() -> None:
        if not "snapshot_path" in bpy.context.scene \
            or bpy.context.scene["snapshot_path"] == ""\
            or not Path(bpy.context.scene["snapshot_path"]).exists():
            return
        snapshot_path = bpy.context.scene["snapshot_path"]
        send2trash.send2trash(snapshot_path)
        bpy.context.scene["snapshot_path"] = ""

    @staticmethod
    def shellarc_autosave():
        if not "snapshot_path" in bpy.context.scene \
            or bpy.context.scene["snapshot_path"] == ""\
            or not Path(bpy.context.scene["snapshot_path"]).exists():
            if sys.platform == "win32":
                snapshot_dir = Path(os.environ.get("APPDATA", home / "AppData" / "Roaming")) / "ShellArc2026" / "snapshot"
            elif sys.platform == "darwin":
                snapshot_dir = Path.home() / "Library" / "Application Support" / "ShellArc2026" / "snapshot"
            snapshot_dir.mkdir(exist_ok=True, parents=True)
            current_file_path = bpy.data.filepath
            snapshot_path = snapshot_dir / f"{Path(current_file_path).stem}_snapshot.blend"
            bpy.context.scene["snapshot_path"] = str(snapshot_path)
        snapshot_path = bpy.context.scene["snapshot_path"]
        bpy.ops.wm.save_as_mainfile(filepath=snapshot_path, 
                                    copy=True)
        return 300.0
    
    @staticmethod
    def open_snapshot() -> None:
        if not "snapshot_path" in bpy.context.scene \
            or bpy.context.scene["snapshot_path"] == ""\
            or not Path(bpy.context.scene["snapshot_path"]).exists():
            return
        bpy.ops.wm.open_mainfile(filepath=bpy.context.scene["snapshot_path"])

    @staticmethod
    def freeze_locally():
        if sys.platform == "win32":
            freeze_dir = Path(os.environ.get("APPDATA", home / "AppData" / "Roaming")) / "ShellArc2026"
        elif sys.platform == "darwin":
            freeze_dir = Path.home() / "Library" / "Application Support" / "ShellArc2026"
        if not freeze_dir.exists():
            freeze_dir.mkdir(parents=True)
        current_file_path = Path(bpy.data.filepath)
        freeze_file_path = freeze_dir / f"{current_file_path.stem}_{datetime.datetime.now().strftime("%y%m%d%H%M%S")}.blend"
        bpy.ops.wm.save_as_mainfile(filepath=str(freeze_file_path), 
                                    copy=True)
        freeze_dir_size = sum(f.stat().st_size for f in freeze_dir.rglob('*') if f.is_file()) / (1024 * 1024)
        bpy.context.scene.shellarc_prop_str_freezedirsize = f"{int(freeze_dir_size)}MB"
        
    @staticmethod
    def delete_freeze_dir():
        if sys.platform == "win32":
            freeze_dir = Path(os.environ.get("APPDATA", home / "AppData" / "Roaming")) / "ShellArc2026"
        elif sys.platform == "darwin":
            freeze_dir = Path.home() / "Library" / "Application Support" / "ShellArc2026"
        if freeze_dir.exists():
            send2trash.send2trash(str(freeze_dir))
        freeze_dir.mkdir(exist_ok=True, parents=True)
        bpy.context.scene.shellarc_prop_str_freezedirsize = "0MB"

    @staticmethod
    def get_freeze_dir_size() -> int:
        if sys.platform == "win32":
            freeze_dir = Path(os.environ.get("APPDATA", home / "AppData" / "Roaming")) / "ShellArc2026"
        elif sys.platform == "darwin":
            freeze_dir = Path.home() / "Library" / "Application Support" / "ShellArc2026"
        freeze_dir_size = sum(f.stat().st_size for f in freeze_dir.rglob('*') if f.is_file()) / (1024 * 1024)
        return int(freeze_dir_size)
    
    @staticmethod
    def is_snapshot_exists(asset_name: str) -> bool:
        if sys.platform == "win32":
            snapshot_dir = Path(os.environ.get("APPDATA", home / "AppData" / "Roaming")) / "ShellArc2026" / "snapshot"
        elif sys.platform == "darwin":
            snapshot_dir = Path.home() / "Library" / "Application Support" / "ShellArc2026" / "snapshot"
        snapshot_dir.mkdir(exist_ok=True, parents=True)
        snapshot_path = snapshot_dir / f"{asset_name}_snapshot.blend"
        if snapshot_path.exists():
            bpy.context.scene["snapshot_path"] = str(snapshot_path)
            return True
        return False
    
    @staticmethod
    def get_frozen_files() -> str:
        rtn_list = []
        asset_name = Path(bpy.data.filepath).stem
        if sys.platform == "win32":
            freeze_dir = Path(os.environ.get("APPDATA", home / "AppData" / "Roaming")) / "ShellArc2026"
        elif sys.platform == "darwin":
            freeze_dir = Path.home() / "Library" / "Application Support" / "ShellArc2026"
        if freeze_dir.exists():
            frozen_list = os.listdir(str(freeze_dir))
            for f in frozen_list:
                if f.startswith(asset_name):
                    rtn_list.append(f"{str(freeze_dir)}/{f}")
        if not rtn_list:
            return ""
        cache_path = Path(__file__).resolve().parent / "cache_reflogidx.pkl"
        with open(cache_path, "wb") as f:
            pickle.dump(rtn_list, f)
        return str(cache_path)
    
    @staticmethod
    def open_frozen_file(frozen_file_path: str) -> None:
        if sys.platform == "win32":
            freeze_dir = Path(os.environ.get("APPDATA", home / "AppData" / "Roaming")) / "ShellArc2026"
        elif sys.platform == "darwin":
            freeze_dir = Path.home() / "Library" / "Application Support" / "ShellArc2026"
        if not freeze_dir.exists():
            return
        current_path = bpy.data.filepath
        BlenderOperation.freeze_locally()
        bpy.ops.wm.open_mainfile(filepath=frozen_file_path)
        bpy.ops.wm.save_as_mainfile(filepath=current_path)
        

class BackendCommunication:
    def __init__(self):
        self.sa_common = Common()
        self.blender_ops = BlenderOperation()

    def get_asset_metadata(self) -> dict:
        """
        The document "general_data" stores a dict of asset_name: str - status: str pair
        status codes are :
        "0" - not assigned
        "1" - assigned but file not made
        "2" - assigned and file made but free now
        "3" - someone working on
        "4" - locked
        "5" - under merging
        """
        cg_asset_data = self.sa_common.ref_cg_obj.collection("assets").document("general_data").get().to_dict()
        return cg_asset_data
    
    def set_asset_metadata(self,
                           asset_name: str,
                           status: list[str]
                           ) -> None:
        self.sa_common.ref_cg_obj.collection("assets").document("general_data").update({asset_name : status})
        

    def get_cg_data(self,
                    asset_name: str
                    ) -> dict:
        cg_asset_data = self.sa_common.ref_cg_obj.collection("assets").document(asset_name).get().to_dict()
        return cg_asset_data


    def get_member_data(self,
                        mem_id: str
                        ) -> list:
        """
        This lists the accessibility to each assets of each registered member 
        It is a dict storing member_id: str - accessible_asset_list: str
        The "accessible_asset_list" is a str in which asset names are separeted by "*"
        """
        member_accessible = self.sa_common.ref_cg_obj.collection("members").document("accessible").get().to_dict()
        if mem_id not in member_accessible:
            return []
        accessible_assets = member_accessible[mem_id]
        if accessible_assets == "ALL":
            return ["ALL"]
        elif accessible_assets == "NIL":
            return ["NIL"]
        accessible_assets_list = accessible_assets.split("*")
        return accessible_assets_list
    
    def register_asset(self,
                       asset_name: str
                       ) -> None:
        current_cg_asset_data = self.sa_common.ref_cg_obj.collection("assets").document("general_data").get().to_dict()
        if asset_name in current_cg_asset_data:
            return
        self.sa_common.ref_cg_obj.collection("assets").add(asset_name)
        self.sa_common.ref_cg_obj.collection("assets").document("general_data").update({asset_name : ["0", ""]})
        
    
    def request_asset(self,
                      mem_id: str,
                      asset_name: str,
                      saving_dir: str
                      ) -> str:
        asset_metadata = self.get_asset_metadata()
        asset_status_info = asset_metadata[asset_name]
        asset_status = asset_status_info[0]
        asset_status_owner = asset_status_info[1]

        if asset_status == "1" or asset_status == "2" or asset_status_owner == mem_id:
            pass
        elif asset_status == "0":
            return "NOT_ASSIGNED"
        elif asset_status == "3":
            return "LOCKED_WORKING"
        elif asset_status == "4":
            return "LOCKED"
        elif asset_status == "5":
            return "LOCKED_MERGING"
        else:
            return "ERROR"
        
        BlenderOperation.freeze_locally()
        if asset_status != "1":
            if not Path(saving_dir).exists():
                Path(saving_dir).mkdir(parents=True)
            r2_service = R2Service(s3_client=self.sa_common.s3_client)
            download_status = r2_service.download_file(
                to_download_file=f"cg/asset/{asset_name}/{asset_name}.blend",
                download_dest=saving_dir,
                file_naming=f"{asset_name}.blend"
                )
            if not download_status:
                return "DOWNLOAD_ERROR"
            self.blender_ops.open_file(local_path=f"{saving_dir}/{asset_name}.blend")
        else:
            self.blender_ops.make_new_file(
                asset_name=asset_name,
                saving_dir=saving_dir
            )
        return asset_name
        
    def upload_asset(self,
                     asset_name: str
                     ) -> str:
        current_local_path = self.blender_ops.save_file()
        r2_service = R2Service(s3_client=self.sa_common.s3_client)
        upload_status = r2_service.upload_file(
            local_file_path=current_local_path,
            cloud_file_path=f"cg/asset/{asset_name}/{asset_name}.blend"
        )
        if not upload_status:
            return "UPLOAD ERROR"
        upload_status = r2_service.upload_file(
            local_file_path=current_local_path,
            cloud_file_path=f"cg/asset/{asset_name}/backup_{datetime.datetime.now().strftime("%y%m%d%H%M%S")}.blend"
        )
        if not upload_status:
            return "UPLOAD ERROR"
        BlenderOperation.delete_snapshot_dir()
        return asset_name
    
    def submit_action(self,
                      asset_name: str,
                      status: list[str]
                      ) -> str:
        upload_status = self.upload_asset(
            asset_name=asset_name
        )
        if upload_status != asset_name:
            return upload_status
        self.set_asset_metadata(
            asset_name=asset_name,
            status=status
        )
        return upload_status

class DiscordCommunication:
    def __init__(self):
        pass