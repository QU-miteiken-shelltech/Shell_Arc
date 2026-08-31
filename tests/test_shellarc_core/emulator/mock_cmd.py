import os
import regex
import asyncio
import json
import traceback
import datetime
from pathlib import Path
from dataclasses import dataclass

from test_shellarc_core.mockio.mock_git_io import Mock_Git_IO
from test_shellarc_core.mockio.mock_r2_io import Mock_R2_IO
from test_shellarc_core.mockio.mock_spreadsheet_io import Mock_Spreadsheet_IO

from shellarc_core.exception.structure_error import (
    SA_AuthError,
    SA_ErrorCode,
    SA_LocalIOError,
    ShellArcError,
)
from shellarc_core.exception.user_exception import ShellArcException
from shellarc_core.interface import Interface_Git, Interface_R2, Interface_Spreadsheet
from shellarc_core.process.query import ShellArc_Query
from shellarc_core.process.register import ShellArc_Register
from shellarc_core.process.requesting import ShellArc_Request
from shellarc_core.process.reviewing import ShellArc_Review
from shellarc_core.process.uploader import ShellArc_Upload
from shellarc_core.sapyc.sapyc_interpreter import SAPYC_Interpreter

@dataclass
class MockMessage:
    content: str
    author: str
    roles: list[str]
    attachments: dict[str, bytes]
    channel: str

@dataclass
class MockReturn:
    content: str

