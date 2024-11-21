from __future__ import annotations
import os
from dotenv import load_dotenv
from openai import OpenAI
from typing import TYPE_CHECKING
import json
from milo.mods.settings import groups as settings_groups

if TYPE_CHECKING:
    from typing import Union
    from openai.types.chat.chat_completion import Choice


class LLMHandler:
    """
    Class to handle communication with the OpenAI API.

    Attributes:
        client: OpenAI
        model: str
        chat_record: list[dict]
            The entire chat with llm. Fill chat if chat memory is to be used.
    """

    def __init__(self):
        load_dotenv()
        self.client: OpenAI = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model: str = "gpt-4o-mini"
        self.chat_record: list[dict] = [
            {
                "role": "system",
                "content": """You are working as a bot called Milo that
                runs functions to help manage gaming sessions. There are going
                to be times where you need more information. Ask for that
                information when necessary; do not assume. You don't need
                to be very expressive other than providing the user with the
                results in a readable format using markdown for a discord user.
                Use markdown codeblocks whenever displaying tables. If there is
                a json object, try to add it in a table. I mean it. Keep your
                responses very short and concise. There are some cases where
                the reply will be an empty value. That just means that the
                function called was run successfully and you can tell the user
                that.""",
            }
        ]

    def add_message_to_record(self, role: str, message: str) -> None:
        """
        Add messages to self.chat_record

        Args:
            role: str
            message: str
        """
        self.chat_record.append(
            {
                "role": role,
                "content": message,
            }
        )

    def get_function_choice(self) -> Choice:
        """
        Evaluate self.user_message using OpenAI function calling to select
        which function to run.

        Returns:
            Choice
        """
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=self.chat_record,
            tools=self.function_descriptions,
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

        if chat_choice.finish_reason == "tool_calls":
            self.chat_record.append(chat_choice.message)
            self.chat_record.append(
                {
                    "role": "tool",
                    "content": json.dumps({"response": results}),
                    "tool_call_id": chat_choice.message.tool_calls[0].id,
                }
            )

        response = self.client.chat.completions.create(
            model=self.model,
            messages=self.chat_record,
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
                    "name": "settings_Settings_get_settings_as_dict",
                    "description": """Use this function to get settings for
                    either the server, personal account.""",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "group": {
                                "type": "string",
                                "enum": settings_groups,
                            }
                        },
                        "required": ["group"],
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
