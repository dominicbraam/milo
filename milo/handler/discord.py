from typing import Optional, Final
import os
from dotenv import load_dotenv
from discord import (
    ButtonStyle,
    Client,
    Intents,
    Interaction,
    Message,
    SelectOption,
    ui,
)


class DiscordHandler:
    """
    Class to handle discord client initialisation.

    Attributes:
        token: Final[str]
        intents: Intents
        members: bool
        guilds: bool
        client: Client
        token: str
        message_content: bool
    """

    def __init__(self) -> None:
        self.token: Final[str] = ""
        self.intents: Intents = Intents.default()
        self.intents.members: bool = True
        self.intents.guilds: bool = True
        self.client: Client = Client(intents=self.intents)

        load_dotenv()
        self.token: str = os.getenv("DISCORD_TOKEN")

    def run(self) -> None:
        self.intents.message_content: bool = True
        self.client.run(token=self.token)


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

    def __init__(self, *, timeout=5, class_obj: type) -> None:
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

        for field in class_obj.fields:
            # loop to populate form with fields. max = 5 fields
            current = class_obj.fields[field].get("current")
            options = class_obj.fields[field].get("options")
            units = class_obj.fields[field].get("units")
            if options:
                self.add_item(FormDropdown(field, options))
            else:
                self.add_item(FormText(field, units, current))

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
    def __init__(self, field, units, current):
        label = f"{field} ({units})"
        super().__init__(
            custom_id=field,
            label=label,
            default=current,
        )
