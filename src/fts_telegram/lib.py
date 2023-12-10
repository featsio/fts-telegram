import os
from functools import wraps

from telethon import TelegramClient
from telethon.tl.custom import Dialog

# Use your own values from https://my.telegram.org/apps
CLIENT = TelegramClient("fts-telegram", int(os.environ["TELEGRAM_API_ID"]), os.environ["TELEGRAM_API_HASH"])


def login_with_phone_password(func):
    """Login with phone and password."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        CLIENT.start(lambda: os.environ["TELEGRAM_PHONE"], lambda: os.environ["TELEGRAM_PASSWORD"])
        return CLIENT.loop.run_until_complete(func(*args, **kwargs))

    return wrapper


@login_with_phone_password
async def list_chats(partial_names: list[str]) -> list[Dialog]:
    """List chats by partial name (case-insensitive)."""
    dialogs = []
    async for dialog in CLIENT.iter_dialogs():
        for name in partial_names:
            if name.casefold() in dialog.name.casefold():
                dialogs.append(dialog)
    return dialogs
