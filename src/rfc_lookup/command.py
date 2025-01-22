"""Command-line interface."""

import click


@click.group()
def cmd() -> None:
    """Command line interface for the RFC lookup tool."""


def main() -> None:
    """Main entry point for the CLI."""
    cmd()


if __name__ == "__main__":
    main()  # pragma: no cover
