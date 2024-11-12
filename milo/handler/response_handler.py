from discord import (
    Message,
    ui,
    ButtonStyle,
    Interaction,
    SelectOption,
)
from table2ascii import table2ascii, PresetStyle


def respond_basic_str(f):
    """runs function and replies with string return result"""

    async def wrapper(message: Message, args: dict):
        s = await f(message, args)
        await message.reply(s)

    return wrapper


def respond_table_from_dict(f):
    """runs function and replies with dictionary return result as a table"""

    async def wrapper(class_obj):
        dictionary = await f(class_obj)
        tbl = table2ascii(
            body=list(dictionary.items()),
            first_col_heading=True,
            style=PresetStyle.double_thin_box,
        )
        await class_obj.message.reply(f"```{tbl}```")

    return wrapper


def admin_privileges(f):
    """runs function only if user is admin"""

    async def wrapper(class_obj):
        if not class_obj.message.author.guild_permissions.administrator:
            await class_obj.message.reply("Must be admin to complete task.")
            # TODO: make the reply dynamic so that the user knows
            # which task it is
        else:
            return await f(class_obj)

    return wrapper


def confirm_decision(additional_process=None):
    """used as a decorator. takes in function, lets user choose to continue or
    not. if the choice is continue, run function. if not, cancel operation."""

    def function_collector(f):
        async def wrapper(class_obj):
            """option - 0: default, 1: form"""
            confirm_view = ConfirmOperation(
                function=f,
                class_obj=class_obj,
                additional_process=additional_process,
            )
            docstring = f.__doc__
            confirm_view.message = await class_obj.message.reply(
                f"Are you sure you want to {docstring}?", view=confirm_view
            )

        return wrapper

    return function_collector


class ConfirmOperation(ui.View):
    def __init__(self, *, timeout=5, function, class_obj, additional_process):
        super().__init__(timeout=timeout)
        self.additional_process = additional_process
        self.user_message = class_obj.message
        self.message = None
        self.function = function
        self.class_obj = class_obj

    async def on_timeout(self):
        if self.message:
            for item in self.children:
                item.disabled = True
            await self.message.edit(view=self)

    async def interaction_check(self, interaction: Interaction):
        if interaction.user != self.user_message.author:
            await interaction.response.edit_message(
                content=f"""{interaction.user.name} cannot complete request for
                {self.user_message.author.name}.""",
            )
            return False
        return True

    @ui.button(label="Continue", style=ButtonStyle.green)
    async def confirm(self, interaction: Interaction, button: ui.Button):
        match self.additional_process:
            case None:
                response = await self.function(self.class_obj)
                self.message = await interaction.response.edit_message(
                    content=response, view=None
                )
            case "form":
                self.message = await interaction.response.send_modal(
                    Form(function=self.function, class_obj=self.class_obj)
                )
            case _:
                self.message = await interaction.response.edit_message(
                    content="Something went wrong", view=None
                )

    @ui.button(label="Cancel", style=ButtonStyle.red)
    async def cancel(self, interaction: Interaction, button: ui.Button):
        self.message = await interaction.response.edit_message(
            content="Operation cancelled.", view=None
        )


class Form(ui.Modal, title="Test"):
    def __init__(self, *, timeout=10, function, class_obj):
        super().__init__(timeout=timeout)
        self.function = function
        self.class_obj = class_obj
        self.user_message = self.class_obj.message
        self.message = None
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
