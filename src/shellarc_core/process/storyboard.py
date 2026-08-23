from pathlib import Path
import tempfile

from shellarc_core.cloudio.io_r2 import R2_IO
from shellarc_core.cloudio.io_notion import Notion_IO
from shellarc_core.cloudio.io_spreadsheet import GCP_IO
from shellarc_core.cfg.cfg_io import Cfg_IO, Cfg_item

from shellarc_core.exception.structure_error import SA_ErrorCode, SA_LocalIOError
from shellarc_core.exception.user_exception import SA_InvalidUserQuery


class ShellArc_Storyboard:
    def __init__(self,
                 cut_num: int
                 ) -> None:
        self.r2_io = R2_IO(bucket_name="shellarc-storyboard")
        self.notion_io = Notion_IO(cut_num=cut_num)
        self.gcp_io = GCP_IO()
        self.cfg_io = Cfg_IO()
        self.cut_num = cut_num

    async def download_storyboard(self) -> str:
        naming = f"cut{self.cut_num}_layout.png"
        temp_dir = tempfile.mkdtemp()
        full_temp_path = Path(temp_dir) / naming
        self.notion_io.get_image_file(
            download_destination=full_temp_path,
            attr_name="画像"
        )
        if not full_temp_path.exists():
            raise SA_LocalIOError(
                error_log=f"making temp file for file download for " \
                    f"c{self.cut_num}{self.working_component}, but temp file disappear",
                error_code=SA_ErrorCode.SA_8000
            )
        return full_temp_path
    
    async def upload_storyboard(self,
                                file_obj: bytes
                                ) -> None:
        file_path = f"storyboard/cut{self.cut_num}.png"
        public_url = self.r2_io.upload_file(
            uploading_file=file_obj,
            file_path=file_path,
            url_prefix=self.cfg_io.get_cfg_setting(Cfg_item.STORYBOARD_URL)
        )
        self.notion_io.put_image_url(
            img_url=public_url,
            attr_name="画像"
        )
        self.gcp_io.update_info(
            info_type="layout_progress",
            cut_num=self.cut_num,
            new_value="完了",
            page_idx=0
        )

    async def repoint_storyboard(self,
                                 repoint_taregt_cut: int
                                 ) -> None:
        target_cut_notion_io = Notion_IO(cut_num=repoint_taregt_cut)
        target_image_url = target_cut_notion_io.get_image_url(attr_name="画像")
        self.notion_io.put_image_url(
            img_url=target_image_url,
            attr_name="画像"
        )
