import os
from dotenv import load_dotenv
from openai import OpenAI
from milo.loggers import get_loggers

app_logger = get_loggers()


class LLMHandler:

    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("OPENAI_API_KEY")

        self.client = OpenAI(api_key=self.api_key)

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
            tools=self.get_function_descriptions(),
            tool_choice="required",
        )

    def get_function_descriptions(self) -> list[dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "responder_default",
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
