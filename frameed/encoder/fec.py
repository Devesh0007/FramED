"""
Reed-Solomon ECC (per-frame) + XOR parity (cross-frame recovery).

Per-frame RS:
  - Each raw chunk is split into 239-byte RS data blocks.
  - Each block gets 16 ECC bytes appended → 255-byte RS codeword.
  - Corrects up to 8 random byte errors per 255-byte block.

Cross-frame XOR parity:
  - Every `parity_group` consecutive DATA frame payloads are XOR-ed together.
  - One PARITY frame per group allows recovery of any single missing frame.
"""
import math
from reedsolo import RSCodec

from frameed.config import RS_NSYM, RS_BLOCK_DATA, RS_BLOCK_TOTAL

_rs = RSCodec(RS_NSYM)


# ── Per-frame RS encode / decode ─────────────────────────────────────────────

def rs_encode(data: bytes) -> bytes:
    """Encode arbitrary-length data with RS ECC. Returns ECC-appended codewords."""
    out = bytearray()
    for i in range(0, len(data), RS_BLOCK_DATA):
        block = data[i:i + RS_BLOCK_DATA]
        out += bytes(_rs.encode(block))
    return bytes(out)


def rs_decode(ecc_data: bytes, raw_len: int) -> bytes:
    """
    Decode RS codewords back to raw bytes, correcting errors where possible.

    Mirrors rs_encode block structure:
      - Full blocks have RS_BLOCK_DATA + RS_NSYM bytes.
      - The last block (if shorter) has remainder + RS_NSYM bytes.
    """
    out = bytearray()
    remaining_raw = raw_len
    pos = 0
    while remaining_raw > 0 and pos < len(ecc_data):
        block_data_len = min(remaining_raw, RS_BLOCK_DATA)
        block_ecc_len  = block_data_len + RS_NSYM
        block = ecc_data[pos:pos + block_ecc_len]
        pos += block_ecc_len
        decoded, _, _ = _rs.decode(block)
        out += bytes(decoded)
        remaining_raw -= block_data_len
    return bytes(out)[:raw_len]


def ecc_size_for(raw_len: int) -> int:
    """
    Return the ECC-encoded byte count for a given raw data length.

    reedsolo.RSCodec.encode() appends RS_NSYM ECC bytes to EACH block
    (it does NOT pad a short last block to RS_BLOCK_TOTAL bytes).
    So a block of `k` data bytes → `k + RS_NSYM` encoded bytes.
    """
    n_full_blocks, remainder = divmod(raw_len, RS_BLOCK_DATA)
    # Full blocks: RS_BLOCK_DATA + RS_NSYM each
    size = n_full_blocks * (RS_BLOCK_DATA + RS_NSYM)
    # Last partial block (if any): remainder + RS_NSYM
    if remainder:
        size += remainder + RS_NSYM
    return size


# ── XOR parity (cross-frame recovery) ────────────────────────────────────────

def xor_parity(payloads: list[bytes]) -> bytes:
    """XOR a list of payloads together (all padded to max length)."""
    max_len = max(len(p) for p in payloads)
    result = bytearray(max_len)
    for p in payloads:
        padded = p.ljust(max_len, b'\x00')
        for i, b in enumerate(padded):
            result[i] ^= b
    return bytes(result)


def generate_parity_frames(raw_chunks: list[bytes], parity_group: int) -> list[tuple[int, bytes]]:
    """
    Return list of (group_start_chunk_id, parity_payload) for each group.
    group_start_chunk_id is the CHUNK_ID of the first DATA frame in the group.
    """
    result = []
    for start in range(0, len(raw_chunks), parity_group):
        group = raw_chunks[start:start + parity_group]
        parity = xor_parity(group)
        result.append((start, parity))
    return result


def recover_missing_chunk(
    group_chunks: list[bytes | None],
    parity: bytes,
) -> bytes:
    """
    Recover one missing chunk (None entry) using XOR parity.
    Returns the recovered raw bytes (trimmed to actual length if known via parity).
    Raises ValueError if more than one chunk is missing.
    """
    missing = [i for i, c in enumerate(group_chunks) if c is None]
    if len(missing) != 1:
        raise ValueError(f"XOR parity can only recover exactly 1 missing chunk; {len(missing)} missing.")
    idx = missing[0]
    known = [c for c in group_chunks if c is not None]
    # XOR all known chunks + parity → missing chunk
    recovered = bytearray(parity)
    for c in known:
        padded = c.ljust(len(parity), b'\x00')
        for i, b in enumerate(padded):
            if i < len(recovered):
                recovered[i] ^= b
    return bytes(recovered)
