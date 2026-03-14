"""Tests for utilities module."""

import logging
import urllib.parse
from typing import Generator
from unittest.mock import Mock, patch

import pytest
from bs4 import BeautifulSoup, Tag

from rfc_lookup.constants import DEFAULT_HEADERS
from rfc_lookup.errors import InvalidRfcIdError, NetworkError
from rfc_lookup.utilities import (
    clean_chars,
    extract_authors,
    get_latest_report_ids,
    get_request,
    get_rfc_report,
    search_rfc_editor,
)


def test_clean_chars_valid() -> None:
    """Test function with the char."""
    assert clean_chars("ab\xa0c") == "ab c"


def test_clean_chars_invalid() -> None:
    """Test function without the char."""
    assert clean_chars("abc") == "abc"


def test_extract_authors() -> None:
    """Test the author extraction from string."""
    assert extract_authors("C. Krasic, M. Bishop, A. Frindell, Ed.") == [
        "C. Krasic",
        "M. Bishop",
        "A. Frindell, Ed.",
    ]


@pytest.fixture
def mock_request() -> Generator[Mock, None, None]:
    """Mock Request object."""
    with patch("rfc_lookup.utilities.urllib.request.Request") as mock:
        yield mock


@pytest.fixture
def mock_urlopen() -> Generator[Mock, None, None]:
    """Mock urlopen context manager."""
    with patch("rfc_lookup.utilities.urllib.request.urlopen") as mock:
        yield mock


def test_get_request(mock_request: Mock, mock_urlopen: Mock) -> None:
    """Test get_request."""
    mock_url = "http://127.0.0.1:80/"
    mock_result = b"Hello, World!"
    mock_read = Mock()
    mock_read.read.side_effect = [mock_result]
    mock_urlopen.return_value = mock_read
    result = get_request(mock_url)
    mock_request.assert_called_once_with(mock_url, headers=DEFAULT_HEADERS)
    assert result == mock_result


def test_get_request_with_params(
    mock_request: Mock, mock_urlopen: Mock
) -> None:
    """Test get_request with query parameters."""
    mock_url = "http://127.0.0.1:80/"
    mock_params = {"a": "1", "b": "2"}
    mock_full_url = f"{mock_url}?{urllib.parse.urlencode(mock_params)}"
    mock_result = b"Hello, World!"
    mock_read = Mock()
    mock_read.read.side_effect = [mock_result]
    mock_urlopen.return_value = mock_read
    result = get_request(mock_url, params=mock_params)
    mock_request.assert_called_once_with(mock_full_url, headers=DEFAULT_HEADERS)
    assert result == mock_result


def test_get_request_invalid_url() -> None:
    """Test get_request with an empty URL."""
    with pytest.raises(ValueError):
        get_request("")


def test_get_request_invalid_scheme() -> None:
    """Test get_request with a disallowed URL scheme."""
    with pytest.raises(ValueError):
        get_request("ssh:127.0.0.1")


def test_get_request_network_error(
    mock_request: Mock, mock_urlopen: Mock
) -> None:
    """Test get_request raises NetworkError on URLError."""
    import urllib.error

    mock_urlopen.side_effect = urllib.error.URLError("connection refused")
    with pytest.raises(NetworkError):
        get_request("http://127.0.0.1:80/")


@pytest.fixture
def mock_get_request() -> Generator[Mock, None, None]:
    """Mock get_request function."""
    with patch("rfc_lookup.utilities.get_request") as mock:
        yield mock


mock_valid_rfc_search = b"""<table class=\"gridtable\">
<tr></tr>
<tr>
<td><a href=\"#\">RFC 1</a></td>
<td><a href=\"#\">TXT</a><a href=\"#\">HTML</a></td>
<td>Title Here</td>
<td>John Doe</td>
<td>January 1</td>
<td>Lorem Ipsum</td>
<td>Proposed Standard (ABC)</td>
</tr>
</table>"""


