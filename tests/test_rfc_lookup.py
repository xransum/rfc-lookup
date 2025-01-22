"""Test file for rfc-lookup package."""

import pytest

def test_import():
    try:
        import rfc_lookup
    except ImportError:
        pytest.fail("Package import failed")
