from typer.testing import CliRunner

from pytrydan.cli import app

runner = CliRunner()


def test_help():
    """The help message includes the CLI name."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Set KeyWord value in Trydan." in result.stdout
    assert "Retrieve Trydan Status." in result.stdout
