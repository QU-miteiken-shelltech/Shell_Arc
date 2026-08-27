import json
import os
import time

import requests
from dotenv import load_dotenv


class DiscordNotice:
    def __init__(self):
        load_dotenv(verbose=True)
        dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
        load_dotenv(dotenv_path)
        self.WEBHOOK_URL = os.environ.get("Discord_webhook_url")

    def discord_notice(self, submitting_cut, submitting_component, submitting_take, submitting_person):
        submitting_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

        message = {
            "content" : f"カット{submitting_cut}・{submitting_component}・テイク{submitting_take}\n{submitting_time} - {submitting_person}"
        }
        headers = {
            "Content-Type": "application/json"
        }

        response = requests.post(self.WEBHOOK_URL, data=json.dumps(message), headers=headers)

        if response.status_code != 204:
            print(f"エラーが発生しました: {response.status_code}")

# dcn = DiscordNotice()
# dcn.discord_notice(3, "テスト", 1, "TestingPerson")

"""
message = {
            "embeds": [
            {
                "title": f"カット*{submitting_cut}*・{submitting_component}・テイク{submitting_take}",
                "description": f"{submitting_time} - {submitting_person}"
            }
        ]
        }
        headers = {
            'Content-Type': 'application/json'
        }
        """