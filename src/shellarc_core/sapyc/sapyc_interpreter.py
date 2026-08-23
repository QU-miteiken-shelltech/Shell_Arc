from shellarc_core.interface import Interface_Git, Interface_Spreadsheet
from shellarc_core.cloudio.io_git import SA_GitLogFilter
from shellarc_core.exception.user_exception import SA_SapycSyntaxError

class SAPYC_Interpreter:
    def __init__(self,
                 git_io: Interface_Git,
                 gcp_io: Interface_Spreadsheet
                 ):
        self.git_io = git_io
        self.gcp_io = gcp_io

    async def get_record(self,
                         *args
                         ) -> dict[str, str]:
        """
        cut_num ; component ; branch ; commit_id
        """
        cut_num = int(args[0])
        component = str(args[1])
        branch = str(args[2])
        commit_id = str(args[3]) if len(args) > 3 else None
        rtn = await self.git_io.get_component_info(
            branch=branch,
            cut_num=cut_num,
            component=component,
            commit_id=commit_id
        )
        return rtn

    async def repoint_data(self,
                           *args
                           ) -> bool:
        """
        be_repointed_cut ; repoint_target_cut ; component
        """
        be_repointed_cut = int(args[0])
        repoint_target_cut = int(args[1])
        component = int(args[2])
        await self.git_io.repoint_data(
            be_repointed_cut=be_repointed_cut,
            repoint_target_cut=repoint_target_cut,
            component=component
        )
        return True

    async def rebase_data(self,
                          *args
                          ) -> bool:
        """
        cut_num ; target_commit_id ; component
        """
        cut_num = int(args[0])
        target_commit_id = str(args[1])
        component = str(args[2])
        await self.git_io.absorb_data(
            absorbing_cut=cut_num,
            absorb_target_cut=cut_num,
            component=component,
            commit_id=target_commit_id
        )
        return True

    async def absorb_data(self,
                          *args
                          ) -> bool:
        """
        absorbing_cut_num ; target_cut_num ; commit_id ; component
        """
        absorbing_cut_num = int(args[0])
        target_cut_num = int(args[1])
        commid_id = str(args[2])
        component = str(args[3])
        await self.git_io.absorb_data(
            absorbing_cut=absorbing_cut_num,
            absorb_target_cut=target_cut_num,
            component=component,
            commit_id=commid_id
        )


    async def get_history_log(self,
                              *args
                              ) -> dict[str, str]:
        """
        commit_type ; cut_num ; component ; log_length ; output_format ; limit_scope ; branch
        """
        log_filter = SA_GitLogFilter(
            commit_type=str(args[0]) if args[0] != "None" else None,
            cut_num=int(args[1]) if args[1] != "None" else None,
            component=str(args[2]) if args[2] != "None" else None,
            log_length=int(args[3]) if args[3] != "None" else None
        )
        output_format = [int(i) for i in args[4].split("+")]
        rtn = await self.git_io.get_log(
            output_format=output_format,
            log_filter=log_filter,
            limit_scope=str(args[5]) if args[5] != "None" else None,
            branch=str(args[6]) if args[6] != "None" else "pending"
        )
        return rtn

    async def read_spreadsheet(self,
                               *args
                               ) -> str:
        """
        cut_num ; info_type ; page_idx
        """
        rtn = self.gcp_io.get_info(
            info_type=str(args[1]),
            cut_num=int(args[0]),
            page_idx=int(args[2]) if len(args) > 2 else 0
        )
        return rtn


    async def interpret_sapyc(self,
                             cmd: str
                             ) -> None:
        try:
            cmd = cmd.split("/")[0]
            command_breakdown = cmd.split("<")
            command_type_breakdown = command_breakdown[0].split(";")
            cmd_domain = command_type_breakdown[0]
            cmd_space = command_type_breakdown[1]
            cmd_name = command_type_breakdown[2]
            command_content_ls = command_breakdown[1].split(";")
        except:
            raise SA_SapycSyntaxError(
                error_log="sapyc syntax error",
                frontend_msg="SAPYC 構文エラー"
            )
        if cmd_name == "record":
            rtn = await self.get_record(*command_content_ls)
        elif cmd_name == "repoint":
            rtn = await self.repoint_data(*command_content_ls)
        elif cmd_name == "history":
            rtn = await self.get_history_log(*command_content_ls)
        elif cmd_name == "spreadsheet":
            rtn = await self.read_spreadsheet(*command_content_ls)
        elif cmd_name == "rebase":
            rtn = await self.rebase_data(*command_content_ls)
        elif cmd_name == "absorb":
            rtn = await self.absorb_data(*command_content_ls)
        else:
            rtn = "Invalid Command"
        return rtn
