"""Tests for Command Line functionality."""

from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from rfc_lookup.command import cli


@pytest.fixture
def cli_runner() -> CliRunner:
    """Fixture to provide a Click CLI runner."""
    return CliRunner()


mock_help = "Usage: rfc [OPTIONS] COMMAND [ARGS]..."


def test_cli_help(cli_runner: CliRunner) -> None:
    """Test the CLI help message."""
    result = cli_runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert mock_help in result.output


def test_cli_version(cli_runner: CliRunner) -> None:
    """Test the CLI version message."""
    result = cli_runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert f"{cli.name}, version" in result.output


def test_cli_no_cmd(cli_runner: CliRunner) -> None:
    """Test the CLI help message."""
    result = cli_runner.invoke(cli, [""])
    assert result.exit_code == 2
    assert mock_help in result.output


@patch("rfc_lookup.command.get_rfc_report")
def test_cli_rfc_get_report(
    mock_get_rfc_report: Mock, cli_runner: CliRunner
) -> None:
    """Test the CLI get report command."""
    mock_get_rfc_report.return_value = "RFC Report"
    result = cli_runner.invoke(cli, ["get", "1234"])
    assert result.exit_code == 0
    assert "RFC Report" in result.output


@patch("rfc_lookup.command.get_rfc_report")
def test_cli_rfc_get_report_url_only(
    mock_get_rfc_report: Mock, cli_runner: CliRunner
) -> None:
    """Test the CLI get report command with URL only."""
    mock_get_rfc_report.return_value = "RFC Report"
    result = cli_runner.invoke(cli, ["get", "1234", "--url"])
    assert result.exit_code == 0
    assert "https://www.rfc-editor.org/rfc/rfc1234" in result.output


@patch("rfc_lookup.utilities.get_latest_report_ids")
def test_cli_rfc_get_report_out_of_range(
    mock_get_latest_report_ids: Mock, cli_runner: CliRunner
) -> None:
    """Test the CLI get report command with an out of range RFC ID."""
    mock_latest_id = 500
    mock_report_id = 99999999
    mock_get_latest_report_ids.return_value = [mock_latest_id]
    result = cli_runner.invoke(cli, ["get", str(mock_report_id)])
    assert result.exit_code == 1
    assert (
        f"Invalid RFC ID {mock_report_id}, must be between 0 and "
        f"{mock_latest_id}"
    ) in result.output


def test_cli_rfc_get_invalid_id(cli_runner: CliRunner) -> None:
    """Test the CLI get report command with an invalid RFC ID."""
    mock_value = "abc"
    result = cli_runner.invoke(cli, ["get", mock_value])
    assert result.exit_code == 2
    assert (
        f"Error: Invalid value for 'ID': {mock_value!r} is not a valid integer"
        in result.output
    )


@patch("rfc_lookup.command.search_rfc_editor")
def test_cli_rfc_search(
    mock_search_rfc_editor: Mock, cli_runner: CliRunner
) -> None:
    """Test the CLI get report command."""
    mock_search_value = "1234"
    mock_search_results = [
        {"id": 1234, "title": "RFC Report 1"},
        {"id": 5678, "title": "RFC Report 2"},
    ]
    mock_search_rfc_editor.return_value = mock_search_results
    result = cli_runner.invoke(cli, ["search", mock_search_value])
    assert result.exit_code == 0
    assert (
        f"Search {mock_search_value!r} with {len(mock_search_results)} results."
        in result.output
    )
    assert (
        "\n".join(
            [
                f"{result['id']}: {result['title']}"
                for result in mock_search_results
            ]
        )
        in result.output
    )
