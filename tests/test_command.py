"""Tests for Command Line functionality."""

import os
from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from rfc_lookup.command import cli
from rfc_lookup.errors import NetworkError


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


# ---------------------------------------------------------------------------
# rfc get
# ---------------------------------------------------------------------------


@patch("rfc_lookup.command.get_rfc_report")
def test_cli_rfc_get_report(mock_get_rfc_report: Mock, cli_runner: CliRunner) -> None:
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


@patch("rfc_lookup.command.get_rfc_report")
def test_cli_rfc_get_report_output_file(
    mock_get_rfc_report: Mock, cli_runner: CliRunner, tmp_path: object
) -> None:
    """Test the CLI get command writes to a file with --output."""
    import tempfile

    mock_get_rfc_report.return_value = "RFC Content"
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as tmp:
        tmp_name = tmp.name

    try:
        result = cli_runner.invoke(cli, ["get", "1234", "--output", tmp_name])
        assert result.exit_code == 0
        assert f"RFC 1234 saved to {tmp_name}" in result.output
        with open(tmp_name, encoding="utf-8") as f:
            assert f.read() == "RFC Content"
    finally:
        os.unlink(tmp_name)


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
        f"Invalid RFC ID {mock_report_id}, must be between 0 and {mock_latest_id}"
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


@patch("rfc_lookup.command.get_rfc_report")
def test_cli_rfc_get_network_error(
    mock_get_rfc_report: Mock, cli_runner: CliRunner
) -> None:
    """Test the CLI get command handles NetworkError."""
    mock_get_rfc_report.side_effect = NetworkError("timeout")
    result = cli_runner.invoke(cli, ["get", "1234"])
    assert result.exit_code == 1
    assert "Network error" in result.output


# ---------------------------------------------------------------------------
# rfc search
# ---------------------------------------------------------------------------


@patch("rfc_lookup.command.search_rfc_editor")
def test_cli_rfc_search(mock_search_rfc_editor: Mock, cli_runner: CliRunner) -> None:
    """Test the CLI search command."""
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
        "\n".join([f"{r['id']}: {r['title']}" for r in mock_search_results])
        in result.output
    )


@patch("rfc_lookup.command.search_rfc_editor")
def test_cli_rfc_search_verbose(
    mock_search_rfc_editor: Mock, cli_runner: CliRunner
) -> None:
    """Test the CLI search command with --verbose flag."""
    mock_search_results = [
        {
            "id": 1234,
            "title": "RFC Report 1",
            "authors": ["A. Author", "B. Author"],
            "status": "Proposed Standard",
            "publication_date": "January 2000",
        }
    ]
    mock_search_rfc_editor.return_value = mock_search_results
    result = cli_runner.invoke(cli, ["search", "http", "--verbose"])
    assert result.exit_code == 0
    assert "A. Author, B. Author" in result.output
    assert "Proposed Standard" in result.output
    assert "January 2000" in result.output


@patch("rfc_lookup.command.search_rfc_editor")
def test_cli_rfc_search_network_error(
    mock_search_rfc_editor: Mock, cli_runner: CliRunner
) -> None:
    """Test the CLI search command handles NetworkError."""
    mock_search_rfc_editor.side_effect = NetworkError("timeout")
    result = cli_runner.invoke(cli, ["search", "http"])
    assert result.exit_code == 1
    assert "Network error" in result.output


# ---------------------------------------------------------------------------
# rfc open
# ---------------------------------------------------------------------------


@patch("rfc_lookup.command.webbrowser.open")
@patch("rfc_lookup.command.get_latest_report_ids")
def test_cli_rfc_open_browser(
    mock_get_latest_report_ids: Mock,
    mock_browser_open: Mock,
    cli_runner: CliRunner,
) -> None:
    """Test the CLI open command opens a URL in the browser."""
    mock_get_latest_report_ids.return_value = [9999]
    result = cli_runner.invoke(cli, ["open", "1234"])
    assert result.exit_code == 0
    mock_browser_open.assert_called_once_with(
        "https://www.rfc-editor.org/rfc/rfc1234.html"
    )


@patch("rfc_lookup.command.get_rfc_report")
@patch("rfc_lookup.command.get_latest_report_ids")
def test_cli_rfc_open_text(
    mock_get_latest_report_ids: Mock,
    mock_get_rfc_report: Mock,
    cli_runner: CliRunner,
) -> None:
    """Test the CLI open command shows plain text via pager."""
    mock_get_latest_report_ids.return_value = [9999]
    mock_get_rfc_report.return_value = "RFC plain text content"
    result = cli_runner.invoke(cli, ["open", "1234", "--text"])
    assert result.exit_code == 0
    assert "RFC plain text content" in result.output


@patch("rfc_lookup.command.get_latest_report_ids")
def test_cli_rfc_open_out_of_range(
    mock_get_latest_report_ids: Mock, cli_runner: CliRunner
) -> None:
    """Test the CLI open command with an out-of-range RFC ID."""
    mock_get_latest_report_ids.return_value = [500]
    result = cli_runner.invoke(cli, ["open", "99999"])
    assert result.exit_code == 1
    assert "Invalid RFC ID" in result.output


@patch("rfc_lookup.command.get_latest_report_ids")
def test_cli_rfc_open_network_error_ids(
    mock_get_latest_report_ids: Mock, cli_runner: CliRunner
) -> None:
    """Test the CLI open command handles NetworkError fetching IDs."""
    mock_get_latest_report_ids.side_effect = NetworkError("timeout")
    result = cli_runner.invoke(cli, ["open", "1234"])
    assert result.exit_code == 1
    assert "Network error" in result.output


@patch("rfc_lookup.command.get_rfc_report")
@patch("rfc_lookup.command.get_latest_report_ids")
def test_cli_rfc_open_text_network_error(
    mock_get_latest_report_ids: Mock,
    mock_get_rfc_report: Mock,
    cli_runner: CliRunner,
) -> None:
    """Test the CLI open --text command handles NetworkError fetching content."""
    mock_get_latest_report_ids.return_value = [9999]
    mock_get_rfc_report.side_effect = NetworkError("timeout")
    result = cli_runner.invoke(cli, ["open", "1234", "--text"])
    assert result.exit_code == 1
    assert "Network error" in result.output
