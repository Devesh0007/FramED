"""
Parse a raw video frame image back into a structured Frame dataclass.

Sampling strategy:
  - Skip the checkerboard border (border_cells wide on every side).
  - For each inner cell, sample the CENTER pixel.
  - Threshold at 128: ≥128 → bit 1 (white), <128 → bit 0 (black).
  - Convert bit stream → bytes → parse HEADER → return Frame.
"""
from __future__ import annotations
import json
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

from frameed.config import (
    MAGIC, HEADER_STRUCT, HEADER_SIZE, CRC_SIZE, FrameType, ModeConfig,
)
from frameed.utils import bits_to_bytes
from frameed.encoder.fec import ecc_size_for


@dataclass
class Frame:
    frame_id:     int
    total_frames: int
    file_id:      bytes
    frame_type:   FrameType
    chunk_id:     int
    payload_len:  int       # raw (pre-ECC) payload length
    flags:        int
    raw_payload:  bytes     # RS-decoded raw payload
    stored_crc:   bytes     # CRC32 read from the frame
    ecc_payload:  bytes     # RS-encoded bytes (for debug)
    valid:        bool      # True if CRC matches
    manifest:     Optional[dict] = field(default=None)  # set for MANIFEST frames


def sample_bytes(gray_or_bgr: np.ndarray, mode: ModeConfig) -> bytes:
    """Sample cell-center pixels from the inner grid; return exact bytes."""
    cs  = mode.cell_size
    b   = mode.border_cells
    gcols = mode.grid_cols
    grows = mode.grid_rows
    ch  = getattr(mode, 'channels', 1)

    if ch == 1 and gray_or_bgr.ndim == 3:
        gray_or_bgr = gray_or_bgr[:, :, 0]

    if grows <= 2*b or gcols <= 2*b:
        return b""

    r_start = b * cs + cs // 2
    r_end = (grows - b) * cs
    
    c_start = b * cs + cs // 2
    c_end = (gcols - b) * cs
    
    samples = gray_or_bgr[r_start:r_end:cs, c_start:c_end:cs]
    
    if ch == 3 and samples.ndim == 3:
        # Reorder BGR to RGB if needed, but since we map directly bytes to values, 
        # as long as python read/write sequences natively align or reverse align it's identical
        # Wait, if we rendered it RGB through CV2, CV2 flipped it BGR. Then on read, CV2 gives BGR! 
        # So we MUST flip BGR -> RGB to recover the byte sequences perfectly!
        samples = samples[:, :, ::-1]

    return samples.astype(np.uint8).ravel().tobytes()


def parse_frame(gray_or_bgr: np.ndarray, mode: ModeConfig) -> Optional[Frame]:
    """Parse a frame array → Frame. Returns None if unrecognised."""
    raw = sample_bytes(gray_or_bgr, mode)

    # Check magic
    if len(raw) < HEADER_SIZE + CRC_SIZE or raw[:4] != MAGIC:
        return None

    (
        _magic, version, ftype,
        frame_id, total_frames, file_id,
        chunk_id, payload_len, flags,
    ) = HEADER_STRUCT.unpack(raw[:HEADER_SIZE])

    # Extract ECC payload and stored CRC
    ecc_len    = ecc_size_for(payload_len)
    ecc_start  = HEADER_SIZE
    ecc_end    = ecc_start + ecc_len
    crc_end    = ecc_end + CRC_SIZE

    if len(raw) < crc_end:
        return None

    ecc_payload  = raw[ecc_start:ecc_end]
    stored_crc   = raw[ecc_end:crc_end]

    # RS decode
    from frameed.encoder.fec import rs_decode
    try:
        raw_payload = rs_decode(ecc_payload, payload_len)
    except Exception:
        raw_payload = ecc_payload[:payload_len]   # fallback (may be corrupt)

    # CRC validation
    from frameed.utils import compute_crc32
    valid = compute_crc32(raw_payload) == stored_crc

    frame_type = FrameType(ftype)
    manifest = None
    if frame_type == FrameType.MANIFEST and valid:
        try:
            manifest = json.loads(raw_payload.decode())
        except Exception:
            manifest = None

    return Frame(
        frame_id=frame_id, total_frames=total_frames, file_id=file_id,
        frame_type=frame_type, chunk_id=chunk_id, payload_len=payload_len,
        flags=flags, raw_payload=raw_payload, stored_crc=stored_crc,
        ecc_payload=ecc_payload, valid=valid, manifest=manifest,
    )
