"""
detector.py
-----------
Real-Time YOLO Object Detection module using Ultralytics YOLOv8.
Handles model loading, inference on video/camera frames, class filtering,
confidence thresholding, bounding box visualization, and coordinate extraction.
"""

import time
from typing import List, Dict, Tuple, Optional
import cv2
import numpy as np
from ultralytics import YOLO


class YOLODetector:
    """Encapsulates the YOLO model and frame detection logic."""

    def __init__(self, model_name: str = "yolov8n.pt"):
        """
        Initializes the YOLO detector.
        Downloads pre-trained weights automatically on first run if not present.
        """
        self.model_name = model_name
        self.model = YOLO(model_name)
        # Class names mapping (80 COCO classes)
        self.class_names = self.model.names if hasattr(self.model, "names") else {}
        # Cooldown tracker to prevent database flooding: {object_class: last_logged_timestamp}
        self.last_log_times: Dict[str, float] = {}

    def get_available_classes(self) -> List[str]:
        """Returns sorted list of all supported class names from the model."""
        return sorted(list(self.class_names.values()))

    def process_frame(
        self,
        frame: np.ndarray,
        target_classes: Optional[List[str]] = None,
        conf_threshold: float = 0.5,
    ) -> Tuple[np.ndarray, List[Dict]]:
        """
        Runs object detection on a single video frame.

        Parameters:
        - frame: BGR image from OpenCV
        - target_classes: List of class strings to detect (None or empty means all classes)
        - conf_threshold: Minimum confidence score (0.0 to 1.0)

        Returns:
        - annotated_frame: Frame with drawn bounding boxes and labels
        - detections: List of dicts with keys:
            ['object_class', 'confidence', 'bbox_x', 'bbox_y', 'bbox_w', 'bbox_h']
        """
        if frame is None:
            return frame, []

        annotated_frame = frame.copy()
        h_frame, w_frame = annotated_frame.shape[:2]
        detections: List[Dict] = []

        # Run inference using YOLOv8
        results = self.model(annotated_frame, conf=conf_threshold, verbose=False)

        if not results or len(results) == 0:
            return annotated_frame, detections

        result = results[0]
        boxes = result.boxes

        if boxes is None or len(boxes) == 0:
            return annotated_frame, detections

        for box in boxes:
            cls_id = int(box.cls[0].item())
            class_name = self.class_names.get(cls_id, f"cls_{cls_id}")
            confidence = float(box.conf[0].item())

            # Apply target classes filter if specified
            if target_classes and len(target_classes) > 0:
                if class_name not in target_classes:
                    continue

            # Extract coordinates: xyxy format -> [x1, y1, x2, y2]
            xyxy = box.xyxy[0].cpu().numpy().astype(int)
            x1, y1, x2, y2 = xyxy

            # Clip within frame dimensions
            x1 = max(0, min(x1, w_frame - 1))
            y1 = max(0, min(y1, h_frame - 1))
            x2 = max(0, min(x2, w_frame - 1))
            y2 = max(0, min(y2, h_frame - 1))

            bbox_w = max(1, x2 - x1)
            bbox_h = max(1, y2 - y1)

            detections.append({
                "object_class": class_name,
                "confidence": round(confidence, 4),
                "bbox_x": int(x1),
                "bbox_y": int(y1),
                "bbox_w": int(bbox_w),
                "bbox_h": int(bbox_h),
            })

            # Draw visual bounding box and stylized badge
            self._draw_detection_overlay(annotated_frame, x1, y1, x2, y2, class_name, confidence)

        return annotated_frame, detections

    def should_log(self, object_class: str, cooldown_seconds: float = 1.0) -> bool:
        """
        Rate limiting check: returns True if enough time has passed
        since this object class was last recorded into the database.
        """
        now = time.time()
        last_time = self.last_log_times.get(object_class, 0.0)
        if (now - last_time) >= cooldown_seconds:
            self.last_log_times[object_class] = now
            return True
        return False

    def _draw_detection_overlay(
        self,
        frame: np.ndarray,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        class_name: str,
        confidence: float,
    ):
        """Draws a clean, modern bounding box and label banner on the frame."""
        # Distinct color palette per class based on hash
        color_seed = abs(hash(class_name)) % 360
        # Convert simple HSV color to BGR for vibrant distinct colors
        hsv_color = np.uint8([[[color_seed // 2, 220, 240]]])
        bgr_color = cv2.cvtColor(hsv_color, cv2.COLOR_HSV2BGR)[0][0]
        color = (int(bgr_color[0]), int(bgr_color[1]), int(bgr_color[2]))

        # Draw main bounding box
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2, cv2.LINE_AA)

        # Draw corner accents for high-tech aesthetic
        corner_len = min(20, (x2 - x1) // 4, (y2 - y1) // 4)
        if corner_len > 3:
            thick = 3
            # Top-left
            cv2.line(frame, (x1, y1), (x1 + corner_len, y1), color, thick)
            cv2.line(frame, (x1, y1), (x1, y1 + corner_len), color, thick)
            # Top-right
            cv2.line(frame, (x2, y1), (x2 - corner_len, y1), color, thick)
            cv2.line(frame, (x2, y1), (x2, y1 + corner_len), color, thick)
            # Bottom-left
            cv2.line(frame, (x1, y2), (x1 + corner_len, y2), color, thick)
            cv2.line(frame, (x1, y2), (x1, y2 - corner_len), color, thick)
            # Bottom-right
            cv2.line(frame, (x2, y2), (x2 - corner_len, y2), color, thick)
            cv2.line(frame, (x2, y2), (x2, y2 - corner_len), color, thick)

        # Draw Label badge background
        label_text = f"{class_name.capitalize()} {confidence:.1%}"
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.55
        thickness = 1
        (text_w, text_h), baseline = cv2.getTextSize(label_text, font, font_scale, thickness)

        label_y1 = max(0, y1 - text_h - 8)
        label_y2 = y1
        label_x2 = min(frame.shape[1], x1 + text_w + 10)

        # Badge rectangle
        cv2.rectangle(frame, (x1, label_y1), (label_x2, label_y2), color, -1)
        # Text in contrasting dark color or white
        cv2.putText(
            frame,
            label_text,
            (x1 + 5, y1 - 4),
            font,
            font_scale,
            (255, 255, 255),
            thickness,
            cv2.LINE_AA,
        )
