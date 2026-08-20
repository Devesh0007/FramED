"""
Render frame blobs into B&W PIL images.

Layout of every output image:
  ┌──────────────────────────────────────┐
  │  border (checkerboard, 2-cell wide)  │
  │  ┌────────────────────────────────┐  │
  │  │  data cells (inner grid)       │  │
  │  │  bits: left→right, top→bottom  │  │
  │  └────────────────────────────────┘  │
  └──────────────────────────────────────┘

Each cell is cell_size × cell_size pixels.
  bit 0 → black  (0)
  bit 1 → white  (255)
Unused inner cells (padding at end of last frame) → grey (128).
"""
import numpy as np
from PIL import Image

from frameed.config import ModeConfig
from frameed.utils import bytes_to_bits


def render_frame(blob: bytes, mode: ModeConfig) -> Image.Image:
    """Convert a frame blob → PIL grayscale image (mode='L')."""
    cs   = mode.cell_size
    w, h = mode.resolution
    b    = mode.border_cells

    # Canvas (neutral grey = unused cells)
    canvas = np.full((h, w), 128, dtype=np.uint8)

    # ── Border: checkerboard ────────────────────────────────────────────────
    gcols = mode.grid_cols
    grows = mode.grid_rows
    for gr in range(grows):
        for gc in range(gcols):
            is_border = gr < b or gr >= grows - b or gc < b or gc >= gcols - b
            if is_border:
                val = 255 if (gr + gc) % 2 == 0 else 0
                canvas[gr * cs:(gr + 1) * cs, gc * cs:(gc + 1) * cs] = val

    # ── Inner data cells ────────────────────────────────────────────────────
    bits    = bytes_to_bits(blob)
    bit_idx = 0
    inner_r_start = b
    inner_r_end   = grows - b
    inner_c_start = b
    inner_c_end   = gcols - b

    for gr in range(inner_r_start, inner_r_end):
        for gc in range(inner_c_start, inner_c_end):
            val = 255 if bits[bit_idx] else 0
            canvas[gr * cs:(gr + 1) * cs, gc * cs:(gc + 1) * cs] = val
            bit_idx += 1
            if bit_idx >= len(bits):
                # Fill remaining cells grey (padding) → already grey
                break
        if bit_idx >= len(bits):
            break

    return Image.fromarray(canvas, mode='L')
