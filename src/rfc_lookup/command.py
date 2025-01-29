"""Command-line interface."""

import click

from rfc_lookup import __version__
from rfc_lookup.errors import InvalidRfcIdError
from rfc_lookup.utilities import get_rfc_report, search_rfc_editor


@click.group(  # pragma: no cover
    name="rfc",
    invoke_without_command=True,
    no_args_is_help=True,
)
@click.pass_context
@click.option("-V", "--version", is_flag=True, help="Show the version number.")
def cli(ctx: click.Context, version: bool) -> None:
    """Command line interface for the RFC lookup tool."""
    if version is True:
        click.echo(f"{ctx.info_name}, version {__version__}")
        ctx.exit()


@click.command(name="get")  # pragma: no cover
@click.argument("id", type=int)
@click.option("--url", is_flag=True, help="Show the URL for the RFC.")
def rfc_get(id: int, url: bool) -> None:
    """Show details for given RFC numbers."""
    try:
        report = get_rfc_report(id)
        if url:
            click.echo(f"URL: https://www.rfc-editor.org/rfc/rfc{id}.html")
        else:
            click.echo(report)

    except InvalidRfcIdError as err:
        click.echo(err, err=True)
        exit(1)


@click.command(name="search")  # pragma: no cover
@click.argument("value")
def rfc_search(value: str) -> None:
    """Search for RFCs by title."""
    results = search_rfc_editor(value)

    click.echo(f"Search {value!r} with {len(results)} results.")
    for result in results:
        line = f"{result['id']}: {result['title']}"
        click.echo(line)


# Add subcommands to the main command
cli.add_command(rfc_get)
cli.add_command(rfc_search)


def main() -> None:
    """Main entry point for the CLI."""
    cli()  # pragma: no cover


if __name__ == "__main__":
    main()  # pragma: no cover
