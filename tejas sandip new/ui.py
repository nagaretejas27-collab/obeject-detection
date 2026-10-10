"""
ui.py
-----
Interactive Dashboard for Real-Time Object Detection & Event Logging.
Built with Streamlit, OpenCV, YOLOv8, and MySQL.
"""

import time
import cv2
import numpy as np
import pandas as pd
import streamlit as st
from PIL import Image

from detector import YOLODetector
from database import db_manager

# Page Configuration
st.set_page_config(
    page_title="VisionPulse | Object Detection & Logging Platform",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS styling for modern dashboard UI
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        color: #1E293B;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        color: #64748B;
        font-size: 1.05rem;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 16px;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .status-badge-online {
        background-color: #DCFCE7;
        color: #15803D;
        padding: 4px 10px;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.85rem;
        display: inline-block;
    }
    .status-badge-offline {
        background-color: #FEE2E2;
        color: #B91C1C;
        padding: 4px 10px;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.85rem;
        display: inline-block;
    }
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def load_detector():
    """Initializes and caches the YOLO detector instance."""
    return YOLODetector(model_name="yolov8n.pt")


detector = load_detector()
available_classes = detector.get_available_classes()

# Top Header
col_header_title, col_header_status = st.columns([3, 1])
with col_header_title:
    st.markdown("<div class='main-title'>🎯 Real-Time Object Detection & Logging Platform</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-title'>Ultralytics YOLOv8 • OpenCV • MySQL Event Stream • Streamlit</div>", unsafe_allow_html=True)

# Test MySQL initial state
db_connected, db_msg = db_manager.test_connection()

with col_header_status:
    st.write("")
    if db_connected:
        st.markdown(
            f"<div style='text-align: right;'><span class='status-badge-online'>🟢 MySQL Connected</span></div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"<div style='text-align: right;'><span class='status-badge-offline'>🔴 MySQL Offline (Buffer Mode)</span></div>",
            unsafe_allow_html=True,
        )

# ================= SIDEBAR CONFIGURATION =================
st.sidebar.header("⚙️ Platform Settings")

# 1. Input Source
input_mode = st.sidebar.selectbox(
    "Select Video Feed Source",
    ("Webcam (Real-Time Live)", "Upload Video File", "Upload Static Image"),
    index=0,
)

# 2. Object Configuration Filter
st.sidebar.subheader("🎯 Object Class Filtering")
enable_all_classes = st.sidebar.checkbox("Detect All 80 Classes", value=False)

popular_defaults = ["person", "cell phone", "laptop", "bottle", "chair", "car", "dog", "book"]
if enable_all_classes:
    selected_classes = available_classes
    st.sidebar.caption(f"Currently tracking all {len(available_classes)} object classes.")
else:
    selected_classes = st.sidebar.multiselect(
        "Choose Specific Target Classes",
        options=available_classes,
        default=[c for c in ["person", "cell phone", "bottle", "laptop"] if c in available_classes],
        help="Only objects in this list will be highlighted and logged.",
    )

# 3. Confidence Threshold
st.sidebar.subheader("🎚️ Detection Sensitivity")
conf_threshold = st.sidebar.slider(
    "Confidence Threshold",
    min_value=0.10,
    max_value=1.00,
    value=0.50,
    step=0.05,
    format="%.2f",
    help="Detections below this confidence score will be ignored.",
)

# 4. Database Event Logging Settings
st.sidebar.subheader("🗄️ MySQL Logging Settings")
logging_enabled = st.sidebar.toggle("Enable Database Event Logging", value=True)
cooldown_seconds = st.sidebar.slider(
    "Logging Cooldown Interval (Seconds)",
    min_value=0.2,
    max_value=5.0,
    value=1.0,
    step=0.2,
    help="Limits consecutive database entries per class to prevent database flooding.",
)

with st.sidebar.expander("🛠️ MySQL Connection Info", expanded=False):
    st.text(f"Host: {db_manager.host}:{db_manager.port}")
    st.text(f"Database: {db_manager.database}")
    st.text(f"User: {db_manager.user}")
    if st.button("Initialize / Create Tables", use_container_width=True):
        ok, msg = db_manager.init_db()
        if ok:
            st.success(msg)
        else:
            st.error(msg)


# ================= DASHBOARD METRICS BAR =================
stats = db_manager.get_statistics()
metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)

with metric_col1:
    st.metric(label="Model Loaded", value="YOLOv8n", delta="Pre-trained")
with metric_col2:
    st.metric(label="Target Classes Active", value=len(selected_classes))
with metric_col3:
    st.metric(label="Total Database Logs", value=stats["total_detections"])
with metric_col4:
    st.metric(label="Top Detected Class", value=stats["top_class"])

st.divider()

# ================= MAIN LAYOUT (FEED + LOGS) =================
feed_col, table_col = st.columns([3, 2])

with feed_col:
    st.subheader("📹 Real-Time Video Feed")
    frame_placeholder = st.empty()
    fps_indicator = st.empty()

with table_col:
    st.subheader("📋 Live MySQL Event Logs")
    table_placeholder = st.empty()
    chart_placeholder = st.empty()


