"""
End-to-end round-trip test: encode a synthetic binary file → video → decode.
Verifies byte-for-byte identity without requiring FFmpeg
by testing pipeline components individually.
"""
import os
import tempfile
import pytest
from pathlib import Path

from frameed.config import MODES
from frameed.pipeline import encode_file, decode_file


@pytest.fixture
def sample_file(tmp_path):
    """Write a 50 KB synthetic binary test file."""
    data = bytes(range(256)) * 200   # 51,200 bytes, full byte range
    src = tmp_path / "test_input.bin"
    src.write_bytes(data)
    return str(src), data


def test_roundtrip_archive(sample_file, tmp_path):
    """Archive mode: encode → decode → identical bytes."""
    src_path, original = sample_file
    video_path = str(tmp_path / "output.avi")
    out_dir    = str(tmp_path / "decoded")

    pytest.importorskip("cv2", reason="opencv-python required")
    _check_ffmpeg()

    encode_file(src_path, video_path, mode_name="archive")
    assert os.path.exists(video_path), "Video file not created."
    assert os.path.getsize(video_path) > 0

    result_path = decode_file(video_path, out_dir)
    assert os.path.exists(result_path), "Decoded file not created."
    recovered = Path(result_path).read_bytes()
    assert recovered == original, (
        f"Round-trip mismatch: original {len(original)} B, recovered {len(recovered)} B"
    )


def test_roundtrip_with_encryption(sample_file, tmp_path):
    """Archive mode + AES-256-GCM encryption round-trip."""
    src_path, original = sample_file
    video_path = str(tmp_path / "output_enc.avi")
    out_dir    = str(tmp_path / "decoded_enc")

    pytest.importorskip("cv2", reason="opencv-python required")
    _check_ffmpeg()

    encode_file(src_path, video_path, mode_name="archive", password="s3cr3t!")
    result_path = decode_file(video_path, out_dir, password="s3cr3t!")
    recovered = Path(result_path).read_bytes()
    assert recovered == original


def _check_ffmpeg():
    import subprocess
    r = subprocess.run(["ffmpeg", "-version"], capture_output=True)
    if r.returncode != 0:
        pytest.skip("FFmpeg not found on PATH")
