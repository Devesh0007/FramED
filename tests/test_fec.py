"""Test Reed-Solomon ECC and XOR parity frame recovery."""
import pytest
from frameed.encoder.fec import (
    rs_encode, rs_decode, generate_parity_frames, recover_missing_chunk,
)


# ── RS ECC ────────────────────────────────────────────────────────────────────

def test_rs_encode_decode_identity():
    data = bytes(range(239))  # one full RS block
    encoded = rs_encode(data)
    recovered = rs_decode(encoded, len(data))
    assert recovered == data


def test_rs_encode_decode_multi_block():
    data = bytes(range(239)) * 3 + b'\xAB' * 100  # multi-block
    encoded = rs_encode(data)
    recovered = rs_decode(encoded, len(data))
    assert recovered == data


def test_rs_corrects_byte_errors():
    """RS should correct up to 8 byte errors per 255-byte block."""
    data = b'X' * 239
    encoded = bytearray(rs_encode(data))
    # Corrupt 8 bytes in the first block
    for i in range(8):
        encoded[i] ^= 0xFF
    recovered = rs_decode(bytes(encoded), len(data))
    assert recovered == data


# ── XOR parity ────────────────────────────────────────────────────────────────

def test_parity_recovery_single_missing():
    chunks = [bytes([i] * 100) for i in range(8)]  # 8 chunks of 100 bytes
    parity_list = generate_parity_frames(chunks, parity_group=8)
    assert len(parity_list) == 1
    group_start, parity = parity_list[0]
    assert group_start == 0

    # Simulate chunk 3 missing
    group_with_missing = [c if i != 3 else None for i, c in enumerate(chunks)]
    recovered = recover_missing_chunk(group_with_missing, parity)
    assert recovered[:100] == chunks[3]


def test_parity_recovery_multiple_groups():
    chunks = [bytes([i] * 50) for i in range(20)]
    parity_list = generate_parity_frames(chunks, parity_group=4)
    assert len(parity_list) == 5  # 20 / 4 = 5 groups
    # Each group can recover one missing chunk
    for group_start, parity in parity_list:
        group = chunks[group_start:group_start + 4]
        group_with_missing = [None if i == 0 else c for i, c in enumerate(group)]
        recovered = recover_missing_chunk(group_with_missing, parity)
        assert recovered[:50] == group[0]
