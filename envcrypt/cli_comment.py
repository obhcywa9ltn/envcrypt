"""CLI commands for managing inline .env key comments."""
import click
from envcrypt.comment import CommentError, add_comment, remove_comment, load_comments, get_comment


@click.group("comment")
def comment_group():
    """Manage inline comments for .env keys."""


@comment_group.command("add")
@click.argument("key")
@click.argument("text")
@click.option("--base-dir", default=None, help="Base directory for .envcrypt data.")
def cmd_comment_add(key: str, text: str, base_dir: str | None):
    """Attach a comment to KEY."""
    try:
        add_comment(key, text, base_dir)
        click.echo(f"Comment set for '{key}'.")
    except CommentError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@comment_group.command("remove")
@click.argument("key")
@click.option("--base-dir", default=None)
def cmd_comment_remove(key: str, base_dir: str | None):
    """Remove the comment for KEY."""
    try:
        remove_comment(key, base_dir)
        click.echo(f"Comment removed for '{key}'.")
    except CommentError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@comment_group.command("show")
@click.argument("key")
@click.option("--base-dir", default=None)
def cmd_comment_show(key: str, base_dir: str | None):
    """Show the comment for KEY."""
    value = get_comment(key, base_dir)
    if value is None:
        click.echo(f"No comment for '{key}'.")
    else:
        click.echo(value)


@comment_group.command("list")
@click.option("--base-dir", default=None)
def cmd_comment_list(base_dir: str | None):
    """List all key comments."""
    try:
        comments = load_comments(base_dir)
    except CommentError asf"Error: {exc}", err=True)
        raise SystemExit(1)
    if not comments:
        click.echo("No comments defined.")
        return
    for key, text in sorted(comments.items()):
        click.echo(f"{key}: {text}")
