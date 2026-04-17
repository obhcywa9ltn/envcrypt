"""CLI commands for label management."""
import click
from envcrypt.label import LabelError, add_label, remove_label, get_label, load_labels
from pathlib import Path


@click.group("label")
def label_group():
    """Manage labels for grouping vault files."""


@label_group.command("add")
@click.argument("name")
@click.argument("files", nargs=-1, required=True)
def cmd_label_add(name: str, files):
    """Add a new label grouping FILES."""
    try:
        add_label(name, list(files))
        click.echo(f"Label '{name}' added with {len(files)} file(s).")
    except LabelError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@label_group.command("remove")
@click.argument("name")
def cmd_label_remove(name: str):
    """Remove a label by NAME."""
    try:
        remove_label(name)
        click.echo(f"Label '{name}' removed.")
    except LabelError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@label_group.command("list")
def cmd_label_list():
    """List all labels."""
    try:
        labels = load_labels()
        if not labels:
            click.echo("No labels defined.")
            return
        for name, files in labels.items():
            click.echo(f"{name}: {', '.join(files)}")
    except LabelError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@label_group.command("show")
@click.argument("name")
def cmd_label_show(name: str):
    """Show files under a label NAME."""
    try:
        files = get_label(name)
        for f in files:
            click.echo(f)
    except LabelError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)
