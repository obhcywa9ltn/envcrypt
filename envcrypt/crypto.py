"""Core encryption/decryption utilities using age encryption."""

import subprocess
import tempfile
import os
from pathlib import Path
from typing import Union


class AgeEncryptionError(Exception):
    """Raised when encryption or decryption fails."""
    pass


def check_age_installed() -> bool:
    """Check if the age binary is available on the system."""
    try:
        result = subprocess.run(
            ["age", "--version"],
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def encrypt_file(input_path: Union[str, Path], output_path: Union[str, Path], recipients: list[str]) -> None:
    """
    Encrypt a file using age with one or more public key recipients.

    Args:
        input_path: Path to the plaintext file.
        output_path: Path where the encrypted file will be written.
        recipients: List of age public keys (recipients).

    Raises:
        AgeEncryptionError: If encryption fails.
    """
    if not recipients:
        raise AgeEncryptionError("At least one recipient public key is required.")

    cmd = ["age", "--output", str(output_path)]
    for recipient in recipients:
        cmd.extend(["--recipient", recipient])
    cmd.append(str(input_path))

    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise AgeEncryptionError(f"Encryption failed: {result.stderr.strip()}")


def decrypt_file(
    input_path: Union[str, Path],
    output_path: Union[str, Path],
    identity_path: Union[str, Path],
) -> None:
    """
    Decrypt an age-encrypted file using an identity (private key) file.

    Args:
        input_path: Path to the encrypted file.
        output_path: Path where the decrypted file will be written.
        identity_path: Path to the age identity (private key) file.

    Raises:
        AgeEncryptionError: If decryption fails.
    """
    cmd = [
        "age",
        "--decrypt",
        "--identity", str(identity_path),
        "--output", str(output_path),
        str(input_path),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise AgeEncryptionError(f"Decryption failed: {result.stderr.strip()}")
