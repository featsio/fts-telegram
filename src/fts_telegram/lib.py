from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import UTC
from datetime import date
from datetime import datetime
from functools import cache
from functools import wraps
from typing import Any

import maya
import typer
from telethon import TelegramClient
from telethon.tl.custom import Dialog
from telethon.tl.custom import Message


@cache
def telegram_client() -> TelegramClient:
    """Return a TelegramClient instance.

    Use your own values from https://my.telegram.org/apps.
    """
    return TelegramClient("fts-telegram", int(os.environ["TELEGRAM_API_ID"]), os.environ["TELEGRAM_API_HASH"])


NOW = datetime.now(tz=UTC)
CURRENT_TZINFO = NOW.astimezone().tzinfo or UTC
CURRENT_TZNAME = CURRENT_TZINFO.tzname(NOW)
LOGSEQ_TIME_FORMAT = "**%H:%M**"
LOGSEQ_DATE_FORMAT = "%A, %d.%m.%Y"


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
    isPartOf: ConversationSchema


@login_with_phone_password
async def fetch_messages(
    limit: int | None,
    start_date: str | None,
    chat_names: list[str],
) -> tuple[dict, list[MessageSchema]]:
    """Fetch message history from multiple chats.

    If both limit and start date are empty, set limit to 10.

    https://docs.telethon.dev/en/latest/modules/client.html#telethon.client.messages.MessageMethods.iter_messages
    """
    meta: dict[str, Any] = {"start_date": start_date, "chat_names": chat_names}
    if start_date:
        parsed_start_date = maya.when(start_date, timezone=CURRENT_TZNAME).datetime()
        meta["parsed_start_date"] = parsed_start_date.isoformat()
        reverse = True
    else:
        parsed_start_date = None
        reverse = False
        if not limit:
            limit = 10
    meta["limit"] = limit
    meta["tz"] = CURRENT_TZNAME

    senders = {}
    messages = []
    for chat in await fetch_chats(chat_names):  # type: Dialog
        conversation = ConversationSchema(headline=chat.name)
        async for msg in telegram_client().iter_messages(
            chat.id,
            limit=limit,
            reverse=reverse,
            offset_date=parsed_start_date,
        ):
            assert isinstance(msg, Message)

            if msg.sender_id not in senders:
                entity = await telegram_client().get_entity(msg.sender_id)
                senders[msg.sender_id] = (
                    entity.title
                    if hasattr(entity, "title")
                    else f"{entity.first_name or ''} {entity.last_name or ''}".strip()
                )

            ms = MessageSchema(
                identifier=str(msg.id),
                text=msg.message,
                sender=senders[msg.sender_id],
                dateSent=msg.date,
                isPartOf=conversation,
            )

            # TODO: get other fields from the message
            # url = ""
            # from_id = msg.fwd_from.from_id if msg.fwd_from else None
            # if from_id:
            #     msg_id = msg.fwd_from.channel_post
            #
            #     channel = await CLIENT.get_entity(from_id)
            #     url = f"https://t.me/{channel.username}/{msg_id}"
            #
            # extra = ""
            # saved_from_peer = msg.fwd_from.saved_from_peer if msg.fwd_from else None
            # if saved_from_peer and saved_from_peer != from_id:
            #     channel = await CLIENT.get_entity(saved_from_peer)
            #     extra = f" (saved on {channel.title})"

            messages.append(ms)
    meta["count"] = len(messages)
    return meta, messages if reverse else list(reversed(messages))


def dump_as_logseq_markdown(message_list: list[MessageSchema]) -> None:
    """Dump messages to stdout as Logseq Markdown."""

    @cache
    def local_date(dt: datetime) -> date:
        return dt.astimezone(CURRENT_TZINFO).date()

    @cache
    def local_time(dt: datetime) -> str:
        return dt.astimezone(CURRENT_TZINFO).strftime(LOGSEQ_TIME_FORMAT)

    generator = (m for m in message_list)
    msg = next(generator, None)
    while msg:
        current_date = local_date(msg.dateSent)
        typer.echo(
            f"- {local_time(msg.dateSent)}"
            f" [[{current_date.strftime(LOGSEQ_DATE_FORMAT)}]]"
            f" Telegram: {msg.isPartOf.headline}"
        )
        while msg and current_date == local_date(msg.dateSent):
            current_sender = msg.sender
            print_sender = f"*{current_sender}*: "

            while msg and current_date == local_date(msg.dateSent) and current_sender == msg.sender:
                current_time = local_time(msg.dateSent)
                typer.echo(f"  - {current_time} {print_sender}", nl=False)

                # The same person can send multiple messages in a row, so we print the sender only when it changes
                print_sender = ""

                while (
                    msg
                    and current_date == local_date(msg.dateSent)
                    and current_sender == msg.sender
                    and current_time == local_time(msg.dateSent)
                ):
                    typer.echo(msg.text)
                    msg = next(generator, None)
