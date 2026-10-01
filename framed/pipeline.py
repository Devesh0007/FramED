"""
High-level orchestration: encode_file() and decode_file().
These are the two entry-points called by main.py CLI.
"""
from __future__ import annotations
import os
from pathlib import Path

from framed.config import MODES, ModeConfig, FrameType
from framed.utils import generate_file_id
from framed.encoder.compressor import compress
from framed.encoder.encryptor import encrypt
from framed.encoder.chunker import chunk_data
from framed.encoder.fec import rs_encode, generate_parity_frames
from framed.encoder.frame_builder import (
    build_manifest_frame, build_frame, build_parity_frame,
)
from framed.encoder.renderer import render_frame
from framed.encoder.video_writer import frames_to_video

from framed.decoder.video_reader import extract_frames
from framed.decoder.frame_parser import parse_frame, Frame
from framed.decoder.fec_reconstructor import reconstruct
from framed.decoder.reassembler import reassemble
from framed.decoder.decryptor import maybe_decrypt
from framed.decoder.decompressor import decompress_data
from framed.decoder.writer import write_output


# ─────────────────────────────────────────────────────────────────────────────
# ENCODE
# ─────────────────────────────────────────────────────────────────────────────

def encode_file(
    input_path:   str,
    output_video: str,
    mode_name:    str = "archive",
    password:     str | None = None,
) -> str:
    """
    Encode any file into a lossless B&W video.
    Returns the path to the generated .avi file.
    """
    mode = MODES[mode_name]
    file_id = generate_file_id()
    src = Path(input_path)

    # 1. Read
    raw_bytes = src.read_bytes()
    original_size = len(raw_bytes)
    extension = src.suffix.lstrip('.')
    print(f"[FramED] Encoding '{src.name}'  ({original_size:,} bytes)  mode={mode_name}")

    # 2. Compress
    processed = compress(raw_bytes, extension)

    # 3. Optionally encrypt
    if password:
        processed = encrypt(processed, password)
        print("[FramED] Encryption applied (AES-256-GCM).")

    processed_size = len(processed)
    chunk_size = mode.raw_chunk_size
    chunks = chunk_data(processed, chunk_size)
    num_data = len(chunks)
    print(f"[FramED] {processed_size:,} processed bytes -> {num_data} DATA chunk(s) of <= {chunk_size:,} B each")

    # 4. Parity frames
    parity_list = generate_parity_frames(chunks, mode.parity_group)
    num_parity  = len(parity_list)
    total_frames = 1 + num_data + num_parity          # MANIFEST + DATA + PARITY

    # 5. Build frame blobs
    blobs: list[bytes] = []

    # MANIFEST (frame_id=0)
    manifest_blob = build_manifest_frame(
        file_id=file_id, total_frames=total_frames,
        filename=src.name, original_size=original_size,
        processed_size=processed_size, mode_name=mode_name, mode=mode,
    )
    blobs.append(manifest_blob)

    # DATA frames (frame_id 1..num_data)
    for idx, chunk in enumerate(chunks):
        blob = build_frame(
            frame_type=FrameType.DATA,
            frame_id=idx + 1,
            total_frames=total_frames,
            file_id=file_id,
            chunk_id=idx,
            raw_payload=chunk,
            mode=mode,
        )
        blobs.append(blob)

    # PARITY frames (frame_id num_data+1..)
    for p_idx, (group_start, parity_payload) in enumerate(parity_list):
        blob = build_parity_frame(
            frame_id=num_data + 1 + p_idx,
            total_frames=total_frames,
            file_id=file_id,
            group_start=group_start,
            raw_parity=parity_payload,
            mode=mode,
        )
        blobs.append(blob)

    assert len(blobs) == total_frames

    # 6. Render to PIL images dynamically
    print(f"[FramED] Rendering & Streaming {total_frames} frames directly to VideoStream …")
    images_gen = (render_frame(b, mode) for b in blobs)

    # 7. Write video
    out_path = str(Path(output_video))
    frames_to_video(images_gen, out_path, mode, total_frames)
    return out_path


# ─────────────────────────────────────────────────────────────────────────────
# DECODE
# ─────────────────────────────────────────────────────────────────────────────

def decode_file(
    input_video: str,
    output_dir:  str,
    mode_name:   str | None = None,      # auto-detected from MANIFEST if None
    password:    str | None = None,
) -> str:
    """
    Decode a FramED video back to the original file.
    Returns the path to the written output file.
    """
    # 1. Extract frames (generator)
    frame_generator = extract_frames(input_video)

    # 2. Determine mode (try both; MANIFEST picks the right one on the FIRST frame)
    manifest_frame: Frame | None = None
    detected_mode: ModeConfig | None = None

    try:
        first_img = next(frame_generator)
    except StopIteration:
        raise ValueError("Video file appears empty.")

    for mode_try in (MODES.get(mode_name) and [MODES[mode_name]] or list(MODES.values())):
        f = parse_frame(first_img, mode_try)
        if f and f.frame_type == FrameType.MANIFEST and f.valid:
            manifest_frame = f
            detected_mode = mode_try
            print(f"[FramED] Detected mode '{manifest_frame.manifest['mode']}'")
            break

    if not manifest_frame:
        raise ValueError("No valid MANIFEST frame found. Is this a FramED video?")

    meta         = manifest_frame.manifest
    mode_name_ok = meta['mode']
    filename     = meta['filename']
    processed_size = meta['processed_size']
    mode = MODES[mode_name_ok]

    # 3. Collect DATA and PARITY frames sequentially to save memory
    data_chunks:  dict[int, bytes] = {}
    parity_map:   dict[int, bytes] = {}

    def _frame_stream():
        yield manifest_frame
        for img in frame_generator:
            yield parse_frame(img, mode)

    num_data_frames = 0
    for f in _frame_stream():
        if f is None or not f.valid:
            continue
        if f.frame_type == FrameType.DATA:
            data_chunks[f.chunk_id] = f.raw_payload
            num_data_frames += 1
        elif f.frame_type == FrameType.PARITY:
            parity_map[f.chunk_id] = f.raw_payload   # chunk_id = group_start

    total_chunks = (processed_size + mode.raw_chunk_size - 1) // mode.raw_chunk_size
    print(f"[FramED] Received {len(data_chunks)}/{total_chunks} DATA chunks, "
          f"{len(parity_map)} PARITY groups.")

    # 4. FEC reconstruction
    data_chunks = reconstruct(data_chunks, parity_map, total_chunks, mode.parity_group)

    # 5. Reassemble
    processed = reassemble(data_chunks, total_chunks)
    processed = processed[:processed_size]  # trim any chunk padding

    # 6. Decrypt
    processed = maybe_decrypt(processed, password)

    # 7. Decompress
    original_bytes, _ = decompress_data(processed)

    # 8. Write output
    return write_output(original_bytes, filename, output_dir)
