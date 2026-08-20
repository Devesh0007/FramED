"""Bit packing / unpacking and CRC32 helpers."""
import struct
import zlib
import uuid
import numpy as np


def bytes_to_bits(data: bytes) -> list[int]:
    """Convert bytes → list of bits, MSB-first."""
    if not data:
        return []
    return np.unpackbits(np.frombuffer(data, dtype=np.uint8)).tolist()


def bits_to_bytes(bits: list[int]) -> bytes:
    """Convert list of bits (MSB-first) → bytes. Pads with zeros if needed."""
    if not bits:
        return b""
    arr = np.array(bits, dtype=np.uint8)
    pad_len = (-len(arr)) % 8
    if pad_len:
        arr = np.pad(arr, (0, pad_len))
    return np.packbits(arr).tobytes()


def compute_crc32(data: bytes) -> bytes:
    """Return CRC32 of data as 4 bytes (big-endian)."""
    crc = zlib.crc32(data) & 0xFFFFFFFF
    return struct.pack('!I', crc)


def verify_crc32(data: bytes, expected: bytes) -> bool:
    return compute_crc32(data) == expected


def generate_file_id() -> bytes:
    """Return a fresh 16-byte UUID."""
    return uuid.uuid4().bytes


def pad_to(data: bytes, length: int) -> bytes:
    """Zero-pad data to exactly `length` bytes."""
    if len(data) >= length:
        return data[:length]
    return data + b'\x00' * (length - len(data))
