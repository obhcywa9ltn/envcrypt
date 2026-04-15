"""envcrypt — encrypt and sync .env files using age encryption."""

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("envcrypt")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "0.0.0.dev0"

__all__ = ["__version__"]
