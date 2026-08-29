import os
import json
import asyncio
import datetime
import traceback
from pathlib import Path

import regex
import requests
from dotenv import load_dotenv
import discord
from discord.ext import commands

from shellarc_core.scheduler.manager import ShellArc_ScheduleManager 
from shellarc_core.process.storyboard import ShellArc_Storyboard

from shellarc_core.exception.user_exception import SA_InvalidUserQuery, ShellArcException
from shellarc_core.exception.structure_error import (
    ShellArcError, SA_LocalIOError, SA_ErrorCode
)

proj_ctx_dir = Path(os.environ.get("SHELLARC_PROJECT_CTX", None))
load_dotenv(verbose=True)
dotenv_path = proj_ctx_dir / ".env"
if not dotenv_path.exists():
    print(".env file not exist")
    exit()
load_dotenv(dotenv_path)
DIFY_KEY = os.environ.get("Dify_token")
DIFY_BASE_URL = os.environ.get("Dify_baseurl") 
DC_CHATBOT_TOKEN = os.environ.get("Discord_pmmanager_token")

discord_config_file_path = proj_ctx_dir / "discord_config.json"
if not discord_config_file_path.exists():
    print("discord_config file not exist")
    exit()
with open(discord_config_file_path, mode="r", encoding="utf-8") as config_file:
    discord_config_dict = json.load(config_file)
    config = discord_config_dict
bot_command = config["bot_command"]
admin_roles = config["admin_roles"]
schedule_file_path = str(Path(config.get("itemi_action_dir", "default")) / "itemi_schedule.json")
memo_file_path = str(Path(config.get("itemi_action_dir", "default")) / "itemi_memo.json")
mainbot_id = int(config["shellarc_bot_id"])
cut_extraction_regex = config["notice_message_cut_extraction_regex"]
channel_name_divider = config.get("channel_name_divider", "_")
shell_arc_pmbot = commands.Bot(command_prefix=bot_command, intents=discord.Intents.all())


@shell_arc_pmbot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return

def process_cut_num(cut_cluster):
    match = regex.search(cut_extraction_regex, cut_cluster)
    if match:
        return str(match.group(1))
    return None

async def response_user(q: str,
                  asking_person: str,
                  file
                  ) -> str:
    endpoint = f"{DIFY_BASE_URL}/chat-messages"
    headers = {
        'Authorization': f'Bearer {DIFY_KEY}',
        'Content-Type': 'application/json',
    }
    payload = {
        "inputs": {
            "chat_mode" : "itemi"
        },        
        "query": q,
        "response_mode": "blocking", 
        "conversation_id": "",      
        "user": asking_person,  
    }

    response = requests.post(endpoint, headers=headers, json=payload, files=file)
    data = response.json()
    ans = str(data.get('answer'))
    return ans

async def send_reminder(*args) -> None:
    channel_id = int(args[0])
    reminder_content = args[1]
    remind_person_id = int(args[2])
    remind_channel = await shell_arc_pmbot.fetch_channel(channel_id)
    await remind_channel.send(f"{reminder_content} <@{remind_person_id}>")

async def reboot_scheduler() -> None:
    sa_sm = ShellArc_ScheduleManager(
        task_callable=send_reminder,
        schedule_file_path=schedule_file_path
        )
    sa_sm.stop_scheduler(recauculate=True)


@shell_arc_pmbot.command()
async def deadline(ctx):
    message = ctx.message
    if message.author.bot:
        return

@shell_arc_pmbot.command()
async def daiben(ctx):
    message: discord.Message = ctx.message
    if message.author.bot:
        return
    try:
        message_breakdown = message.content.split(" ")
        message_to_say = str(message_breakdown[1])
        target_channel_id = int(message_breakdown[2])
        target_person_id = int(message_breakdown[3])
        target_channel = discord.utils.get(message.guild.text_channels, id=target_channel_id)
        target_person = discord.utils.get(message.guild.members, id=target_person_id)
        await target_channel.send(f"{message_to_say} {target_person.mention}")
    except Exception as e:
        await message.channel.send(f"無効なコマンドです : {e}")
        return
    
