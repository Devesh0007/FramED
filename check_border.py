import cv2
import numpy as np

cap = cv2.VideoCapture("youtube_output3.mp4")
ret, frame = cap.read()
if ret:
    frame = cv2.resize(frame, (1920, 1080), interpolation=cv2.INTER_LINEAR)
    print("0,0 val:", frame[2, 2])
    print("0,1 val:", frame[2, 6])
    print("1,0 val:", frame[6, 2])
    print("1,1 val:", frame[6, 6])
    print("9,9 val:", frame[38, 38])
    print("Row 0 all 10 cells (channel 0): ", frame[2, 2:40:4, 0])
else:
    print("Failed")
