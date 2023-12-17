from typer.testing import CliRunner

from fts_telegram.cli import app


def test_main():
    runner = CliRunner()
    result = runner.invoke(app, [])

    assert result.output == "()\n"
    assert result.exit_code == 0
