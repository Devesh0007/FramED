"""Bit packing / unpacking and CRC32 helpers."""
import struct
import zlib
import uuid


def bytes_to_bits(data: bytes) -> list[int]:
    """Convert bytes → list of bits, MSB-first."""
    bits = []
    for byte in data:
        for i in range(7, -1, -1):
            bits.append((byte >> i) & 1)
    return bits


def bits_to_bytes(bits: list[int]) -> bytes:
    """Convert list of bits (MSB-first) → bytes. Pads with zeros if needed."""
    padded = bits + [0] * ((-len(bits)) % 8)
    result = bytearray()
    for i in range(0, len(padded), 8):
        byte = 0
        for j in range(8):
            byte = (byte << 1) | padded[i + j]
        result.append(byte)
    return bytes(result)


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
