"""
main.py
-------
Main entry point for the Real-Time Object Detection & Logging Platform.
Can launch either the interactive Streamlit Web Dashboard or a native OpenCV
desktop window feed with real-time MySQL event logging.

Usage:
    python main.py         -> Launches the Streamlit Dashboard (ui.py)
    python main.py --cv    -> Launches the native OpenCV Desktop GUI
    python main.py --init  -> Initializes MySQL Database and Schema
"""

import sys
import os
import argparse
import time
import cv2

from database import db_manager
from detector import YOLODetector


def run_opencv_mode(camera_index: int = 0, conf_threshold: float = 0.50, cooldown: float = 1.0):
    """
    Runs real-time object detection directly in a native OpenCV window.
    Logs events to MySQL according to configured parameters.
    """
    print("\n=======================================================")
    print("   VisionPulse: OpenCV Desktop Detection Mode")
    print("=======================================================")
    print("Press 'q' in the video window to quit.")
    print("Press 's' to print current database status.")
    print(f"Confidence Threshold: {conf_threshold:.2f} | Cooldown: {cooldown}s\n")

    # Initialize Database
    db_ok, msg = db_manager.init_db()
    print(f"[*] Database Status: {msg}")

    # Load YOLO Detector
    print("[*] Loading YOLOv8 model (yolov8n.pt)...")
    detector = YOLODetector(model_name="yolov8n.pt")
    print("[*] YOLOv8 loaded successfully.")

    # Target classes: None = detect all 80 classes, or filter to specific items
    target_classes = ["person", "cell phone", "bottle", "laptop", "chair"]
    print(f"[*] Active target filters: {target_classes}")

    # Open webcam
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        print(f"[ERROR] Cannot open webcam index {camera_index}. Please check device.")
        return

    prev_time = time.time()

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("[WARNING] Failed to capture video frame.")
                break

            # Process frame through YOLO
            annotated_frame, detections = detector.process_frame(
                frame=frame,
                target_classes=target_classes,
                conf_threshold=conf_threshold,
            )

            # Log to MySQL with cooldown
            for det in detections:
                obj_cls = det["object_class"]
                if detector.should_log(obj_cls, cooldown_seconds=cooldown):
                    logged = db_manager.log_detection(
                        object_class=det["object_class"],
                        confidence=det["confidence"],
                        bbox_x=det["bbox_x"],
                        bbox_y=det["bbox_y"],
                        bbox_w=det["bbox_w"],
                        bbox_h=det["bbox_h"],
                    )
                    status_text = "MySQL" if logged else "Buffer"
                    print(f"[{status_text} LOGGED] {obj_cls} ({det['confidence']:.1%}) @ [{det['bbox_x']},{det['bbox_y']},{det['bbox_w']},{det['bbox_h']}]")

            # FPS calculation and overlay
            curr_time = time.time()
            fps = 1.0 / max(curr_time - prev_time, 1e-5)
            prev_time = curr_time

            cv2.putText(
                annotated_frame,
                f"FPS: {fps:.1f} | Objects: {len(detections)}",
                (15, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0),
                2,
                cv2.LINE_AA,
            )

            cv2.imshow("VisionPulse - Real-Time YOLO Detection", annotated_frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                print("[*] Quitting detection window...")
                break
            elif key == ord("s"):
                stats = db_manager.get_statistics()
                print(f"[STATUS] Total Logs: {stats['total_detections']} | Connected: {stats['connected']}")

    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("[*] Video stream released and windows closed.")


def run_streamlit_mode():
    """Launches the Streamlit interactive dashboard (ui.py)."""
    import subprocess

    ui_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui.py")
    print(f"\n[*] Launching Streamlit Dashboard: {ui_path}")
    print("[*] Press Ctrl+C in terminal to stop dashboard server.\n")
    cmd = [sys.executable, "-m", "streamlit", "run", ui_path]
    subprocess.run(cmd)


def main():
    parser = argparse.ArgumentParser(description="Real-Time Object Detection & Logging Platform")
    parser.add_argument(
        "--cv",
        action="store_true",
        help="Run detection inside a native OpenCV desktop window",
    )
    parser.add_argument(
        "--ui",
        action="store_true",
        help="Run the Streamlit web dashboard (Default)",
    )
    parser.add_argument(
        "--init",
        action="store_true",
        help="Initialize the MySQL database and table schema",
    )
    parser.add_argument(
        "--cam",
        type=int,
        default=0,
        help="Webcam device index (default: 0)",
    )
    parser.add_argument(
        "--conf",
        type=float,
        default=0.50,
        help="Confidence threshold (default: 0.50)",
    )

    args = parser.parse_args()

    if args.init:
        print("[*] Initializing MySQL Database...")
        ok, msg = db_manager.init_db()
        print(f"Result: {msg}")
        return

    if args.cv:
        run_opencv_mode(camera_index=args.cam, conf_threshold=args.conf)
    else:
        # Default mode launches Streamlit UI
        run_streamlit_mode()


if __name__ == "__main__":
    main()
