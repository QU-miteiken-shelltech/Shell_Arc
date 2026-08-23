from typing import Protocol, runtime_checkable

from shellarc_core.cloudio.io_git import (
    ShellArcGitBranch, SA_GitLogFilter
)


@runtime_checkable
class Interface_Git(Protocol):
    """Protocol interface for Git IO operations.
    """

    def get_components(self,
                       cut_num: int
                       ) -> list[str]:
        """Get the component list for the specified cut number.

        Args:
            cut_num (int): The cut number to get the component list for.

        Returns:
            list[str]: A list of component names for the specified cut number.
        """
        ...

    async def make_proj_repo(self,
                             proj_settings: dict
                             ) -> None:
        """Initialize the local git repository for the project based on the provided project settings.

        Args:
            proj_settings (dict): A dictionary containing the project settings,
                including "cut_num" and "components".
        """
        ...

    async def get_component_info(self,
                                 branch: ShellArcGitBranch | str,
                                 cut_num: int,
                                 component: str,
                                 commit_id: str | None = None
                                 ) -> dict[str, str]:
        """Get the component information for the specified cut number and component name.

        Args:
            branch (ShellArcGitBranch | str): The git branch to get the component information from.
            cut_num (int): The cut number of the component.
            component (str): The name of the component.
            commit_id (str | None): The specific commit ID. If None, use the latest commit (Default : None).

        Returns:
            dict[str, str]: A dictionary containing the component information.
        """
        ...

    async def get_log(self,
                      output_format: list[int],
                      log_filter: SA_GitLogFilter | None = None,
                      limit_scope: str | None = None,
                      branch: ShellArcGitBranch | str = ShellArcGitBranch.PENDING
                      ) -> dict[str, str]:
        """Get the git log records from the specified branch, filtered and formatted.

        Args:
            output_format (list[int]): A list of integers representing the indices of the commit record fields to include.
            log_filter (SA_GitLogFilter | None): Filter criteria for the git log records (Default : None).
            limit_scope (str | None): Limit scope for the git log command (Default : None).
            branch (ShellArcGitBranch | str): The git branch to get the log records from (Default : ShellArcGitBranch.PENDING).

        Returns:
            dict[str, str]: A dictionary of filtered log records.
        """
        ...

    async def get_pending_status(self) -> str:
        """Get the pending status of the git repository.

        Returns:
            str: The status string of the pending branch.
        """
        ...

    async def repoint_data(self,
                           be_repointed_cut: int,
                           repoint_target_cut: int,
                           component: str
                           ) -> None:
        """Repoint the specified component data from one cut to another.

        Args:
            be_repointed_cut (int): The original cut number of the component data.
            repoint_target_cut (int): The target cut number to repoint to.
            component (str): The name of the component to be repointed.
        """
        ...

    async def absorb_data(self,
                          absorbing_cut: int,
                          absorb_target_cut: int,
                          component: str,
                          commit_id: str = None,
                          branch: ShellArcGitBranch = ShellArcGitBranch.PENDING
                          ) -> None:
        """Absorb the specified component data from a target cut into another cut.

        Args:
            absorbing_cut (int): The cut number that will absorb the data.
            absorb_target_cut (int): The target cut number to absorb from.
            component (str): The name of the component.
            commit_id (str): The specific commit ID (Default : None).
            branch (ShellArcGitBranch): The git branch (Default : ShellArcGitBranch.PENDING).
        """
        ...

    async def pend_data(self,
                        cut_num: int,
                        component: str,
                        processing_person: str,
                        is_approve: bool,
                        message: str = ""
                        ) -> None:
        """Pend the specified component data for approval or decline.

        Args:
            cut_num (int): The cut number of the component data.
            component (str): The name of the component.
            processing_person (str): The name of the person processing.
            is_approve (bool): Whether the component data is approved (True) or declined (False).
            message (str): An optional commit message (Default : "").
        """
        ...

    async def update_data(self,
                          cut_num: int,
                          component: str,
                          creator_name: str,
                          message: str = ""
                          ) -> str:
        """Update the specified component data in the git repository.

        Args:
            cut_num (int): The cut number of the component data.
            component (str): The name of the component.
            creator_name (str): The name of the creator.
            message (str): An optional commit message (Default : "").

        Returns:
            str: The generated file index name for the updated component data.
        """
        ...

    async def sync_remote(self) -> None:
        """Synchronize the local git repository with the remote repository.
        """
        ...
