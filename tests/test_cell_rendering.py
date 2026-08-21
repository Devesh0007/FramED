"""Test cell rendering and pixel-level readback accuracy."""
import numpy as np
import pytest
from frameed.config import MODES
from frameed.encoder.renderer import render_frame
from frameed.decoder.frame_parser import sample_bytes


def test_render_and_readback_archive():
    """Render a known blob and verify every sampled byte matches."""
    mode = MODES["archive"]
    capacity_bytes = mode.payload_capacity_bytes + 43
    blob = bytes(range(256)) * (capacity_bytes // 256) + bytes(range(capacity_bytes % 256))
    blob = blob[:capacity_bytes]

    img = render_frame(blob, mode)
    gray = np.array(img)
    if mode.channels == 3:
        gray = gray[:, :, ::-1]
    sampled_bytes = sample_bytes(gray, mode)

    sampled_trimmed = sampled_bytes[:len(blob)]
    assert sampled_trimmed == blob, "Byte mismatches found in render→readback (archive)."


def test_render_and_readback_optical():
    """Same test for optical mode (8×8 cells)."""
    mode = MODES["optical"]
    capacity_bytes = mode.payload_capacity_bytes + 43
    blob = bytes(range(256)) * (capacity_bytes // 256) + bytes(range(capacity_bytes % 256))
    blob = blob[:capacity_bytes]

    img = render_frame(blob, mode)
    gray = np.array(img)
    if mode.channels == 3:
        gray = gray[:, :, ::-1]
    sampled_bytes = sample_bytes(gray, mode)
    
    sampled_trimmed = sampled_bytes[:len(blob)]
    assert sampled_trimmed == blob, "Byte mismatches in render→readback (optical)."


def test_render_and_readback_youtube():
    """Same test for youtube mode (8x8 cells, 1-bit)."""
    mode = MODES["youtube"]
    capacity_bytes = mode.payload_capacity_bytes + 43
    blob = bytes(range(256)) * (capacity_bytes // 256) + bytes(range(capacity_bytes % 256))
    blob = blob[:capacity_bytes]

    img = render_frame(blob, mode)
    gray = np.array(img)
    if mode.channels == 3:
        gray = gray[:, :, ::-1]
    sampled_bytes = sample_bytes(gray, mode)
    
    sampled_trimmed = sampled_bytes[:len(blob)]
    assert sampled_trimmed == blob, "Byte mismatches in render→readback (youtube)."


def test_border_cells_are_checkerboard():
    """Verify sync border has alternating B/W pattern."""
    mode = MODES["archive"]
    blob = b'\xAA' * (mode.payload_capacity_bytes + 43)
    img = render_frame(blob, mode)
    gray = np.array(img)
    cs = mode.cell_size
    b  = mode.border_cells

    top_left_val = gray[cs // 2, cs // 2]
    if isinstance(top_left_val, np.ndarray):
        assert np.array_equal(top_left_val, [255, 255, 255]), f"Expected white border cell at (0,0), got {top_left_val}"
    else:
        assert top_left_val == 255, f"Expected white border cell at (0,0), got {top_left_val}"

    next_val = gray[cs // 2, cs + cs // 2]
    if isinstance(next_val, np.ndarray):
        assert np.array_equal(next_val, [0, 0, 0]), f"Expected black border cell at (0,1), got {next_val}"
    else:
        assert next_val == 0, f"Expected black border cell at (0,1), got {next_val}"
