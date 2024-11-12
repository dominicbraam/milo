from discord import Message
from pydantic import BaseModel
from pydantic_core import from_json
import toml
from milo.handler.database import Settings as SettingsTbl
from milo.handler.response import (
    admin_privileges,
    confirm_decision,
    respond_table_from_dict,
)
from milo.globals import bot_server_id


class ServerSettings(BaseModel):
    reminder_time: int


def load_settings_from_defaults_file(settings_group: str) -> ServerSettings:
    """get default settings from defaults file and return struct"""

    match settings_group:
        case "server":
            settings_class = ServerSettings
        case _:
            raise ValueError(f"{settings_group} is not a valid setting group.")

    with open("settings.default.toml", "r") as f:
        settings = toml.load(f)

    return settings_class.parse_obj(settings[settings_group])


def insert_default_server_settings(server_id) -> None:
    """insert default values for the bot. to be referenced by servers"""

    settings0 = SettingsTbl.get_or_none(SettingsTbl.server_id == server_id)

    settings = load_settings_from_defaults_file("server")
    settings_json = settings.model_dump_json()

    if settings0 is None:
        SettingsTbl.create(server_id=server_id, settings=settings_json)
    else:
        settings0.settings = settings_json
        settings0.save()


class Settings:

    def __init__(self, message: Message, args: dict):
        self.message: Message = message
        self.args: dict = args
        self.settings_fields: list = ServerSettings.model_fields
        self.__ensure_settings_exist_for_server()

    @property
    def settings_options(self):
        settings_obj = self.__get_settings(self.message.guild.id)
        settings_model = self.__settings_json_to_model(
            ServerSettings, settings_obj.settings
        )

        return {
            "reminder_time": {
                "current": settings_model.reminder_time,
                "units": "mins",
            },
        }

    @respond_table_from_dict
    async def get_server_settings_as_dict(self) -> dict:
        """get bot settings for server"""

        settings_obj = self.__get_settings(self.message.guild.id)
        settings_model = self.__settings_json_to_model(
            ServerSettings, settings_obj.settings
        )

        return settings_model.dict()

    @admin_privileges
    @confirm_decision(additional_process=None)
    async def reset_server_settings(self) -> str:
        """reset settings to default values for server"""

        settings_obj = self.__get_settings(self.message.guild.id)
        default_settings_obj = self.__get_settings(bot_server_id)

        settings_obj.settings = default_settings_obj.settings
        settings_obj.save()

        return "Default settings applied."

    @admin_privileges
    @confirm_decision(additional_process="form")
    async def edit_server_settings(self, updated_settings: dict) -> str:
        """edit settings"""

        settings_obj = self.__get_settings(self.message.guild.id)

        new_settings = ServerSettings.parse_obj(updated_settings)
        settings_obj.settings = new_settings.model_dump_json()
        settings_obj.save()

        return "Settings updated."

    def __get_settings(self, server_id: int):
        """get current server settings"""
        return SettingsTbl.get(SettingsTbl.server_id == server_id)

    def __settings_json_to_model(
        self, settings_obj: BaseModel, settings_json: str
    ):
        return settings_obj.model_validate(from_json(settings_json))

    def __ensure_settings_exist_for_server(self):
        """insert default settings for server if it does not exist"""

        default_settings_obj = self.__get_settings(bot_server_id)

        SettingsTbl.get_or_create(
            server_id=self.message.guild.id,
            defaults={"settings": default_settings_obj.settings},
        )
