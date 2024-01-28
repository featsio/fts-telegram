from typer.testing import CliRunner

from fts_telegram.cli import app


def test_main():
    runner = CliRunner()
    result = runner.invoke(app, [])

    assert "Telegram crawler for Feats" in result.output
    assert result.exit_code == 0
