"""
Module that contains the command line app.

Why does this file exist, and why not put this in __main__?

  You might be tempted to import things from __main__ later, but that will cause
  problems: the code will get executed twice:

  - When you run `python -mfts_telegram` python will execute
    ``__main__.py`` as a script. That means there will not be any
    ``fts_telegram.__main__`` in ``sys.modules``.
  - When you import __main__ it will get executed again (as a module) because
    there"s no ``fts_telegram.__main__`` in ``sys.modules``.

  Also see (1) from http://click.pocoo.org/5/setuptools/#setuptools-integration
"""

from __future__ import annotations

from dataclasses import asdict

import typer
from orjson import OPT_OMIT_MICROSECONDS
from orjson import OPT_SORT_KEYS
from orjson import dumps

from fts_telegram.lib import dump_as_logseq_markdown
from fts_telegram.lib import fetch_chats
from fts_telegram.lib import fetch_messages

app = typer.Typer(no_args_is_help=True)


@app.callback()
def fts_telegram() -> None:
    """Telegram crawler for Feats."""


@app.command()
def chats(
    verbose: bool = False,
    names: list[str] = typer.Argument(None, help="Partial name of a chat"),
) -> None:
    """List chats by partial name."""
    for chat in fetch_chats(names):
        if verbose:
            typer.echo(chat.stringify())
        else:
            # TODO: return JSON following some schema.org
            typer.echo(f"{chat.name} (ID {chat.id})")


@app.command()
def messages(
    limit: int = typer.Option(
        None,
        "--limit",
        "-l",
        help="Limit the number of messages to return. If not provided, defaults to 10 if no date is provided either.",
    ),
    start_date: str = typer.Option(
        None,
        "--start-date",
        "-s",
        help="Start date in YYYY-MM-DD format or English (today, yesterday...). If not provided, defaults to now.",
    ),
    markdown: bool = typer.Option(False, "--markdown", "-m", help="Format output as Logseq Markdown"),
    saved: bool = typer.Option(False, "--saved", help="Read messages from 'Saved Messages' chat"),
    collapsed: bool = typer.Option(False, "--collapsed", help="Collapse messages in Logseq Markdown output"),
    chat_names: list[str] = typer.Argument(None, help="Partial name of a chat"),
) -> None:
    """List messages of multiple chats, as JSON."""
    if not chat_names and not saved:
        typer.echo("You must specify at least one chat or --saved.")
        raise typer.Abort

    meta, message_list = fetch_messages(limit, start_date, chat_names, saved)
    if markdown:
        dump_as_logseq_markdown(message_list, collapsed)
        return

    json_dict = {"meta": meta, "data": [asdict(msg) for msg in message_list]}
    typer.echo(dumps(json_dict, option=OPT_SORT_KEYS | OPT_OMIT_MICROSECONDS))
