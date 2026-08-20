"""Extract frames from a video file using OpenCV."""
import cv2
import numpy as np
from pathlib import Path


def extract_frames(video_path: str) -> list[np.ndarray]:
    """
    Return all frames from the video as a list of grayscale numpy arrays
    (shape: H×W, dtype uint8).
    """
    path = str(Path(video_path))
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        raise FileNotFoundError(f"Cannot open video: {path}")

    frames = []
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if len(frame.shape) == 3:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            gray = frame
        frames.append(gray)

    cap.release()
    if not frames:
        raise ValueError(f"No frames extracted from: {path}")

    print(f"[FrameED] Extracted {len(frames)} frames from {path}")
    return frames
