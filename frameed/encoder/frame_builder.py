"""
Assemble the binary blob for a single video frame.

Blob layout:
  [ HEADER 39 B ] [ ECC-encoded payload ] [ CRC32 of raw payload 4 B ]

The CRC is computed over the RAW (pre-ECC) payload so the decoder can
verify integrity after RS decoding.
"""
import json
from frameed.config import (
    MAGIC, VERSION, FrameType, HEADER_STRUCT, HEADER_SIZE, CRC_SIZE,
    ModeConfig,
)
from frameed.utils import compute_crc32, generate_file_id
from frameed.encoder.fec import rs_encode


def build_frame(
    frame_type: FrameType,
    frame_id: int,
    total_frames: int,
    file_id: bytes,
    chunk_id: int,
    raw_payload: bytes,
    mode: ModeConfig,
    flags: int = 0,
) -> bytes:
    """
    Return the complete frame blob (header + ECC payload + CRC32).
    The blob length in bits must fit inside mode.total_inner_cells.
    """
    payload_len = len(raw_payload)
    header = HEADER_STRUCT.pack(
        MAGIC, VERSION, int(frame_type),
        frame_id, total_frames, file_id,
        chunk_id, payload_len, flags,
    )
    ecc_payload = rs_encode(raw_payload)
    crc = compute_crc32(raw_payload)
    blob = header + ecc_payload + crc
    # Sanity-check: blob bytes must fit in frame
    assert len(blob) <= mode.total_inner_cells, (
        f"Frame blob {len(blob)} bytes > capacity {mode.total_inner_cells} bytes"
    )
    return blob


def build_manifest_frame(
    file_id: bytes,
    total_frames: int,
    filename: str,
    original_size: int,
    processed_size: int,
    mode_name: str,
    mode: ModeConfig,
) -> bytes:
    """Build the MANIFEST (frame_id=0) that carries file metadata as JSON."""
    meta = json.dumps({
        "filename":       filename,
        "original_size":  original_size,
        "processed_size": processed_size,
        "mode":           mode_name,
    }).encode()
    return build_frame(
        frame_type=FrameType.MANIFEST,
        frame_id=0,
        total_frames=total_frames,
        file_id=file_id,
        chunk_id=0,
        raw_payload=meta,
        mode=mode,
    )


def build_parity_frame(
    frame_id: int,
    total_frames: int,
    file_id: bytes,
    group_start: int,     # CHUNK_ID of first DATA frame in the group
    raw_parity: bytes,
    mode: ModeConfig,
) -> bytes:
    """Build a PARITY frame for one XOR group."""
    return build_frame(
        frame_type=FrameType.PARITY,
        frame_id=frame_id,
        total_frames=total_frames,
        file_id=file_id,
        chunk_id=group_start,
        raw_payload=raw_parity,
        mode=mode,
    )
