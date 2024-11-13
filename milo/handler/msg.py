from discord import Interaction, Message
from milo.handler.llm import LLMHandler
from milo.globals import parent_mod
from milo.handler.log import Logger

app_logger = Logger("milo").get_logger()


async def process_message(message: Message, user_message: str) -> None:

    llm_handler = LLMHandler(user_message)
    chat_choice = llm_handler.get_function_choice()

    if (
        chat_choice.finish_reason == "tool_calls"
        and chat_choice.message.tool_calls[0].type == "function"
    ):

        await call_function(message, chat_choice)

    else:
        await message.channel.reply("Something went wrong.")
        app_logger.error("finish_reason and call_type not supported")


async def create_response(message: Message, chat_choice, results):
    llm_handler = LLMHandler(message.content)
    response = llm_handler.get_response(chat_choice, results)
    return response.message.content


async def reply_to_message(message: Message, chat_choice, results, view=None):
    response = await create_response(message, chat_choice, results)
    return await message.reply(response, view=view)


async def reply_to_interaction(
    interaction: Interaction, message: Message, chat_choice, results
):
    response = await create_response(message, chat_choice, results)
    return await interaction.response.edit_message(content=response, view=None)


async def reply_to_interaction_error(
    interaction: Interaction, message: Message, chat_choice
):
    response = await create_response(message, chat_choice, "error")
    return await interaction.response.edit_message(content=response, view=None)


def call_function(message: Message, chat_choice):
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
