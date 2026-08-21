import cv2
import numpy as np
from frameed.utils import bits_to_bytes

cap = cv2.VideoCapture("youtube_output3.mp4")
ret, frame = cap.read()
if ret:
    frame = cv2.resize(frame, (1920, 1080), interpolation=cv2.INTER_LINEAR)
    samples = frame[42, 42:82:4]
    print("Inner cell samples (raw BGR from OpenCV):")
    for i, s in enumerate(samples):
        print(f"Cell {i}: {s}")
    
    samples_rgb = samples[:, ::-1]
    bits = (samples_rgb >= 128).astype(np.uint8).ravel().tolist()
    print("Extracted bits:", bits)
    print("Bytes:", bits_to_bytes(bits))
