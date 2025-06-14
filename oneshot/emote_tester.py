import asyncio
import os
import sys

import emoji
import twitchio
from twitchio.ext import commands

sys.path.append("..")
sys.path.append(".")

import global_value as g

g.app_name = "twitch_chat_to_3tene"
g.base_dir = os.path.abspath(os.path.join(os.path.dirname(sys.argv[0]), os.pardir))

from config_helper import read_config
from emote_manager import EmoteManager

args = len(sys.argv)
if args <= 1:
    exit(1)
text = sys.argv[1]

g.config = read_config()


async def main(text: str):
    em = EmoteManager()
    await em.do_emote(text)


if __name__ == "__main__":
    asyncio.run(main(text))
