import json
import os
import tempfile
from pathlib import Path

from shellarc_core.cfg.cfg_io import Cfg_IO, Cfg_item
from shellarc_core.cloudio.io_git import Git_IO
from shellarc_core.cloudio.io_r2 import R2_IO
from shellarc_core.cloudio.io_spreadsheet import GCP_IO
from shellarc_core.exception.user_exception import SA_InvalidUserQuery
from shellarc_core.utils.file_operation import FileOperation


class ShellArc_Upload:
    def __init__(self,
                 cut_num: int,
                 working_component: str
                 ) -> None:
        self.r2_io = R2_IO()
        self.git_io = Git_IO()
        self.gcp_io = GCP_IO()
        self.cfg_io = Cfg_IO()
        self.working_component = working_component
        self.cut_num = cut_num

    async def upload_file(self,
                    file: dict[str, bytes],
                    submitter_name: str,
                    message: str=""
                    ) -> None:
        """Upload a file to the R2 storage based on the provided file, submitter name, and message, 
        and update the corresponding information in the Google Spreadsheet to reflect the new submission.

        Args:
            file (dict[str, bytes]): A dictionary containing the file name as the key and the file content as bytes as the value, representing the file to be uploaded.
            submitter_name (str): The name of the person submitting the file, used for updating the Google Spreadsheet with the new PIC and progress information.
            message (str): An optional message provided by the submitter to be included in the Git commit message when updating the data in the Git repository (Default : "").
        """
        required_format = self.cfg_io.get_cfg_setting(Cfg_item.COMPONENT, self.working_component, "format").split("|")
        filename = ""
        if len(file) > 1 and "zip" in required_format:
            fileobj = await FileOperation.make_zip(
                files=file,
                required_format=required_format
                )
            filename = Path(fileobj).name
        elif len(file) > 1 and "zip" not in required_format:
            raise SA_InvalidUserQuery(
                error_log=f"file with invalid extension format uploaded by {submitter_name}",
                frontend_msg=f"{'または'.join(required_format)}形式でご提出ください"
            )
        elif len(file) == 1:
            filename, fileobj= file.popitem()
        else:
            raise Exception
        submission_format = Path(filename).suffix.lstrip(".")

        try:
            if submission_format not in required_format:
                raise SA_InvalidUserQuery(
                    error_log=f"file with invalid extension format uploaded by {submitter_name}",
                    frontend_msg=f"{'または'.join(required_format)}形式でご提出ください"
                )
            collection_name = self.cfg_io.get_cfg_setting(Cfg_item.COLL_NAME)

            file_index_name = await self.git_io.update_data(
                cut_num=self.cut_num,
                component=self.working_component,
                creator_name=submitter_name,
                message=message
            )

            self.r2_io.upload_file(
                uploading_file=fileobj,
                file_path=f"{collection_name}/stage/{file_index_name}.{submission_format}"
            )
        except Exception:
            raise
        finally:
            if Path(filename).exists():
                os.unlink(filename)

        self.gcp_io.update_info(
            info_type=f"{self.working_component}_PIC",
            cut_num=self.cut_num,
            new_value=submitter_name
        )
        self.gcp_io.update_info(
            info_type=f"{self.working_component}_progress",
            cut_num=self.cut_num,
            new_value="作業中"
        )
        self.gcp_io.color_cell(
            info_type=f"{self.working_component}_PIC",
            cut_num=self.cut_num,
            target_color=(1, 1, 0)
        )


    async def _get_upload_url(self,
                             submitter_name: str,
                             message: str="", 
                             required_format: str=""
                             ) -> str:
        # DEPREACTED
        """Get a presigned URL for uploading a file to the R2 storage based on the provided submitter name and message,
        and update the corresponding information in the Google Spreadsheet to reflect the new submission (Internal method).

        Args:
            submitter_name (str): The name of the person submitting the file, used for updating the Google Spreadsheet with the new PIC and progress information.
            message (str): An optional message provided by the submitter to be included in the Git commit message when updating the data in the Git repository (Default : "").

        Returns:
            str: A presigned URL for uploading the file to the R2 storage.
            """
        collection_name = self.cfg_io.get_cfg_setting(Cfg_item.COLL_NAME)

        file_index_name = await self.git_io.update_data(
            cut_num=self.cut_num,
            component=self.working_component,
            creator_name=submitter_name,
            message=message
        )

        presigned_url = self.r2_io.issue_presigned_url(
            target_s3_file=f"{collection_name}/stage/{file_index_name}.{required_format}",
            url_client_method="put_object",
            http_method="PUT",
            time_limit=300
        )

        self.gcp_io.update_info(
            info_type=f"{self.working_component}_PIC",
            cut_num=self.cut_num,
            new_value=submitter_name
        )
        self.gcp_io.update_info(
            info_type=f"{self.working_component}_progress",
            cut_num=self.cut_num,
            new_value="作業中"
        )

        return presigned_url
    
    async def get_upload_page(self,
                              submitter_name: str,
                              message: str
                              ) -> tuple[str]:
        """Get the file path of the generated HTML upload page for uploading a file to the R2 storage,
        which includes a presigned URL for uploading the file, and update the corresponding information in the Google Spreadsheet to reflect the new submission.

        Args:
            submitter_name (str): The name of the person submitting the file, used for updating the Google Spreadsheet with the new PIC and progress information.
            message (str): An optional message provided by the submitter to be included in the Git commit message when updating the data in the Git repository (Default : "").
        
        Returns:
            tuple[str]: A tuple containing the file path of the generated HTML upload page and the temporary directory where the HTML file is stored, 
                which can be used for uploading the file to the R2 storage via the presigned URL included in the HTML page.
                The temporary directory should be cleaned up after the upload process is completed to avoid leaving unnecessary files on the server.
        """
        allowed_formats = self.cfg_io.get_cfg_setting(Cfg_item.COMPONENT, self.working_component, "format").split("|")
        collection_name = self.cfg_io.get_cfg_setting(Cfg_item.COLL_NAME)
        file_index_name = await self.git_io.update_data(
            cut_num=self.cut_num,
            component=self.working_component,
            creator_name=submitter_name,
            message=message
        )
        allowed_formats_url = {}
        for required_format in allowed_formats:
            presigned_url = self.r2_io.issue_presigned_url(
                target_s3_file=f"{collection_name}/stage/{file_index_name}.{required_format}",
                url_client_method="put_object",
                http_method="PUT",
                time_limit=300
            )
            allowed_formats_url[required_format] = presigned_url
        self.gcp_io.update_info(
            info_type=f"{self.working_component}_PIC",
            cut_num=self.cut_num,
            new_value=submitter_name
        )
        self.gcp_io.update_info(
            info_type=f"{self.working_component}_progress",
            cut_num=self.cut_num,
            new_value="作業中"
        )

        allowed_formats_url_jsonstr = json.dumps(allowed_formats_url)
        html_template_path = Path(__file__).resolve().parent / "uploader_from_url.html.template"
        with open(html_template_path, "r", encoding="utf-8") as f:
            html_template = f.read()
        html_page_code = html_template.replace(
            "__S3_PRESIGNED_JS_URLMAP_CONST__", 
            allowed_formats_url_jsonstr
            )
        temp_dir = tempfile.mkdtemp()
        html_path = Path(temp_dir) / f"cut{self.cut_num}_uploader.html"
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_page_code)
        return (str(html_path), temp_dir)


    @staticmethod
    async def sync_vps_with_remote() -> None:
        """Synchronize the VPS with the remote Git repository
        """
        await Git_IO().sync_remote()