async def dl_lo(message: discord.Message,
                cut_num: int
                ) -> None:
    try:
        sa_storyboard = ShellArc_Storyboard(cut_num=cut_num)
        downloaded_lo_path = await sa_storyboard.download_storyboard()
        if not Path(downloaded_lo_path).exists():
            raise SA_LocalIOError(
                    error_log="generated temp download path not exist",
                    error_code=SA_ErrorCode.SA_8000
                )
        await message.channel.send(
            f"カット{cut_num}LO が取得されました",
            file=discord.File(downloaded_lo_path)
            )
    except ShellArcException as e:
        await message.channel.send(content=e.frontend_msg, view=None)
        return
    except ShellArcError as e:
        await message.channel.send(content=e.frontend_msg, view=None)
        return
    except Exception as e:
        await message.channel.send(content=f"技術班にご連絡ください !  EXCEPTION : {e}", view=None)
        tb = traceback.format_exc()
        error_moment = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9), 'JST'))
        print(f"!!UNEXPECTED : {error_moment.strftime('%Y%m%d%H%M%S')} -- {tb}")
        return
    finally:
        if Path(downloaded_lo_path).exists():
            os.unlink(downloaded_lo_path)
        download_lo_dir = Path(downloaded_lo_path).resolve().parent
        if download_lo_dir.exists():
            try: os.rmdir(download_lo_dir)
            except: pass
        


async def up_lo(message: discord.Message,
                cut_num: int
                ) -> None:
    try:
        lo_file = message.attachments[0]
        lo_file_bytes = await lo_file.read()
        sa_storyboard = ShellArc_Storyboard(cut_num=cut_num)
        await sa_storyboard.upload_storyboard(file_obj=lo_file_bytes)
        confirm_msg = f"カット{cut_num}レイアウト が提出されました"
        for keyframe_qc in admin_roles.get("keyframe_qc", []):
            mentioning_role = discord.utils.get(message.guild.roles, name=keyframe_qc)
            if mentioning_role is not None:
                confirm_msg += f" {mentioning_role.mention}"
        await message.channel.send(confirm_msg)
    except ShellArcException as e:
        await message.channel.send(content=e.frontend_msg, view=None)
        return
    except ShellArcError as e:
        await message.channel.send(content=e.frontend_msg, view=None)
        return
    except Exception as e:
        await message.channel.send(content=f"技術班にご連絡ください !  EXCEPTION : {e}", view=None)
        tb = traceback.format_exc()
        error_moment = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9), 'JST'))
        print(f"!!UNEXPECTED : {error_moment.strftime('%Y%m%d%H%M%S')} -- {tb}")
        return
    

async def rpt_lo(message: discord.Message,
                 cut_num: int,
                 repoint_target_cut: int
                 ) -> None:
    try:
        sa_storyboard = ShellArc_Storyboard(cut_num=cut_num)
        await sa_storyboard.repoint_storyboard(repoint_taregt_cut=repoint_target_cut)
        await message.channel.send(f"カット{cut_num}LOがカット{repoint_target_cut}にリポイントされました")
    except ShellArcException as e:
        await message.channel.send(content=e.frontend_msg, view=None)
        return
    except ShellArcError as e:
        await message.channel.send(content=e.frontend_msg, view=None)
        return
    except Exception as e:
        await message.channel.send(content=f"技術班にご連絡ください !  EXCEPTION : {e}", view=None)
        tb = traceback.format_exc()
        error_moment = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9), 'JST'))
        print(f"!!UNEXPECTED : {error_moment.strftime('%Y%m%d%H%M%S')} -- {tb}")
        return

    
@shell_arc_pmbot.command()
async def lo(ctx):
    message = ctx.message
    if message.author.bot:
        return
    channel_name = message.channel.name
    cut_num = int(process_cut_num(channel_name.split(channel_name_divider)[0]))
    message_breakdown = message.content.split(" ")
    if len(message_breakdown) > 2:
        if message_breakdown[1] == "repoint":
            repoint_target_cut = int(message_breakdown[2])
            await rpt_lo(
                message=message,
                cut_num=cut_num,
                repoint_target_cut=repoint_target_cut
            )
        return
    file_attachments = message.attachments
    if not file_attachments:
        await dl_lo(
            message=message,
            cut_num=cut_num
        )
    else:
        await up_lo(
            message=message,
            cut_num=cut_num
        )


