from typing import Final
import os
from dotenv import load_dotenv
from discord import Intents, Client, Message, Guild, User, VoiceChannel
from milo.loggers import get_loggers

app_logger = get_loggers()


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
        self.server_vcs: [VoiceChannel] = self.server.voice_channels

        for vc in self.server_vcs:
            if self.user in vc.members:
                self.user_vc: VoiceChannel = vc
                break
            else:
                self.user_vc = None

    def get_context_data(self) -> dict:
        return {
            "user": self.user,
            "server": self.server,
            "server_vcs": self.server_vcs,
            "user_vc": self.user_vc,
        }
