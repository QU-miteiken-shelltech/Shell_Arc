import re

from shellarc_core.cfg.spreadsheet_map_io import SpreadsheetMap_IO
from shellarc_core.cloudio.io_git import (
    SA_CommitType,
    SA_GitLogFilter,
    ShellArcGitBranch,
)
from shellarc_core.exception.structure_error import SA_ErrorCode, SA_InternalSyntaxError
from shellarc_core.interface import Interface_Git, Interface_Spreadsheet


class ShellArc_Query:
    def __init__(self,
                 gcp_io: Interface_Spreadsheet,
                 git_io: Interface_Git
                 ):
        self.gcp_io = gcp_io
        self.git_io = git_io

    async def efficient_get_spreadsheet_info(self,
                                             target_index_value: str,
                                             index_info_types: list[str],
                                             target_info_types: list[str],
                                             search_range: list[int],
                                             output_key: str="index_info_type",
                                             page_idx: int=0
                                             ) -> dict:
        """Efficiently retrieve specific information from the Google Spreadsheet by searching for a target index value
        within a specified range and returning the corresponding information based on the provided index and target information types.

        Args:
            target_index_value (str): The value to be searched for in the specified index column of the spreadsheet.
            index_info_types (list[str]): A list of information types corresponding to the columns that contain the index values to be searched for in the spreadsheet.
            target_info_types (list[str]): A list of information types corresponding to the columns that contain the target values to be retrieved from the spreadsheet.
            search_range (list[int]): A list containing two integers representing the starting and ending cut numbers that define the range of rows to be searched in the spreadsheet.
            output_key (str): A string that specifies the key to be used in the returned dictionary for the retrieved information,
                which can be either "index_info_type" to use the index information type as the key or "target_info_type" to use the target information type as the key (Default : "index_info_type").
            page_idx (int): The index of the spreadsheet page to perform the search and retrieval from (Default : 0).

        Returns:
            dict: A dictionary containing the retrieved information from the spreadsheet,
                where the keys are determined by the specified output_key parameter and the values are the corresponding retrieved values from the spreadsheet.
        """
        smap_io = SpreadsheetMap_IO()
        vert_offset = smap_io.get_vert_offset()
        if len(search_range) != 2:
            raise SA_InternalSyntaxError(
                error_log="a range is needed for efficient_get_spreadsheet",
                error_code=SA_ErrorCode.SA_7000
            )
        elif search_range[0] > search_range[1]:
            raise SA_InternalSyntaxError(
                error_log="starting cut cannot be greater than ending cut",
                error_code=SA_ErrorCode.SA_7000
            )
        elif len(index_info_types) != len(target_info_types):
            raise SA_InternalSyntaxError(
                error_log="index_info_types must be of same length of target_info_types",
                error_code=SA_ErrorCode.SA_7000
            )

        current_spreadsheet_cache = self.gcp_io.spreadsheet_cache
        rtn = {}
        cycle = len(index_info_types)
        for i in range(cycle):
            index_info_type = index_info_types[i]
            target_info_type = target_info_types[i]
            index_col = smap_io.get_cell_coord(
                cut_num=1,
                item=index_info_type,
                page_idx=page_idx
            )[1]
            target_col = smap_io.get_cell_coord(
                cut_num=1,
                item=target_info_type,
                page_idx=page_idx
            )[1]
            for row_num in range(search_range[0] + vert_offset - 1, search_range[1] + vert_offset):
                searching_row = current_spreadsheet_cache[row_num]
                target_value = searching_row[target_col-1]
                index_value = searching_row[index_col-1]
                if index_value == target_index_value:
                    if output_key == "index_info_type":
                        rtn[index_info_type] = str(target_value)
                    else:
                        rtn[target_info_type] = str(target_value)

        return rtn


    def get_components_enname(self, cut_num: int) -> list[str]:
        """Get the list of component names in English for the specified cut number by retrieving the information from the Git repository.

        Args:
            cut_num (int): The cut number of the components to retrieve the names for.

        Returns:
            list[str]: A list of component names in English corresponding to the specified cut number.
        """
        return self.git_io.get_components(cut_num=cut_num)

    async def get_spreadsheet_info(self,
                                   info_type: str,
                                   cut_num: int,
                                   page_idx: int=0
                                   ) -> str | None:
        """Get the specified information from the Google Spreadsheet for the given cut number and page index by retrieving the corresponding value from the spreadsheet.

        Args:
            info_type (str): The type of information to retrieve from the spreadsheet.
            cut_num (int): The cut number of the information to retrieve from the spreadsheet.
            page_idx (int): The index of the spreadsheet page to retrieve the information from (Default : 0).

        Returns:
            str | None: The retrieved information from the spreadsheet as a string, or None if the specified information type or cut number is not found in the spreadsheet.
        """
        rtn = self.gcp_io.get_info(
            info_type=info_type,
            cut_num=cut_num)
        return str(rtn)


    async def get_history(self,
                    cut_num: int,
                    component: str,
                    max_length: int | None=None
                    ) -> dict[str, str]:
        """Get the commit history for the specified cut number and component by retrieving the log information from the Git repository,
        and filter the log entries based on the commit type and maximum length if provided.

        Args:
            cut_num (int): The cut number of the component to retrieve the history for.
            component (str): The name of the component to retrieve the history for.
            max_length (int | None): The maximum number of log entries to retrieve for the specified cut number and component, or None to retrieve all log entries (Default : None).

        Returns:
            hist_dict (dict[str, str]): A dictionary containing the commit history for the specified cut number and component
        """
        json_file_path = f"stage/cut{cut_num}/{component}.json"
        log_filter = SA_GitLogFilter(
            commit_type=SA_CommitType.SUBMIT,
            log_length=max_length
        )
        hist_dict = await self.git_io.get_log(
            output_format=[5, 3, 4],
            log_filter=log_filter,
            limit_scope=json_file_path
        )
        return hist_dict


    async def get_pending_status(self, is_raw: bool = False) -> str | list[tuple[int, str]]:
        pending_status = await self.git_io.get_pending_status()
        if is_raw:
            return pending_status
        pending_status_ls = pending_status.split("\n")
        pattern = r"cut(\d+).*\.sa_pending_(.+)"
        rtn_list = []
        for s in pending_status_ls:
            match = re.search(pattern, s)
            cut_num = int(match.group(1))
            component = str(match.group(2))
            rtn_list.append((cut_num, component))
        return rtn_list



    async def get_approve_history(self,
                            cut_num: int,
                            component: str,
                            max_length: int | None=None
                            ) -> dict[str, str]:
        """Get the approval commit history for the specified cut number and component by retrieving the log information from the Git repository,
        and filter the log entries based on the commit type and maximum length if provided.

        Args:
            cut_num (int): The cut number of the component to retrieve the approval history for.
            component (str): The name of the component to retrieve the approval history for.
            max_length (int | None): The maximum number of log entries to retrieve for the specified cut number and component, or None to retrieve all log entries (Default : None).

        Returns:
            hist_dict (dict[str, str]): A dictionary containing the approval commit history for the specified cut number and component
        """
        json_file_path = f"stage/cut{cut_num}/{component}.json"
        log_filter = SA_GitLogFilter(
            commit_type=SA_CommitType.APPROVE,
            log_length=max_length
        )
        hist_dict = await self.git_io.get_log(
            output_format=[5, 3, 4],
            log_filter=log_filter,
            limit_scope=json_file_path,
            branch=ShellArcGitBranch.MAIN
        )
        return hist_dict
