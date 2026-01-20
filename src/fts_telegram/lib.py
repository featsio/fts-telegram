from __future__ import annotations

import os
import re
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from datetime import UTC
from datetime import datetime
from functools import cache
from functools import wraps
from pathlib import Path
from typing import Any

import maya
from telethon import TelegramClient
from telethon.tl.custom import Dialog
from telethon.tl.custom import Message
from tzlocal import get_localzone_name


@cache
def telegram_client() -> TelegramClient:
    """Return a TelegramClient instance.

    Use your own values from https://my.telegram.org/apps.
    """
    return TelegramClient(
        str(Path.home() / "fts-telegram"), int(os.environ["TELEGRAM_API_ID"]), os.environ["TELEGRAM_API_HASH"]
    )


NOW = datetime.now(tz=UTC)
CURRENT_TZINFO = NOW.astimezone().tzinfo or UTC
# Get the IANA timezone name (e.g., 'America/Sao_Paulo') instead of the abbreviation (e.g., '-03')
CURRENT_TZNAME = get_localzone_name()
WORDS_REGEX = re.compile(r"[A-Za-z]+|[-\d:]+")


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
        # If no names are provided, show all chats
        if not partial_names:
            dialogs.append(dialog)
            continue

        for name in partial_names:
            if name.casefold() in dialog.name.casefold():
                dialogs.append(dialog)
    return dialogs


@dataclass(kw_only=True)
class ConversationSchema:
    """[Conversation - Schema.org Type](https://schema.org/Conversation)."""

    headline: str


@dataclass(kw_only=True)
class MessageSchema:
    """[Message](https://schema.org/Message)."""

    identifier: str
    text: str
    sender: str
    dateSent: datetime
    datePublished: datetime | None = None
    isPartOf: ConversationSchema
    url: str | None = None


@dataclass(kw_only=True)
class TelegramEntity:
    title: str
    username: str


def normalize_start_date(start_date: str) -> str:
    """Normalize the start date.

    1. split characters and numbers into words
    2. add missing colon in the time
    3. add 00:00 if no time is provided

    >>> normalize_start_date("1may1120")
    '1 may 11:20'

    >>> normalize_start_date("today1032")
    'today 10:32'

    >>> normalize_start_date("2024-05-01")
    '2024-05-01 00:00'

    >>> normalize_start_date("2024-02-02 930")
    '2024-02-02 09:30'

    >>> normalize_start_date("2 Apr 134")
    '2 Apr 01:34'
    """
    words = []
    for word in WORDS_REGEX.findall(start_date):  # type: str
        if word.isdigit() and len(word) >= 3:
            padded_number = f"{word:0>4}"
            words.append(padded_number[:2] + ":" + padded_number[2:])
        else:
            words.append(word)

    if len(words) == 1 and ":" not in words[0]:
        words.append("00:00")

    return " ".join(words)


@login_with_phone_password
async def fetch_messages(
    limit: int | None,
    start_date: str | None,
    chat_names: list[str],
    saved: bool = False,
) -> tuple[dict, list[MessageSchema]]:
    """Fetch message history from multiple chats.

    If both limit and start date are empty, set limit to 10.

    If saved is True, fetches messages from the "Saved Messages" chat instead of the chats specified in chat_names.

    https://docs.telethon.dev/en/stable/modules/client.html#telethon.client.messages.MessageMethods.iter_messages
    """
    meta: dict[str, Any] = {"start_date": start_date, "chat_names": chat_names, "saved_messages": saved}
    if start_date:
        parsed_start_date = maya.when(normalize_start_date(start_date), timezone=CURRENT_TZNAME).datetime()
        meta["parsed_start_date"] = parsed_start_date.isoformat()
        reverse = True
    else:
        parsed_start_date = None
        reverse = False
        if not limit:
            limit = 10
    meta["limit"] = limit
    meta["tz"] = CURRENT_TZNAME

    senders: dict[str, TelegramEntity] = {}
    messages = []

    async def generate_chat_id_name() -> AsyncGenerator[tuple[int | str, str], None]:
        if saved:
            yield "me", "Saved Messages"
            return
        for chat in await fetch_chats(chat_names):  # type: Dialog
            yield chat.id, chat.name

    # Fetch messages from specified chats
    async for chat_id, chat_name in generate_chat_id_name():
        conversation = ConversationSchema(headline=chat_name)
        async for msg in telegram_client().iter_messages(
            chat_id,
            limit=limit,
            reverse=reverse,
            offset_date=parsed_start_date,
        ):
            assert isinstance(msg, Message)

            if msg.forward and msg.forward.from_id:
                sender_or_channel_id = (
                    msg.forward.from_id.channel_id if msg.forward.is_channel else msg.forward.from_id.user_id
                )
            else:
                sender_or_channel_id = msg.sender_id

            if sender_or_channel_id not in senders:
                entity = await telegram_client().get_entity(sender_or_channel_id)
                sender = TelegramEntity(
                    title=(
                        entity.title
                        if hasattr(entity, "title")
                        else f"{entity.first_name or ''} {entity.last_name or ''}".strip()
                    ),
                    username=entity.username,
                )
                senders[sender_or_channel_id] = sender
            else:
                sender = senders[sender_or_channel_id]

            identifier = str(msg.id)

            url = None
            if msg.forward:
                unique_id = msg.forward.channel_post
                if unique_id:
                    url = f"https://t.me/{sender.username}/{unique_id}"
                    identifier = unique_id

            text = msg.text
            if preview := msg.web_preview:
                text += f"\n{preview.site_name}: {preview.title}\n{preview.description}"

            ms = MessageSchema(
                identifier=identifier,
                text=text,
                sender=sender.title,
                dateSent=msg.date,
                isPartOf=conversation,
                datePublished=msg.forward.date if msg.forward else None,
                url=url,
            )

            # TODO: get other fields from the message
            # extra = ""
            # saved_from_peer = msg.fwd_from.saved_from_peer if msg.fwd_from else None
            # if saved_from_peer and saved_from_peer != from_id:
            #     channel = await CLIENT.get_entity(saved_from_peer)
            #     extra = f" (saved on {channel.title})"

            messages.append(ms)
    meta["count"] = len(messages)
    return meta, messages if reverse else list(reversed(messages))
