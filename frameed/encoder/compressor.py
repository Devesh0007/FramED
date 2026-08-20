"""zstd compression with embedded metadata header."""
import struct
import zstandard as zstd

# Header: original_size(4B) + ext_len(1B) + ext(variable)
_HDR_FMT = struct.Struct('!IB')


def compress(data: bytes, extension: str) -> bytes:
    """Compress and prepend: original_size(4) + ext_len(1) + ext bytes."""
    ext_b = extension.lstrip('.').encode()[:255]
    header = _HDR_FMT.pack(len(data), len(ext_b)) + ext_b
    cctx = zstd.ZstdCompressor(level=3)
    return header + cctx.compress(data)


def decompress(data: bytes) -> tuple[bytes, str]:
    """Return (original_bytes, extension_without_dot)."""
    original_size, ext_len = _HDR_FMT.unpack_from(data, 0)
    offset = _HDR_FMT.size
    extension = data[offset:offset + ext_len].decode()
    offset += ext_len
    dctx = zstd.ZstdDecompressor()
    original = dctx.decompress(data[offset:], max_output_size=original_size + 1)
    if len(original) != original_size:
        raise ValueError(f"Decompressed size mismatch: expected {original_size}, got {len(original)}")
    return original, extension
