import asyncio
import os
import json
import hashlib
import datetime

from enum import StrEnum
from dataclasses import dataclass
from pathlib import Path

from shellarc_core.cfg.cfg_io import Cfg_IO, Cfg_item
from shellarc_core.exception.structure_error import (
    SA_ProjStructError, SA_LocalIOError, SA_ErrorCode,
    SA_InternalSyntaxError
)
from shellarc_core.exception.user_exception import SA_InvalidRequestObj


class GitCommands(StrEnum):
    """Enum class for git command strings.
    """
    SHOW = "show"
    COMMIT = "commit"
    CHECKOUT = "checkout"
    MERGE = "merge"
    PUSH = "push"
    ADD = "add"
    INIT = "init"
    LOG = "log"
    STATUS = "status"


class SA_CommitType(StrEnum):
    """Enum class for commit type strings used in git commit messages.
    """
    DECLINE = "DECLINE"
    APPROVE = "APPROVE"
    SUBMIT = "SUBMIT"
    REPOINT = "REPOINT"
    ABSORPTION = "ABSORPTION"


class ShellArcGitBranch(StrEnum):
    """Enum class for git branch names used in the ShellArc project.
    """
    PENDING = "pending"
    MAIN = "main"


@dataclass
class SA_GitLogFilter:
    """Data class for filtering git log records based on commit type, cut number, component name, and log length.

    Attributes:
        commit_type (SA_CommitType | str | None): The type of commit to filter by (e.g., "SUBMIT", "APPROVE", "DECLINE", "REPOINT"). If None, do not filter by commit type.
        cut_num (int | None): The cut number to filter by. If None, do not filter by cut number.
        component (str | None): The component name to filter by. If None, do not filter by component name.
        log_length (int | None): The maximum number of log records to return. If None, return all log records that match the other filter criteria. 
    """
    commit_type: SA_CommitType | str | None = None
    cut_num: int | None = None
    component: str | None = None
    log_length: int | None = None