@shell_arc_pmbot.command()
async def memo(ctx):
    message: discord.Message = ctx.message
    if message.author.bot:
        return
    memo_file = Path(memo_file_path)
    if len(message.content.split(" ")) > 2 and message.content.split(" ")[1] == "get":
        kw = message.content.split(" ")[2]
        if memo_file.exists():
            with open(memo_file, "r", encoding="utf-8") as f:
                current_memo = json.load(f)
        else:
            await message.channel.send("メモはありません")
            return
        hits = [m for m in current_memo if kw in m] if kw.lower() != "all" else [m for m in current_memo]
        rtn = ""
        for hit in hits:
            msg_url = current_memo[hit]["url"]
            memo_person = current_memo[hit]["author"]
            rtn += f"{memo_person} : {hit} - {msg_url} \n"
        await message.channel.send(rtn)

    else:
        memo_content = message.content.strip("..memo").strip()
        channel_id = str(message.channel.id)
        msg_id = str(message.id)
        guild_id = str(message.guild.id)
        memo_person = str(message.author.display_name)
        if memo_file.exists():
            with open(memo_file, "r", encoding="utf-8") as f:
                current_memo = json.load(f)
                current_memo[memo_content] = {
                    "author" : memo_person, 
                    "url" : f"https://discord.com/channels/{guild_id}/{channel_id}/{msg_id}"
                }
        else:
            current_memo = {
                memo_content : {
                    "author" : memo_person, 
                    "url" : f"https://discord.com/channels/{guild_id}/{channel_id}/{msg_id}"
                }
            }
        with open(memo_file, "w", encoding="utf-8") as f:
            json.dump(current_memo, f, ensure_ascii=False, indent=3)
        await message.channel.send("メモを記録しました！")


@shell_arc_pmbot.command()
async def remind(ctx):
    message = ctx.message
    if message.author.id != mainbot_id and message.author.bot:
        return
    message_str = str(message.content)
    try:
        message_breakdown = message_str.split(" ")
        if len(message_breakdown) < 3:
            raise SA_InvalidUserQuery(
                error_log="Incorrect schedule format",
                frontend_msg="「..remind YYYYMMDDHHMM メッセージ内容」で記述してください"
            )
        when = message_breakdown[1]
        if len(when) != 12 or not when.isdigit():
            raise SA_InvalidUserQuery(
                error_log="Incorrect datetime format for itemi action register",
                frontend_msg="日時設定をYYYYMMDDHHMMで記述してください（例えば2026年5月20日14時30分は「202605201430」）"
            )
        try:
            task_datetime = datetime.datetime(
                int(when[0:4]),
                int(when[4:6]),
                int(when[6:8]),
                int(when[8:10]),
                int(when[10:12])
                )
        except:
            raise SA_InvalidUserQuery(
                error_log="Invalid value for datetime",
                frontend_msg="無効な日時数値です"
            )
        if (task_datetime - datetime.datetime.now()).total_seconds() <= 0:
            raise SA_InvalidUserQuery(
                error_log="Past datetime scheduled",
                frontend_msg="未来の時間点を指定してください"
            )
        remind_text = str(message_breakdown[2])
        if len(message_breakdown) >= 4 and message_breakdown[3].isdigit():
            channel_id = int(message_breakdown[3])
        else:
            channel_id = message.channel.id
        if len(message_breakdown) >= 5 and message_breakdown[4].isdigit():
            reminding_person_id = int(message_breakdown[4])
        else:
            reminding_person_id = message.author.id
        remind_content = [channel_id, remind_text, reminding_person_id]
        sa_sm = ShellArc_ScheduleManager(
            task_callable=send_reminder,
            schedule_file_path=schedule_file_path
            )
        sa_sm.make_schedule(
            task_datetime=task_datetime,
            task=remind_content
        )
        sa_sm.stop_scheduler(recauculate=True)
        await message.channel.send(f"{task_datetime} - {remind_text} を登録しました")
    except ShellArcException as e:
        await message.channel.send(e.frontend_msg)
        return

    

@shell_arc_pmbot.event
async def on_ready():
    print("PM : ログインしました")
    await reboot_scheduler()
    

shell_arc_pmbot.run(DC_CHATBOT_TOKEN)
