import asyncio
import os
import sys

import emoji
import twitchio
from twitchio.ext import commands

import global_value as g

g.app_name = "twitch_chat_to_3tene"
g.base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))

from config_helper import read_config
from emote_manager import EmoteManager

g.config = read_config()


class Bot(commands.Bot):
    def __init__(self):
        super().__init__(
            token=g.config["twitch"]["accessToken"],
            prefix="!",
            initial_channels=[g.config["twitch"]["loginChannel"]],
        )
        self.em = EmoteManager()

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

        await self.em.do_emote(decode_emoji)


async def main():
    bot = Bot()
    await bot.start()


if __name__ == "__main__":
    asyncio.run(main())
