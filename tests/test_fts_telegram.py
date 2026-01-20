from typer.testing import CliRunner

from fts_telegram.cli import app


def test_main():
    runner = CliRunner()
    result = runner.invoke(app, [])

    assert "Telegram crawler for Feats" in result.output
    # Exit code 2 is expected when no_args_is_help=True and no arguments are provided
    assert result.exit_code == 2
