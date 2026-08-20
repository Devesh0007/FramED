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

    gcols = mode.grid_cols
    grows = mode.grid_rows
    
    # ── Grid (pre-scale) ───────────
    grid = np.full((grows, gcols), 128, dtype=np.uint8)
    
    # Border
    # Checkboard pattern: (row + col) % 2 == 0 -> 255 else 0
    R, C = np.indices((grows, gcols))
    checkerboard = np.where((R + C) % 2 == 0, 255, 0).astype(np.uint8)
    
    # Fill border
    mask = np.ones((grows, gcols), dtype=bool)
    if b > 0 and grows > 2*b and gcols > 2*b:
        mask[b:-b, b:-b] = False
    grid[mask] = checkerboard[mask]

    # ── Inner data cells ────────────────────────────────────────────────────
    inner_r_start = b
    inner_r_end   = grows - b
    inner_c_start = b
    inner_c_end   = gcols - b
    
    inner_rows = inner_r_end - inner_r_start
    inner_cols = inner_c_end - inner_c_start
    
    if inner_rows > 0 and inner_cols > 0:
        max_cells = inner_rows * inner_cols
        if len(blob) > 0:
            pixel_arr = np.frombuffer(blob, dtype=np.uint8)
            num_bytes = min(len(pixel_arr), max_cells)
            
            if num_bytes > 0:
                inner_grid = np.full(max_cells, 128, dtype=np.uint8)
                inner_grid[:num_bytes] = pixel_arr[:num_bytes]
                grid[inner_r_start:inner_r_end, inner_c_start:inner_c_end] = inner_grid.reshape((inner_rows, inner_cols))

    # Scale up if cell_size > 1
    if cs > 1:
        grid = np.repeat(np.repeat(grid, cs, axis=0), cs, axis=1)

    canvas[:grid.shape[0], :grid.shape[1]] = grid

    return Image.fromarray(canvas, mode='L')
