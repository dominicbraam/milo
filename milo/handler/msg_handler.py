from discord import Message
from handler.llm_handler import LLMHandler
from handler.func_handler import FuncHandler


class MsgHandler:

    async def process_message(self, message: Message, user_message: str) -> None:

        llm_handler = LLMHandler()
        chat_completion = llm_handler.chat_completions_custom(user_message)
        finish_reason = chat_completion.choices[0].finish_reason
        call_type = chat_completion.choices[0].message.tool_calls[0].type

        if finish_reason == "tool_calls" and call_type == "function":
            func_identifier = (
                chat_completion.choices[0].message.tool_calls[0].function.name
            )
            func_args = (
                chat_completion.choices[0].message.tool_calls[0].function.arguments
            )

            func_handler = FuncHandler(func_identifier, func_args)
            response = func_handler.call_function()

            await self.send_response(message, response)
        else:
            print("An unexpected error occured.")

    async def send_response(self, message: Message, response: str) -> None:

        try:
            await message.channel.send(response)
        except Exception as e:
            print(e)
