"""Tests for envcrypt.compress."""

import gzip
from pathlib import Path

import pytest

from envcrypt.compress import CompressError, compress_file, decompress_file, is_compressed


# ---------------------------------------------------------------------------
# compress_file
# ---------------------------------------------------------------------------


class TestCompressFile:
    def test_creates_compressed_output(self, tmp_path):
        src = tmp_path / "data.env"
        src.write_text("KEY=value\nFOO=bar\n")
        dest = tmp_path / "data.env.gz"

        result = compress_file(src, dest)

        assert result == dest
        assert dest.exists()
        assert is_compressed(dest)

    def test_compressed_content_roundtrips(self, tmp_path):
        original = "SECRET=hunter2\nDB=postgres\n"
        src = tmp_path / "orig.env"
        src.write_text(original)
        dest = tmp_path / "orig.env.gz"

        compress_file(src, dest)

        with gzip.open(dest, "rt") as fh:
            recovered = fh.read()
        assert recovered == original

    def test_raises_when_source_missing(self, tmp_path):
        with pytest.raises(CompressError, match="Source file not found"):
            compress_file(tmp_path / "ghost.env", tmp_path / "out.gz")

    def test_creates_parent_directories(self, tmp_path):
        src = tmp_path / "a.env"
        src.write_text("X=1")
        dest = tmp_path / "nested" / "deep" / "a.env.gz"

        compress_file(src, dest)

        assert dest.exists()


# ---------------------------------------------------------------------------
# decompress_file
# ---------------------------------------------------------------------------


class TestDecompressFile:
    def test_restores_original_content(self, tmp_path):
        original = "API_KEY=abc123\n"
        src = tmp_path / "enc.env.gz"
        with gzip.open(src, "wt") as fh:
            fh.write(original)
        dest = tmp_path / "dec.env"

        result = decompress_file(src, dest)

        assert result == dest
        assert dest.read_text() == original

    def test_raises_when_source_missing(self, tmp_path):
        with pytest.raises(CompressError, match="Source file not found"):
            decompress_file(tmp_path / "missing.gz", tmp_path / "out.env")

    def test_creates_parent_directories(self, tmp_path):
        src = tmp_path / "data.gz"
        with gzip.open(src, "wt") as fh:
            fh.write("K=V")
        dest = tmp_path / "sub" / "dir" / "data.env"

        decompress_file(src, dest)

        assert dest.exists()


# ---------------------------------------------------------------------------
# is_compressed
# ---------------------------------------------------------------------------


class TestIsCompressed:
    def test_returns_true_for_gzip_file(self, tmp_path):
        path = tmp_path / "file.gz"
        with gzip.open(path, "wb") as fh:
            fh.write(b"hello")
        assert is_compressed(path) is True

    def test_returns_false_for_plain_file(self, tmp_path):
        path = tmp_path / "file.txt"
        path.write_bytes(b"hello world")
        assert is_compressed(path) is False

    def test_returns_false_for_missing_file(self, tmp_path):
        assert is_compressed(tmp_path / "nope.gz") is False
