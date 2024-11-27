from __future__ import annotations
from milo.handler.database import sqlitedb, tables
from milo.handler.discord import DiscordHandler
from milo.handler.log import Logger
from milo.mods.settings import insert_default_settings_from_file

Logger("discord")
Logger("openai")
Logger("peewee")


def main() -> None:

    sqlitedb.connect()
    sqlitedb.create_tables(tables, safe=True)
    insert_default_settings_from_file("server")

    dc_handler = DiscordHandler()
    dc_handler.run()


if __name__ == "__main__":
    main()
