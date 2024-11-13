import os
from dotenv import load_dotenv
from openai import OpenAI
from openai.types.chat.chat_completion import Choice
from typing import Union
import json


class LLMHandler:
    """
    Class to handle communication with the OpenAI API.

    Attributes:
        client: OpenAI
        user_message: str
        model: str
        chat: list[dict]
            The entire chat with llm. Fill chat if chat memory is to be used.
    """

    def __init__(self, user_message: str):
        load_dotenv()
        self.client: OpenAI = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.user_message: str = user_message
        self.model: str = "gpt-4o-mini"
        self.chat: list[dict] = [
            {
                "role": "system",
                "content": """You are working alongside a bot called Milo that
                runs functions to help manage gaming sessions. You don't need
                to be very expressive other than providing the user with the
                results in a readable format using markdown for a discord user.
                Use markdown codeblocks whenever displaying tables. If there is
                a json object, try to add it in a table. I mean it. Keep your
                responses very short and concise. There are some cases where
                the reply will be an empty value. That just means that the
                function called was run successfully and you can tell the user
                that.""",
            },
            {
                "role": "user",
                "content": self.user_message,
            },
        ]

    def get_function_choice(self) -> Choice:
        """
        Evaluate self.user_message using OpenAI function calling to select
        which function to run.

        Returns:
            Choice
        """
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=self.chat,
            tools=self.function_descriptions,
            tool_choice="required",
        )

        return completion.choices[0]

    def get_response(
        self, chat_choice: Choice, results: Union[str, dict]
    ) -> Choice:
        """
        Takes results and uses OpenAI completion to get response in a human
        readable format.

        Args:
            chat_choice: Choice
            results: Union[str, dict]

        Returns:
            Choice
        """
        function_call_result_message = {
            "role": "tool",
            "content": json.dumps({"response": results}),
            "tool_call_id": chat_choice.message.tool_calls[0].id,
        }

        self.chat.append(chat_choice.message)
        self.chat.append(function_call_result_message)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=self.chat,
        )

        return response.choices[0]

    @property
    def function_descriptions(self) -> list[dict]:
        """
        Creates function_description property for class. It contains tools for
        use with OpenAI function calling.

        Returns:
            list[dict]
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "general_default",
                    "description": """Use this function as the default
                    function. Call this function either when the user wants to
                    know about our capabilities/features or when there is no
                    proper match for any other function.""",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "additionalProperties": False,
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "settings_Settings_get_server_settings_as_dict",
                    "description": """Use this function to get settings for the
                    current server.""",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "additionalProperties": False,
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "settings_Settings_reset_server_settings",
                    "description": """Only use this function if the user
                    explicitly mentions that they want to reset server
                    settings. The user has to use the word settings. Do not use
                    if the user only mentions the word default or reset.""",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "additionalProperties": False,
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "settings_Settings_edit_server_settings",
                    "description": """Use this function if the user wants to
                    edit a server setting.""",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "additionalProperties": False,
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "gamebattles_get_schedule",
                    "description": """Get the schedule for scrims or game
                    battles. Call this whenever you need to see all sessions
                    for upcoming scrims or game battles or example when a
                    customer asks 'scrims?' or 'schedule'""",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "additionalProperties": False,
                    },
                },
            },
        ]
