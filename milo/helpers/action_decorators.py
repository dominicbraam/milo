from __future__ import annotations
from typing import TYPE_CHECKING
from milo.handler.responder import Responder
from milo.helpers.discord.ui import ConfirmView, FormModal

if TYPE_CHECKING:
    from openai.types.chat.chat_completion import Choice


def no_response(f):
    """
    Decorator: runs function without responding unless there is an error.

    Args:
        f ()
            function using the decorator
    """

    async def wrapper(class_obj: type, chat_choice: Choice) -> None:
        """
        Inner function for no_response decorator. Runs function and replies
        to message if and only if there is an error.

        Args:
            class_obj: type
                The methods being called are from within a class so a class
                object is needed. It is the same as calling the
                function using self.f()
            chat_choice: Choice
        """
        error = await f(class_obj)

        if error:
            responder = Responder(class_obj.llm_handler, chat_choice, error)
            await responder.reply_to_message(class_obj.message)

    return wrapper


def simple_response(f):
    """
    Decorator: runs function and uses llm to handle result formatting.

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
        responder = Responder(class_obj.llm_handler, chat_choice, results)
        await responder.reply_to_message(class_obj.message)

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
            responder = Responder(
                class_obj.llm_handler,
                chat_choice,
                "not_admin",
            )
            await responder.reply_to_message(class_obj.message)
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

            responder = Responder(
                class_obj.llm_handler,
                chat_choice,
                "ask if they are sure if they want to continue with the task",
                confirm_view,
            )
            confirm_view.bot_message_obj = await responder.reply_to_message(
                class_obj.message
            )

            await confirm_view.wait()

            match confirm_view.exit_status:
                case "continued":
                    match additional_process:
                        case "form":
                            form_modal = FormModal(
                                title="test", class_obj=class_obj
                            )  # TODO: find a way to create title dynamically

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

            responder = Responder(
                class_obj.llm_handler,
                chat_choice,
                results,
            )
            # only reply if there is an interaction from user
            if confirm_view.interaction is not None:
                if (
                    confirm_view.exit_status == "continued"
                    and additional_process == "form"
                ):
                    # reply using form interaction if and only if
                    # the user continued
                    await responder.reply_to_interaction(
                        form_modal.interaction
                    )
                else:
                    # reply directly to confirm view message for
                    # everything else
                    await responder.reply_to_interaction(
                        confirm_view.interaction
                    )

        return wrapper

    return function_collector
