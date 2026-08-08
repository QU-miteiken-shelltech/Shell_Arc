from pathlib import Path

import requests

from shellarc_core.auth.access_notion import Notion_Access
from shellarc_core.cfg.cfg_io import Cfg_IO, Cfg_item

from shellarc_core.exception.structure_error import SA_CommunicationError, SA_ErrorCode
from shellarc_core.exception.user_exception import SA_InvalidRequestObj

class Notion_IO:
    def __init__(self,
                 cut_num: int
                 ):
        self.notion = Notion_Access().get_notion_client
        self.database_id = str(Cfg_IO().get_cfg_setting(Cfg_item.NOTION_DBID))
        data_source_id = self.notion.databases.retrieve(self.database_id)['data_sources'][0]['id']
        self.notion_db = self.notion.data_sources.query(data_source_id = data_source_id)
        requied_page = ((cut_num - 1) // 100) + 1
        if requied_page > 1:
            for _ in range(0,requied_page - 1):
                next_cursor = self.notion_db.get("next_cursor")
                if not next_cursor: 
                    break
                self.notion_db = self.notion.data_sources.query(
                    data_source_id=data_source_id,
                    start_cursor=next_cursor
                )
        self.cut_num = cut_num
        if cut_num < 100:
            self.offset_cut_num = self.cut_num
            next_cursor = self.notion_db.get("next_cursor")
            if not next_cursor: 
                return
            self.notion_db = self.notion.data_sources.query(
                data_source_id=data_source_id,
                start_cursor=next_cursor
            )
        else:
            self.offset_cut_num = self.cut_num - 100

    def get_image_url(self,
                      attr_name: str="画像"
                      ) -> str:
        if self.offset_cut_num > len(self.notion_db["results"]):
            raise SA_InvalidRequestObj(
                error_log="Requesting lo of an unexisting cut",
                frontend_msg=f"カット{self.cut_num}のLOはまだ存在しません"
            )
        notion_response_files = self.notion_db["results"][self.offset_cut_num * -1]["properties"][attr_name]["files"][0]
        if "files" in notion_response_files:
            image_url = self.notion_db["results"][self.offset_cut_num * -1]["properties"][attr_name]["files"][0]["file"]["url"]
        elif "external" in notion_response_files:
            image_url = self.notion_db["results"][self.offset_cut_num * -1]["properties"][attr_name]["files"][0]["external"]["url"]
        else:
            raise SA_CommunicationError(
                error_log="Required key not in notion response",
                error_code=SA_ErrorCode.SA_3000
            )
        return image_url

    def get_image_file(self,
                       download_destination: str | Path,
                       attr_name: str="画像"
                       ) -> None:
        if isinstance(download_destination, Path):
            download_destination = str(download_destination)
        if self.offset_cut_num > len(self.notion_db["results"]):
            raise SA_InvalidRequestObj(
                error_log="Requesting lo of an unexisting cut",
                frontend_msg=f"カット{self.cut_num}のLOはまだ存在しません"
            )
        notion_response_files = self.notion_db["results"][self.offset_cut_num * -1]["properties"][attr_name]["files"][0]
        if "files" in notion_response_files:
            image_url = self.notion_db["results"][self.offset_cut_num * -1]["properties"][attr_name]["files"][0]["file"]["url"]
        elif "external" in notion_response_files:
            image_url = self.notion_db["results"][self.offset_cut_num * -1]["properties"][attr_name]["files"][0]["external"]["url"]
        else:
            raise SA_CommunicationError(
                error_log="Required key not in notion response",
                error_code=SA_ErrorCode.SA_3000
            )
        response = requests.get(image_url)
        if response.status_code != 200:
            raise SA_CommunicationError(
                error_log="Request failed when getting image from an image url on Notion",
                error_code=SA_ErrorCode.SA_3000
            )
        with open(download_destination, "wb") as f:
            f.write(response.content)

    def put_image_url(self,
                      img_url: str,
                      attr_name: str="画像"
                      ) -> None:
        img_info = [
                        {
                            "name": f"cut{self.cut_num}_lo.png",
                            "type": "external",
                            "external": {"url": img_url}
                        }
                    ]
        if self.offset_cut_num > len(self.notion_db["results"]):
            raise SA_InvalidRequestObj(
                error_log="Requesting lo of an unexisting cut",
                frontend_msg=f"カット{self.cut_num}のLOはまだ準備されていません"
            )
        print(self.notion_db["results"])
        print(len(self.notion_db["results"]))
        target_page_id = self.notion_db["results"][self.offset_cut_num * -1]["id"]

        try:
            self.notion.pages.update(
                page_id=target_page_id,
                properties={attr_name: {"files": img_info}}
            )
        except:
            raise SA_CommunicationError(
                error_log="Request failed when uploadng image url to Notion",
                error_code=SA_ErrorCode.SA_3000
            )

