import os
import tempfile
import zipfile
from pathlib import Path

from shellarc_core.cfg.cfg_io import Cfg_IO, Cfg_item
from shellarc_core.exception.structure_error import SA_ErrorCode, SA_LocalIOError
from shellarc_core.exception.user_exception import SA_InvalidUserQuery


class FileOperation:
    @staticmethod
    def renamed(cut_num: int,
                take: int,
                component: str, 
                ) -> str:
        cfg_io = Cfg_IO()
        name_section_num = cfg_io.get_cfg_setting(Cfg_item.COMPONENT, component, "naming_section")
        naming_ls = []
        for i in range(1, name_section_num + 1):
            naming_rule = cfg_io.get_cfg_setting(Cfg_item.COMPONENT, component, f"name_component_{i}")
            if naming_rule == "-cut":
                naming_ls.append(f"cut{cut_num}")
            elif naming_rule == "-take":
                naming_ls.append(f"take{take}")
            else:
                naming_ls.append(naming_rule.strip("-").strip())
        naming = "_".join(naming_ls)
        return naming

    @staticmethod
    async def make_zip(files: dict[str, bytes],
                       required_format: list[str]
                       ) -> str:
        tempzip_path = tempfile.NamedTemporaryFile(suffix=".zip", delete=False)
        tempzip_path_name = tempzip_path.name
        try:
            with zipfile.ZipFile(tempzip_path.name, "w", compression=zipfile.ZIP_DEFLATED) as zf:
                for name, byte_data in files.items():
                    if Path(name).suffix.lstrip(".").lower() != "png":
                        print(Path(name).suffix.lstrip(".").lower())
                        raise SA_InvalidUserQuery(
                            error_log="file with invalid extension format uploaded detected during auto zipping",
                            frontend_msg="PNG形式のみ圧縮可能です"
                        )
                    zf.writestr(name, byte_data)
        except Exception:
            if Path(tempzip_path_name).exists():
                os.unlink(tempzip_path_name)
            raise SA_LocalIOError(
                error_log="Make zip file failed",
                error_code=SA_ErrorCode.SA_8000
            )
        return tempzip_path_name

                

