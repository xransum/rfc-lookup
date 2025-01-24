"""Tests for constants module."""

import re

from rfc_lookup.constants import ALLOWED_SCHEMES, DEFAULT_HEADERS, USER_AGENT


def test_user_agent() -> None:
    """Test for calid format of user agent."""
    assert (
        re.findall(r"[a-zA-Z]{3,}\/\d*\.?\d* \((.|[\s])+\)", USER_AGENT)
        is not None
    )


def test_default_headers() -> None:
    """Test header for valid keys and values."""
    for key, value in DEFAULT_HEADERS.items():
        assert issubclass(type(key), str) is True
        assert issubclass(type(value), str) is True


def test_default_headers_user_agent() -> None:
    """Test header for the user agent."""
    assert DEFAULT_HEADERS.get("User-Agent") == USER_AGENT


def test_allowed_scheme() -> None:
    """Test for allowed schemas."""
    assert issubclass(type(ALLOWED_SCHEMES), set) is True
    assert len(ALLOWED_SCHEMES) > 0


def test_allowed_scheme_invalid() -> None:
    """Test invalid schema."""
    assert ("file" in ALLOWED_SCHEMES) is False
