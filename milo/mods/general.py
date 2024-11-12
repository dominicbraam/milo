from discord import Message
from milo.handler.response_handler import respond_basic_str
from milo.loggers import get_loggers

app_logger = get_loggers()


@respond_basic_str
async def default(message: Message, args: dict) -> str:
    return "See my features below:"
