import cv2
from frameed.config import MODES
from frameed.decoder.frame_parser import parse_frame, sample_bytes

cap = cv2.VideoCapture("youtube_output3.mp4")
ret, frame = cap.read()
if ret:
    print("Frame shape:", frame.shape)
    mode = MODES["youtube"]
    f = parse_frame(frame, mode)
    if f:
        print(f"Valid: {f.valid}, Type: {f.frame_type}")
    else:
        print("parse_frame returned None")
        
        target_width, target_height = mode.resolution
        if frame.shape[:2] != (target_height, target_width):
            frame = cv2.resize(frame, (target_width, target_height), interpolation=cv2.INTER_LINEAR)
        raw = sample_bytes(frame, mode)
        print("Raw slice size:", len(raw))
        print("Magic bytes:", raw[:4])
else:
    print("Failed to read video youtube_output3.mp4")
