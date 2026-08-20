"""Test B&W cell rendering and pixel-level readback accuracy."""
import numpy as np
import pytest
from frameed.config import MODES
from frameed.encoder.renderer import render_frame
from frameed.decoder.frame_parser import sample_bits
from frameed.utils import bytes_to_bits, bits_to_bytes


def test_render_and_readback_archive():
    """Render a known blob and verify every sampled bit matches."""
    mode = MODES["archive"]
    # Create a blob that fills exactly the inner capacity
    capacity_bytes = mode.payload_capacity_bytes + 43  # header overhead
    blob = bytes(range(256)) * (capacity_bytes // 256) + bytes(range(capacity_bytes % 256))
    blob = blob[:capacity_bytes]

    img = render_frame(blob, mode)
    gray = np.array(img)
    sampled_bits = sample_bits(gray, mode)

    expected_bits = bytes_to_bits(blob)
    # Compare only the first len(expected_bits) sampled bits
    sampled_trimmed = sampled_bits[:len(expected_bits)]
    mismatches = sum(a != b for a, b in zip(expected_bits, sampled_trimmed))
    assert mismatches == 0, f"{mismatches} bit mismatches found in render→readback."


def test_render_and_readback_optical():
    """Same test for optical mode (8×8 cells)."""
    mode = MODES["optical"]
    capacity_bytes = mode.payload_capacity_bytes + 43
    blob = bytes(range(256)) * (capacity_bytes // 256) + bytes(range(capacity_bytes % 256))
    blob = blob[:capacity_bytes]

    img = render_frame(blob, mode)
    gray = np.array(img)
    sampled_bits = sample_bits(gray, mode)
    expected_bits = bytes_to_bits(blob)
    sampled_trimmed = sampled_bits[:len(expected_bits)]
    mismatches = sum(a != b for a, b in zip(expected_bits, sampled_trimmed))
    assert mismatches == 0, f"{mismatches} bit mismatches in optical render→readback."


def test_border_cells_are_checkerboard():
    """Verify sync border has alternating B/W pattern."""
    mode = MODES["archive"]
    blob = b'\xAA' * (mode.payload_capacity_bytes + 43)
    img = render_frame(blob, mode)
    gray = np.array(img)
    cs = mode.cell_size
    b  = mode.border_cells

    # Top-left border cell should be white (row+col = 0+0 = even → 255)
    top_left_val = gray[cs // 2, cs // 2]
    assert top_left_val == 255, f"Expected white border cell at (0,0), got {top_left_val}"

    # Adjacent cell (row=0, col=1) should be black
    next_val = gray[cs // 2, cs + cs // 2]
    assert next_val == 0, f"Expected black border cell at (0,1), got {next_val}"
