"""
Quick diagnostic: encode one known frame to a video, read it back,
and check if pixel values are preserved exactly.
"""
import sys
import numpy as np
import cv2
from PIL import Image
from frameed.config import MODES, MAGIC
from frameed.encoder.renderer import render_frame
from frameed.encoder.frame_builder import build_manifest_frame
from frameed.encoder.fec import rs_encode
from frameed.utils import generate_file_id

mode = MODES["archive"]
file_id = generate_file_id()

# 1. Build a real MANIFEST frame blob
blob = build_manifest_frame(
    file_id=file_id,
    total_frames=1,
    filename="test.txt",
    original_size=100,
    processed_size=90,
    mode_name="archive",
    mode=mode,
)
print(f"Blob length: {len(blob)} bytes, starts with magic: {blob[:4]!r}")
print(f"First 8 bytes hex: {blob[:8].hex()}")

# 2. Render to PIL image
pil_img = render_frame(blob, mode)
w, h = mode.resolution
print(f"PIL image size: {pil_img.size}, mode: {pil_img.mode}")

# 3. Convert to numpy (what OpenCV will write)
arr = np.array(pil_img, dtype=np.uint8)
print(f"Numpy array shape: {arr.shape}, dtype: {arr.dtype}")
print(f"Unique pixel values: {np.unique(arr)}")  # should be only [0, 255]

# 4. Write to video using OpenCV (same path as video_writer.py)
out_path = "_debug_test.avi"
fourcc = cv2.VideoWriter_fourcc(*'FFV1')
is_color = getattr(mode, 'channels', 1) == 3
writer = cv2.VideoWriter(out_path, fourcc, mode.fps, (w, h), isColor=is_color)
opened = writer.isOpened()
print(f"VideoWriter opened (FFV1): {opened}")
if not opened:
    writer.release()
    for fc in ('FFV1', 'DIB '):
        fourcc = cv2.VideoWriter_fourcc(*fc)
        writer = cv2.VideoWriter(out_path, fourcc, mode.fps, (w, h), isColor=False)
        if writer.isOpened():
            print(f"Using codec: {fc}")
            break

writer.write(arr)
writer.release()

# 5. Read back with OpenCV (same path as video_reader.py)
cap = cv2.VideoCapture(out_path)
ret, frame = cap.read()
cap.release()
print(f"Read back: ret={ret}, frame shape={frame.shape if ret else None}")

if ret:
    # Convert back to grayscale if needed
    if not is_color and frame.ndim == 3:
        gray = frame[:, :, 0]
        print("NOTE: frame was written as grayscale but read back as BGR — extracted channel 0")
    else:
        gray = frame
    
    # Debug info
    print(f"Readback unique pixel values: {np.unique(gray)}")
    
    # 5. Compare with original array (which is RGB from PIL)
    arr_bgr = arr[:, :, ::-1] if is_color else arr
    diff = np.abs(arr_bgr.astype(int) - gray.astype(int))
    print(f"Max pixel diff: {np.max(diff)}")
    print(f"Pixel-perfect round-trip: {np.array_equal(arr_bgr, gray)}")

    # 6. Try parsing the readback frame
    from frameed.decoder.frame_parser import sample_bytes
    raw = sample_bytes(gray, mode)
    print(f"\nDecoded raw[:8] hex: {raw[:8].hex()}")
    print(f"Expected MAGIC hex:  {MAGIC.hex()}")
    print(f"Magic matches: {raw[:4] == MAGIC}")
