from discord import Message
from pydantic import BaseModel
import toml
from milo.database import Settings as SettingsTbl
from milo.handler.response_handler import (
    admin_privileges,
    confirm_decision,
    respond_table_from_dict,
)
from milo.loggers import get_loggers

app_logger = get_loggers()

server0 = 0


class ServerSettings(BaseModel):
    reminder_time: int


class Settings:

    def __init__(self, message: Message, args: dict):
        self.message = message
        self.args = args
        self.server_id = self.message.guild.id

        default_settings_row = self.get_server_settings_row(server0)
        self.default_settings = self.make_settings_struct_from_row(
            default_settings_row
        )
        self.settings_fields = ServerSettings.model_fields

        self.ensure_settings_exist_for_server()
        self.server_current_settings_row = self.get_server_settings_row(
            self.server_id
        )
        self.current_settings_struct = self.make_settings_struct_from_row(
            self.server_current_settings_row
        )
        self.settings_options = {
            "reminder_time": {
                "current": self.current_settings_struct.reminder_time,
                "units": "mins",
            },
        }

    @respond_table_from_dict
    async def get_server_settings_as_dict(self) -> dict:
        """get bot settings for server"""

        return self.current_settings_struct.dict()

    @admin_privileges
    @confirm_decision(additional_process=None)
    async def reset_server_settings(self) -> str:
        """reset settings to default values for server"""

        settings_default_json = self.default_settings.model_dump_json()
        self.server_current_settings_row.settings = settings_default_json
        self.server_current_settings_row.save()

        return "Default settings applied."

    @admin_privileges
    @confirm_decision(additional_process="form")
    async def edit_server_settings(self, updated_settings: dict) -> str:
        """edit settings"""

        new_settings = ServerSettings.parse_obj(updated_settings)
        self.server_current_settings_row.settings = (
            new_settings.model_dump_json()
        )
        self.server_current_settings_row.save()

        return "Settings updated."

    def get_server_settings_row(self, server_id: int):
        """get server settings row from db"""
        return SettingsTbl.get(SettingsTbl.server_id == server_id)

    def make_settings_struct_from_row(self, settings_db_row) -> ServerSettings:
        """get server settings for server"""
        return ServerSettings.model_validate_json(settings_db_row.settings)

    def ensure_settings_exist_for_server(self):
        """insert default settings for server if it does not exist"""

        server_settings = SettingsTbl.get_or_none(
            SettingsTbl.server_id == self.server_id
        )

        if server_settings is None:
            settings_default_json = self.default_settings.model_dump_json()
            SettingsTbl.create(
                server_id=self.server_id, settings=settings_default_json
            )


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


def load_settings_from_defaults_file(settings_group: str) -> ServerSettings:
    """get default settings from defaults file and return struct"""
    with open("settings.default.toml", "r") as f:
        settings = toml.load(f)

    return ServerSettings.parse_obj(settings[settings_group])
