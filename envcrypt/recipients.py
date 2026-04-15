"""Manage recipient public keys for shared .env encryption."""

import json
from pathlib import Path
from typing import Dict, List

DEFAULT_RECIPIENTS_FILE = Path(".envcrypt") / "recipients.json"


class RecipientsError(Exception):
    """Raised when a recipient operation fails."""
    pass


def get_recipients_file(base_dir: Path = Path(".")) -> Path:
    """Return the path to the recipients file."""
    return base_dir / DEFAULT_RECIPIENTS_FILE


def load_recipients(recipients_file: Path) -> Dict[str, str]:
    """Load recipients from a JSON file.

    Returns a dict mapping alias -> public key.
    Raises RecipientsError on invalid data.
    """
    if not recipients_file.exists():
        return {}

    try:
        data = json.loads(recipients_file.read_text())
    except json.JSONDecodeError as exc:
        raise RecipientsError(f"Invalid recipients file: {exc}") from exc

    if not isinstance(data, dict):
        raise RecipientsError("Recipients file must contain a JSON object.")

    return data


def save_recipients(recipients: Dict[str, str], recipients_file: Path) -> None:
    """Save recipients dict to a JSON file."""
    recipients_file.parent.mkdir(parents=True, exist_ok=True)
    recipients_file.write_text(json.dumps(recipients, indent=2) + "\n")


def add_recipient(alias: str, public_key: str, recipients_file: Path) -> None:
    """Add or update a recipient.

    Raises RecipientsError if the public key does not start with 'age1'.
    """
    if not public_key.startswith("age1"):
        raise RecipientsError(f"Invalid age public key: {public_key!r}")

    recipients = load_recipients(recipients_file)
    recipients[alias] = public_key
    save_recipients(recipients, recipients_file)


def remove_recipient(alias: str, recipients_file: Path) -> None:
    """Remove a recipient by alias.

    Raises RecipientsError if alias is not found.
    """
    recipients = load_recipients(recipients_file)
    if alias not in recipients:
        raise RecipientsError(f"Recipient not found: {alias!r}")
    del recipients[alias]
    save_recipients(recipients, recipients_file)


def list_public_keys(recipients_file: Path) -> List[str]:
    """Return a list of all public keys from the recipients file."""
    recipients = load_recipients(recipients_file)
    return list(recipients.values())
