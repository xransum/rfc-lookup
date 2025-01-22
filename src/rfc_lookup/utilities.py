"""Module for package utility functions."""

import sys
import urllib.error
from typing import Any, Dict, Optional
from urllib.request import urlopen

from rfc_lookup.constants import RFC_INDEX_URL


def is_virt_env() -> bool:
    """Get if execution within a virtual env."""
    return sys.prefix != sys.base_prefix


def download_file(url: str) -> Optional[bytes]:
    """Download and return the content of a file from a URL."""
    try:
        with urlopen(url, timeout=10) as response:
            # Read the response as bytes
            content: bytes = response.read()
            return content
    except (urllib.error.URLError, urllib.error.HTTPError) as e:
        print(f"An error occurred: {e}")
        return None


def download_rfc_index() -> Optional[str]:
    """Download and return the text of the RFC index."""
    content: Optional[bytes] = download_file(RFC_INDEX_URL)
    if content is not None:
        return content.decode("utf-8")
    return None


def download_rfc_latest() -> Optional[str]:
    """Download and return the text of the latest RFC index."""
    content: Optional[bytes] = download_file(RFC_INDEX_URL)
    if content is not None:
        return content.decode("utf-8")
    return None
