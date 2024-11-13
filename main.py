from discord import Message, Guild
from milo.handler.database import sqlitedb, tables
from milo.handler.discord import DiscordHandler
from milo.handler.msg import process_message
from milo.mods.settings import (
    insert_default_server_settings,
)
from milo.globals import bot_name, bot_name_len, bot_server_id
from milo.handler.log import Logger

app_logger = Logger("milo").get_logger()
Logger("discord").get_logger()
Logger("openai").get_logger()
Logger("peewee").get_logger()


def main() -> None:

    sqlitedb.connect()
    sqlitedb.create_tables(tables)
    insert_default_server_settings(bot_server_id)

    dc_handler = DiscordHandler()

    @dc_handler.client.event
    async def on_guild_join(guild: Guild) -> None:
        insert_default_server_settings(guild.id)

    @dc_handler.client.event
    async def on_ready() -> None:
        app_logger.info(f"{dc_handler.client.user} is now running!")

    @dc_handler.client.event
    async def on_message(message: Message) -> None:
        username: str = str(message.author)
        user_message: str = message.content
        channel: str = str(message.channel)

        if username == dc_handler.client.user:
            return

        user_message = user_message.lower()
        if user_message.startswith(bot_name):
            user_message = user_message[bot_name_len:]
            user_message = user_message.lstrip()

            app_logger.info(f"[{channel}] {username}: '{user_message}'")
            await process_message(message, user_message)

    dc_handler.run()


if __name__ == "__main__":
    main()
