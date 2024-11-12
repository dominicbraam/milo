from discord import Message
from milo.handler.llm_handler import LLMHandler
from milo.handler.func_handler import FuncHandler
from milo.loggers import get_loggers

app_logger = get_loggers()


class MsgHandler:

    def __init__(self, message: Message, user_message: str):
        self.message = message
        self.user_message = user_message
        self.response = ""

    async def process_message(self) -> str:

        llm_handler = LLMHandler()
        chat_completion = llm_handler.chat_completions_custom(
            self.user_message
        )
        finish_reason = chat_completion.choices[0].finish_reason
        call_type = chat_completion.choices[0].message.tool_calls[0].type

        if finish_reason == "tool_calls" and call_type == "function":
            func_identifier = (
                chat_completion.choices[0].message.tool_calls[0].function.name
            )
            func_args = (
                chat_completion.choices[0]
                .message.tool_calls[0]
                .function.arguments
            )

            func_handler = FuncHandler(
                self.message, func_identifier, func_args
            )
            await func_handler.call_function()

        else:
            await self.message.channel.send("Something went wrong.")
            app_logger.error("An unexpected error occured")
