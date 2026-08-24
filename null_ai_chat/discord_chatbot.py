import os
import json
from pathlib import Path

import requests
from dotenv import load_dotenv
import discord
from discord.ext import commands

proj_ctx_dir = Path(os.environ.get("SHELLARC_PROJECT_CTX", None))
load_dotenv(verbose=True)
dotenv_path = proj_ctx_dir / ".env"
if not dotenv_path.exists():
    print(".env file not exist")
    exit()
load_dotenv(dotenv_path)
DIFY_KEY = os.environ.get("Dify_token")
DIFY_BASE_URL = os.environ.get("Dify_baseurl") 
DC_CHATBOT_TOKEN = os.environ.get("Discord_charbot_token")

discord_config_file_path = proj_ctx_dir / "discord_config.json"
if not discord_config_file_path.exists():
    print("discord_config file not exist")
    exit()
with open(discord_config_file_path, mode="r", encoding="utf-8") as config_file:
    discord_config_dict = json.load(config_file)
    config = discord_config_dict
bot_command = config["bot_command"]
shell_arc_chatbot = commands.Bot(command_prefix=bot_command, intents=discord.Intents.all())

@shell_arc_chatbot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return

async def response_user(q: str,
                  asking_person: str,
                  chat_mode: str
                  ) -> str:
    endpoint = f"{DIFY_BASE_URL}/chat-messages"
    headers = {
        'Authorization': f'Bearer {DIFY_KEY}',
        'Content-Type': 'application/json',
    }
    payload = {
        "inputs": {
            "chat_mode" : chat_mode
        },        
        "query": q,
        "response_mode": "blocking", 
        "conversation_id": "",      
        "user": asking_person,  
    }

    response = requests.post(endpoint, headers=headers, json=payload)
    data = response.json()
    ans = str(data.get('answer'))
    return ans

@shell_arc_chatbot.command()
async def nuru(ctx):
    message = ctx.message
    if message.author.bot:
        return
    message_str = str(message.content)
    message_str = message_str.lstrip(f"{bot_command}nuru").strip()
    if not message_str:
        return
    await message.channel.send("考えているぬる...")
    print(message_str)
    sender_name = str(message.author.display_name)
    server_id = str(message.guild.id)
    casual_server = config.get("casual_server", [])
    chat_mode = "casual" if server_id in casual_server else "technical"
    try:
        resp = await response_user(
            q = message_str,
            asking_person=sender_name,
            chat_mode=chat_mode
        )
    except Exception as e:
        print(f"Dify error : {e}")
        return
    await message.channel.send(resp)


@shell_arc_chatbot.command()
async def summary(ctx):
    message = ctx.message
    if message.author.bot:
        return
    target_message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
    target_message = str(target_message.content)
    await message.channel.send("考えているぬる...")
    sender_name = str(message.author.display_name)
    server_id = str(message.guild.id)
    casual_server = config.get("casual_server", [])
    chat_mode = "casual" if server_id in casual_server else "technical"
    try:
        resp = await response_user(
            q = f"以下の内容を日本語でわかりやすく要約してください：{target_message}",
            asking_person=sender_name,
            chat_mode=chat_mode
        )
    except Exception as e:
        print(f"Dify error : {e}")
        return
    await message.channel.send(resp)


@shell_arc_chatbot.command()
async def weather(ctx):
    message = ctx.message
    if message.author.bot:
        return
    city_name = "福岡" if len(message.content.split(" ")) < 2 else message.content.split(" ")[1]
    with open(Path(__file__).resolve().parent / "city_id.json", "r", encoding="utf-8") as f:
        city_id_dict = json.load(f)
    city_id = city_id_dict.get(city_name, None)
    if city_id is None:
        await message.channel.send("無効な地名です")
        return
    response = requests.get(f"https://weather.tsukumijima.net/api/forecast/city/{city_id}")
    if response.status_code != 200:
        await message.channel.send("API通信無効です")
        return
    weather_json_str = response.text
    weather_json_dict = json.loads(weather_json_str)
    date = weather_json_dict["forecasts"][0]["date"]
    report = weather_json_dict["description"]["bodyText"]
    summary = weather_json_dict["forecasts"][0]["telop"]
    weather = weather_json_dict["forecasts"][0]["detail"]["weather"]
    min_temp = weather_json_dict["forecasts"][0]["temperature"]["min"]["celsius"]
    max_temp = weather_json_dict["forecasts"][0]["temperature"]["max"]["celsius"]
    reply_msg = f"{date}\n{report}\n\n天気：{summary}・{weather}\n温度：{min_temp}〜{max_temp}"
    await message.channel.send(reply_msg)



shell_arc_chatbot.run(DC_CHATBOT_TOKEN)
