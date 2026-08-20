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
        if len(frame.shape) == 3:
            gray = frame[:, :, 0]  # R=G=B for grayscale; direct slice avoids cvtColor integer rounding
        else:
            gray = frame
        extracted += 1
        yield gray

    cap.release()
    if extracted == 0:
        raise ValueError(f"No frames extracted from: {path}")

    print(f"[FrameED] Extracted {extracted} frames from {path}")
