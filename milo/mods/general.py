from discord import Message
from milo.handler.response import respond_basic_str


@respond_basic_str
async def default(message: Message, args: dict) -> str:
    return "See my features below:"
