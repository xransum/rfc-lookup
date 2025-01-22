"""Test file for rfc-lookup package."""

import pytest


def test_import() -> None:
    """Test package import."""
    try:
        import rfc_lookup  # noqa: F401
    except ImportError:
        pytest.fail("Package import failed")
