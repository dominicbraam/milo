from __future__ import annotations
from discord import ui

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from discord import Interaction, Message
    from openai.types.chat.chat_completion import Choice
    from typing import Union
    from milo.handler.llm import LLMHandler


class Responder:
    """
    Class to help with responding to messages in Discord.

    Attributes:
        llm_handler: LLMHandler
        chat_choice: Choice
        results: Union[str, dict]
        view: Union[ui.View, None]
    """

    def __init__(
        self,
        llm_handler: LLMHandler,
        chat_choice: Choice,
        results: Union[str, dict],
        view: Union[ui.View, None] = None,
    ):
        self.llm_handler = llm_handler
        self.chat_choice = chat_choice
        self.results = results
        self.view = view

    async def create_response(self) -> str:
        """
        Creates human readable response using llm.

        Returns:
            str
        """
        response = self.llm_handler.get_response(
            self.chat_choice, self.results
        )
        return response.message.content

    async def reply_to_message(self, message: Message) -> Message:
        """
        Replies to Discord message and returns message object in case it needs
        to be used.

        Args:
            message: Message

        Returns:
            Message
        """
        response = await self.create_response()
        return await message.reply(response, view=self.view)

    async def reply_to_interaction(self, interaction: Interaction) -> None:
        """
        Replies to Discord Interaction with a Message.

        Args:
            interaction: Interaction
        """
        response = await self.create_response()
        await interaction.response.edit_message(
            content=response, view=self.view
        )
