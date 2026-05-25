import cv2
import numpy as np
from ultralytics import YOLO
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional
import time

@dataclass
class Detection:
    label: str          # product name
    confidence: float   # 0.0 - 1.0
    bbox: list          # [x1, y1, x2, y2]
    slot_id: str        # shelf zone like "A1", "B3"

@dataclass
class ShelfAnalysis:
    timestamp: float
    detections: List[Detection]
    out_of_stock: List[str]      # slot IDs with no product
    misplaced: List[str]         # slots where wrong item found
    frame_path: Optional[str]

class ShelfDetector:
    def __init__(self, model_path: str = "yolov8n.pt"):
        # Load pretrained YOLOv8 (or your fine-tuned weights)
        self.model = YOLO(model_path)
        self.conf_threshold = 0.5

    def preprocess(self, frame: np.ndarray) -> np.ndarray:
        """Resize + normalize frame for model input"""
        frame = cv2.resize(frame, (640, 640))
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return frame

    def get_slot_id(self, bbox: list, shelf_zones: dict) -> str:
        """Map bounding box center to a shelf slot ID"""
        cx = (bbox[0] + bbox[2]) / 2
        cy = (bbox[1] + bbox[3]) / 2
        for slot_id, (x1, y1, x2, y2) in shelf_zones.items():
            if x1 <= cx <= x2 and y1 <= cy <= y2:
                return slot_id
        return "unknown"

    def detect(self, frame: np.ndarray, shelf_zones: dict) -> List[Detection]:
        """Run YOLOv8 on a single frame"""
        results = self.model(frame, conf=self.conf_threshold)
        detections = []
        for r in results:
            for box in r.boxes:
                bbox = box.xyxy[0].tolist()
                label = self.model.names[int(box.cls)]
                conf  = float(box.conf)
                slot  = self.get_slot_id(bbox, shelf_zones)
                detections.append(Detection(label, conf, bbox, slot))
        return detections

    def analyze_shelf(self, frame, shelf_zones, planogram) -> ShelfAnalysis:
        """Full pipeline: detect → compare planogram → flag issues"""
        processed = self.preprocess(frame)
        detections = self.detect(processed, shelf_zones)

        detected_by_slot = {d.slot_id: d.label for d in detections}

        out_of_stock, misplaced = [], []
        for slot_id, expected_product in planogram.items():
            actual = detected_by_slot.get(slot_id)
            if actual is None:
                out_of_stock.append(slot_id)   # nothing detected
            elif actual != expected_product:
                misplaced.append(slot_id)      # wrong product

        return ShelfAnalysis(
            timestamp=time.time(),
            detections=detections,
            out_of_stock=out_of_stock,
            misplaced=misplaced,
            frame_path=None
        )