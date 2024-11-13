from openai.types.chat.chat_completion import Choice
from milo.handler.discord import ConfirmView, FormModal
from milo.handler.msg import (
    reply_to_interaction,
    reply_to_message,
)


def simple_response(f):
    """
    Decorator: runs function and uses llm to format handle result formatting.

    Args:
        f ()
            function using the decorator
    """

    async def wrapper(class_obj: type, chat_choice: Choice) -> None:
        """
        Inner function for simple_response decorator. Runs function and replies
        to message.

        Args:
            class_obj: type
                The methods being called are from within a class so a class
                object is needed. It is the same as calling the
                function using self.f()
            chat_choice: Choice
        """
        results = await f(class_obj)
        await reply_to_message(class_obj.message, chat_choice, results)

    return wrapper


def admin_privileges(f):
    """
    Decorator: runs function only if user is admin

    Args:
        f ()
            function using the decorator
    """

    async def wrapper(class_obj: type, chat_choice: Choice) -> None:
        """
        Inner function for admin_privileges decorator. Runs function if the
        user has admin privileges; replies with relevant message if not admin.

        Args:
            class_obj: type
                The methods being called are from within a class so a class
                object is needed. It is the same as calling the
                function using self.f()
            chat_choice: Choice
        """
        if not class_obj.message.author.guild_permissions.administrator:
            await reply_to_message(class_obj.message, chat_choice, "not admin")
        else:
            await f(class_obj, chat_choice)

    return wrapper


def confirm_decision_response(additional_process=None):
    """
    Decorator: Prompts the user to confirm if they would like to continue with
    the task. If yes, continue and if no, exit. The function can create an
    additional interaction for the user if necessary.

    Args:
        additional_process: Union[str, None]
            options: "form", None
    """

    def function_collector(f):
        async def wrapper(class_obj: type, chat_choice: Choice):
            """
            Inner function to handle the views. First the confirm view and then
            another view if specified.

            Args:
                class_obj: type
                    The methods being called are from within a class so a class
                    object is needed. It is the same as calling the
                    function using self.f()
                chat_choice: Choice
            """
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
                                case "error":
                                    results = form_modal.exit_status
                        case _:
                            results = await f(class_obj)

                case _:
                    results = confirm_view.exit_status

            if confirm_view.interaction is not None:
                if (
                    confirm_view.exit_status == "continued"
                    and additional_process == "form"
                ):
                    await reply_to_interaction(
                        form_modal.interaction,
                        class_obj.message,
                        chat_choice,
                        results,
                    )
                else:
                    await reply_to_interaction(
                        confirm_view.interaction,
                        class_obj.message,
                        chat_choice,
                        results,
                    )

        return wrapper

    return function_collector
