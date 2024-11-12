import os
from dotenv import load_dotenv
from openai import OpenAI


class LLMHandler:

    def __init__(self):
        load_dotenv()
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def chat_completions_custom(self, user_message: str):
        messages = [
            {
                "role": "system",
                "content": """You are a manager for gamebattles and scrims for
                Call of Duty. You provide information and organise scrims/
                game battles.""",
            },
            {
                "role": "user",
                "content": user_message,
            },
        ]

        return self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=self.function_descriptions,
            tool_choice="required",
        )

    @property
    def function_descriptions(self) -> list[dict]:
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
