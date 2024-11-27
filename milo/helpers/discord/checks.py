from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from discord import Message


def is_reply_to_message(message: Message, reply_message: Message) -> bool:
    """
    Check if the message is a reply to another message.

    Args:
        message: Message
        reply_message: Message

    Returns:
        bool
    """
    if message.reference.message_id == reply_message.id:
        return True
    return False
