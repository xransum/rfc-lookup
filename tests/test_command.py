"""Tests for Command Line functionality."""
import pytest
import unittest
from unittest.mock import patch

from click.testing import CliRunner

from rfc_lookup.command import cli


@pytest.fixture
def cli_runner():
    """Fixture to provide a Click CLI runner."""
    return CliRunner()


def test_cli_help(cli_runner):
    """Test the CLI help message."""
    result = cli_runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Usage: rfc [OPTIONS] COMMAND [ARGS]..." in result.output


def test_cli_version(cli_runner) -> None:
    """Test the CLI version message."""
    result = cli_runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert f"{cli.name}, version" in result.output

