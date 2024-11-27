from __future__ import annotations
import os
from asyncio import sleep
from discord import Client, Intents
from dotenv import load_dotenv
from typing import TYPE_CHECKING
from milo.globals import app_logger, voice_client_disconnect_time
from milo.handler.msg import process_message

if TYPE_CHECKING:
    from discord import Guild, Member, Message, VoiceState
    from typing import Final


class DiscordHandler:
    """
    Class to handle discord client initialisation.

    Attributes:
        token: Final[str]
        intents: Intents
        members: bool
        guilds: bool
        client: Client
        token: str
        message_content: bool
    """

    def __init__(self) -> None:
        self.token: Final[str] = ""
        self.intents: Intents = Intents.default()
        self.intents.members: bool = True
        self.intents.guilds: bool = True
        self.client: Client = Client(intents=self.intents)

        load_dotenv()
        self.token: str = os.getenv("DISCORD_TOKEN")

        @self.client.event
        async def on_guild_join(guild: Guild) -> None:
            app_logger.info(
                f"Joined new server; name='{guild.name}' and id={guild.id}"
            )

        @self.client.event
        async def on_ready() -> None:
            app_logger.info(f"{self.client.user} is now running!")

        @self.client.event
        async def on_message(message: Message) -> None:

            # ignore messages from itself
            if message.author == self.client.user:
                return

            await process_message(self, message)

        @self.client.event
        async def on_voice_state_update(
            member: Member, before: VoiceState, after: VoiceState
        ) -> None:

            # ignore if not itself
            if not member == self.client.user:
                return

            elif before.channel is None:
                voice_client = after.channel.guild.voice_client
                time = 0
                while True:
                    # disconnect from voice client after
                    # voice_client_disconnect_time runs out
                    # if it is not being used
                    await sleep(1)
                    time = time + 1
                    if (
                        voice_client.is_playing()
                        and not voice_client.is_paused()
                    ):
                        time = 0
                    if time == voice_client_disconnect_time:
                        await voice_client.disconnect()
                    if not voice_client.is_connected():
                        break

    def run(self) -> None:
        self.intents.message_content: bool = True
        self.client.run(token=self.token)
