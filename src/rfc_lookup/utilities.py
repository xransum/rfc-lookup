"""Module for package utility functions."""

import re
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup

from rfc_lookup.constants import ALLOWED_SCHEMES, DEFAULT_HEADERS
from rfc_lookup.errors import InvalidRfcIdError


def clean_chars(text: str) -> str:
    """Clean up special characters."""
    return text.replace("\xa0", " ")


def extract_authors(line):
    """Splits a line of author data into individual authors.

    Keeps 'Ed.' attached to the corresponding name.

    Args:
        line (str): A single line of author data.

    Returns:
        list: A list of individual authors.
    """
    # Split by commas
    parts = [part.strip() for part in line.split(",")]
    authors = []

    # Combine "Ed." with the preceding name
    for i, part in enumerate(parts):
        if "Ed." in part and i > 0:
            authors[-1] += f", {part}"  # Attach "Ed." to the previous author
        else:
            authors.append(part)

    return authors


def get_request(
    url: str,
    params: Optional[Dict[str, Any]] = None,
) -> bytes:
    """Get the content of a web page."""
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

    # Create the request
    headers = DEFAULT_HEADERS
    req = urllib.request.Request(full_url, headers=headers)
    # with urllib.request.urlopen(req) as res:
    #     return res.read()
    return urllib.request.urlopen(req).read()


def search_rfc_editor(value: str) -> List[Dict[str, Any]]:
    """Search the RFC editor for RFCs by title."""
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
    results = []

    if table is None:
        return results

    rows = table.find_all("tr")[1:]
    for row in rows:
        cells = row.find_all("td")

        if len(cells) != 7:
            # There's a chance that the table column breaks for the report column
            print(f"Skipping row with {len(cells)} columns")
            continue

        report_anchor = cells[0].find("a")
        report_url = report_anchor.get("href")

        _id = int(clean_chars(report_anchor.text.strip()).split(" ")[1])
        results.append(
            {
                "id": _id,
                "link": report_url,
                "files": {
                    clean_chars(a.text.strip()): a.get("href")
                    for a in cells[1].find_all("a")
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
    """Get and parse the IETF latest reports."""
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
    """Get the RFC report for a given RFC ID."""
    latest_ids = get_latest_report_ids()
    latest_id = latest_ids[-1]

    if 0 >= report_id or report_id > latest_id:
        raise InvalidRfcIdError(
            f"Invalid RFC ID {report_id}, must be between 0 and {latest_id}"
        )

    url = f"https://www.rfc-editor.org/rfc/rfc{report_id}.txt"
    content = get_request(url).decode("utf-8")
    return content
