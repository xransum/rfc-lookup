"""Tests for utilities module."""
from rfc_lookup.utilities import (
    clean_chars,
    extract_authors,
    get_request,
    search_rfc_editor,
    get_latest_report_ids,
    get_rfc_report,
)


def test_clean_chars_valid() -> None:
    """Test function with the char."""
    assert clean_chars("ab\xa0c") == "ab c"


def test_clean_chars_invalid() -> None:
    """Test function without the char."""
    assert clean_chars("abc") == "abc"


def test_extract_authors() -> None:
    """Test the author extraction from string."""
    assert extract_authors("C. Krasic, M. Bishop, A. Frindell, Ed.") == ['C. Krasic', 'M. Bishop', 'A. Frindell, Ed.']

