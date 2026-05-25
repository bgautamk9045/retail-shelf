# model/camera.py  — replace the whole file with this
import cv2
import os
import numpy as np

class CameraReader:
    def __init__(self):
        cam = os.getenv("CAMERA_URL", "0")
        src = int(cam) if cam.isdigit() else cam
        self.cap = cv2.VideoCapture(src)
        self.dummy_mode = not self.cap.isOpened()
        if self.dummy_mode:
            print("WARNING: Camera not available, using dummy frames")

    def read_frame(self):
        if self.dummy_mode:
            # Return a blank test frame so the API doesn't crash
            return np.zeros((640, 640, 3), dtype=np.uint8)
        ret, frame = self.cap.read()
        return frame if ret else None

    def release(self):
        if not self.dummy_mode:
            self.cap.release()