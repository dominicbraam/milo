from discord import Message
from pydantic import BaseModel
from pydantic_core import from_json
import toml
from milo.handler.database import Settings as SettingsTbl
from milo.handler.response import (
    admin_privileges,
    confirm_decision_response,
    simple_response,
)
from milo.globals import bot_server_id


class ServerSettings(BaseModel):
    reminder_time: int


def load_settings_from_defaults_file(settings_group: str) -> ServerSettings:
    """
    Get default settings from defaults file and return ServerSettings struct.

    Args:
        settings_group: str

    Raises:
        ValueError

    Returns:
        ServerSettings
    """
    match settings_group:
        case "server":
            settings_class = ServerSettings
        case _:
            raise ValueError(f"{settings_group} is not a valid setting group.")

    with open("settings.default.toml", "r") as f:
        settings = toml.load(f)

    return settings_class.parse_obj(settings[settings_group])


def insert_default_server_settings(server_id: int) -> None:
    """
    Insert default server settings values from defaults file. Used mainly for:
        - bot startup to either insert or update with default values
        - insert default settings the first time when the bot joins a server

    Args:
        server_id: int
    """

    settings0 = SettingsTbl.get_or_none(SettingsTbl.server_id == server_id)

    settings = load_settings_from_defaults_file("server")
    settings_json = settings.model_dump_json()

    if settings0 is None:
        SettingsTbl.create(server_id=server_id, settings=settings_json)
    else:
        settings0.settings = settings_json
        settings0.save()


class Settings:
    """
    Class to handle the settings module.

    Attributes:
        message: Message
        args: dict
        settings_fields: list
    """

    def __init__(self, message: Message, args: dict):
        self.message = message
        self.args = args
        self.settings_fields: list = ServerSettings.model_fields
        self.__ensure_settings_exist_for_server()

    @property
    def fields(self) -> dict:
        """
        Creates property to hold data on the current settings.

        Returns:
            dict
        """
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

    @simple_response
    async def get_server_settings_as_dict(self) -> dict:
        """
        Return server settings as a Python dictionary.

        Returns:
            dict
        """
        settings_obj = self.__get_settings(self.message.guild.id)
        settings_model = self.__settings_json_to_model(
            ServerSettings, settings_obj.settings
        )

        return settings_model.dict()

    @admin_privileges
    @confirm_decision_response(additional_process=None)
    async def reset_server_settings(self) -> None:
        """Reset server settings to default values."""

        settings_obj = self.__get_settings(self.message.guild.id)
        default_settings_obj = self.__get_settings(bot_server_id)

        settings_obj.settings = default_settings_obj.settings
        settings_obj.save()

    @admin_privileges
    @confirm_decision_response(additional_process="form")
    async def edit_server_settings(self, updated_settings: dict) -> None:
        """
        Edit server settings.

        Args:
            updated_settings: dict
        """
        settings_obj = self.__get_settings(self.message.guild.id)

        new_settings = ServerSettings.parse_obj(updated_settings)
        settings_obj.settings = new_settings.model_dump_json()
        settings_obj.save()

    def __get_settings(self, server_id: int):
        """
        Get current server settings from database.

        Args:
            server_id: int

        Returns:
            SettingsTbl
                The database model for table
        """
        return SettingsTbl.get(SettingsTbl.server_id == server_id)

    def __settings_json_to_model(
        self, settings_model: BaseModel, settings_json: str
    ) -> BaseModel:
        """
        Takes json settings and creates an object based on the model model
        supplied.

        Args:
            settings_model: BaseModel
            settings_json: str

        Returns:
            BaseModel
        """
        return settings_model.model_validate(from_json(settings_json))

    def __ensure_settings_exist_for_server(self) -> None:
        """Insert default settings for server if it does not exist."""

        default_settings_obj = self.__get_settings(bot_server_id)

        SettingsTbl.get_or_create(
            server_id=self.message.guild.id,
            defaults={"settings": default_settings_obj.settings},
        )
