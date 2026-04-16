"""Optional compression layer for vault files before encryption."""

import gzip
import shutil
from pathlib import Path


class CompressError(Exception):
    """Raised when compression or decompression fails."""


def compress_file(src: Path, dest: Path) -> Path:
    """Compress *src* with gzip and write to *dest*.

    Returns the destination path.
    Raises CompressError on any I/O problem.
    """
    try:
        src = Path(src)
        dest = Path(dest)
        if not src.exists():
            raise CompressError(f"Source file not found: {src}")
        dest.parent.mkdir(parents=True, exist_ok=True)
        with src.open("rb") as f_in, gzip.open(dest, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)
        return dest
    except CompressError:
        raise
    except Exception as exc:  # pragma: no cover
        raise CompressError(f"Compression failed: {exc}") from exc


def decompress_file(src: Path, dest: Path) -> Path:
    """Decompress gzip-compressed *src* and write plain bytes to *dest*.

    Returns the destination path.
    Raises CompressError on any I/O problem.
    """
    try:
        src = Path(src)
        dest = Path(dest)
        if not src.exists():
            raise CompressError(f"Source file not found: {src}")
        dest.parent.mkdir(parents=True, exist_ok=True)
        with gzip.open(src, "rb") as f_in, dest.open("wb") as f_out:
            shutil.copyfileobj(f_in, f_out)
        return dest
    except CompressError:
        raise
    except Exception as exc:  # pragma: no cover
        raise CompressError(f"Decompression failed: {exc}") from exc


def is_compressed(path: Path) -> bool:
    """Return True if *path* looks like a gzip file (magic bytes check)."""
    path = Path(path)
    if not path.exists():
        return False
    with path.open("rb") as fh:
        magic = fh.read(2)
    return magic == b"\x1f\x8b"


def compressed_size(path: Path) -> int:
    """Return the total number of uncompressed bytes stored in a gzip file.

    Reads the ISIZE field from the last 4 bytes of the gzip trailer, which
    stores the original data length modulo 2**32.  For files larger than 4 GiB
    this value wraps around, but it is sufficient for typical vault files.

    Raises CompressError if *path* does not exist or is not a valid gzip file.
    """
    path = Path(path)
    if not path.exists():
        raise CompressError(f"File not found: {path}")
    if not is_compressed(path):
        raise CompressError(f"File does not appear to be gzip-compressed: {path}")
    try:
        with path.open("rb") as fh:
            fh.seek(-4, 2)
            isize_bytes = fh.read(4)
        return int.from_bytes(isize_bytes, byteorder="little")
    except Exception as exc:
        raise CompressError(f"Could not read compressed size: {exc}") from exc
