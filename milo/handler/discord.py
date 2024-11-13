from typing import Final
import os
from dotenv import load_dotenv
from discord import (
    ButtonStyle,
    Client,
    Intents,
    Interaction,
    SelectOption,
    ui,
)


class DiscordHandler:
    def __init__(self):
        self.token: Final[str] = ""
        self.intents: Intents = Intents.default()
        self.intents.members = True
        self.intents.guilds = True
        self.client: Client = Client(intents=self.intents)

        load_dotenv()
        self.token = os.getenv("DISCORD_TOKEN")

    def run(self) -> None:
        self.intents.message_content = True
        self.client.run(token=self.token)


class ConfirmView(ui.View):
    def __init__(self, *, timeout=5, class_obj):
        super().__init__(timeout=timeout)
        self.user_message_obj = class_obj.message
        self.bot_message_obj = None
        self.exit_status = None

    async def on_timeout(self):
        # disable buttons after on timeout
        if self.bot_message_obj:
            for item in self.children:
                item.disabled = True
            await self.bot_message_obj.edit(view=self)

    async def interaction_check(self, interaction: Interaction):
        # reject any user that isn't the author of the message
        if interaction.user != self.user_message_obj.author:
            self.exit_status = "not_author"
            self.interaction = interaction
            self.stop()

            return False
        return True

    @ui.button(label="Continue", style=ButtonStyle.green)
    async def confirm(self, interaction: Interaction, button: ui.Button):
        self.exit_status = "continued"
        self.interaction = interaction
        self.stop()

    @ui.button(label="Cancel", style=ButtonStyle.red)
    async def cancel(self, interaction: Interaction, button: ui.Button):
        self.exit_status = "cancelled"
        self.interaction = interaction
        self.stop()


class FormModal(ui.Modal):
    def __init__(self, *, title, class_obj):
        super().__init__(title=title)
        self.class_obj = class_obj
        self.results = dict()

        for field in class_obj.fields:
            current = class_obj.fields[field].get("current")
            options = class_obj.fields[field].get("options")
            units = class_obj.fields[field].get("units")
            if options:
                self.add_item(FormDropdown(field, options))
            else:
                self.add_item(FormText(field, units, current))

    async def on_submit(self, interaction: Interaction):
        for child in self.children:
            self.results[child.custom_id] = child.value

        self.interaction = interaction
        self.exit_status = "submitted"

    async def on_error(
        self, interaction: Interaction, error: Exception
    ) -> None:
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
