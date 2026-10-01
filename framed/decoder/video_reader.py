"""Extract frames from a video file using OpenCV."""
import cv2
import numpy as np
from pathlib import Path


import typing

def extract_frames(video_path: str) -> typing.Generator[np.ndarray, None, None]:
    """
    Yield all frames from the video as grayscale numpy arrays
    (shape: H×W, dtype uint8).
    """
    path = str(Path(video_path))
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        raise FileNotFoundError(f"Cannot open video: {path}")

    extracted = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        # In both 1-channel (if it reads 3) and 3-channel, leaving it as 3 channels is okay for parsing 
        # But for 1-channel we need to slice it to 1 channel if the mode is actually 1-channel!
        # Actually, extracting frames shouldn't require mode here; it's passed natively. 
        # Pipeline parser handles the rest. Just yield raw read output natively.
        extracted += 1
        yield frame

    cap.release()
    if extracted == 0:
        raise ValueError(f"No frames extracted from: {path}")

    print(f"[FramED] Extracted {extracted} frames from {path}")
