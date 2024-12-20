from __future__ import annotations
from discord import (
    ButtonStyle,
    SelectOption,
    ui,
)
from typing import TYPE_CHECKING
from milo.globals import timeout_wait_for_button_interaction

if TYPE_CHECKING:
    from discord import Interaction, Message
    from typing import Optional


class ConfirmView(ui.View):
    """
    Class to create confirm views in discord. It implements 2 buttons:
    Continue and Cancel.

    Attributes:
        user_message_obj: Message
        bot_message_obj: Optional[Message]
            Message created as a reply to the user.
        interaction: Interaction
        exit_status: str
            Different predefined functions from ui.View makes it so that the
            view can exit in multiple ways. For example, it can exit when the
            user clicks on Continue or it can simply timeout.
            Options:
              'premature', 'continued', 'cancelled', 'not_author', 'error'
    """

    def __init__(
        self, *, timeout=timeout_wait_for_button_interaction, class_obj: type
    ) -> None:
        super().__init__(timeout=timeout)
        self.user_message_obj: Message = class_obj.message
        self.bot_message_obj: Optional[Message] = None
        self.interaction: Interaction = None
        self.exit_status: str = "error"

    async def on_timeout(self):
        """
        Use builtin function from ui.View to disable buttons after timeout.
        """
        if self.bot_message_obj:
            for item in self.children:
                item.disabled = True
            await self.bot_message_obj.edit(view=self)

    async def interaction_check(self, interaction: Interaction) -> bool:
        """
        Use builtin function from ui.View to stop interaction if the
        interaction user is not the author of the original message.

        Args:
            interaction: Interaction

        Returns:
            bool
        """

        if interaction.user != self.user_message_obj.author:
            self.interaction = interaction
            self.exit_status = "not_author"
            self.stop()

            return False
        return True

    @ui.button(label="Continue", style=ButtonStyle.green)
    async def confirm(self, interaction: Interaction, button: ui.Button):
        """
        Stops interaction if this button is used and sets exit_status and
        interaction properties for view object.

        Args:
            interaction: Interaction
            button: ui.Button
        """
        self.interaction = interaction
        self.exit_status = "continued"
        self.stop()

    @ui.button(label="Cancel", style=ButtonStyle.red)
    async def cancel(self, interaction: Interaction, button: ui.Button):
        """
        Stops interaction if this button is used and sets exit_status and
        interaction properties for view object.

        Args:
            interaction: Interaction
            button: ui.Button
        """
        self.exit_status = "cancelled"
        self.interaction = interaction
        self.stop()


class FormModal(ui.Modal):
    """
    Class to create modals in discord.

    Attributes:
        class_obj: type
            Supports mutliple classes. For example, it can create forms for
            changing settings or inputting data for a session.
        results: dict
            Hold results from modal after user submitted.
        interaction: Interaction
        exit_status: str
            Different predefined functions from ui.Modal makes it so that the
            view can exit in multiple ways. For example, it can exit when the
            submits the form or it can simply timeout.
            Options:
              'submitted', 'error'
    """

    def __init__(self, *, title: str, class_obj: type) -> None:
        super().__init__(title=title)
        self.class_obj = class_obj
        self.results = dict()
        self.interaction: Interaction = None
        self.exit_status: str = "error"

        for field_key in class_obj.fields_extra_data:
            # loop to populate form with fields. max = 5 fields
            field_data = class_obj.fields_extra_data.get(field_key)
            value = field_data.get("value")
            options = field_data.get("options")
            unit = field_data.get("unit")
            if options:
                self.add_item(FormDropdown(field_key, options))
            else:
                self.add_item(FormText(field_key, value, unit))

    async def on_submit(self, interaction: Interaction):
        """
        Uses builtin function for ui.Modal to set properties:
            - results: containing the results from the modal interaction
            - interaction
            - exit_status

        Args:
            interaction: Interaction
        """
        for child in self.children:
            self.results[child.custom_id] = child.value

        self.interaction = interaction
        self.exit_status = "submitted"

    async def on_error(self, interaction: Interaction, error: Exception):
        """
        Uses builtin function to set properties: interaction and exit_status
        when the modal exits with an error.

        Args:
            interaction: Interaction
            error: Exception
        """
        self.interaction = interaction
        self.exit_status = "error"


class FormDropdown(ui.Select):
    def __init__(self, field, options):

        select_options = list()
        for o in options:
            select_options.append(SelectOption(label=o))

        super().__init__(
            custom_id=field,
            max_values=1,
            min_values=1,
            options=select_options,
        )


class FormText(ui.TextInput):
    def __init__(self, field, value, unit):
        label = f"{field} ({unit})"
        super().__init__(
            custom_id=field,
            label=label,
            default=value,
        )
