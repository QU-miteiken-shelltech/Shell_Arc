from shellarc_core.cloudio.io_git import Git_IO
from shellarc_core.cloudio.io_spreadsheet import GCP_IO
from shellarc_core.cfg.cfg_io import Cfg_IO

from shellarc_core.exception.user_exception import SA_InvalidRequestObj

class ShellArc_Review:
    def __init__(self,
                 cut_num: int,
                 reviewing_component: str
                 ) -> None:
        """Initialize the ShellArc_Review class with the specified cut number and reviewing component,
        and set up the necessary cloud I/O instances for Git operations, Google Spreadsheet interactions, and configuration management.

        Args:
            cut_num (int): The cut number for which the review process is being conducted.
            reviewing_component (str): The name of the component being reviewed (e.g., "modeling", "texturing").
        """
        self.git_io = Git_IO()
        self.gcp_io = GCP_IO()
        self.cfg_io = Cfg_IO()
        self.cut_num = cut_num
        self.reviewing_component = reviewing_component


    async def _existence_check(self,
                         reviewer_name: str
                         ) -> None:
        """Check the existence of the pending data for the specified cut number and reviewing component, 
        and raise an exception if the pending data does not exist (Internal method).

        Args:
            reviewer_name (str): The name of the reviewer who is performing the review action, 
                used for error logging and frontend messaging in case the pending data does not exist.
        """
        current_pending = await self.git_io.get_component_info(
            branch="pending",
            cut_num=self.cut_num,
            component=self.reviewing_component
        )
        if current_pending == {}:
            raise SA_InvalidRequestObj(
                error_log=f"not yet existing tempdata requester by {reviewer_name}",
                frontend_msg="確認待ちのカットはありません"
            )
        

    async def pending_action(self,
                       reviewer_name: str,
                       is_approve: bool,
                       message: str=""
                       ) -> None:
        """Perform the pending action for the specified cut number and reviewing component by first checking the existence of the pending data,
        and then updating the pending data in the Git repository based on the reviewer's decision (approval or rejection) and the provided message.

        Args:
            reviewer_name (str): The name of the reviewer who is performing the review action, used for error logging and frontend messaging in case the pending data does not exist.
            is_approve (bool): A boolean flag indicating whether the review action is an approval (True) or a rejection (False) of the pending data.
            message (str): An optional message provided by the reviewer to be included in the pending data update, 
                which can contain feedback or comments related to the review action (Default : "").
        """
        await self._existence_check(reviewer_name=reviewer_name)
        await self.git_io.pend_data(
            cut_num=self.cut_num,
            component=self.reviewing_component,
            processing_person=reviewer_name,
            is_approve=is_approve,
            message=message
        )
        if is_approve:
            self.gcp_io.update_info(
                info_type=f"{self.reviewing_component}_progress",
                cut_num=self.cut_num,
                new_value="完了"
            )
            self.gcp_io.color_cell(
                info_type=f"{self.reviewing_component}_PIC",
                cut_num=self.cut_num,
                target_color=(0, 1, 0)
            )
