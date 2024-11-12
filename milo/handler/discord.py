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
    def __init__(self, *, timeout=5, function, class_obj, additional_process):
        super().__init__(timeout=timeout)
        self.additional_process = additional_process
        self.function = function
        self.class_obj = class_obj
        self.user_message_obj = class_obj.message
        self.bot_message_obj = None

    async def on_timeout(self):
        # disable buttons after on timeout
        if self.bot_message_obj:
            for item in self.children:
                item.disabled = True
            await self.bot_message_obj.edit(view=self)

    async def interaction_check(self, interaction: Interaction):
        # reject any user that isn't the author of the message
        if interaction.user != self.user_message_obj.author:
            await interaction.response.edit_message(
                content=f"""{interaction.user.name} cannot complete request for
                {self.user_message_obj.author.name}.""",
            )
            return False
        return True

    @ui.button(label="Continue", style=ButtonStyle.green)
    async def confirm(self, interaction: Interaction, button: ui.Button):
        match self.additional_process:
            # when case None, the supplied function runs directly without any
            # any additional processes being involved
            case None:
                response = await self.function(self.class_obj)
                # after getting a response, remove buttons and replace message
                # with response
                self.bot_message_obj = await interaction.response.edit_message(
                    content=response, view=None
                )
            case "form":
                self.bot_message_obj = await interaction.response.send_modal(
                    Form(
                        title="test",
                        function=self.function,
                        class_obj=self.class_obj,
                    )
                )
            case _:
                self.bot_message_obj = await interaction.response.edit_message(
                    content="Something went wrong", view=None
                )

    @ui.button(label="Cancel", style=ButtonStyle.red)
    async def cancel(self, interaction: Interaction, button: ui.Button):
        self.bot_message_obj = await interaction.response.edit_message(
            content="Operation cancelled.", view=None
        )


class Form(ui.Modal):
    def __init__(self, *, title, function, class_obj):
        super().__init__(title=title)
        self.function = function
        self.class_obj = class_obj
        self.user_message_obj = self.class_obj.message
        self.results = dict()

        for field in class_obj.settings_fields:
            current = class_obj.settings_options[field].get("current")
            options = class_obj.settings_options[field].get("options")
            units = class_obj.settings_options[field].get("units")
            if options:
                self.add_item(FormDropdown(field, options))
            else:
                self.add_item(FormText(field, units, current))

    async def on_submit(self, interaction: Interaction):
        for child in self.children:
            self.results[child.custom_id] = child.value
        response = await self.function(self.class_obj, self.results)
        await interaction.response.edit_message(content=response, view=None)

    async def on_error(
        self, interaction: Interaction, error: Exception
    ) -> None:
        await interaction.response.edit_message(
            content="Oops! Something went wrong.", view=None
        )


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
