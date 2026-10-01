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

from framed.config import ModeConfig


from typing import Iterable

# ── Helpers ───────────────────────────────────────────────────────────────────

def _ffmpeg_available() -> bool:
    return shutil.which('ffmpeg') is not None or os.path.exists('ffmpeg.exe')


def _write_ffmpeg(images: Iterable[Image.Image], output_path: str, mode: ModeConfig) -> None:
    """FFmpeg path: uses stdin pipe to mux directly to bypass IO stalls."""
    w, h = mode.resolution
    ch = getattr(mode, 'channels', 1)
    pix_fmt = 'bgr24' if ch == 3 else 'gray'
    
    crf_val = str(getattr(mode, 'video_crf', 0))
    if crf_val == '0':
        out_pix_fmt = 'bgr24' if ch == 3 else 'gray'
        codec = 'libx264rgb' if ch == 3 else 'libx264'
    else:
        out_pix_fmt = 'yuv420p' if ch == 3 else 'gray'
        codec = 'libx264'
        
    cmd = [
        'ffmpeg', '-y',
        '-f', 'rawvideo',
        '-vcodec', 'rawvideo',
        '-s', f'{w}x{h}',
        '-pix_fmt', pix_fmt,
        '-framerate', str(mode.fps),
        '-i', '-',
        '-c:v', codec,
        '-pix_fmt', out_pix_fmt,
        '-crf', crf_val,
        '-preset', 'ultrafast' if crf_val == '0' else 'medium',
        output_path
    ]
    process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
    
    try:
        for img in images:
            # OpenCV and FFmpeg bgr24 expect BGR array format.
            arr = np.array(img, dtype=np.uint8)
            if ch == 3:
                arr = arr[:, :, ::-1] # flip RGB from PIL to BGR natively
            process.stdin.write(arr.tobytes())
    except Exception as e:
        process.stdin.close()
        process.kill()
        raise e
        
    process.stdin.close()
    process.wait()
    if process.returncode != 0:
        raise RuntimeError(
            f"FFmpeg failed (exit {process.returncode})"
        )


def _write_opencv(images: Iterable[Image.Image], output_path: str, mode: ModeConfig) -> None:
    """OpenCV fallback path: tries lossless codecs in order."""
    w, h = mode.resolution
    ch = getattr(mode, 'channels', 1)
    is_color = (ch == 3)

    # Try codecs in order of preference (lossless first)
    candidates = [
        ('FFV1', 'FFV1 lossless'),
        ('DIB ', 'Uncompressed (large file)'),
    ]

    writer = None
    chosen = None
    for fourcc_str, label in candidates:
        fourcc = cv2.VideoWriter_fourcc(*fourcc_str)
        w_test = cv2.VideoWriter(output_path, fourcc, float(mode.fps), (w, h), isColor=is_color)
        if w_test.isOpened():
            writer = w_test
            chosen = label
            break
        w_test.release()

    if writer is None or not writer.isOpened():
        raise RuntimeError(
            "No working lossless VideoWriter codec found."
        )

    print(f"[FramED] Using OpenCV VideoWriter ({chosen}).")

    for img in images:
        frame = np.array(img, dtype=np.uint8)
        if ch == 3:
            frame = frame[:, :, ::-1] # Convert PIL RGB to OpenCV BGR
        writer.write(frame)
    writer.release()


# ── Public API ────────────────────────────────────────────────────────────────

def frames_to_video(
    images: Iterable[Image.Image],
    output_path: str,
    mode: ModeConfig,
    total_frames: int = 0
) -> str:
    """
    Encode images into a lossless AVI file.
    Uses FFmpeg if available, otherwise falls back to OpenCV VideoWriter.
    Returns the path of the written file.
    """
    output_path = str(Path(output_path).with_suffix('.avi'))

    if _ffmpeg_available():
        _write_ffmpeg(images, output_path, mode)
    else:
        print("[FramED] FFmpeg not found on PATH — falling back to OpenCV VideoWriter.")
        _write_opencv(images, output_path, mode)

    print(f"[FramED] Video written -> {output_path}")
    print(f"[FramED] (Streamed dynamically @ {mode.fps} FPS  "
          f"{mode.resolution[0]}×{mode.resolution[1]}, cell={mode.cell_size}×{mode.cell_size}px)")
    return output_path
