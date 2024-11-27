from __future__ import annotations
import json
from asyncio import TimeoutError
from typing import TYPE_CHECKING
from milo.helpers.discord.checks import is_reply_to_message
from milo.globals import (
    app_logger,
    bot_name,
    bot_name_len,
    parent_mod,
    timeout_wait_for_reply,
)
from milo.handler.llm import LLMHandler

if TYPE_CHECKING:
    from discord import Message
    from openai.types.chat.chat_completion import Choice
    from milo.handler.discord import DiscordHandler


async def process_message(
    dc_handler: DiscordHandler,
    message: Message,
    llm_handler: LLMHandler = None,
) -> None:
    """
    Gets function data based on user message and tries to call that function.
    It will recursively call itself if the bot needs more information to make
    a decision.

    Args:
        dc_handler: DiscordHandler
        message: Message
        llm_handler: LLMHandler
    """
    username = str(message.author)
    message_content = str(message.content)
    channel = str(message.channel)

    message_content = message_content.lower()
    # stop processing if the bot name wasn't used as an initial message
    # or if an llm_handler does not exist (it will exist if it is a reply
    # message in an already started chat with the bot
    if not (message_content.startswith(bot_name) or llm_handler):
        return

    # create new variable without bot name in message for further processing
    if message_content.startswith(bot_name):
        user_message = message_content[bot_name_len:]
    else:
        user_message = message_content

    user_message = user_message.lstrip()
    app_logger.debug(f"[{channel}] {username}: '{user_message}'")

    # create llm_handler if not already created (only created when the function
    # is called recursively). used to keep track of chat session with bot
    if not llm_handler:
        llm_handler = LLMHandler()
    llm_handler.add_message_to_record("user", user_message)
    chat_choice = llm_handler.get_function_choice()
    finish_reason = chat_choice.finish_reason

    if finish_reason == "stop":
        # runs whenever OpenAI does not have enough information to make a
        # function call
        reply_assistant = chat_choice.message.content
        llm_handler.add_message_to_record("assistant", reply_assistant)
        message_assistant = await message.reply(reply_assistant)

        def check_for_reply(m):
            if m.reference is not None:
                if is_reply_to_message(m, message_assistant):
                    return True
            return False

        # let Discord wait for reply to assistant message with specified
        # timeout
        try:
            message_reply_user = await dc_handler.client.wait_for(
                "message",
                check=check_for_reply,
                timeout=timeout_wait_for_reply,
            )
        # TODO: replies even if the message has nothing to do with bot
        # functions. For example, if there is a random question like
        # asking who it is, it will repond like a human and then respond
        # with "Ignoring. Took too long." even though there is no prompt
        # for a response - no prompt is the expected behaviour.
        except TimeoutError:
            await message.reply("Ignoring. Took too long.")
            return

        # if there is a user reply, recursively call function
        if message_reply_user:
            await process_message(dc_handler, message_reply_user, llm_handler)

    # once there is enough information, make funciton call
    elif finish_reason == "tool_calls":
        if chat_choice.message.tool_calls[0].type == "function":
            await call_function(dc_handler, message, chat_choice, llm_handler)

    else:
        await message.reply("Something went wrong.")
        app_logger.error(f"""finish_reason: {finish_reason} not supported""")


def call_function(
    dc_handler: DiscordHandler,
    message: Message,
    chat_choice: Choice,
    llm_handler: LLMHandler,
):
    """
    Calls function based on choice from llm.

    Args:
        dc_handler: DiscordHandler
        message: Message
        chat_choice: Choice
        llm_handler: LLMHandler

    Returns:
        Caroutine
    """
    func_identifier = chat_choice.message.tool_calls[0].function.name
    func_args = json.loads(
        chat_choice.message.tool_calls[0].function.arguments
    )

    d = "_"
    split_data = func_identifier.split(d)
    module_name = split_data[0]
    class_name = split_data[1]
    func_name = d.join(split_data[2:])

    module = __import__(f"{parent_mod}.{module_name}", fromlist=["object"])
    class_obj = getattr(module, class_name)(
        dc_handler, message, func_args, llm_handler
    )
    try:
        return getattr(class_obj, func_name)(chat_choice)
    except Exception as e:
        app_logger.error(e)
