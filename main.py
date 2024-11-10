from discord import Message
from milo.database import create_tables
from milo.handler.discord_handler import DiscordHandler
from milo.handler.msg_handler import MsgHandler
from milo.loggers import get_loggers

app_logger = get_loggers()


def main() -> None:

    create_tables()

    dc_handler = DiscordHandler()

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
        if user_message.startswith(dc_handler.name):
            user_message = user_message[dc_handler.name_len :]
            user_message = user_message.lstrip()

            app_logger.info(f"[{channel}] {username}: '{user_message}'")
            msg_handler = MsgHandler()
            await msg_handler.process_message(message, user_message)

    dc_handler.run()


if __name__ == "__main__":
    main()
