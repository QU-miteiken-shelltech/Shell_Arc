import re
import os
import sys
import io
import time
import asyncio
import json
import random
from enum import Enum
from pathlib import Path

import discord
from discord.ext import commands
from discord import Webhook as Webhook
from dotenv import load_dotenv
import gspread

from shellarc_core.process.register import ShellArc_Register
from shellarc_core.process.requesting import ShellArc_Request
from shellarc_core.process.reviewing import ShellArc_Review
from shellarc_core.process.uploader import ShellArc_Upload
from shellarc_core.process.query import ShellArc_Query
from shellarc_core.exception.structure_error import (
    ShellArcError, SA_AuthError, SA_ErrorCode,
    SA_LocalIOError
)
from shellarc_core.exception.user_exception import ShellArcException
async def ask(n):

    asking_person = "TESTER"
    shellarc_query = ShellArc_Query()
    query_result = await shellarc_query.efficient_get_spreadsheet_info(
        target_index_value=asking_person,
        index_info_types=[f"{c}_PIC" for c in ["keyframe", "bg", "animation", "editing", "compo"]],
        target_info_types=["cut_num", "cut_num", "cut_num", "cut_num", "cut_num"],
        search_range=[1, 5]
    )
    output_msg = asking_person
    for k, v in query_result.items():
        output_msg += f"\nカット{v} {k.split('_')[0]}"
    print(output_msg)

if __name__ == "__main__":
    asyncio.run(ask("TESTER"))