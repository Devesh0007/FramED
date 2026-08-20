"""Test zstd compression/decompression identity."""
import pytest
from frameed.encoder.compressor import compress, decompress


@pytest.mark.parametrize("data,ext", [
    (b"Hello World!", "txt"),
    (bytes(range(256)) * 100, "bin"),
    (b"\x00" * 10_000, "dat"),
], ids=["ascii_txt", "full_byte_range_bin", "zeros_dat"])
def test_compress_decompress_identity(data, ext):
    compressed = compress(data, ext)
    recovered, recovered_ext = decompress(compressed)
    assert recovered == data, "Decompressed data does not match original."
    assert recovered_ext == ext.lstrip('.')


def test_compression_reduces_size_for_compressible_data():
    data = b"AAAAAAAAAA" * 1000
    compressed = compress(data, "txt")
    assert len(compressed) < len(data), "Compression did not reduce size."
