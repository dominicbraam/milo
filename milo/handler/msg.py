from discord import Interaction, Message, ui
from openai.types.chat.chat_completion import Choice
from typing import Union
from milo.handler.llm import LLMHandler
from milo.globals import parent_mod
from milo.handler.log import Logger

app_logger = Logger("milo").get_logger()


async def process_message(message: Message, user_message: str) -> None:
    """
    Gets function data based on user message and tries to call that function.

    Args:
        message: Message
        user_message: str
    """
    llm_handler = LLMHandler(user_message)
    chat_choice = llm_handler.get_function_choice()

    if (
        chat_choice.finish_reason == "tool_calls"
        and chat_choice.message.tool_calls[0].type == "function"
    ):

        await call_function(message, chat_choice)

    else:
        reply_to_message(message, chat_choice, "error")
        app_logger.error("finish_reason and call_type not supported")


async def create_response(
    message: Message, chat_choice: Choice, results: Union[str, dict]
) -> str:
    """
    Creates response using llm.

    Args:
        message: Message
        chat_choice: Choice
        results: Union[str, dict]

    Returns:
        str
    """
    llm_handler = LLMHandler(message.content)
    response = llm_handler.get_response(chat_choice, results)
    return response.message.content


async def reply_to_message(
    message: Message,
    chat_choice: Choice,
    results: Union[str, dict],
    view: ui.View = None,
) -> Message:
    """
    Replies to discord message and returns message object in case it needs to
    be used.

    Args:
        message: Message
        chat_choice: Choice
        results: Union[str, dict]
        view: ui.View

    Returns:
        Message
    """
    response = await create_response(message, chat_choice, results)
    return await message.reply(response, view=view)


async def reply_to_interaction(
    interaction: Interaction,
    message: Message,
    chat_choice: Choice,
    results: Union[str, dict],
    view: ui.View = None,
) -> None:
    """
    Replies to discord message with interaction.

    Args:
        interaction: Interaction
        message: Message
        chat_choice: Choice
        results: Union[str, dict]
        view: ui.View
    """
    response = await create_response(message, chat_choice, results)
    await interaction.response.edit_message(content=response, view=view)


def call_function(message: Message, chat_choice: Choice):
    """
    Calls function based on choice from llm.

    Args:
        message: Message
        chat_choice: Choice

    Returns:
        Caroutine
    """
    func_identifier = chat_choice.message.tool_calls[0].function.name
    func_args = chat_choice.message.tool_calls[0].function.arguments

    d = "_"
    split_data = func_identifier.split(d)
    module_name = split_data[0]
    class_name = split_data[1]
    func_name = d.join(split_data[2:])

    module = __import__(f"{parent_mod}.{module_name}", fromlist=["object"])
    class_obj = getattr(module, class_name)(message, func_args)
    return getattr(class_obj, func_name)(chat_choice)
