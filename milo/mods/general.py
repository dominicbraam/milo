from __future__ import annotations
from typing import TYPE_CHECKING
from milo.handler.action_decorators import simple_response

if TYPE_CHECKING:
    from discord import Message
    from milo.handler.discord import DiscordHandler
    from milo.handler.llm import LLMHandler


class General:
    """
    Handle all general functions. Not even sure how to even
    describe what general is.

    Attributes:
        dc_handler: DiscordHandler
        llm_handler: LLMHandler
        message: Message
        args: dict
    """

    def __init__(
        self,
        dc_handler: DiscordHandler,
        message: Message,
        args: dict,
        llm_handler: LLMHandler = None,
    ) -> None:
        self.dc_handler = dc_handler
        self.llm_handler = llm_handler
        self.message = message
        self.args = args

    @simple_response
    async def default(self) -> str:
        """
        Sends the base response when there are no other options.

        Returns:
            str
        """
        return "not sure what you are saying. list my functionalities"
