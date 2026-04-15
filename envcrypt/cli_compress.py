"""CLI commands for compressing and decompressing vault files."""

from pathlib import Path

import click

from envcrypt.compress import CompressError, compress_file, decompress_file, is_compressed


@click.group("compress")
def compress_group() -> None:
    """Compress or decompress encrypted vault files."""


@compress_group.command("pack")
@click.argument("src", type=click.Path(exists=True, path_type=Path))
@click.argument("dest", type=click.Path(path_type=Path), required=False)
def cmd_compress_pack(src: Path, dest: Path | None) -> None:
    """Compress SRC with gzip. Writes to DEST (default: SRC + .gz)."""
    if dest is None:
        dest = src.with_suffix(src.suffix + ".gz")
    try:
        out = compress_file(src, dest)
        click.echo(f"Compressed: {out}")
    except CompressError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@compress_group.command("unpack")
@click.argument("src", type=click.Path(exists=True, path_type=Path))
@click.argument("dest", type=click.Path(path_type=Path), required=False)
def cmd_compress_unpack(src: Path, dest: Path | None) -> None:
    """Decompress gzip SRC. Writes to DEST (default: SRC without .gz suffix)."""
    if dest is None:
        stem = src.stem if src.suffix == ".gz" else str(src)
        dest = src.parent / stem
    try:
        out = decompress_file(src, dest)
        click.echo(f"Decompressed: {out}")
    except CompressError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@compress_group.command("check")
@click.argument("path", type=click.Path(exists=True, path_type=Path))
def cmd_compress_check(path: Path) -> None:
    """Check whether PATH is a gzip-compressed file."""
    if is_compressed(path):
        click.echo(f"{path}: compressed (gzip)")
    else:
        click.echo(f"{path}: not compressed")
