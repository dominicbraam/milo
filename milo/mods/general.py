from typing import TYPE_CHECKING
from milo.handler.response import respond_basic_str

if TYPE_CHECKING:
    from discord import Message


@respond_basic_str
async def default(message: Message, args: dict) -> str:
    return "See my features below:"