class MockCommands:
    def __init__(self, 
                 project_ctx_dir: str,
                 git_repo_dir: str):
        project_ctx_dir = Path(project_ctx_dir)
        discord_config_file_path = project_ctx_dir / "discord_config.json"
        with open(discord_config_file_path, mode="r", encoding="utf-8") as config_file:
            discord_config_dict = json.load(config_file)
            config = discord_config_dict

        self.TOTAL_CUT_COUNT = config["total_cut_count"]
        self.webhook_bot_name = config["webhook_bot_name"]
        self.cut_extraction_regex = config["notice_message_cut_extraction_regex"]
        self.channel_name_divider = config.get("channel_name_divider", "_")
        self.bot_command = config.get("bot_command", "..")
        self.component_name_e2j = config["component_reference"]
        self.component_name_j2e = {v : k for k, v in self.component_name_e2j.items()}
        self.admin_roles = config["admin_roles"]
        self.shellarc_center = config["center_channel_names"]

        self.setup_shellarc_io(
            r2_io=Mock_R2_IO(),
            git_io=Mock_Git_IO(git_repo_local_dir=git_repo_dir),
            gcp_io=Mock_Spreadsheet_IO()
        )

    def setup_shellarc_io(self,
                          r2_io: Interface_R2,
                          git_io: Interface_Git,
                          gcp_io: Interface_Spreadsheet
                          ) -> None:
        self.r2_io = r2_io
        self.git_io = git_io
        self.gcp_io = gcp_io
        self.shellarc_query = ShellArc_Query(gcp_io=gcp_io, git_io=git_io)
        self.sapyc_interpreter = SAPYC_Interpreter(git_io=git_io, gcp_io=gcp_io)

    def parse_channel_name(self, channel_name: str):
        try:
            processing_cut_cluster = str(channel_name.split(self.channel_name_divider)[0])
            print(f"submitting_cut_cluster is {processing_cut_cluster}")
            processing_cut = self.process_cut_num(processing_cut_cluster)
            print(f"submitting_cut is {processing_cut}")
            if processing_cut is None:
                raise ValueError("カット番号の抽出に失敗しました")
            print(f"抽出されたカット番号: {processing_cut}")
            processing_cut = regex.sub(r"[^\d]", "", processing_cut)
            processing_cut= int(processing_cut)
            return processing_cut
        except Exception as e:
            print("Error occurred while processing the submission selection")
            print(e)
            return

    def process_cut_num(self, cut_cluster):
        match = regex.search(self.cut_extraction_regex, cut_cluster)
        if match:
            return str(match.group(1))
        return None

    async def up(self, message: MockMessage, component: str):
        if self.channel_name_divider not in message.channel.name:
            return
        if not message.attachments:
            return MockReturn(content="ファイルを添付してから提出してください")
        return await self.on_push_action(
            message=message,
            submitting_cut=self.parse_channel_name(channel_name=message.channel),
            submitting_component=component,
            submitting_person=message.author
        )


    async def upbig(self, message: MockMessage):
        if self.channel_name_divider not in message.channel:
            return

        return await self.on_push_action(
            message=message,
            submitting_cut=self.parse_channel_name(channel_name=message.channel),
            submitting_component=component,
            submitting_person=message.author
        )


    async def appr(ctx):
        message = ctx.message
        if message.author.bot:
            return
        if channel_name_divider not in message.channel.name:
            return
        view = ShellArcDropdownView(
            sa_action=ShellArcActions.APPR,
            message=message
        )
        await ctx.send(view=view)


    async def dl(ctx):
        message = ctx.message
        if message.author.bot:
            return
        if channel_name_divider not in message.channel.name:
            return
        view = ShellArcDropdownView(
            sa_action=ShellArcActions.DL,
            message=message
        )
        await ctx.send(view=view)


    async def check(ctx):
        message = ctx.message
        if message.author.bot:
            return
        if channel_name_divider not in message.channel.name:
            return
        view = ShellArcDropdownView(
            sa_action=ShellArcActions.CAPPR,
            message=message
        )
        await ctx.send(view=view)


    async def reg(ctx):
        message = ctx.message
        if message.author.bot:
            return
        view = ShellArcDropdownView(
            sa_action=ShellArcActions.REG,
            message=message
        )
        await ctx.send(view=view)


    async def history(ctx):
        message = ctx.message
        if message.author.bot:
            return
        channel_name = str(message.channel.name.lower())
        message_command = message.content.split(" ")
        if len(message_command) < 2:
            await message.channel.send("作業工程を指定してください")
            return
        quering_component = message_command[1]
        quering_component = component_name_j2e.get(quering_component, quering_component)
        try:
            quering_cut_cluster = str(channel_name.split(channel_name_divider)[0])
            quering_cut = int(process_cut_num(quering_cut_cluster))
            print(f"submitting_cut is {quering_cut}")
        except Exception as e:
            print(f"Error occurred while processing the submission selection : {e}")
            return
        max_length = None
        if len(message_command) == 3:
            try:
                max_length = int(message_command[2])
            except:
                max_length = None
        if len(message_command) == 4 and message_command[3] == "-appr":
            history_dict = await shell_arc_bot.shellarc_query.get_approve_history(
                cut_num=quering_cut,
                component=quering_component,
                max_length=max_length
            )
        else:
            history_dict = await shell_arc_bot.shellarc_query.get_history(
                cut_num=quering_cut,
                component=quering_component,
                max_length=max_length
            )
        reply_text = ""
        for commit_id, commit_content in history_dict.items():
            reply_text += f"{commit_id} - {commit_content}\n"
        if not reply_text:
            reply_text = f"カット{quering_cut}履歴はありません"
        await message.channel.send(reply_text)


    async def ask(ctx):
        message = ctx.message
        if message.author.bot:
            return
        if message.channel.id != int(shellarc_center["schedule_query_center"]):
            return
        try:
            asking_person = str(message.content.split(" ")[1])
        except:
            asking_person = str(message.author.display_name)
        await message.reply("検索中...\n10秒ほどお待ちいただく場合があります")
        query_result = await shell_arc_bot.shellarc_query.efficient_get_spreadsheet_info(
            target_index_value=asking_person,
            index_info_types=[f"{c}_PIC" for c in component_name_e2j],
            target_info_types=["cut_num"] * len(component_name_e2j),
            search_range=[1, TOTAL_CUT_COUNT]
        )
        output_msg = asking_person + ":"
        if not query_result:
            await message.reply(output_msg + "\n担当作業がありません")
            return
        for k, v in query_result.items():
            output_msg += f"\nカット{v} {component_name_e2j[k.split('_')[0]]}"
        await message.reply(output_msg)


    async def myid(ctx):
        message = ctx.message
        if message.author.bot:
            return
        creator_name = message.author.display_name
        creator_id = hashlib.shake_128(creator_name.encode('utf-8')).hexdigest(3)
        await message.channel.send(f"{creator_name}さんのIDは {creator_id} です")


    async def sync(ctx):
        message = ctx.message
        if message.author.bot:
            return
        try:
            await ShellArc_Upload.sync_vps_with_remote(git_io=shell_arc_bot.git_io)
            await message.channel.send("同期しました")
        except ShellArcException as e:
            await message.channel.send(content=e.frontend_msg, view=None)
        except ShellArcError as e:
            await message.channel.send(content=e.frontend_msg, view=None)
        except Exception as e:
            await message.channel.send(content=f"技術班にご連絡ください !  EXCEPTION : {e}", view=None)
            tb = traceback.format_exc()
            error_moment = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9), 'JST'))
            print(f"!!UNEXPECTED : {error_moment.strftime('%Y%m%d%H%M%S')} -- {tb}")
        

    async def spin(ctx):
        message = ctx.message
        if message.author.bot:
            return
        message_txt = message.content
        regex_search = re.search(r"<@&([0-9]+)>", message_txt)
        if regex_search is None:
            await message.channel.send("ロールをメンションしてください")
            return
        spin_msg = await message.channel.send("選ばれたのは。。。。。。。")
        await asyncio.sleep(0.5)
        await spin_msg.edit(content="気になるよね〜〜")
        await asyncio.sleep(0.5)
        mentioned_role_id = int(regex_search.group(1))
        mentioned_role = message.guild.get_role(mentioned_role_id)
        chosen_member = random.choice(mentioned_role.members)
        await spin_msg.edit(content=f"{chosen_member.display_name}さん です！")


    async def sapyc(ctx):
        message = ctx.message
        if message.author.bot:
            return
        try:
            cmd = message.content.lstrip("..sapyc").strip()
            rtn = await shell_arc_bot.sapyc_interpreter.interpret_sapyc(cmd=cmd)
            await message.channel.send(rtn)
        except ShellArcException as e:
            await message.channel.send(content=e.frontend_msg, view=None)
        except ShellArcError as e:
            await message.channel.send(content=e.frontend_msg, view=None)
        except Exception as e:
            await message.channel.send(content=f"技術班にご連絡ください !  EXCEPTION : {e}", view=None)
            tb = traceback.format_exc()
            error_moment = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9), 'JST'))
            print(f"!!UNEXPECTED : {error_moment.strftime('%Y%m%d%H%M%S')} -- {tb}")


    async def status(ctx):
        message: discord.Message = ctx.message
        if message.author.bot: 
            return
        pending_status = await shell_arc_bot.shellarc_query.get_pending_status(is_raw=False)
        rtn_msg = ""
        for s in pending_status:
            rtn_msg += f"カット{s[0]} - {component_name_e2j.get(s[1], s[1])}\n"
        await message.channel.send(rtn_msg)



    
    async def on_push_action(self,
                             message: MockMessage,
                             submitting_cut, 
                             submitting_component, 
                             submitting_person
                             ):
        msg_splitted = message.content.split(" ")
        submitting_component_en = self.component_name_j2e.get(submitting_component, submitting_component)
        git_message = ""
        if len(msg_splitted) > 1:
            if not msg_splitted[1].endswith("*"):
                git_message = msg_splitted[1]
                if len(msg_splitted) > 2:
                    if msg_splitted[2].endswith("*"):
                        git_message += f" -agent by {submitting_person}"
                        submitting_person = msg_splitted[2].rstrip("*")
                    else:
                        return MockReturn(content="提出を代行するには、代理対象の名前の後ろに*（半角）をつけてください\n意図せぬ誤提出を防ぐため本提出を棄却します")
            else:
                git_message += f" -agent by {submitting_person}"
                submitting_person = msg_splitted[1].rstrip("*")
        upload_page_path = ""
        temp_dir = ""
        try:
            shellarc_upload = ShellArc_Upload(
                cut_num=int(submitting_cut),
                working_component=submitting_component_en,
                r2_io=self.r2_io,
                git_io=self.git_io,
                gcp_io=self.gcp_io
            )
            submissions_raw = message.attachments
            if submissions_raw:
                files = submissions_raw
                await shellarc_upload.upload_file(
                    file=files,
                    submitter_name=submitting_person,
                    message=git_message
                )
            else:
                upload_page_path, temp_dir = await shellarc_upload.get_upload_page(
                    submitter_name=submitting_person,
                    message=git_message
                )
                return MockReturn(content="180秒以内、このからファイルをアップロードしてください")
        except ShellArcException as e:
            return MockReturn(content=e.frontend_msg)
        except ShellArcError as e:
            return MockReturn(content=e.frontend_msg)
        except Exception as e:
            tb = traceback.format_exc()
            error_moment = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9), 'JST'))
            print(f"!!UNEXPECTED : {error_moment.strftime('%Y%m%d%H%M%S')} -- {tb}")
            return MockReturn(content=f"技術班にご連絡ください !  EXCEPTION : {e}")
        finally:
            if upload_page_path and Path(upload_page_path).exists():
                os.unlink(upload_page_path)
            try:
                if temp_dir and Path(temp_dir).exists():
                    os.rmdir(temp_dir)
            except:
                print("Unable to delete tempdir")
        
        confirm_msg = f"カット{submitting_cut} {submitting_component} が提出されました"
        for keyframe_qc in self.admin_roles.get("keyframe_qc", []):
            confirm_msg += f" @{keyframe_qc}"
        return MockReturn(content=confirm_msg)



    @shell_arc_bot.event
    async def on_reviewing_action(interaction: discord.Interaction, 
                                message: discord.Message,
                                reviewing_cut, 
                                reviewing_component, 
                                reviewing_person,
                                is_approve
                                ):
        reviewing_component_en = component_name_j2e.get(reviewing_component, reviewing_component)
        git_message = message.content.split(" ")[1] if len(message.content.split(" ")) > 1 else ""
        try:
            shellarc_review = ShellArc_Review(
                cut_num=int(reviewing_cut),
                reviewing_component=reviewing_component_en,
                git_io=shell_arc_bot.git_io,
                gcp_io=shell_arc_bot.gcp_io
            )
            await shellarc_review.pending_action(
                reviewer_name=reviewing_person,
                is_approve=is_approve,
                message=git_message
            )
            if is_approve:
                await interaction.edit_original_response(content=f"カット{reviewing_cut} {reviewing_component} が確定されました", view=None)
            else:
                await interaction.edit_original_response(content=f"カット{reviewing_cut} {reviewing_component} がアーカイブされました", view=None)
        except ShellArcException as e:
            await interaction.edit_original_response(content=e.frontend_msg, view=None)
            return
        except ShellArcError as e:
            await interaction.edit_original_response(content=e.frontend_msg, view=None)
            return
        except Exception as e:
            await interaction.edit_original_response(content=f"技術班にご連絡ください !  EXCEPTION : {e}", view=None)
            tb = traceback.format_exc()
            error_moment = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9), 'JST'))
            print(f"!!UNEXPECTED : {error_moment.strftime('%Y%m%d%H%M%S')} -- {tb}")
            return
            
        
    @shell_arc_bot.event
    async def on_download_action(interaction: discord.Interaction,
                                requesting_cut,
                                requesting_component,
                                requesting_take
                                ):
        downloaded_path = ""
        requesting_component_en = component_name_j2e.get(requesting_component, requesting_component)
        try:
            shellarc_request = ShellArc_Request(
                cut_num=int(requesting_cut),
                requesting_component=requesting_component_en,
                r2_io=shell_arc_bot.r2_io,
                git_io=shell_arc_bot.git_io
            )
            downloaded_material = await shellarc_request.download_material(requesting_take=requesting_take)
            downloaded_path = downloaded_material[0]
            downloaded_filename = downloaded_material[1]
            downloaded_method = downloaded_material[2]
            take_name = requesting_take
            if downloaded_method == "path":
                if not Path(downloaded_path).exists():
                    raise SA_LocalIOError(
                        error_log="generated temp download path not exist",
                        error_code=SA_ErrorCode.SA_8000
                    )
                if requesting_take == "0": take_name = "最新テイク"
                if requesting_take == "-1": take_name = "作業中テイク"
                await interaction.edit_original_response(content=f"カット{requesting_cut} {take_name} {requesting_component} を取得中", view=None)
                await interaction.channel.send(
                    f"カット{requesting_cut} {take_name} {requesting_component} が取得されました",
                    file=discord.File(downloaded_path)
                    )
            elif downloaded_method == "url":
                await interaction.edit_original_response(content=f"カット{requesting_cut} {take_name} {requesting_component} のファイルが大きすぎるため、URLでお渡しします", view=None)
                await interaction.channel.send(f"URL : {downloaded_path}\n180秒以内でダウンロードしてください")
        except ShellArcException as e:
            await interaction.edit_original_response(content=e.frontend_msg, view=None)
            return
        except ShellArcError as e:
            await interaction.edit_original_response(content=e.frontend_msg, view=None)
            return
        except Exception as e:
            await interaction.edit_original_response(content=f"技術班にご連絡ください !  EXCEPTION : {e}", view=None)
            tb = traceback.format_exc()
            error_moment = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9), 'JST'))
            print(f"!!UNEXPECTED : {error_moment.strftime('%Y%m%d%H%M%S')} -- {tb}")
            return
        finally:
            if Path(downloaded_path).exists():
                os.unlink(downloaded_path)

        
    @shell_arc_bot.event
    async def on_register_action(interaction: discord.Interaction,
                                message: discord.Message,
                                registering_cut,
                                registering_component,
                                registering_person,
                                force
                                ):
        registering_component_en = component_name_j2e.get(registering_component, registering_component)
        try:
            shellarc_register = ShellArc_Register(gcp_io=shell_arc_bot.gcp_io)
            await shellarc_register.register_work(
                registering_person=registering_person,
                registering_component=registering_component_en,
                registering_cut=registering_cut,
                force=force
            )
        except ShellArcException as e:
            await interaction.edit_original_response(content=e.frontend_msg, view=None)
            return
        except ShellArcError as e:
            await interaction.edit_original_response(content=e.frontend_msg, view=None)
            return
        except Exception as e:
            await interaction.edit_original_response(content=f"技術班にご連絡ください !  EXCEPTION : {e}", view=None)
            tb = traceback.format_exc()
            error_moment = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9), 'JST'))
            print(f"!!UNEXPECTED : {error_moment.strftime('%Y%m%d%H%M%S')} -- {tb}")
            return

        if "*" not in message.content:
            current_channel_name = interaction.channel.name.split(channel_name_divider)
            if len(current_channel_name) > 1:
                current_channel_name[1] = registering_person
            else:
                current_channel_name.append(registering_person)
            new_channel_name = channel_name_divider.join(current_channel_name)
            await interaction.channel.edit(name=new_channel_name)
        await interaction.edit_original_response(content=f"{registering_person}をカット{registering_cut} {registering_component}に登録しました", view=None)
        #await interaction.channel.send(f"..remind {deadline} あしたカット{registering_cut}の締切だよ {message.author.id}")

    async def on_register_dconly_action(interaction: discord.Interaction,
                                        message: discord.Message,
                                        registering_cut,
                                        registering_component
                                        ):
        try:
            registering_component_en = component_name_j2e.get(registering_component, registering_component)
            get_info_type_name = f"{registering_component_en}_PIC"
            component_pic = await shell_arc_bot.shellarc_query.get_spreadsheet_info(
                info_type=get_info_type_name,
                cut_num=registering_cut
            )
        except ShellArcException as e:
            await interaction.edit_original_response(content=e.frontend_msg, view=None)
            return
        except ShellArcError as e:
            await interaction.edit_original_response(content=e.frontend_msg, view=None)
            return
        except Exception as e:
            await interaction.edit_original_response(content=f"技術班にご連絡ください !  EXCEPTION : {e}", view=None)
            tb = traceback.format_exc()
            error_moment = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9), 'JST'))
            print(f"!!UNEXPECTED : {error_moment.strftime('%Y%m%d%H%M%S')} -- {tb}")
            return
        current_channel_name = interaction.channel.name.split(channel_name_divider)
        if len(current_channel_name) > 1:
            current_channel_name[1] = component_pic
        else:
            current_channel_name.append(component_pic)
        new_channel_name = channel_name_divider.join(current_channel_name)

        if component_pic:
            await interaction.channel.edit(name=new_channel_name)
            await interaction.edit_original_response(content="スイッチできました", view=None)
        else:
            await interaction.edit_original_response(content="担当データが見つかりませんでした", view=None)

