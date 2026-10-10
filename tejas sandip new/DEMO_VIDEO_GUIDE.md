# 🎥 1-2 Minute Video Demonstration Recording Guide

This guide provides the exact scene-by-scene script and instructions to record your demonstration video for **Assignment 5: Real-Time Object Detection & Logging Platform**.

---

## 🛠️ Recording Setup

1. **Screen Recorder**: Use **OBS Studio** (free), **Windows Game Bar** (`Win + G`), or **Clipchamp**.
2. **Resolution & Audio**: Set to 1080p (1920x1080), ensure microphone audio is clear.
3. **Screen Setup (Side-by-Side Recommended)**:
   - **Left Half of Screen**: Your web browser showing the **Streamlit Dashboard** (`http://localhost:8501`).
   - **Right Half of Screen**: **phpMyAdmin** (in XAMPP at `http://localhost/phpmyadmin`) or **MySQL Workbench** showing the `vision_platform.detection_logs` table.

---

## ⏱️ Video Demonstration Script (Total Time: ~90–110 Seconds)

### 🎬 Scene 1: Introduction (0:00 – 0:15)
- **Visual**: Show your Streamlit Dashboard open on the screen.
- **What to say**:
  > *"Hello everyone! In this video, I am demonstrating my project for Assignment 5: A Real-Time Object Detection and Logging Platform built using Python, OpenCV, Ultralytics YOLOv8, MySQL, and Streamlit."*

### 🎬 Scene 2: Architecture & Live Webcam Feed (0:15 – 0:45)
- **Visual**: In the sidebar, point to the filters (e.g. `person`, `cell phone`). Check **"Start Live Webcam Stream"**.
- **Action**: Hold up a phone or sit in front of the camera. The bounding box will appear around you ("Person 85%") and your phone ("Cell phone 82%").
- **What to say**:
  > *"The platform utilizes a modular architecture divided into `detector.py`, `database.py`, `ui.py`, and `main.py`. Here is the live webcam feed running at 30 FPS. Notice how YOLOv8 draws clean bounding boxes with confidence scores around me and the objects I hold up."*

### 🎬 Scene 3: Dynamic Filters & Sensitivity (0:45 – 1:05)
- **Visual**: In the sidebar, change the target class selection (e.g., remove `person` so only `cell phone` is detected, or adjust the confidence slider from 50% to 75%).
- **What to say**:
  > *"We have dynamic object configuration. I can filter specific classes such as person, cell phone, or bottle, and adjust the confidence threshold slider in real-time to eliminate false detections."*

### 🎬 Scene 4: Real-Time MySQL Verification (1:05 – 1:35)
- **Visual**: Point to the **"Live MySQL Event Logs"** table on the Streamlit dashboard updating with timestamps and coordinates. Then switch or look at **phpMyAdmin / MySQL Workbench**, click **Browse / Execute Query** on `detection_logs`, and show the newly inserted rows matching the video feed.
- **What to say**:
  > *"Now let's examine the MySQL integration. As objects appear, they are recorded into the `vision_platform` database. We have an integrated rate limiter to prevent database spamming. In phpMyAdmin, you can see the latest entries with log_id, timestamp, object_class, confidence, and bounding box coordinates matching the live feed."*

### 🎬 Scene 5: Wrap-up & Credentials Security (1:35 – 1:50)
- **Visual**: Show the project folder structure in VS Code, highlighting `.env.example`, `database_schema.sql`, and `requirements.txt`.
- **What to say**:
  > *"All sensitive database credentials are securely kept in a local `.env` file and excluded from version control using `.gitignore`. The complete code, documentation, schema, and article are uploaded to GitHub. Thank you!"*

---

## 📤 Submission Steps for the Video:
1. Stop recording.
2. Check the video length (must be between **1 to 2 minutes**).
3. Upload to:
   - **YouTube**: Set visibility to **Unlisted** (anyone with the link can view).
   - *OR* **Google Drive**: Right-click video file -> **Share** -> Set access to **"Anyone with the link can view"**.
4. Test opening the link in an Incognito/Private window to verify access.
5. Paste into the Assignment 5 Google Submission Form!
