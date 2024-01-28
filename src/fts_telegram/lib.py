import os
from dataclasses import asdict
from dataclasses import dataclass
from datetime import datetime
from functools import cache
from functools import wraps

import maya
from telethon import TelegramClient
from telethon.tl.custom import Dialog
from telethon.tl.custom import Message


@cache
def telegram_client() -> TelegramClient:
    """Return a TelegramClient instance.

    Use your own values from https://my.telegram.org/apps.
    """
    return TelegramClient("fts-telegram", int(os.environ["TELEGRAM_API_ID"]), os.environ["TELEGRAM_API_HASH"])


def login_with_phone_password(func):
    """Login with phone and password."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        if telegram_client().loop.is_running():
            return func(*args, **kwargs)

        telegram_client().start(lambda: os.environ["TELEGRAM_PHONE"], lambda: os.environ["TELEGRAM_PASSWORD"])
        return telegram_client().loop.run_until_complete(func(*args, **kwargs))

    return wrapper


@login_with_phone_password
async def fetch_chats(partial_names: list[str]) -> list[Dialog]:
    """List chats by partial name (case-insensitive)."""
    dialogs = []
    async for dialog in telegram_client().iter_dialogs():
        for name in partial_names:
            if name.casefold() in dialog.name.casefold():
                dialogs.append(dialog)
    return dialogs


@dataclass(kw_only=True)
class MessageSchema:
    """[Message](https://schema.org/Message)."""

    identifier: str
    text: str
    sender: str
    dateSent: datetime


@login_with_phone_password
async def fetch_messages(
    limit: int | None,
    start_date: str | None,
    chat_names: list[str],
) -> dict:
    """Fetch message history from multiple chats, as JSON.

    If both limit and start date are empty, set limit to 10.

    https://docs.telethon.dev/en/latest/modules/client.html#telethon.client.messages.MessageMethods.iter_messages
    """
    meta = {"start_date": start_date, "chat_names": chat_names}
    if start_date:
        parsed_date = maya.when(start_date).date
        meta["parsed_date"] = parsed_date.isoformat()
        reverse = True
    else:
        parsed_date = None
        reverse = False
        if not limit:
            limit = 10
    meta["limit"] = str(limit)

    senders = {}
    messages = []
    for chat in await fetch_chats(chat_names):  # type: Dialog
        async for msg in telegram_client().iter_messages(
            chat.id,
            limit=limit,
            reverse=reverse,
            offset_date=parsed_date,
        ):
            assert isinstance(msg, Message)

            if msg.sender_id not in senders:
                entity = await telegram_client().get_entity(msg.sender_id)
                senders[msg.sender_id] = (
                    entity.title if hasattr(entity, "title") else f"{entity.first_name} {entity.last_name}"
                )

            ms = MessageSchema(
                identifier=str(msg.id),
                text=msg.message,
                sender=senders[msg.sender_id],
                dateSent=msg.date,
            )
            messages.append(asdict(ms))
    return {
        "meta": meta,
        "data": messages if reverse else list(reversed(messages)),
    }
