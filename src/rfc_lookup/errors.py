"""Exceptions for the rfc_lookup package."""


class InvalidRfcIdError(Exception):
    """Raised when an invalid RFC ID is provided."""

    pass


class NetworkError(Exception):
    """Raised when a network request fails."""

    pass
