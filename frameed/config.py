"""
Central configuration: frame header layout, encoding modes, and computed capacities.

Frame blob layout (bits in a video frame, inner grid left-to-right / top-to-bottom):
  [ HEADER 39 B ] [ ECC-encoded payload (variable) ] [ CRC32 of raw payload 4 B ]

HEADER fields (big-endian):
  MAGIC        4 B  b'DV01'
  VERSION      1 B
  TYPE         1 B  FrameType enum
  FRAME_ID     4 B  uint32  (sequential across entire video)
  TOTAL_FRAMES 4 B  uint32
  FILE_ID     16 B  UUID bytes
  CHUNK_ID     4 B  uint32  (DATA: chunk index; PARITY: group start index)
  PAYLOAD_LEN  4 B  uint32  (raw, pre-ECC data length in this frame)
  FLAGS        1 B
"""
import struct
from dataclasses import dataclass
from enum import IntEnum

# ── Protocol constants ────────────────────────────────────────────────────────
MAGIC   = b'DV01'
VERSION = 1

class FrameType(IntEnum):
    MANIFEST = 0x00   # First frame: file metadata as JSON
    DATA     = 0x01   # Compressed (+encrypted) data chunk
    PARITY   = 0x02   # XOR parity for a group of DATA frames

# ── Header struct ─────────────────────────────────────────────────────────────
# !  = big-endian
# 4s = MAGIC, B = VERSION, B = TYPE, I = FRAME_ID, I = TOTAL_FRAMES
# 16s = FILE_ID, I = CHUNK_ID, I = PAYLOAD_LEN, B = FLAGS
HEADER_STRUCT        = struct.Struct('!4sBBII16sIIB')
HEADER_SIZE          = HEADER_STRUCT.size   # 39 bytes
CRC_SIZE             = 4                    # CRC32
FRAME_OVERHEAD_BYTES = HEADER_SIZE + CRC_SIZE  # 43 bytes
FRAME_OVERHEAD_BITS  = FRAME_OVERHEAD_BYTES * 8  # 344 bits

# ── Reed-Solomon settings (GF 2^8) ───────────────────────────────────────────
RS_NSYM       = 0                    # Disabled to bypass pure-Python bottlenecks. XOR parity active.
RS_BLOCK_TOTAL = 255                 # Max RS codeword length
RS_BLOCK_DATA  = RS_BLOCK_TOTAL - RS_NSYM  # Variable block


# ── Mode configuration ────────────────────────────────────────────────────────
@dataclass
class ModeConfig:
    cell_size:     int    # n×n pixels = 1 bit
    resolution:    tuple  # (width_px, height_px)
    fps:           int
    fec_ratio:     float  # parity_frames / data_frames (informational)
    border_cells:  int    # border strip width in cells
    parity_group:  int    # every N data frames → 1 XOR parity frame
    channels:      int = 1 # 1 for grayscale, 3 for RGB

    # ── Derived geometry ──────────────────────────────────────────────────────
    @property
    def grid_cols(self)  -> int: return self.resolution[0] // self.cell_size
    @property
    def grid_rows(self)  -> int: return self.resolution[1] // self.cell_size
    @property
    def inner_cols(self) -> int: return self.grid_cols - 2 * self.border_cells
    @property
    def inner_rows(self) -> int: return self.grid_rows - 2 * self.border_cells
    @property
    def total_inner_cells(self) -> int: return self.inner_cols * self.inner_rows

    @property
    def payload_capacity_bytes(self) -> int:
        """Bytes available for ECC-encoded payload per frame."""
        ch = getattr(self, 'channels', 1)
        return (self.total_inner_cells * ch) - FRAME_OVERHEAD_BYTES

    @property
    def max_rs_blocks(self) -> int:
        """Full RS blocks that fit in the payload area."""
        return self.payload_capacity_bytes // RS_BLOCK_TOTAL

    @property
    def raw_chunk_size(self) -> int:
        """Max raw (pre-ECC) data bytes per DATA frame."""
        return self.max_rs_blocks * RS_BLOCK_DATA

    @property
    def ecc_chunk_size(self) -> int:
        """Bytes written into the frame for the ECC-encoded chunk."""
        return self.max_rs_blocks * RS_BLOCK_TOTAL


MODES: dict[str, ModeConfig] = {
    'archive': ModeConfig(
        cell_size=1,
        resolution=(3840, 2160),
        fps=60,
        fec_ratio=0.10,
        border_cells=20,
        parity_group=8,
        channels=3,
    ),
    'optical': ModeConfig(
        cell_size=8,
        resolution=(1920, 1080),
        fps=30,
        fec_ratio=0.30,
        border_cells=10,
        parity_group=3,
        channels=3,
    )
}
