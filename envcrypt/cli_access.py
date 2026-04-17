"""CLI commands for managing recipient access control per env file."""
import click
from envcrypt.access import AccessError, grant_access, revoke_access, load_access, is_allowed


@click.group("access")
def access_group():
    """Manage per-file recipient access control."""


@access_group.command("grant")
@click.argument("env_name")
@click.argument("recipient")
@click.option("--base-dir", default=None, help="Base directory for access file.")
def cmd_access_grant(env_name: str, recipient: str, base_dir: str | None):
    """Grant RECIPIENT access to ENV_NAME."""
    try:
        grant_access(env_name, recipient, base_dir)
        click.echo(f"Granted {recipient} access to {env_name}.")
    except AccessError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@access_group.command("revoke")
@click.argument("env_name")
@click.argument("recipient")
@click.option("--base-dir", default=None)
def cmd_access_revoke(env_name: str, recipient: str, base_dir: str | None):
    """Revoke RECIPIENT access to ENV_NAME."""
    try:
        revoke_access(env_name, recipient, base_dir)
        click.echo(f"Revoked {recipient} from {env_name}.")
    except AccessError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@access_group.command("list")
@click.option("--base-dir", default=None)
def cmd_access_list(base_dir: str | None):
    """List all access rules."""
    try:
        mapping = load_access(base_dir)
        if not mapping:
            click.echo("No access rules defined.")
            return
        for env_name, recipients in mapping.items():
            click.echo(f"{env_name}: {', '.join(recipients) if recipients else '(none)'}")
    except AccessError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@access_group.command("check")
@click.argument("env_name")
@click.argument("recipient")
@click.option("--base-dir", default=None)
def cmd_access_check(env_name: str, recipient: str, base_dir: str | None):
    """Check if RECIPIENT is allowed to access ENV_NAME."""
    try:
        allowed = is_allowed(env_name, recipient, base_dir)
        if allowed:
            click.echo(f"{recipient} is allowed to access {env_name}.")
        else:
            click.echo(f"{recipient} is NOT allowed to access {env_name}.")
            raise SystemExit(1)
    except AccessError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)
