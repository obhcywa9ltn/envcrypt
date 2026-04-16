"""CLI commands for vault history in envcrypt."""
import click

from envcrypt.history import HistoryError, clear_history, load_history, record_event


@click.group("history")
def history_group() -> None:
    """Commands for viewing and managing vault history."""


@history_group.command("log")
@click.option("--base-dir", default=None, help="Base directory for history file.")
@click.option("--limit", default=20, show_default=True, help="Max entries to show.")
def cmd_history_log(base_dir: str | None, limit: int) -> None:
    """Print recent vault history entries."""
    try:
        entries = load_history(base_dir)
    except HistoryError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)
    if not entries:
        click.echo("No history recorded.")
        return
    for entry in entries[-limit:]:
        ts = entry.get("timestamp", "?")
        click.echo(f"{ts}  {entry.get('action')}  {entry.get('env_file')}  actor={entry.get('actor')}")


@history_group.command("clear")
@click.option("--base-dir", default=None, help="Base directory for history file.")
@click.confirmation_option(prompt="Clear all history?")
def cmd_history_clear(base_dir: str | None) -> None:
    """Clear all vault history entries."""
    try:
        clear_history(base_dir)
        click.echo("History cleared.")
    except HistoryError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@history_group.command("record")
@click.argument("action")
@click.argument("env_file")
@click.option("--actor", default="unknown", help="Actor performing the action.")
@click.option("--base-dir", default=None)
def cmd_history_record(action: str, env_file: str, actor: str, base_dir: str | None) -> None:
    """Manually record a history event."""
    try:
        entry = record_event(action, env_file, actor=actor, base_dir=base_dir)
        click.echo(f"Recorded: {entry['action']} on {entry['env_file']} at {entry['timestamp']:.0f}")
    except HistoryError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)