def test_search_rfc_editor(mock_get_request: Mock) -> None:
    """Test requests for rfc editor."""
    mock_result = [
        {
            "id": 1,
            "link": "#",
            "files": {"TXT": "#", "HTML": "#"},
            "title": "Title Here",
            "authors": ["John Doe"],
            "publication_date": "January 1",
            "more_info": "Lorem Ipsum",
            "status": "Proposed Standard",
        }
    ]
    mock_get_request.return_value = mock_valid_rfc_search
    result = search_rfc_editor("Hello, World!")
    assert result == mock_result


def test_search_rfc_editor_empty(mock_get_request: Mock) -> None:
    """Test requests for empty rfc editor."""
    mock_get_request.return_value = b"Hello, World"
    result = search_rfc_editor("Hello, World!")
    assert result == []


def test_search_rfc_editor_no_anchor(mock_get_request: Mock) -> None:
    """Test search_rfc_editor skips rows where first cell has no anchor."""
    html = b"""<table class="gridtable">
<tr></tr>
<tr>
<td>RFC 1</td>
<td><a href="#">TXT</a></td>
<td>Title Here</td>
<td>John Doe</td>
<td>January 1</td>
<td>Lorem Ipsum</td>
<td>Proposed Standard</td>
</tr>
</table>"""
    mock_get_request.return_value = html
    result = search_rfc_editor("Hello, World!")
    assert result == []


def test_search_rfc_editor_invalid_cols(
    mock_get_request: Mock, caplog: pytest.LogCaptureFixture
) -> None:
    """Test requests for rfc editor with invalid cols logs a debug message."""
    # Mock result by nuking one of the td elements
    soup = BeautifulSoup(mock_valid_rfc_search, "html.parser")
    tr = soup.find_all("tr")[-1]
    assert isinstance(tr, Tag)
    td = tr.find("td")
    assert isinstance(td, Tag)
    td.replace_with("")

    mock_get_request.return_value = str(soup).encode("utf-8")
    with caplog.at_level(logging.DEBUG, logger="rfc_lookup.utilities"):
        result = search_rfc_editor("Hello, World!")
    assert result == []
    assert "Skipping row with" in caplog.text


mock_latest_reports = b"""
1234 Lorem ipsum dolor sit amet, consectetur adipiscing elit.
     Proin ultricies, erat volutpat aliquet lobortis, mi nulla
     euismod leo, non pulvinar turpis mauris a nisi.

abcd Lorem ipsum dolor sit amet, consectetur adipiscing elit.
     Proin ultricies, erat volutpat aliquet lobortis, mi nulla
     euismod leo, non pulvinar turpis mauris a nisi.
"""


def test_get_latest_report_ids(mock_get_request: Mock) -> None:
    """Test for fetching valid request ID's."""
    mock_get_request.return_value = mock_latest_reports
    result = get_latest_report_ids()
    assert result == [1234]


@pytest.fixture()
def mock_get_latest_report_ids() -> Generator[Mock, None, None]:
    """Mock get_latest_report_ids function."""
    with patch("rfc_lookup.utilities.get_latest_report_ids") as mock:
        yield mock


def test_get_rfc_report(
    mock_get_request: Mock, mock_get_latest_report_ids: Mock
) -> None:
    """Test fetching rfc report."""
    mock_get_latest_report_ids.return_value = [2]
    mock_get_request.return_value = b"Hello, World!"
    result = get_rfc_report(1)
    assert result == "Hello, World!"


def test_get_rfc_report_exception(mock_get_latest_report_ids: Mock) -> None:
    """Test get rfc report exception."""
    mock_get_latest_report_ids.side_effect = [[2]] * 2

    # Test with negative report ID
    with pytest.raises(InvalidRfcIdError):
        get_rfc_report(-1)

    # Test with overflow report ID
    with pytest.raises(InvalidRfcIdError):
        get_rfc_report(9999)
