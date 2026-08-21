import cv2
import numpy as np
from frameed.config import MODES
from frameed.encoder.renderer import render_frame
from frameed.decoder.frame_parser import parse_frame
from frameed.encoder.frame_builder import build_frame
from frameed.config import FrameType

mode = MODES['youtube']
capacity = mode.payload_capacity_bytes
blob = bytes(range(256)) * ((capacity) // 256) + bytes(range((capacity) % 256))

frame_blob = build_frame(FrameType.DATA, 1, 1, b'1234567890123456', 0, blob, mode)

# Render
img = render_frame(frame_blob, mode)
rgb = np.array(img)

# Downscale to 720p 
bgr_720p = cv2.resize(rgb[:, :, ::-1], (1280, 720), interpolation=cv2.INTER_LINEAR)

frame = parse_frame(bgr_720p, mode)
if frame is not None and frame.valid:
    print("SUCCESS")
else:
    print("FAILED")
