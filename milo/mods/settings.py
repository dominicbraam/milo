from __future__ import annotations
from playhouse.shortcuts import model_to_dict
from typing import TYPE_CHECKING
import toml
from milo.handler.database import SettingsServer
from milo.handler.action_decorators import (
    admin_privileges,
    confirm_decision_response,
    simple_response,
)

if TYPE_CHECKING:
    from discord import Message
    from milo.handler.llm import LLMHandler
    from milo.handler.database import BaseModel


groups = ["server, personal"]  # used in other places like llm.py as an enum
group_data = {"server": {"table_model": SettingsServer}}


class Settings:
    """
    Class to handle the settings module.

    Attributes:
        message: Message
        group: str
        llm_handler: LLMHandler
    """

    def __init__(self, message: Message, args: dict, llm_handler: LLMHandler):
        self.message = message
        self.group: str = args["group"]
        self.llm_handler = llm_handler

    @property
    def group_data(self) -> dict:
        """
        Property to hold extra data that can be useful for the settings group
        outside the class.

        Raises:
            ValueError:

        Returns:
            dict
        """
        match self.group:
            case "server":
                data = group_data[self.group]
                data["item_id"] = self.message.guild.id
                return data
            # case "person":
            #     return {
            #         "table_model": "Poop",
            #         "item_id": self.message.author.id,
            #     }
            case _:
                raise ValueError(f"Group '{self.group}' does not exist.")

    @property
    def settings_default(self) -> BaseModel:
        """
        Property to hold the default settings found in the database.

        Returns:
            BaseModel
        """
        table_model = self.group_data["table_model"]

        return table_model.get(table_model.id == 0)

    @property
    def settings_current(self) -> BaseModel:
        """
        Property to hold the current settings found in the database.

        Returns:
            BaseModel
        """
        table_model = self.group_data["table_model"]
        item_id = self.group_data["item_id"]

        settings_default_copy = self.settings_default.__data__.copy()
        settings_default_copy.pop("id")

        settings_current, created = table_model.get_or_create(
            id=item_id, defaults=settings_default_copy
        )

        return settings_current

    @property
    def fields_extra_data(self) -> dict:
        """
        Property to hold data on the current settings.

        Returns:
            dict
        """
        dictionary = dict()

        model_dict = model_to_dict(self.settings_current)
        for field_name in model_dict:
            if field_name == "id":
                continue

            dictionary.update(
                {
                    field_name: {
                        "value": model_dict[field_name],
                        "unit": self.settings_current.get_unit(field_name),
                    }
                }
            )
        return dictionary

    @simple_response
    async def get_settings_as_dict(self) -> dict:
        """
        Return server settings as a Python dictionary.

        Returns:
            dict
        """
        return self.fields_extra_data

    @admin_privileges
    @confirm_decision_response(additional_process=None)
    async def reset_server_settings(self) -> None:
        """Reset server settings to default values."""

        settings_default_copy = self.settings_default.__data__.copy()
        settings_default_copy.pop("id")

        table_model = self.group_data["table_model"]
        item_id = self.group_data["id"]

        q = table_model.update(settings_default_copy).where(
            table_model.id == item_id
        )
        q.execute()

    @admin_privileges
    @confirm_decision_response(additional_process="form")
    async def edit_server_settings(self, updated_settings: dict) -> None:
        """
        Update server settings.

        Args:
            updated_settings: dict
        """
        table_model = self.group_data["table_model"]
        item_id = self.group_data["item_id"]

        q = table_model.update(updated_settings).where(
            table_model.id == item_id
        )
        q.execute()


def insert_default_settings_from_file(group: str) -> None:
    """
    Insert default settings from defaults file.

    Args:
        group: str

    Raises:
        ValueError
    """
    match group:
        case "server":
            table_model = SettingsServer
        case _:
            raise ValueError(f"Group '{group}' does not exist.'")

    with open("data/system/settings.default.toml", "r") as f:
        settings = toml.load(f)

    settings_default_from_file = settings[group]
    table_model = group_data[group]["table_model"]

    settings_default, created = table_model.get_or_create(
        id=0, defaults=settings_default_from_file
    )

    if not created:
        q = table_model.update(settings_default_from_file).where(
            table_model.id == 0
        )
        q.execute()
