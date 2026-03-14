"""Command-line interface."""

import webbrowser

import click

from rfc_lookup import __version__
from rfc_lookup.errors import InvalidRfcIdError, NetworkError
from rfc_lookup.utilities import (
    get_latest_report_ids,
    get_rfc_report,
    search_rfc_editor,
)


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
@click.option(
    "-o",
    "--output",
    type=click.Path(),
    default=None,
    help="Write RFC content to a file instead of stdout.",
)
def rfc_get(id: int, url: bool, output: str) -> None:
    """Show details for given RFC numbers."""
    try:
        report = get_rfc_report(id)
        if url:
            click.echo(f"https://www.rfc-editor.org/rfc/rfc{id}.html")
        elif output:
            with open(output, "w", encoding="utf-8") as f:
                f.write(report)
            click.echo(f"RFC {id} saved to {output}")
        else:
            click.echo(report)

    except InvalidRfcIdError as err:
        click.echo(err, err=True)
        raise SystemExit(1)
    except NetworkError as err:
        click.echo(f"Network error: {err}", err=True)
        raise SystemExit(1)


@click.command(name="search")  # pragma: no cover
@click.argument("value")
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    help="Show authors, status, and publication date.",
)
def rfc_search(value: str, verbose: bool) -> None:
    """Search for RFCs by title."""
    try:
        results = search_rfc_editor(value)
    except NetworkError as err:
        click.echo(f"Network error: {err}", err=True)
        raise SystemExit(1)

    click.echo(f"Search {value!r} with {len(results)} results.")
    for result in results:
        line = f"{result['id']}: {result['title']}"
        if verbose:
            authors = ", ".join(result["authors"])
            line += (
                f"\n  Authors: {authors}"
                f"\n  Status: {result['status']}"
                f"\n  Published: {result['publication_date']}"
            )
        click.echo(line)


@click.command(name="open")  # pragma: no cover
@click.argument("id", type=int)
@click.option(
    "--text",
    is_flag=True,
    help="Display the plain-text RFC in the terminal pager instead of"
    " opening a browser.",
)
def rfc_open(id: int, text: bool) -> None:
    """Open an RFC in the browser or view it as plain text in the terminal."""
    try:
        latest_ids = get_latest_report_ids()
    except NetworkError as err:
        click.echo(f"Network error: {err}", err=True)
        raise SystemExit(1)

    latest_id = latest_ids[-1]
    if 0 >= id or id > latest_id:
        click.echo(
            f"Invalid RFC ID {id}, must be between 0 and {latest_id}",
            err=True,
        )
        raise SystemExit(1)

    if text:
        try:
            content = get_rfc_report(id)
        except NetworkError as err:
            click.echo(f"Network error: {err}", err=True)
            raise SystemExit(1)
        click.echo_via_pager(content)
    else:
        url = f"https://www.rfc-editor.org/rfc/rfc{id}.html"
        webbrowser.open(url)


# Add subcommands to the main command
cli.add_command(rfc_get)
cli.add_command(rfc_search)
cli.add_command(rfc_open)


def main() -> None:
    """Main entry point for the CLI."""
    cli()  # pragma: no cover


if __name__ == "__main__":
    main()  # pragma: no cover
