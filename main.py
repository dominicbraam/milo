from __future__ import annotations
from typing import TYPE_CHECKING
from milo.handler.database import sqlitedb, tables
from milo.handler.discord import DiscordHandler
from milo.handler.log import Logger
from milo.handler.msg import process_message
from milo.mods.settings import insert_default_settings_from_file

if TYPE_CHECKING:
    from discord import Message, Guild


app_logger = Logger("milo").get_logger()
Logger("discord").get_logger()
Logger("openai").get_logger()
Logger("peewee").get_logger()


def main() -> None:

    sqlitedb.connect()
    sqlitedb.create_tables(tables, safe=True)
    insert_default_settings_from_file("server")

    dc_handler = DiscordHandler()

    @dc_handler.client.event
    async def on_guild_join(guild: Guild) -> None:
        app_logger.info(
            f"Joined new server with name = {guild.name} and id = {guild.id}"
        )

    @dc_handler.client.event
    async def on_ready() -> None:
        app_logger.info(f"{dc_handler.client.user} is now running!")

    @dc_handler.client.event
    async def on_message(message: Message) -> None:

        if message.author == dc_handler.client.user:
            return

        await process_message(dc_handler, message)

    dc_handler.run()


if __name__ == "__main__":
    main()