class Git_IO:
    _git_lock = asyncio.Lock()

    def __init__(self,
                 git_repo_local_dir: str | None=None):
        cfg_io = Cfg_IO()
        self.git_repo_local_dir = Path(cfg_io.get_cfg_setting(Cfg_item.GIT_LREPO)) \
            if git_repo_local_dir is None else Path(git_repo_local_dir)


    def get_components(self,
                       cut_num: int
                       ) -> list[str]:
        """Get the component list for the specified cut number from project_main.json file.
        
        Args:
            cut_num (int): The cut number to get the component list for.

        Returns:
            list[str]: A list of component names for the specified cut number.
        """
        with open(self.git_repo_local_dir / "project_main.json", "r", encoding="utf-8") as f:
            pj_main = json.load(f)
            components = pj_main.get("common", None)
            if components is None:
                raise SA_ProjStructError(
                    error_log="The common key not found in project_main.json file",
                    error_code=SA_ErrorCode.SA_6001
                )
            components = pj_main.get(f"cut{cut_num}", components)
        return [component for component in components]
    

    @property
    def _get_timemark(self) -> str:
        """Get the current time mark in JST timezone (Property)(Internal method).
        
        Returns:
            time_mark (str): The current time mark in JST timezone, formatted as YYYYMMDDHHMMSS.
        """
        t_delta = datetime.timedelta(hours=9)
        now = datetime.datetime.now(datetime.timezone(t_delta, 'JST'))
        time_mark = now.strftime('%Y%m%d%H%M%S')
        return time_mark
    

    def _make_index_name(self,
                        cut_num: int,
                        component: str,
                        creator_name: str
                        ) -> str:
        """Generate a unique index name for the component data file based on the cut number, component name, creator name, and current time mark (Internal method).

        Args:
            cut_num (int): The cut number of the component.
            component (str): The name of the component.
            creator_name (str): The name of the creator of the component data.

        Returns:
            index_name (str): A unique index name for the component data file, formatted as 'cut{cut_num}_{component}_{creator_id}_{time_mark}'.
        """
        component = component.replace("_", "-")
        creator_id = hashlib.shake_128(creator_name.encode('utf-8')).hexdigest(3)
        index_name = f"cut{cut_num}_{component}_{creator_id}_{self._get_timemark}"
        return index_name


    async def _git_command(self,
                          *git_cmds_param
                          ) -> asyncio.subprocess.Process:
        """Execute a single git command asynchronously in the local git repository (Internal method).

        Args:
            *git_cmds_param: Variable length argument list for git command and its parameters (e.g., "checkout", "main").

        Returns:
            git_proc (asyncio.subprocess.Process): The process object representing the executed git command.
        """
        git_cmds = ["git"] + list(git_cmds_param)
        git_proc = await asyncio.create_subprocess_exec(
                *git_cmds,
                cwd=str(self.git_repo_local_dir),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
        return git_proc
    

    async def _continuous_git_command(self,
                                      git_commands: list
                                      ) -> None:
        """Execute multiple git commands sequentially in the local git repository (Internal method).

        Args:
            git_commands (list): A list of git commands, where each command is represented as a list of command and its parameters (e.g., ["checkout", "main"]).
        """
        for git_command in git_commands:
            git_proc = await self._git_command(*git_command)
            stdout, stderr = await git_proc.communicate()
            if git_proc.returncode != 0:
                print(stderr.decode('utf-8'))
                raise SA_LocalIOError(
                    error_log=f"A git command error : {stderr.decode('utf-8')}",
                    error_code=SA_ErrorCode.SA_8002
                )


    async def make_proj_repo(self,
                             proj_settings: dict 
                             ) -> None:
        """Initialize the local git repository for the project based on the provided project settings, and create the necessary directory structure and initial commit.

        Args:
            proj_settings (dict): A dictionary containing the project settings, 
                including "cut_num" (the number of cuts in the project) and "components" (a dictionary of components for each cut). 
                The "components" dictionary should have the format {component_name: {"format": component_format}}
        """
        self.git_repo_local_dir.mkdir(parents=True, exist_ok=True)
        stage_dir = self.git_repo_local_dir / "stage"
        stage_dir.mkdir(parents=True, exist_ok=True)
        proj_main_dict = {
            "cut_num" : int(proj_settings["cut_num"]),
            "common" : {c : [c_info["format"]] for c, c_info in proj_settings["components"].items()}
        }
        with open(self.git_repo_local_dir / "project_main.json", "w", encoding="utf-8") as f:
            json.dump(proj_main_dict, f, ensure_ascii=False, indent=3)
        for c in range(1, int(proj_settings["cut_num"]) + 1):
            cut_dir = stage_dir / f"cut{c}"
            cut_dir.mkdir(parents=True, exist_ok=True)
        git_commands = [
            [GitCommands.INIT, "-b", ShellArcGitBranch.MAIN],
            [GitCommands.ADD, "."],
            [GitCommands.COMMIT, "-m", f"Initialized project ({self._get_timemark})"],
            [GitCommands.CHECKOUT, "-b", ShellArcGitBranch.PENDING],
            [GitCommands.ADD, "."],
            [GitCommands.COMMIT, "--allow-empty", "-m", f"Initialized pending branch ({self._get_timemark})"],
            [GitCommands.CHECKOUT, "main"]
        ]
        await self._continuous_git_command(git_commands=git_commands)
        print(f"Project repo built ({self._get_timemark})")
        

    async def get_component_info(self,
                                 branch: ShellArcGitBranch | str,
                                 cut_num: int,
                                 component: str,
                                 commit_id: str | None=None
                                 ) -> dict[str, str]:
        """Get the component information for the specified cut number and component name from the git repository, based on the specified branch and commit ID.

        Args:
            branch (ShellArcGitBranch | str): The git branch to get the component information from (e.g., "pending" or "main").
            cut_num (int): The cut number of the component to get the information for.
            component (str): The name of the component to get the information for.
            commit_id (str | None): The specific commit ID to get the component information from. 
                If None, get the information from the latest commit in the specified branch (Default : None).

        Returns:
            requested_info (dict[str, str]): A dictionary containing the component information retrieved from the git
        """
        await self._continuous_git_command([[GitCommands.CHECKOUT, branch]])
        component_json_path = self.git_repo_local_dir / f"stage/cut{cut_num}/{component}.json"
        if component_json_path.exists():
            commit_id = commit_id if commit_id is not None else branch
            git_proc = await self._git_command(GitCommands.SHOW, f"{commit_id}:stage/cut{cut_num}/{component}.json")
            stdout, stderr = await git_proc.communicate()
            if git_proc.returncode == 0:
                requested_info_str = stdout.decode("utf-8")
                requested_info = json.loads(requested_info_str)
            else:
                requested_info = {}
        else:
            requested_info = {}
        repointer = requested_info.get("repointer", None)
        if repointer is not None:
            repointer = int(repointer)
            requested_info = await self.get_component_info(
                branch=branch,
                cut_num=repointer,
                component=component,
                commit_id=branch
            )
        return requested_info
    

    async def get_log(self,
                      output_format: list[int],
                      log_filter: SA_GitLogFilter | None=None,
                      limit_scope: str | None=None,
                      branch: ShellArcGitBranch | str=ShellArcGitBranch.PENDING
                      ) -> dict[str, str]:
        """Get the git log records from the specified branch in the git repository, 
        filtered and formatted based on the provided log filter and output format.

        Args:
            output_format (list[int]): A list of integers representing the indices of the commit record fields to include in the output log records. 
                The commit record fields are expected to be in the following order in the git log output: commit_type, cut_num, component, creator_name, commit_message, timemark, file_index_name. 
                For example, if output_format is [0, 2, 3], the output log records will include the commit_type, component, and creator_name fields.
            log_filter (SA_GitLogFilter | None): An instance of SA_GitLogFilter containing the filter criteria for the git log records. 
                If None, do not apply any filtering and return all log records that match the output format criteria (Default : None).
            limit_scope (str | None): A string representing the limit scope for the git log command (e.g., a specific file path or directory). 
                If None, do not limit the scope and return log records for all commits in the specified branch (Default : None).
            branch (ShellArcGitBranch | str): The git branch to get the log records from (Default : ShellArcGitBranch.PENDING).
        """
        if log_filter is None:
            log_filter = SA_GitLogFilter()
        if limit_scope is None:
            git_log_proc = await self._git_command(GitCommands.LOG, branch, f"--format=%h=&=%s")
        else:
            git_log_proc = await self._git_command(GitCommands.LOG, branch, f"--format=%h=&=%s", "--", limit_scope)
        stdout, stderr = await git_log_proc.communicate()
        if git_log_proc.returncode != 0:
            raise SA_LocalIOError(
                error_log=f"A git command error : {stderr.decode('utf-8')}",
                error_code=SA_ErrorCode.SA_8002
            )
        log_list = stdout.decode("utf-8").split("\n")
        rtn = {}
        for log_piece in log_list:
            if not log_piece.strip():
                continue
            breakdown_log = log_piece.split("=&=")
            breakdown_commit_record_ls = breakdown_log[1].split("*")
            if output_format and max(output_format) >= len(breakdown_commit_record_ls):
                continue
            breakdown_commit_record_ls = [x.strip() for x in breakdown_commit_record_ls]
            # "commit_type" : breakdown_commit_record_ls[0],
            # "cut_num" : breakdown_commit_record_ls[1],
            # "component" : breakdown_commit_record_ls[2],
            # "creator_name" : breakdown_commit_record_ls[3],
            # "commit_message" : breakdown_commit_record_ls[4],
            # "timemark" : breakdown_commit_record_ls[5],
            # "file_index_name" : breakdown_commit_record_ls[6]?
            if log_filter.commit_type is not None and log_filter.commit_type != breakdown_commit_record_ls[0]:
                continue
            elif log_filter.cut_num is not None and str(log_filter.cut_num) != breakdown_commit_record_ls[1]:
                continue
            elif log_filter.component is not None and log_filter.component != breakdown_commit_record_ls[2]:
                continue
            filtered_record_ls = [breakdown_commit_record_ls[i] for i in output_format]
            filtered_record = " ".join(filtered_record_ls)
            rtn[breakdown_log[0]] = filtered_record
            if log_filter.log_length is not None and len(rtn) >= log_filter.log_length:
                break
        return rtn


    async def get_pending_status(self) -> str:
        await self._continuous_git_command([[GitCommands.CHECKOUT, ShellArcGitBranch.PENDING]])
        git_statuscheck_proc = await self._git_command(GitCommands.STATUS, "--porcelain")
        stdout, stderr = await git_statuscheck_proc.communicate()
        if git_statuscheck_proc.returncode != 0:
            print(stderr.decode('utf-8'))
            raise SA_LocalIOError(
                error_log=f"A git command error : {stderr.decode('utf-8')}",
                error_code=SA_ErrorCode.SA_8002
            )
        status_str = stdout.decode("utf-8").strip()
        return status_str
    

    async def repoint_data(self,
                           be_repointed_cut: int,
                           repoint_target_cut: int,
                           component: str
                           ) -> None:
        """Repoint the specified component data from the original cut number to the target cut number in the git repository, 
        by creating a new commit in the pending branch with the updated component information.

        Args:
            be_repointed_cut (int): The original cut number of the component data to be repointed.
            repoint_target_cut (int): The target cut number to repoint the component data to.
            component (str): The name of the component to be repointed.
        """
        async with self.__class__._git_lock:
            await self._continuous_git_command([[GitCommands.CHECKOUT, ShellArcGitBranch.PENDING]])
            current_component_info = {
                "repointer" : repoint_target_cut
            }
            with open(self.git_repo_local_dir / f"stage/cut{be_repointed_cut}/{component}.json", "w", encoding="utf-8") as f:
                json.dump(current_component_info, f, ensure_ascii=False, indent=3)
            git_commands = [
                [GitCommands.ADD, f"stage/cut{be_repointed_cut}/{component}.json"],
                [GitCommands.COMMIT, "-m", f"{SA_CommitType.REPOINT} * {be_repointed_cut} * {component} * REPOINT * {be_repointed_cut}->{repoint_target_cut} * {self._get_timemark} * 'na'"]
            ]
            await self._continuous_git_command(git_commands=git_commands)
            with open(self.git_repo_local_dir / f"stage/cut{be_repointed_cut}/.sa_pending_{component}", "w") as f:
                f.write("")
        
    async def absorb_data(self,
                          absorbing_cut: int,
                          absorb_target_cut: int,
                          component: str,
                          commit_id: str=None,
                          branch: ShellArcGitBranch=ShellArcGitBranch.PENDING
                          ) -> None:
        await self._continuous_git_command([[GitCommands.CHECKOUT, branch]])
        component_json_path = self.git_repo_local_dir / f"stage/cut{absorb_target_cut}/{component}.json"
        if component_json_path.exists():
            commit_id = commit_id if commit_id is not None else branch
            git_proc = await self._git_command(GitCommands.SHOW, f"{commit_id}:stage/cut{absorb_target_cut}/{component}.json")
            stdout, stderr = await git_proc.communicate()
            if git_proc.returncode == 0:
                requested_info_str = stdout.decode("utf-8")
                requested_info = json.loads(requested_info_str)
            else:
                requested_info = {}
        else:
            requested_info = {}
        await self._continuous_git_command([[GitCommands.CHECKOUT, ShellArcGitBranch.PENDING]])
        with open(self.git_repo_local_dir / f"stage/cut{absorbing_cut}/{component}.json", "w", encoding="utf-8") as f:
            json.dump(requested_info, f, ensure_ascii=False, indent=3)
        git_commands = [
            [GitCommands.ADD, f"stage/cut{absorbing_cut}/{component}.json"],
            [GitCommands.COMMIT, "-m", f"{SA_CommitType.ABSORPTION} * {absorbing_cut} * {component} * ABSORB * {absorb_target_cut}->{absorbing_cut} * {self._get_timemark} * 'na'"]
        ]
        await self._continuous_git_command(git_commands=git_commands)
        with open(self.git_repo_local_dir / f"stage/cut{absorbing_cut}/.sa_pending_{component}", "w") as f:
            f.write("")

    
    async def pend_data(self,
                        cut_num: int,
                        component: str,
                        processing_person: str,
                        is_approve: bool,
                        message: str=""
                        ) -> None:
        """Pend the specified component data for approval or decline in the git repusository,
        by creating a new commit in the pending branch with the approval or decline information, and removing the pending status file for the component.

        Args:
            cut_num (int): The cut number of the component data to be pended.
            component (str): The name of the component to be pended.
            processing_person (str): The name of the person processing the approval or decline.
            is_approve (bool): A boolean value indicating whether the component data is approved (True) or declined (False).
            message (str): An optional message to include in the commit message for the approval or decline action (Default : "").
        """
        if not message:
            message = "No message"
        async with self.__class__._git_lock:
            message = message.replace("*", "+")
            git_statuscheck_proc = await self._git_command(GitCommands.STATUS, "--porcelain", f"stage/cut{cut_num}")
            stdout, stderr = await git_statuscheck_proc.communicate()
            if git_statuscheck_proc.returncode != 0:
                print(stderr.decode('utf-8'))
                raise SA_LocalIOError(
                    error_log=f"A git command error : {stderr.decode('utf-8')}",
                    error_code=SA_ErrorCode.SA_8002
                )
            status_str = stdout.decode("utf-8").strip()
            if f".sa_pending_{component}" not in status_str:
                raise SA_InvalidRequestObj(
                    error_log=f"c{cut_num} {component} pending attempted by {processing_person} but not exist",
                    frontend_msg="承認待ちの提出はありません"
                )
            os.unlink(self.git_repo_local_dir / f"stage/cut{cut_num}/.sa_pending_{component}")
            print("osunlink")
            git_commands_approve = [
                [GitCommands.CHECKOUT, ShellArcGitBranch.PENDING],
                [GitCommands.ADD, f"stage/cut{cut_num}"],
                [GitCommands.COMMIT, "--allow-empty", "-m", f"{SA_CommitType.APPROVE} * {cut_num} * {component} * {processing_person} * {message} * {self._get_timemark} * 'na'"],
                [GitCommands.CHECKOUT, ShellArcGitBranch.MAIN],
                [GitCommands.CHECKOUT, ShellArcGitBranch.PENDING, "--", f"stage/cut{cut_num}/{component}.json"],
                [GitCommands.ADD, f"stage/cut{cut_num}/{component}.json"],
                [GitCommands.COMMIT, "--allow-empty", "-m", f"{SA_CommitType.APPROVE} * {cut_num} * {component} * {processing_person} * {message} * {self._get_timemark} * 'na'"]
            ]
            git_commands_decline = [
                [GitCommands.CHECKOUT, ShellArcGitBranch.PENDING],
                [GitCommands.ADD, f"stage/cut{cut_num}"],
                [GitCommands.COMMIT, "--allow-empty", "-m", f"{SA_CommitType.DECLINE} * {cut_num} * {component} * {processing_person} * {message} * {self._get_timemark} * 'na'"]
            ]
            git_commands = git_commands_approve if is_approve else git_commands_decline
            try:
                await self._continuous_git_command(git_commands=git_commands)
            except Exception as e:
                with open(self.git_repo_local_dir / f"stage/cut{cut_num}/.sa_pending_{component}", "w") as f:
                    f.write("")
                raise SA_LocalIOError(
                    error_log="Git error while approving",
                    error_code=SA_ErrorCode.SA_8002
                )
            
            
    async def update_data(self,
                          cut_num: int,
                          component: str,
                          creator_name: str,
                          message: str=""
                          ) -> str:
        """Update the specified component data in the git repository by creating a new commit in the pending branch with the updated component information, 
        and returning the generated file index name for the updated component data.

        Args:
            cut_num (int): The cut number of the component data to be updated.
            component (str): The name of the component to be updated.
            creator_name (str): The name of the creator of the updated component data.
            message (str): An optional message to include in the commit message for the update action (Default : "").

        Returns:
            file_index_name (str): The generated file index name for the updated component data, formatted
        """
        if not message:
            message = "No message"
        async with self.__class__._git_lock:
            message = message.replace("*", "+")
            file_index_name = self._make_index_name(
                cut_num=cut_num,
                component=component,
                creator_name=creator_name
            )
            await self._continuous_git_command([[GitCommands.CHECKOUT, ShellArcGitBranch.PENDING]])
            current_component_info = {
                "creator" : creator_name,
                "fileindex" : file_index_name
            }
            with open(self.git_repo_local_dir / f"stage/cut{cut_num}/{component}.json", "w", encoding="utf-8") as f:
                json.dump(current_component_info, f, ensure_ascii=False, indent=3)
            git_commands = [
                [GitCommands.ADD, f"stage/cut{cut_num}/{component}.json"],
                [GitCommands.COMMIT, "-m", f"{SA_CommitType.SUBMIT} * {cut_num} * {component} * {creator_name} * {message} * {self._get_timemark} * {file_index_name}"]
            ]
            await self._continuous_git_command(git_commands=git_commands)
            with open(self.git_repo_local_dir / f"stage/cut{cut_num}/.sa_pending_{component}", "w") as f:
                f.write("")
            return file_index_name
    

    async def sync_remote(self) -> None:
        """Synchronize the local git repository with the remote repository by pushing the latest commits from both the main and pending branches to the remote origin.
        """
        git_commands = [
            [GitCommands.PUSH, "origin", ShellArcGitBranch.MAIN],
            [GitCommands.CHECKOUT, ShellArcGitBranch.PENDING],
            [GitCommands.PUSH, "origin", ShellArcGitBranch.PENDING]
        ]
        await self._continuous_git_command(git_commands=git_commands)
        
