from discord import Message
from table2ascii import table2ascii, PresetStyle
from milo.handler.discord import ConfirmView


def respond_basic_str(f):
    """decorator: runs function and replies with string return result"""

    async def wrapper(message: Message, args: dict):
        s = await f(message, args)
        await message.reply(s)

    return wrapper


def respond_table_from_dict(f):
    """decorator: runs function and replies with dictionary return result
    as a table"""

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
    """decorator: runs function only if user is admin"""

    async def wrapper(class_obj):
        if not class_obj.message.author.guild_permissions.administrator:
            await class_obj.message.reply("Must be admin to complete task.")
            # TODO: make the reply dynamic so that the user knows
            # which task it is
        else:
            return await f(class_obj)

    return wrapper


def confirm_decision(additional_process=None):
    """decorator: takes in function, lets user choose to continue or
    not. if the choice is continue, run function. if not, cancel operation."""

    def function_collector(f):
        async def wrapper(class_obj):
            """option - 0: default, 1: form"""
            confirm_view = ConfirmView(
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
