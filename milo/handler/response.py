from milo.handler.discord import ConfirmView, FormModal
from milo.handler.msg import (
    reply_to_interaction,
    reply_to_message,
)


def simple_response(f):
    """decorator: runs function and replies with dictionary return result
    as a table"""

    async def wrapper(class_obj, chat_choice):
        results = await f(class_obj)
        await reply_to_message(class_obj.message, chat_choice, results)

    return wrapper


def admin_privileges(f):
    """decorator: runs function only if user is admin"""

    async def wrapper(class_obj, chat_choice):
        if not class_obj.message.author.guild_permissions.administrator:
            await reply_to_message(class_obj.message, chat_choice, "not admin")
        else:
            return await f(class_obj, chat_choice)

    return wrapper


def confirm_decision_response(additional_process=None):
    """decorator: takes in function, lets user choose to continue or
    not. if the choice is continue, run function. if not, cancel operation."""
    """options: None, form"""

    def function_collector(f):
        async def wrapper(class_obj, chat_choice):
            confirm_view = ConfirmView(class_obj=class_obj)

            confirm_view.bot_message_obj = await reply_to_message(
                class_obj.message,
                chat_choice,
                "ask if they are sure if they want to continue with the task",
                confirm_view,
            )

            await confirm_view.wait()

            match confirm_view.exit_status:
                case "continued":
                    match additional_process:
                        # when case None, the supplied function runs directly
                        # without any additional processes being involved
                        case None:
                            results = await f(class_obj)
                        case "form":
                            form_modal = FormModal(
                                title="test", class_obj=class_obj
                            )

                            await confirm_view.interaction.response.send_modal(
                                form_modal
                            )
                            await form_modal.wait()

                            match form_modal.exit_status:
                                case "submitted":
                                    results = await f(
                                        class_obj, form_modal.results
                                    )
                                    await reply_to_interaction(
                                        form_modal.interaction,
                                        class_obj.message,
                                        chat_choice,
                                        results,
                                    )
                                case "error":
                                    await reply_to_interaction(
                                        form_modal.interaction,
                                        class_obj.message,
                                        chat_choice,
                                        results,
                                    )

                case _:
                    results = confirm_view.exit_status

            if not (
                confirm_view.exit_status == "continued"
                and additional_process == "form"
            ):
                confirm_view.bot_message_obj = await reply_to_interaction(
                    confirm_view.interaction,
                    class_obj.message,
                    chat_choice,
                    results,
                )

        return wrapper

    return function_collector
