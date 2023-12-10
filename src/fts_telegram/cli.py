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
import typer

from fts_telegram.lib import list_chats

app = typer.Typer(no_args_is_help=True)


@app.callback()
def fts_telegram() -> None:
    """Telegram crawler for Feats."""


@app.command()
def chats(names: list[str] = typer.Argument(None, help="Partial name of a chat"), verbose: bool = False) -> None:
    """List chats by partial name."""
    for chat in list_chats(names):
        if verbose:
            typer.echo(chat.stringify())
        else:
            typer.echo(f"{chat.name} (ID {chat.id})")
