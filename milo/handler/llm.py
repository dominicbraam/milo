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
                runs functions play music, text to speech, help manage gaming
                sessions. Ask for more information when necessary. You don't
                need to be very expressive other than providing the user with
                the results in a readable format using markdown for a discord
                user. Use markdown codeblocks whenever displaying tables. If
                there is a json object, try to add it in a table. Keep your
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

    def text_to_speech(self, filepath: str, text: str) -> None:
        """
        Text to speech.

        Args:
            filepath (): str
            text (): str
        """
        response = self.client.audio.speech.create(
            model="tts-1",
            voice="onyx",
            input=text,
        )

        response.stream_to_file(filepath)

    def summarize_text(self, text: str, char_limit: int) -> str:
        """
        Sumarize text and use a hard limit.

        Returns:
            Choice
        """
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": f"""Summarize into less than {char_limit}
                    characters: {text}""",
                }
            ],
        )

        return completion.choices[0].message.content

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
                    "name": "general_General_default",
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
                    "description": """Use this function to get and show
                    settings.""",
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
                    "name": "settings_Settings_reset_settings",
                    "description": """Only use this function if the user
                    explicitly mentions that they want to reset settings.
                    The user has to use the word settings. Do not use if
                    the user only mentions the word default or reset.""",
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
                    "name": "settings_Settings_edit_settings",
                    "description": """Use this function if the user wants to
                    edit the settings.""",
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
                    "name": "audio_DiscordAudio_say_text",
                    "description": """Use this function if the user wants to
                    say a piece of text.""",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "text": {
                                "type": "string",
                                "description": """Just text. Whatever comes
                                after say""",
                            }
                        },
                        "required": ["text"],
                        "additionalProperties": False,
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "audio_DiscordAudio_stream_audio",
                    "description": """Use this function if the user wants to
                    play audio that'll be streamed.""",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": """A song title or URL.""",
                            }
                        },
                        "required": ["query"],
                        "additionalProperties": False,
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "audio_DiscordAudio_pause",
                    "description": """Use this function if the user wants to
                    pause sound.""",
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
                    "name": "audio_DiscordAudio_resume",
                    "description": """Use this function if the user wants to
                    resume sound.""",
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
                    "name": "audio_DiscordAudio_stop",
                    "description": """Use this function if the user wants to
                    stop sound.""",
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
