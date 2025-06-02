import asyncio

from pywinauto import application

import global_value as g
from config_helper import read_config


class EmoteManager:
    def __init__(self):
        self.send_key_title = g.config["3tene"]["title"]
        self.active_emote = None
        self.emotion = None

    async def do_emote_motion(self, key_code: str):
        if self.active_emote:
            return

        await asyncio.sleep(1)

        add_motions = self.emotion["addMotions"]
        if key_code in add_motions:
            add_motion = add_motions[key_code]
        else:
            add_motion = add_motions[""]

        add_key_code = add_motion["keyCode"]
        add_end_sec = add_motion["endSec"]
        await self.do_emote_detail({key_code, add_key_code}, add_end_sec)

    async def do_emote(self, decode_emoji: str):
        self.emotion = read_config("emotion.json")
        face_list = self.emotion["face_list"]
        key_code = None
        for k, v in face_list.items():
            if k in decode_emoji:
                key_code = v
                break

        await self.do_emote_motion(key_code)

    def send_key_to_3tene(self, key_code: str):
        if not key_code:
            return
        app = application.Application().connect(title=self.send_key_title)
        tw = app.top_window()
        tw.send_keystrokes(key_code)

    async def do_emote_reset(self, end_sec: int):
        await asyncio.sleep(end_sec)
        for reset in self.emotion["resets"]:
            self.send_key_to_3tene(reset)
        self.active_emote = None

    async def do_emote_detail(self, key_codes: set[str], end_sec: int):
        for key_code in key_codes:
            self.send_key_to_3tene(key_code)
        await self.do_emote_reset(end_sec)
