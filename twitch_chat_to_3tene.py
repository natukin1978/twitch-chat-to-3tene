import asyncio
import emoji
import os
import sys

import twitchio
from twitchio.ext import commands

from pywinauto import application

import global_value as g

g.app_name = "twitch_chat_to_3tene"
g.base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))

from config_helper import read_config

g.config = read_config()

# a = anger  (怒り)
# f = fun    (楽しい)
# j = joy    (喜び)
# s = sorrow (悲しい)
# o = open-mouth (驚き)
# c = close-eye (目を閉じる)
dict_emotion = read_config("emotion.json")


def send_key_to_3tene(key_code: str):
    if not key_code:
        return
    app = application.Application().connect(title=g.config["3tene"]["title"])
    tw = app.top_window()
    tw.send_keystrokes(key_code)


class Bot(commands.Bot):
    def __init__(self):
        super().__init__(
            token=g.config["twitch"]["accessToken"],
            prefix="!",
            initial_channels=[g.config["twitch"]["loginChannel"]],
        )

    async def event_message(self, msg: twitchio.Message):
        if msg.echo:
            return

        if msg.content.startswith("!"):
            await self.handle_commands(msg)
            return

        id = msg.author.name
        if id != g.config["target"]["id"]:
            return

        text = msg.content
        decode_emoji = emoji.demojize(text, language="en")

        key_code = None
        for k, v in dict_emotion.items():
            if k in decode_emoji:
                key_code = v
                break

        send_key_to_3tene(key_code)


async def main():
    bot = Bot()
    await bot.start()


if __name__ == "__main__":
    asyncio.run(main())
