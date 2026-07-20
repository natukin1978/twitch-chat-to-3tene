import logging
import re
from typing import TYPE_CHECKING

import asqlite
import emoji
import twitchio
from twitchio import eventsub
from twitchio.ext import commands

if TYPE_CHECKING:
    import sqlite3


import global_value as g
from emote_manager import EmoteManager

logger = logging.getLogger(__name__)


class TwitchBot(commands.AutoBot):
    def __init__(
        self, *, token_database: asqlite.Pool, subs: list[eventsub.SubscriptionPayload]
    ) -> None:
        self.token_database = token_database

        ctw = g.config["twitch"]
        super().__init__(
            client_id=ctw["clientId"],
            client_secret=ctw["clientSecret"],
            bot_id=ctw["bot"]["id"],
            owner_id=ctw["owner"]["id"],
            prefix="!",
            subscriptions=subs,
            force_subscribe=True,
        )

    async def setup_hook(self) -> None:
        # Add our component which contains our commands...
        await self.add_component(MyComponent(self))

    async def event_oauth_authorized(
        self, payload: twitchio.authentication.UserTokenPayload
    ) -> None:
        await self.add_token(payload.access_token, payload.refresh_token)

        if not payload.user_id:
            return

        if payload.user_id == self.bot_id:
            # We usually don't want subscribe to events on the bots channel...
            return

        # A list of subscriptions we would like to make to the newly authorized channel...
        subs: list[eventsub.SubscriptionPayload] = [
            eventsub.ChatMessageSubscription(
                broadcaster_user_id=payload.user_id, user_id=self.bot_id
            ),
        ]

        resp: twitchio.MultiSubscribePayload = await self.multi_subscribe(subs)
        if resp.errors:
            logger.warning(
                "Failed to subscribe to: %r, for user: %s", resp.errors, payload.user_id
            )

    async def add_token(
        self, token: str, refresh: str
    ) -> twitchio.authentication.ValidateTokenPayload:
        # Make sure to call super() as it will add the tokens interally and return us some data...
        resp: twitchio.authentication.ValidateTokenPayload = await super().add_token(
            token, refresh
        )

        # Store our tokens in a simple SQLite Database when they are authorized...
        query = """
        INSERT INTO tokens (user_id, token, refresh)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id)
        DO UPDATE SET
            token = excluded.token,
            refresh = excluded.refresh;
        """

        async with self.token_database.acquire() as connection:
            await connection.execute(query, (resp.user_id, token, refresh))

        logger.info("Added token to the database for user: %s", resp.user_id)
        return resp

    async def event_ready(self) -> None:
        bot = self.user
        logger.info("Successfully logged in as: %s (%s)", bot.display_name, bot.name, extra={'force': True})
        owner_user = self.owner
        g.owner_attr = {
            "id": owner_user.id,
            "name": owner_user.name,
            "display_name": owner_user.display_name,
            "description": owner_user.description,
        }


class MyComponent(commands.Component):
    # An example of a Component with some simple commands and listeners
    # You can use Components within modules for a more organized codebase and hot-reloading.

    def __init__(self, bot: TwitchBot) -> None:
        # Passing args is not required...
        # We pass bot here as an example...
        self.bot = bot
        self.em = EmoteManager()

    # An example of listening to an event
    # We use a listener in our Component to display the messages received.
    @commands.Component.listener()
    async def event_message(self, payload: twitchio.ChatMessage) -> None:
        await self.event_base_message(payload)

    async def event_base_message(self, payload: twitchio.ChatMessage) -> None:
        if payload.chatter.id != self.bot.bot_id:
            return

        combined_parts = []
        for fragment in payload.fragments:
            if fragment.type == "text":
                # 普通のコメ
                text = fragment.text.strip()
                if text:
                    combined_parts.append(text)

            elif fragment.type == "emote":
                # Twitchスタンプは括弧で囲んで表現
                raw_text = fragment.text
                clean_text = re.sub(r"^[^A-Z]*", "", raw_text)
                display_text = clean_text if clean_text else raw_text
                combined_parts.append(f"({display_text})")

        text = " ".join(combined_parts)
        decode_emoji = emoji.demojize(text, language="en")

        await self.em.do_emote(decode_emoji)


async def setup_database(
    db: asqlite.Pool,
) -> tuple[list[tuple[str, str]], list[eventsub.SubscriptionPayload]]:
    # Create our token table, if it doesn't exist..
    # You should add the created files to .gitignore or potentially store them somewhere safer
    # This is just for example purposes...

    query = """CREATE TABLE IF NOT EXISTS tokens(user_id TEXT PRIMARY KEY, token TEXT NOT NULL, refresh TEXT NOT NULL)"""
    async with db.acquire() as connection:
        await connection.execute(query)

        # Fetch any existing tokens...
        rows: list[sqlite3.Row] = await connection.fetchall("""SELECT * from tokens""")

        tokens: list[tuple[str, str]] = []
        subs: list[eventsub.SubscriptionPayload] = []

        bot_id = g.config["twitch"]["bot"]["id"]

        for row in rows:
            tokens.append((row["token"], row["refresh"]))

            if row["user_id"] == bot_id:
                continue

            subs.extend(
                [
                    eventsub.ChatMessageSubscription(
                        broadcaster_user_id=row["user_id"], user_id=bot_id
                    ),
                ]
            )

    return tokens, subs