def render_logs_and_chart():
    """Refreshes and renders the latest logs table and frequency distribution."""
    logs_df = db_manager.get_recent_logs(limit=10)
    if not logs_df.empty:
        table_placeholder.dataframe(
            logs_df[["timestamp", "object_class", "confidence", "bbox_x", "bbox_y", "bbox_w", "bbox_h"]],
            use_container_width=True,
            height=280,
            hide_index=True,
        )
        # Class distribution chart
        class_counts = logs_df["object_class"].value_counts().reset_index()
        class_counts.columns = ["Object Class", "Count"]
        chart_placeholder.bar_chart(class_counts, x="Object Class", y="Count", color="#3B82F6")
    else:
        table_placeholder.info("No detections recorded yet. Point camera at objects to begin logging.")


# Initial render of logs table
render_logs_and_chart()


# ================= EXECUTION LOGIC =================
if input_mode == "Webcam (Real-Time Live)":
    # Feed control buttons
    col_btn1, col_btn2 = feed_col.columns([1, 1])
    with col_btn1:
        run_camera = st.checkbox("▶️ Start Live Webcam Stream", value=False)
    with col_btn2:
        st.caption("Press checkbox to activate local webcam stream.")

    if run_camera:
        # Open default webcam (0)
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            feed_col.error("⚠️ Unable to access webcam. Please check your camera permissions or use another video source.")
        else:
            prev_time = time.time()
            frame_counter = 0

            while run_camera:
                ret, frame = cap.read()
                if not ret:
                    feed_col.warning("Failed to grab camera frame.")
                    break

                # Object Detection via YOLO
                annotated_frame, detections = detector.process_frame(
                    frame=frame,
                    target_classes=selected_classes,
                    conf_threshold=conf_threshold,
                )

                # Database Logging with Cooldown
                if logging_enabled and detections:
                    for det in detections:
                        obj_cls = det["object_class"]
                        if detector.should_log(obj_cls, cooldown_seconds=cooldown_seconds):
                            db_manager.log_detection(
                                object_class=det["object_class"],
                                confidence=det["confidence"],
                                bbox_x=det["bbox_x"],
                                bbox_y=det["bbox_y"],
                                bbox_w=det["bbox_w"],
                                bbox_h=det["bbox_h"],
                            )

                # Calculate FPS
                current_time = time.time()
                fps = 1.0 / max(current_time - prev_time, 1e-5)
                prev_time = current_time

                # Convert OpenCV BGR to RGB for Streamlit display
                rgb_frame = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
                frame_placeholder.image(rgb_frame, channels="RGB", use_container_width=True)

                frame_counter += 1
                if frame_counter % 5 == 0:
                    fps_indicator.caption(f"⚡ Processing Speed: **{fps:.1f} FPS** | Objects in View: **{len(detections)}**")
                    render_logs_and_chart()

            cap.release()

elif input_mode == "Upload Video File":
    uploaded_video = feed_col.file_uploader("Upload a Video File", type=["mp4", "avi", "mov", "mkv"])
    if uploaded_video is not None:
        import tempfile
        tfile = tempfile.NamedTemporaryFile(delete=False)
        tfile.write(uploaded_video.read())
        cap = cv2.VideoCapture(tfile.name)

        start_btn = feed_col.button("🚀 Process Video Stream")
        if start_btn:
            frame_counter = 0
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break

                annotated_frame, detections = detector.process_frame(
                    frame=frame,
                    target_classes=selected_classes,
                    conf_threshold=conf_threshold,
                )

                if logging_enabled and detections:
                    for det in detections:
                        if detector.should_log(det["object_class"], cooldown_seconds=cooldown_seconds):
                            db_manager.log_detection(
                                object_class=det["object_class"],
                                confidence=det["confidence"],
                                bbox_x=det["bbox_x"],
                                bbox_y=det["bbox_y"],
                                bbox_w=det["bbox_w"],
                                bbox_h=det["bbox_h"],
                            )

                rgb_frame = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
                frame_placeholder.image(rgb_frame, channels="RGB", use_container_width=True)
                frame_counter += 1
                if frame_counter % 8 == 0:
                    render_logs_and_chart()

            cap.release()
            render_logs_and_chart()
            feed_col.success("Finished processing uploaded video.")

elif input_mode == "Upload Static Image":
    uploaded_image = feed_col.file_uploader("Upload an Image", type=["jpg", "jpeg", "png"])
    if uploaded_image is not None:
        pil_image = Image.open(uploaded_image)
        opencv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

        annotated_frame, detections = detector.process_frame(
            frame=opencv_image,
            target_classes=selected_classes,
            conf_threshold=conf_threshold,
        )

        if logging_enabled and detections:
            for det in detections:
                db_manager.log_detection(
                    object_class=det["object_class"],
                    confidence=det["confidence"],
                    bbox_x=det["bbox_x"],
                    bbox_y=det["bbox_y"],
                    bbox_w=det["bbox_w"],
                    bbox_h=det["bbox_h"],
                )

        rgb_frame = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
        frame_placeholder.image(rgb_frame, channels="RGB", use_container_width=True)
        feed_col.info(f"Detected **{len(detections)}** object(s) matching current criteria.")
        render_logs_and_chart()
