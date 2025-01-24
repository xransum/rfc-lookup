"""Command-line interface."""

import click
from rfc_lookup.utilities import get_rfc_report, search_rfc_editor
from rfc_lookup.errors import InvalidRfcId


@click.group()
def cmd():
    """Command line interface for the RFC lookup tool."""


@click.command(name="get")
@click.argument("id", type=int)
@click.option("--url", is_flag=True, help="Show the URL for the RFC.")
def rfc_get(id, url) -> None:
    """Show details for given RFC numbers."""
    try:
        report = get_rfc_report(id)
        if url:
            click.echo(f"URL: https://www.rfc-editor.org/rfc/rfc{id}.html")
        else:
            click.echo(report)
            
    except InvalidRfcId as err:
        click.echo(err, err=True)

@click.command(name="search")
@click.argument("value")
def rfc_search(value):
    """Search for RFCs by title."""
    results = search_rfc_editor(value)
    
    click.echo(f"Search '{value}' with {len(results)} results.")
    for result in results:
        line = f"{result['id']}: {result['title']}"
        click.echo(line)


# Add subcommands to the main command
cmd.add_command(rfc_get)
cmd.add_command(rfc_search)


def main() -> None:
    """Main entry point for the CLI."""
    cmd()


if __name__ == "__main__":
    main()  # pragma: no cover
