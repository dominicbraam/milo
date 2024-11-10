from typing import Final
import os
from dotenv import load_dotenv
from discord import Intents, Client, Message, Guild, User, VoiceChannel


class DiscordHandler:
    def __init__(self):
        self.name = "milo"
        self.name_len = len(self.name)
        self.token: Final[str] = ""
        self.intents: Intents = Intents.default()
        self.intents.members = True
        self.intents.guilds = True
        self.client: Client = Client(intents=self.intents)

        load_dotenv()
        self.token = os.getenv("DISCORD_TOKEN")

    def run(self) -> None:
        self.intents.message_content = True
        self.client.run(token=self.token)


class Context:

    def __init__(self, message: Message):
        self.user: User = message.author
        self.server: Guild = message.guild
        self.server_vcs: [VoiceChannel] = self.server

        for vc in self.server_vcs:
            if self.user in vc.members:
                self.user_vc: VoiceChannel = vc
                break
