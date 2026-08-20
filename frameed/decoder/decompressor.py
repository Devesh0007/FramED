"""Decompress wrapper — delegates to encoder.compressor."""
from frameed.encoder.compressor import decompress


def decompress_data(data: bytes) -> tuple[bytes, str]:
    """Return (original_bytes, extension_without_dot)."""
    return decompress(data)
