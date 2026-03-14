"""Module for package utility functions."""

import logging
import re
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional, cast

from bs4 import BeautifulSoup, Tag

from rfc_lookup.constants import ALLOWED_SCHEMES, DEFAULT_HEADERS
from rfc_lookup.errors import InvalidRfcIdError, NetworkError


logger = logging.getLogger(__name__)


def clean_chars(text: str) -> str:
    """Clean up special characters in a string.

    Args:
        text (str): The input string to clean.

    Returns:
        str: The cleaned string with non-breaking spaces replaced.
    """
    return text.replace("\xa0", " ")


def extract_authors(line: str) -> List[str]:
    """Split a line of author data into individual authors.

    Keeps 'Ed.' attached to the corresponding name.

    Args:
        line (str): A single line of author data.

    Returns:
        list: A list of individual authors.
    """
    # Split by commas
    parts = [part.strip() for part in line.split(",")]
    authors: List[str] = []

    # Combine "Ed." with the preceding name
    for i, part in enumerate(parts):
        if "Ed." in part and i > 0:
            authors[-1] += f", {part}"  # Attach "Ed." to the previous author
        else:
            authors.append(part)

    return authors


def get_request(
    url: str,
    params: Optional[Dict[str, str]] = None,
) -> bytes:
    """Get the content of a web page.

    Args:
        url (str): The URL to request.
        params (dict, optional): Query parameters to append to the URL.

    Returns:
        bytes: The raw response body.

    Raises:
        ValueError: If the URL is empty or uses a disallowed scheme.
        NetworkError: If the request fails due to a network or HTTP error.
    """
    if not url:
        raise ValueError("URL cannot be empty.")

    # Construct the full URL with query parameters
    full_url = url
    if params is not None:
        full_url = f"{url}?{urllib.parse.urlencode(params)}"

    # Parse the URL to validate the scheme
    parsed = urllib.parse.urlparse(full_url)
    if parsed.scheme not in ALLOWED_SCHEMES:
        raise ValueError(
            f"Invalid URL scheme {parsed.scheme!r}. "
            f"Allowed schemes are: {', '.join(ALLOWED_SCHEMES)}"
        )

    # Create and execute the request
    headers = DEFAULT_HEADERS
    req = urllib.request.Request(full_url, headers=headers)
    try:
        return cast(bytes, urllib.request.urlopen(req).read())
    except (urllib.error.URLError, urllib.error.HTTPError) as exc:
        raise NetworkError(f"Request to {full_url!r} failed: {exc}") from exc


def search_rfc_editor(value: str) -> List[Dict[str, Any]]:
    """Search the RFC editor for RFCs by title.

    Args:
        value (str): The title or keyword to search for.

    Returns:
        list: A list of dicts, each representing a matching RFC with keys:
            id, link, files, title, authors, publication_date, more_info,
            status.
    """
    url = "https://www.rfc-editor.org/search/rfc_search_detail.php"
    params = {
        "title": value,
        "pubstatus[]": "Any",
        "pub_date_type": "any",
        "page": "All",
        "sortkey": "Number",
        "sorting": "ASC",
    }
    html = get_request(url, params).decode("utf-8")
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", class_="gridtable")
    results: List[Dict[str, Any]] = []

    if not isinstance(table, Tag):
        return results

    rows = table.find_all("tr")[1:]

    for row in rows:
        if not isinstance(row, Tag):  # pragma: no cover
            continue
        cells = row.find_all("td")

        if len(cells) != 7:
            # There's a chance that the table column breaks for the report column
            logger.debug("Skipping row with %d columns", len(cells))
            continue

        report_anchor = cells[0].find("a")
        if not isinstance(report_anchor, Tag):  # pragma: no cover
            continue
        report_url = report_anchor.get("href")

        _id = int(clean_chars(report_anchor.text.strip()).split(" ")[1])
        results.append(
            {
                "id": _id,
                "link": report_url,
                "files": {
                    clean_chars(a.text.strip()): a.get("href")
                    for a in cells[1].find_all("a")
                    if isinstance(a, Tag)
                },
                "title": clean_chars(cells[2].text.strip()),
                "authors": extract_authors(clean_chars(cells[3].text.strip())),
                "publication_date": clean_chars(cells[4].text.strip()),
                "more_info": clean_chars(cells[5].text.strip()),
                "status": clean_chars(cells[6].text.strip()).split(" (")[0],
            }
        )

    return results


def get_latest_report_ids() -> List[int]:
    """Get and parse the IETF latest reports.

    Returns:
        list: A sorted list of known RFC IDs as integers.
    """
    url = "https://www.ietf.org/rfc/rfc-index-latest.txt"
    content = get_request(url).decode("utf-8")

    report_ids = []
    for line in content.split("\n"):
        split = line.split(" ")
        if len(split) < 1:  # pragma: no cover
            # Skip empty lines
            continue

        c = split[0]
        if re.search(r"^[0-9]+$", c) is not None:
            report_ids.append(int(c))

    report_ids.sort()
    return report_ids


def get_rfc_report(report_id: int) -> str:
    """Get the RFC report for a given RFC ID.

    Args:
        report_id (int): The RFC number to retrieve.

    Returns:
        str: The plain-text content of the RFC document.

    Raises:
        InvalidRfcIdError: If report_id is out of the valid range.
    """
    latest_ids = get_latest_report_ids()
    latest_id = latest_ids[-1]

    if 0 >= report_id or report_id > latest_id:
        raise InvalidRfcIdError(
            f"Invalid RFC ID {report_id}, must be between 0 and {latest_id}"
        )

    url = f"https://www.rfc-editor.org/rfc/rfc{report_id}.txt"
    res: bytes = get_request(url)
    content: str = res.decode("utf-8")
    return content
