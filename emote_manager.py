import asyncio

from pywinauto import application

import global_value as g


class EmoteManager:
    def __init__(self):
        self.send_key_title = g.config["3tene"]["title"]
        self.active_emote = None

    async def do_emote(self, key_code: str):
        if self.active_emote:
            return

        await asyncio.sleep(1)

        if key_code == "a":
            # 台パン
            await self.do_emote_detail([key_code, "d"], 3)
            return

        await self.do_emote_detail([key_code, "t"], 5)

    def send_key_to_3tene(self, key_code: str):
        if not key_code:
            return
        app = application.Application().connect(title=self.send_key_title)
        tw = app.top_window()
        tw.send_keystrokes(key_code)

    async def do_emote_reset(self, end_sec: int):
        await asyncio.sleep(end_sec)
        self.send_key_to_3tene("n")
        self.send_key_to_3tene("i")
        self.active_emote = None

    async def do_emote_detail(self, key_codes: list[str], end_sec: int):
        for key_code in key_codes:
            self.send_key_to_3tene(key_code)
        await self.do_emote_reset(end_sec)
