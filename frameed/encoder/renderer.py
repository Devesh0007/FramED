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
    """
    Render a single deterministic video frame payload onto arrays.
    """
    cs    = mode.cell_size
    b     = mode.border_cells
    gcols = mode.grid_cols
    grows = mode.grid_rows
    ch    = getattr(mode, 'channels', 1)

    if grows <= 2*b or gcols <= 2*b:
        raise ValueError(f"Resolution too small for borders: {grows}x{gcols}")

    if ch == 1:
        grid = np.full((grows, gcols), 128, dtype=np.uint8)
        R, C = np.indices((grows, gcols))
        checkerboard = np.where((R + C) % 2 == 0, 255, 0).astype(np.uint8)
        
        # Border
        grid[:b, :] = checkerboard[:b, :]
        grid[-b:, :] = checkerboard[-b:, :]
        grid[:, :b] = checkerboard[:, :b]
        grid[:, -b:] = checkerboard[:, -b:]
    else:
        grid = np.full((grows, gcols, ch), 128, dtype=np.uint8)
        R, C = np.indices((grows, gcols))
        mask = ((R + C) % 2 == 0)
        grid[mask] = [255, 255, 255]
        grid[~mask] = [0, 0, 0]

        # Reset inner grid to 128 (protecting borders)
        grid[b:grows-b, b:gcols-b] = [128, 128, 128]

    # Inner cells
    inner_rows = mode.inner_rows
    inner_cols = mode.inner_cols
    
    if inner_rows > 0 and inner_cols > 0:
        max_cells = inner_rows * inner_cols * ch
        if len(blob) > 0:
            pixel_arr = np.frombuffer(blob, dtype=np.uint8)
            num_bytes = min(len(pixel_arr), max_cells)
            
            if num_bytes > 0:
                inner_grid = np.full(max_cells, 128, dtype=np.uint8)
                inner_grid[:num_bytes] = pixel_arr[:num_bytes]
                if ch == 1:
                    grid[b:grows-b, b:gcols-b] = inner_grid.reshape((inner_rows, inner_cols))
                else:
                    grid[b:grows-b, b:gcols-b] = inner_grid.reshape((inner_rows, inner_cols, ch))

    # Scale up if cell_size > 1
    if cs > 1:
        grid = grid.repeat(cs, axis=0).repeat(cs, axis=1)

    if ch == 1:
        return Image.fromarray(grid, mode='L')
    else:
        return Image.fromarray(grid, mode='RGB')
