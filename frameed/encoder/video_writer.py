"""
Stitch rendered PNG frames into a lossless video.

Priority:
  1. FFmpeg with FFV1 codec (truly lossless, smallest file) — requires ffmpeg on PATH.
  2. OpenCV VideoWriter with HFYU (Huffyuv lossless).
  3. OpenCV VideoWriter with FFV1 (if OpenCV built with it).
  4. OpenCV VideoWriter with DIB  (uncompressed RGB — always works, large files).

The decoder (video_reader.py) uses OpenCV to read, so all options are compatible.
"""
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from frameed.config import ModeConfig


# ── Helpers ───────────────────────────────────────────────────────────────────

def _ffmpeg_available() -> bool:
    return shutil.which('ffmpeg') is not None


def _write_ffmpeg(images: list[Image.Image], output_path: str, mode: ModeConfig) -> None:
    """FFmpeg path: saves PNGs to temp dir, muxes with FFV1 lossless codec."""
    with tempfile.TemporaryDirectory(prefix='frameed_') as tmp_dir:
        for idx, img in enumerate(images):
            img.save(os.path.join(tmp_dir, f'frame_{idx:06d}.png'), format='PNG')

        pattern = os.path.join(tmp_dir, 'frame_%06d.png')
        cmd = [
            'ffmpeg', '-y',
            '-framerate', str(mode.fps),
            '-i', pattern,
            '-vcodec', 'ffv1',
            '-pix_fmt', 'gray',
            output_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(
                f"FFmpeg failed (exit {result.returncode}):\n{result.stderr}"
            )


def _write_opencv(images: list[Image.Image], output_path: str, mode: ModeConfig) -> None:
    """OpenCV fallback path: tries lossless codecs in order."""
    w, h = mode.resolution

    # Try codecs in order of preference (lossless first)
    candidates = [
        ('HFYU', 'Huffyuv lossless'),
        ('FFV1', 'FFV1 lossless'),
        ('DIB ', 'Uncompressed (large file)'),
    ]

    writer = None
    chosen = None
    for fourcc_str, label in candidates:
        fourcc = cv2.VideoWriter_fourcc(*fourcc_str)
        w_test = cv2.VideoWriter(output_path, fourcc, float(mode.fps), (w, h), isColor=False)
        if w_test.isOpened():
            writer = w_test
            chosen = label
            break
        w_test.release()

    if writer is None or not writer.isOpened():
        raise RuntimeError(
            "No working lossless VideoWriter codec found. "
            "Install FFmpeg (https://ffmpeg.org/download.html) and add it to PATH."
        )

    print(f"[FrameED] Using OpenCV VideoWriter ({chosen}). "
          f"Note: install FFmpeg for smaller, guaranteed-lossless files.")

    for img in images:
        frame = np.array(img, dtype=np.uint8)
        writer.write(frame)
    writer.release()


# ── Public API ────────────────────────────────────────────────────────────────

def frames_to_video(
    images: list[Image.Image],
    output_path: str,
    mode: ModeConfig,
) -> str:
    """
    Encode images into a lossless AVI file.
    Uses FFmpeg if available, otherwise falls back to OpenCV VideoWriter.
    Returns the path of the written file.
    """
    if not images:
        raise ValueError("No frames to write.")

    output_path = str(Path(output_path).with_suffix('.avi'))

    if _ffmpeg_available():
        _write_ffmpeg(images, output_path, mode)
    else:
        print("[FrameED] FFmpeg not found on PATH — falling back to OpenCV VideoWriter.")
        _write_opencv(images, output_path, mode)

    print(f"[FrameED] Video written -> {output_path}")
    print(f"[FrameED] {len(images)} frames @ {mode.fps} FPS  "
          f"({mode.resolution[0]}×{mode.resolution[1]}, cell={mode.cell_size}×{mode.cell_size}px)")
    return output_path
